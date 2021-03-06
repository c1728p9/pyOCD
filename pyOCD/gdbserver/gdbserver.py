"""
 mbed CMSIS-DAP debugger
 Copyright (c) 2006-2015 ARM Limited

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
"""

import logging, threading, socket
from ..target.target import (TARGET_HALTED, BREAKPOINT_HW, BREAKPOINT_SW,
    WATCHPOINT_READ, WATCHPOINT_WRITE, WATCHPOINT_READ_WRITE)
from ..transport import TransferError
from ..utility.conversion import hexToByteList, hexEncode, hexDecode
from struct import unpack
from time import sleep, time
import sys
from gdb_socket import GDBSocket
from gdb_websocket import GDBWebSocket
from syscall import GDBSyscallIOHandler
from ..target import semihost
import traceback
import Queue

CTRL_C = '\x03'

# Logging options. Set to True to enable.
LOG_MEM = False # Log memory accesses.
LOG_ACK = False # Log ack or nak.
LOG_PACKETS = False # Log all packets sent and received.

def checksum(data):
    return "%02x" % (sum([ord(c) for c in data]) % 256)

## @brief Exception used to signal the GDB server connection closed.
class ConnectionClosedException(Exception):
    pass

## @brief Packet I/O thread.
#
# This class is a thread used by the GDBServer class to perform all RSP packet I/O. It
# handles verifying checksums, acking, and receiving Ctrl-C interrupts. There is a queue
# for received packets. The interface to this queue is the receive() method. The send()
# method writes outgoing packets to the socket immediately.
class GDBServerPacketIOThread(threading.Thread):
    def __init__(self, abstract_socket):
        super(GDBServerPacketIOThread, self).__init__(name="gdb-packet-thread")
        self._abstract_socket = abstract_socket
        self._receive_queue = Queue.Queue()
        self._shutdown_event = threading.Event()
        self.interrupt_event = threading.Event()
        self.send_acks = True
        self._clear_send_acks = False
        self._buffer = ''
        self._expecting_ack = False
        self.drop_reply = False
        self._last_packet = ''
        self._closed = False
        self.setDaemon(True)
        self.start()

    def set_send_acks(self, ack):
        if ack:
            self.send_acks = True
        else:
            self._clear_send_acks = True

    def stop(self):
        self._shutdown_event.set()

    def send(self, packet):
        if self._closed or not packet:
            return
        if not self.drop_reply:
            self._last_packet = packet
            self._write_packet(packet)
        else:
            self.drop_reply = False
            logging.debug("GDB dropped reply %s", packet)

    def receive(self, block=True):
        if self._closed:
            raise ConnectionClosedException()
        while True:
            try:
                # If block is false, we'll get an Empty exception immediately if there
                # are no packets in the queue. Same if block is true and it times out
                # waiting on an empty queue.
                return self._receive_queue.get(block, 0.1)
            except Queue.Empty:
                # Only exit the loop if block is false or connection closed.
                if not block:
                    return None
                if self._closed:
                    raise ConnectionClosedException()

    def run(self):
        self._abstract_socket.setTimeout(0.01)

        while not self._shutdown_event.is_set():
            try:
                data = self._abstract_socket.read()

                # Handle closed connection
                if len(data) == 0:
                    logging.debug("GDB packet thread: other side closed connection")
                    self._closed = True
                    break

                if LOG_PACKETS:
                    logging.debug('-->>>>>>>>>>>> GDB read %d bytes: %s', len(data), data)

                self._buffer += data
            except socket.error:
                pass

            if self._shutdown_event.is_set():
                break

            self._process_data()

        logging.debug("GDB packet thread stopping")

    def _write_packet(self, packet):
        if LOG_PACKETS:
            logging.debug('--<<<<<<<<<<<< GDB send %d bytes: %s', len(packet), packet)

        # Make sure the entire packet is sent.
        remaining = len(packet)
        while remaining:
            written = self._abstract_socket.write(packet)
            remaining -= written
            if remaining:
                packet = packet[written:]

        if self.send_acks:
            self._expecting_ack = True

    def _check_expected_ack(self):
        # Handle expected ack.
        c = self._buffer[0]
        if c in ('+', '-'):
            self._buffer = self._buffer[1:]
            if LOG_ACK:
                logging.debug('got ack: %s', c)
            if c == '-':
                # Handle nack from gdb
                self._write_packet(self._last_packet)
                return

            # Handle disabling of acks.
            if self._clear_send_acks:
                self.send_acks = False
                self._clear_send_acks = False
        else:
            logging.debug("GDB: expected n/ack but got '%s'", c)

    def _process_data(self):
        # Process all incoming data until there are no more complete packets.
        while len(self._buffer):
            if self._expecting_ack:
                self._expecting_ack = False
                self._check_expected_ack()

            # Check for a ctrl-c.
            if len(self._buffer) and self._buffer[0] == CTRL_C:
                self.interrupt_event.set()
                self._buffer = self._buffer[1:]

            try:
                # Look for complete packet and extract from buffer.
                pkt_begin = self._buffer.index("$")
                pkt_end = self._buffer.index("#") + 2
                if pkt_begin >= 0 and pkt_end < len(self._buffer):
                    pkt = self._buffer[pkt_begin:pkt_end+1]
                    self._buffer = self._buffer[pkt_end+1:]
                    self._handling_incoming_packet(pkt)
                else:
                    break
            except ValueError:
                # No complete packet received yet.
                break

    def _handling_incoming_packet(self, packet):
        # Compute checksum
        data, cksum = packet[1:].split('#')
        computedCksum = checksum(data)
        goodPacket = (computedCksum.lower() == cksum.lower())

        if self.send_acks:
            ack = '+' if goodPacket else '-'
            self._abstract_socket.write(ack)
            if LOG_ACK:
                logging.debug(ack)

        if goodPacket:
            self._receive_queue.put(packet)

class GDBServer(threading.Thread):
    """
    This class start a GDB server listening a gdb connection on a specific port.
    It implements the RSP (Remote Serial Protocol).
    """
    def __init__(self, board, port_urlWSS, options = {}):
        threading.Thread.__init__(self)
        self.board = board
        self.target = board.target
        self.flash = board.flash
        self.abstract_socket = None
        self.wss_server = None
        self.port = 0
        if isinstance(port_urlWSS, str) == True:
            self.wss_server = port_urlWSS
        else:
            self.port = port_urlWSS
        self.break_at_hardfault = bool(options.get('break_at_hardfault', True))
        self.board.target.setVectorCatchFault(self.break_at_hardfault)
        self.break_on_reset = options.get('break_on_reset', False)
        self.board.target.setVectorCatchReset(self.break_on_reset)
        self.step_into_interrupt = options.get('step_into_interrupt', False)
        self.persist = options.get('persist', False)
        self.soft_bkpt_as_hard = options.get('soft_bkpt_as_hard', False)
        self.chip_erase = options.get('chip_erase', None)
        self.hide_programming_progress = options.get('hide_programming_progress', False)
        self.fast_program = options.get('fast_program', False)
        self.enable_semihosting = options.get('enable_semihosting', False)
        self.telnet_port = options.get('telnet_port', 4444)
        self.semihost_use_syscalls = options.get('semihost_use_syscalls', False)
        self.server_listening_callback = options.get('server_listening_callback', None)
        self.packet_size = 2048
        self.packet_io = None
        self.gdb_features = []
        self.flashBuilder = None
        self.lock = threading.Lock()
        self.shutdown_event = threading.Event()
        self.detach_event = threading.Event()
        if self.wss_server == None:
            self.abstract_socket = GDBSocket(self.port, self.packet_size)
        else:
            self.abstract_socket = GDBWebSocket(self.wss_server)

        # Init semihosting and telnet console.
        if self.semihost_use_syscalls:
            semihost_io_handler = GDBSyscallIOHandler(self)
        else:
            # Use internal IO handler.
            semihost_io_handler = semihost.InternalSemihostIOHandler()
        self.telnet_console = semihost.TelnetSemihostIOHandler(self.telnet_port)
        self.semihost = semihost.SemihostAgent(self.target, io_handler=semihost_io_handler, console=self.telnet_console)

        self.setDaemon(True)
        self.start()

    def restart(self):
        if self.isAlive():
            self.detach_event.set()

    def stop(self):
        if self.isAlive():
            self.shutdown_event.set()
            while self.isAlive():
                pass
            logging.info("GDB server thread killed")
        self.board.uninit()

    def setBoard(self, board, stop = True):
        self.lock.acquire()
        if stop:
            self.restart()
        self.board = board
        self.target = board.target
        self.flash = board.flash
        self.lock.release()
        return

    def _cleanup(self):
        logging.debug("GDB server cleaning up")
        if self.packet_io:
            self.packet_io.stop()
            self.packet_io = None
        if self.semihost:
            self.semihost.cleanup()
            self.semihost = None
        if self.telnet_console:
            self.telnet_console.stop()
            self.telnet_console = None

    def run(self):
        while True:
            logging.info('GDB server started at port:%d', self.port)

            # Inform callback that the server is running.
            if self.server_listening_callback:
                self.server_listening_callback(self)

            self.shutdown_event.clear()
            self.detach_event.clear()

            while not self.shutdown_event.isSet() and not self.detach_event.isSet():
                connected = self.abstract_socket.connect()
                if connected != None:
                    self.packet_io = GDBServerPacketIOThread(self.abstract_socket)
                    break

            if self.shutdown_event.isSet():
                self._cleanup()
                return

            if self.detach_event.isSet():
                continue

            logging.info("One client connected!")

            while True:

                if self.shutdown_event.isSet():
                    self._cleanup()
                    return

                if self.detach_event.isSet():
                    break

                if self.packet_io.interrupt_event.isSet():
                    logging.debug("Got unexpected ctrl-c, ignoring")
                    self.packet_io.interrupt_event.clear()

                # read command
                try:
                    packet = self.packet_io.receive()
                except ConnectionClosedException:
                    break

                if self.shutdown_event.isSet():
                    self._cleanup()
                    return

                if self.detach_event.isSet():
                    break

                self.lock.acquire()

                if len(packet) != 0:
                    # decode and prepare resp
                    resp, detach = self.handleMsg(packet)

                    if resp is not None:
                        # send resp
                        self.packet_io.send(resp)

                    if detach:
                        self.abstract_socket.close()
                        self.packet_io.stop()
                        self.packet_io = None
                        self.lock.release()
                        if self.persist:
                            break
                        else:
                            self._cleanup()
                            return

                self.lock.release()

    def handleMsg(self, msg):
        if msg[0] != '$':
            logging.debug('msg ignored: first char != $')
            return None, 0

        # query command
        if msg[1] == '?':
            return self.createRSPPacket(self.target.getTResponse()), 0

        # we don't send immediately the response for C and S commands
        elif msg[1] == 'C' or msg[1] == 'c':
            return self.resume()

        elif msg[1] == 'D':
            return self.detach(msg[1:]), 1

        elif msg[1] == 'g':
            return self.getRegisters(), 0

        elif msg[1] == 'G':
            return self.setRegisters(msg[2:]), 0

        elif msg[1] == 'H':
            return self.createRSPPacket(''), 0

        elif msg[1] == 'k':
            return self.kill(), 1

        elif msg[1] == 'm':
            return self.getMemory(msg[2:]), 0

        elif msg[1] == 'M': # write memory with hex data
            return self.writeMemoryHex(msg[2:]), 0

        elif msg[1] == 'p':
            return self.readRegister(msg[2:]), 0

        elif msg[1] == 'P':
            return self.writeRegister(msg[2:]), 0

        elif msg[1] == 'q':
            return self.handleQuery(msg[2:]), 0

        elif msg[1] == 'Q':
            return self.handleGeneralSet(msg[2:]), 0

        elif msg[1] == 'S' or msg[1] == 's':
            return self.step()

        elif msg[1] == 'v':
            return self.flashOp(msg[2:]), 0

        elif msg[1] == 'X': # write memory with binary data
            return self.writeMemory(msg[2:]), 0

        elif msg[1] == 'Z' or msg[1] == 'z':
            return self.breakpoint(msg[1:]), 0

        else:
            logging.error("Unknown RSP packet: %s", msg)
            return self.createRSPPacket(""), 0

    def detach(self, data):
        logging.info("Client detached")
        resp = "OK"
        return self.createRSPPacket(resp)

    def kill(self):
        logging.debug("GDB kill")
        # Keep target halted and leave vector catches if in persistent mode.
        if not self.persist:
            self.board.target.setVectorCatchFault(False)
            self.board.target.setVectorCatchReset(False)
            self.board.target.resume()
        return self.createRSPPacket("")

    def breakpoint(self, data):
        # handle breakpoint/watchpoint commands
        split = data.split('#')[0].split(',')
        addr = int(split[1], 16)
        logging.debug("GDB breakpoint %s%d @ %x" % (data[0], int(data[1]), addr))

        # handle software breakpoint Z0/z0
        if data[1] == '0' and not self.soft_bkpt_as_hard:
            if data[0] == 'Z':
                if not self.target.setBreakpoint(addr, BREAKPOINT_SW):
                    return self.createRSPPacket('E01') #EPERM
            else:
                self.target.removeBreakpoint(addr)
            return self.createRSPPacket("OK")

        # handle hardware breakpoint Z1/z1
        if data[1] == '1' or (self.soft_bkpt_as_hard and data[1] == '0'):
            if data[0] == 'Z':
                if self.target.setBreakpoint(addr, BREAKPOINT_HW) == False:
                    return self.createRSPPacket('E01') #EPERM
            else:
                self.target.removeBreakpoint(addr)
            return self.createRSPPacket("OK")

        # handle hardware watchpoint Z2/z2/Z3/z3/Z4/z4
        if data[1] == '2':
            # Write-only watch
            watchpoint_type = WATCHPOINT_WRITE
        elif data[1] == '3':
            # Read-only watch
            watchpoint_type = WATCHPOINT_READ
        elif data[1] == '4':
            # Read-Write watch
            watchpoint_type = WATCHPOINT_READ_WRITE
        else:
            return self.createRSPPacket('E01') #EPERM

        size = int(split[2], 16)
        if data[0] == 'Z':
            if self.target.setWatchpoint(addr, size, watchpoint_type) == False:
                return self.createRSPPacket('E01') #EPERM
        else:
            self.target.removeWatchpoint(addr, size, watchpoint_type)
        return self.createRSPPacket("OK")

    def resume(self):
        self.target.resume()
        logging.debug("target resumed")

        val = ''

        while True:
            if self.shutdown_event.isSet():
                self.packet_io.interrupt_event.clear()
                return self.createRSPPacket(val), 0

            # Wait for a ctrl-c to be received.
            if self.packet_io.interrupt_event.wait(0.01):
                logging.debug("receive CTRL-C")
                self.packet_io.interrupt_event.clear()
                self.target.halt()
                val = self.target.getTResponse(True)
                break

            try:
                if self.target.getState() == TARGET_HALTED:
                    # Handle semihosting
                    if self.enable_semihosting:
                        was_semihost = self.semihost.check_and_handle_semihost_request()

                        if was_semihost:
                            self.target.resume()
                            continue

                    logging.debug("state halted")
                    val = self.target.getTResponse()
                    break
            except Exception as e:
                try:
                    self.target.halt()
                except:
                    pass
                traceback.print_exc()
                logging.debug('Target is unavailable temporarily.')
                val = 'S%02x' % self.target.getSignalValue()
                break

        return self.createRSPPacket(val), 0

    def step(self):
        logging.debug("GDB step")
        self.target.step(not self.step_into_interrupt)
        return self.createRSPPacket(self.target.getTResponse()), 0

    def halt(self):
        self.target.halt()
        return self.createRSPPacket(self.target.getTResponse()), 0

    def flashOp(self, data):
        ops = data.split(':')[0]
        logging.debug("flash op: %s", ops)

        if ops == 'FlashErase':
            return self.createRSPPacket("OK")

        elif ops == 'FlashWrite':
            write_addr = int(data.split(':')[1], 16)
            logging.debug("flash write addr: 0x%x", write_addr)
            # search for second ':' (beginning of data encoded in the message)
            second_colon = 0
            idx_begin = 0
            while second_colon != 2:
                if data[idx_begin] == ':':
                    second_colon += 1
                idx_begin += 1

            # Get flash builder if there isn't one already
            if self.flashBuilder == None:
                self.flashBuilder = self.flash.getFlashBuilder()

            # Add data to flash builder
            self.flashBuilder.addData(write_addr, self.unescape(data[idx_begin:len(data) - 3]))


            return self.createRSPPacket("OK")

        # we need to flash everything
        elif 'FlashDone' in ops :

            def print_progress(progress):
                # Reset state on 0.0
                if progress == 0.0:
                    print_progress.done = False

                # print progress bar
                if not print_progress.done:
                    sys.stdout.write('\r')
                    i = int(progress*20.0)
                    sys.stdout.write("[%-20s] %3d%%" % ('='*i, round(progress * 100)))
                    sys.stdout.flush()

                # Finish on 1.0
                if progress >= 1.0:
                    if not print_progress.done:
                        print_progress.done = True
                        sys.stdout.write("\r\n")

            if self.hide_programming_progress:
                progress_cb = None
            else:
                 progress_cb = print_progress

            self.flashBuilder.program(chip_erase = self.chip_erase, progress_cb=progress_cb, fast_verify=self.fast_program)

            # Set flash builder to None so that on the next flash command a new
            # object is used.
            self.flashBuilder = None

            return self.createRSPPacket("OK")

        elif 'Cont' in ops:
            if 'Cont?' in ops:
                return self.createRSPPacket("vCont;c;s;t")

        return None

    def unescape(self, data):
        data_idx = 0

        # unpack the data into binary array
        str_unpack = str(len(data)) + 'B'
        data = unpack(str_unpack, data)
        data = list(data)

        # check for escaped characters
        while data_idx < len(data):
            if data[data_idx] == 0x7d:
                data.pop(data_idx)
                data[data_idx] = data[data_idx] ^ 0x20
            data_idx += 1

        return data


    def getMemory(self, data):
        split = data.split(',')
        addr = int(split[0], 16)
        length = split[1].split('#')[0]
        length = int(length,16)

        if LOG_MEM:
            logging.debug("GDB getMem: addr=%x len=%x", addr, length)

        try:
            val = ''
            mem = self.target.readBlockMemoryUnaligned8(addr, length)
            # Flush so an exception is thrown now if invalid memory was accesses
            self.target.flush()
            for x in mem:
                if x >= 0x10:
                    val += hex(x)[2:4]
                else:
                    val += '0' + hex(x)[2:3]
        except TransferError:
            logging.debug("getMemory failed at 0x%x" % addr)
            val = 'E01' #EPERM
        return self.createRSPPacket(val)

    def writeMemoryHex(self, data):
        split = data.split(',')
        addr = int(split[0], 16)

        split = split[1].split(':')
        length = int(split[0], 16)

        split = split[1].split('#')
        data = hexToByteList(split[0])

        if LOG_MEM:
            logging.debug("GDB writeMemHex: addr=%x len=%x", addr, length)

        try:
            if length > 0:
                self.target.writeBlockMemoryUnaligned8(addr, data)
                # Flush so an exception is thrown now if invalid memory was accessed
                self.target.flush()
            resp = "OK"
        except TransferError:
            logging.debug("writeMemory failed at 0x%x" % addr)
            resp = 'E01' #EPERM

        return self.createRSPPacket(resp)

    def writeMemory(self, data):
        split = data.split(',')
        addr = int(split[0], 16)
        length = int(split[1].split(':')[0], 16)

        if LOG_MEM:
            logging.debug("GDB writeMem: addr=%x len=%x", addr, length)

        idx_begin = 0
        for i in range(len(data)):
            if data[i] == ':':
                idx_begin += 1
                break
            idx_begin += 1

        data = data[idx_begin:len(data) - 3]
        data = self.unescape(data)

        try:
            if length > 0:
                self.target.writeBlockMemoryUnaligned8(addr, data)
                # Flush so an exception is thrown now if invalid memory was accessed
                self.target.flush()
            resp = "OK"
        except TransferError:
            logging.debug("writeMemory failed at 0x%x" % addr)
            resp = 'E01' #EPERM

        return self.createRSPPacket(resp)

    def readRegister(self, which):
        return self.createRSPPacket(self.target.gdbGetRegister(which))

    def writeRegister(self, data):
        reg = int(data.split('=')[0], 16)
        val = data.split('=')[1].split('#')[0]
        self.target.setRegister(reg, val)
        return self.createRSPPacket("OK")

    def getRegisters(self):
        return self.createRSPPacket(self.target.getRegisterContext())

    def setRegisters(self, data):
        self.target.setRegisterContext(data)
        return self.createRSPPacket("OK")

    def handleQuery(self, msg):
        query = msg.split(':')
        logging.debug('GDB received query: %s', query)

        if query is None:
            logging.error('GDB received query packet malformed')
            return None

        if query[0] == 'Supported':
            # Save features sent by gdb.
            self.gdb_features = query[1].split(';')

            # Build our list of features.
            features = ['qXfer:features:read+', 'QStartNoAckMode+']
            features.append('PacketSize=' + hex(self.packet_size)[2:])
            if self.target.getMemoryMapXML() is not None:
                features.append('qXfer:memory-map:read+')
            resp = ';'.join(features)
            return self.createRSPPacket(resp)

        elif query[0] == 'Xfer':

            if query[1] == 'features' and query[2] == 'read' and \
               query[3] == 'target.xml':
                data = query[4].split(',')
                resp = self.handleQueryXML('read_feature', int(data[0], 16), int(data[1].split('#')[0], 16))
                return self.createRSPPacket(resp)

            elif query[1] == 'memory-map' and query[2] == 'read':
                data = query[4].split(',')
                resp = self.handleQueryXML('memory_map', int(data[0], 16), int(data[1].split('#')[0], 16))
                return self.createRSPPacket(resp)

            else:
                return None

        elif query[0] == 'C#b4':
            return self.createRSPPacket("")

        elif query[0].find('Attached') != -1:
            return self.createRSPPacket("1")

        elif query[0].find('TStatus') != -1:
            return self.createRSPPacket("")

        elif query[0].find('Tf') != -1:
            return self.createRSPPacket("")

        elif 'Offsets' in query[0]:
            resp = "Text=0;Data=0;Bss=0"
            return self.createRSPPacket(resp)

        elif 'Symbol' in query[0]:
            resp = "OK"
            return self.createRSPPacket(resp)

        elif query[0].startswith('Rcmd,'):
            cmd = hexDecode(query[0][5:].split('#')[0])
            return self.handleRemoteCommand(cmd)

        else:
            return self.createRSPPacket("")

    # TODO rewrite the remote command handler
    def handleRemoteCommand(self, cmd):
        logging.debug('Remote command: %s', cmd)

        safecmd = {
            'reset' : ['Reset target', 0x1],
            'halt'  : ['Halt target', 0x2],
            'resume': ['Resume target', 0x4],
            'help'  : ['Display this help', 0x80],
            'reg'   : ['Show registers', 0],
            'init'  : ['Init reset sequence', 0]
        }
        resultMask = 0x00
        resp = 'OK'
        if cmd == 'help':
            resp = ''
            for k,v in safecmd.items():
                resp += '%s\t%s\n' % (k,v[0])
            resp = hexEncode(resp)
        elif cmd.startswith('arm semihosting'):
            self.enable_semihosting = 'enable' in cmd
            logging.info("Semihosting %s", ('enabled' if self.enable_semihosting else 'disabled'))
        else:
            cmdList = cmd.split(' ')
            #check whether all the cmds is valid cmd for monitor
            for cmd_sub in cmdList:
                if not cmd_sub in safecmd:
                    #error cmd for monitor
                    logging.warning("Invalid mon command '%s'", cmd)
                    resp = 'Invalid Command: "%s"\n' % cmd
                    resp = hexEncode(resp)
                    return self.createRSPPacket(resp)
                else:
                    resultMask = resultMask | safecmd[cmd_sub][1]
            #10000001 for help reset, so output reset cmd help information
            if resultMask == 0x81:
                resp = 'Reset the target\n'
                resp = hexEncode(resp)
            #10000010 for help halt, so output halt cmd help information
            elif resultMask == 0x82:
                resp = 'Halt the target\n'
                resp = hexEncode(resp)
            #10000100 for help resume, so output resume cmd help information
            elif resultMask == 0x84:
                resp = 'Resume the target\n'
                resp = hexEncode(resp)
            #11 for reset halt cmd, so launch self.target.resetStopOnReset()
            elif resultMask == 0x3:
                self.target.resetStopOnReset()
            #111 for reset halt resume cmd, so launch self.target.resetStopOnReset() and self.target.resume()
            elif resultMask == 0x7:
                self.target.resetStopOnReset()
                self.target.resume()
            elif resultMask == 0x1:
                self.target.reset()
            elif resultMask == 0x2:
                self.target.halt()

            if self.target.getState() != TARGET_HALTED:
                logging.error("Remote command left target running!")
                logging.error("Forcing target to halt")
                self.target.halt()

        return self.createRSPPacket(resp)

    def handleGeneralSet(self, msg):
        logging.debug("GDB general set: %s", msg)
        feature = msg.split('#')[0]

        if feature == 'StartNoAckMode':
            # Disable acks after the reply and ack.
            self.packet_io.set_send_acks(False)
            return self.createRSPPacket("OK")
        else:
            return self.createRSPPacket("")

    def handleQueryXML(self, query, offset, size):
        logging.debug('GDB query %s: offset: %s, size: %s', query, offset, size)
        xml = ''
        if query == 'memory_map':
            xml = self.target.getMemoryMapXML()
        elif query == 'read_feature':
            xml = self.target.getTargetXML()

        size_xml = len(xml)

        prefix = 'm'

        if offset > size_xml:
            logging.error('GDB: offset target.xml > size!')
            return

        if size > (self.packet_size - 4):
            size = self.packet_size - 4

        nbBytesAvailable = size_xml - offset

        if size > nbBytesAvailable:
            prefix = 'l'
            size = nbBytesAvailable

        resp = prefix + xml[offset:offset + size]

        return resp


    def createRSPPacket(self, data):
        resp = '$' + data + '#' + checksum(data)
        return resp

    def syscall(self, op):
        logging.debug("GDB server syscall: %s", op)
        request = self.createRSPPacket('F' + op)
        self.packet_io.send(request)

        while not self.packet_io.interrupt_event.is_set():
            # Read a packet.
            packet = self.packet_io.receive(False)
            if packet is None:
                sleep(0.1)
                continue

            # Check for file I/O response.
            if packet[0] == '$' and packet[1] == 'F':
                logging.debug("Syscall: got syscall response " + packet)
                args = packet[2:packet.index('#')].split(',')
                result = int(args[0], base=16)
                errno = int(args[1], base=16) if len(args) > 1 else 0
                ctrl_c = args[2] if len(args) > 2 else ''
                if ctrl_c == 'C':
                    self.packet_io.interrupt_event.set()
                    self.packet_io.drop_reply = True
                return result, errno

            # decode and prepare resp
            resp, detach = self.handleMsg(packet)

            if resp is not None:
                # send resp
                self.packet_io.send(resp)

            if detach:
                self.detach_event.set()
                logging.warning("GDB server received detach request while waiting for file I/O completion")
                break

        return -1, 0

