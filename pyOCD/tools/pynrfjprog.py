#!/usr/bin/env python
"""
 mbed CMSIS-DAP debugger
 Copyright (c) 2006-2013 ARM Limited

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

import argparse, os, sys, logging, itertools
from struct import unpack
from StringIO import StringIO

try:
    from intelhex import IntelHex, bin2hex
    intelhex_available = True
except:
    intelhex_available = False

parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parentdir)

import pyOCD
from pyOCD.board import MbedBoard
from pyOCD.target.target_nrf51 import NVMC_CONFIG

UICR_CLENR0 = 0x10001000

LEVELS={'debug':logging.DEBUG,
        'info':logging.INFO,
        'warning':logging.WARNING,
        'error':logging.ERROR,
        'critical':logging.CRITICAL
        }

interface = None
board = None

supported_targets = pyOCD.target.TARGET.keys()
supported_targets.remove('cortex_m')    # No generic programming

debug_levels = LEVELS.keys()

def convert_to_number(val):
    try:
        ret_val = int(val,0)
    except Exception:
        raise argparse.ArgumentTypeError("'%s' is not a valid positive number" % val)
    return ret_val

def print_none(progress):
    pass

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
            sys.stdout.write("\n")


def print_progress_simple(progress):
    sp = print_progress_simple
    progress_str = "|==========Progress=========|"
    if not hasattr(sp, 'bars'):
        sp.bars = -1

    if progress == 0.0:
        if sp.bars < 0:
            sys.stdout.write(progress_str + "\n")
            sys.stdout.flush()
            sp.bars = 0

    if sp.bars >= 0:
        i = int(progress*len(progress_str))
        #print("Count: %i, i=%i, bars=%i, progress=%s" % ((i - sp.bars),i,sp.bars, progress))
        sys.stdout.write("#" * (i - sp.bars))
        sys.stdout.flush()
        sp.bars = i

    # Finish on 1.0
    if progress >= 1.0:
        if sp.bars > 0:
            sys.stdout.write("\nDone\n")
            sp.bars = -1

PROGRESS = {
    "normal" : print_progress,
    "noret" : print_progress_simple,
    "none" : print_none,
}
progress_choices = PROGRESS.keys()
progress_default = "normal"

parser = argparse.ArgumentParser(description='pynrfjprog utility')
parser.add_argument("-b", "--board", dest = "board_id", default = None, help="Connect to board by board id.  Use -l to list all connected boards.")
parser.add_argument("-l", "--list", action = "store_true", dest = "list_all", default = False, help = "List all connected boards.")
parser.add_argument("-d", "--debug", dest = "debug_level", choices = debug_levels, default = 'info', help = "Set the level of system logging output. Supported choices are: "+", ".join(debug_levels), metavar="LEVEL")
parser.add_argument("-t", "--target", default = "nrf51", dest = "target_override", choices=supported_targets, help = "Override target to debug.  Supported targets are: "+", ".join(supported_targets), metavar="TARGET")
parser.add_argument("-c", "--clockspeed", dest = "frequency", default = 1000, type=int, help = "Set the SWD clock frequency in kHz." )
group = parser.add_mutually_exclusive_group()
group.add_argument("-ce", "--chip_erase", action="store_true",help="Use chip erase when programming.")
group.add_argument("-se", "--sector_erase", action="store_true",help="Use sector erase when programming.")
parser.add_argument("-pr", "--progress", default=progress_default, choices=progress_choices, help = "Set how progress is displayed when programming." )
parser.add_argument("-fp", "--fast_program", action="store_true", help = "Use only the CRC of each page to determine if it already has the same data.")
parser.add_argument("--recover", action="store_true", default=False, help="Erases all user flash and disables the read back protection mechanism if enabled.")
parser.add_argument("-e", "--eraseall", action="store_true", default=False, help="Erases all user available program flash memory and the UICR page.")
parser.add_argument("--readuicr", default = None, help = "Reads the device UICR and stores it in the given path.")
parser.add_argument("-r", "--reset", action="store_true", help = "Performs a SysResetReq. Core will run after the operation.")
parser.add_argument("--memwr", type=convert_to_number, default = None, help = "Writes to memory with the help of the NVM Controller to the address provided with --val.")
parser.add_argument("--val", type=convert_to_number, default = None, help = "Value to write to address specified with --memwr.")
group = parser.add_mutually_exclusive_group()
group.add_argument("--program", default = None, help = "Programs the specified hex file into the device.")
group.add_argument("--programs", default = None, help = "Same as --program only designed for softdevices, implicitly does -e and -r before programming softdevice.")

def main():
    args = parser.parse_args()

    UICR_ADDRESS = 0x10001000

    # Set logging level
    level = LEVELS.get(args.debug_level, logging.NOTSET)
    logging.basicConfig(level=level)

    def ranges(i):
        for a, b in itertools.groupby(enumerate(i), lambda (x, y): y - x):
            b = list(b)
            yield b[0][1], b[-1][1]

    # Check frequency
    if args.frequency > 1000:
        print("Warning frequency %i KHz is too high" % args.frequency)
        args.frequency = 1000
        print("Setting frequency to %i" % args.frequency)

    # Memwr requires an integer
    if args.memwr is not None and args.val is None:
        print("Error: --memwr requires --val to be specified")
        exit(1)

    # Make sure required module is present
    if args.readuicr and not intelhex_available:
        print("IntelHex required for readuicr")
        exit(1)

    if args.list_all:
        MbedBoard.listConnectedBoards()
    else:
        board_selected = MbedBoard.chooseBoard(board_id = args.board_id, target_override = args.target_override, frequency = args.frequency * 1000)
        with board_selected as board:
            flash = board.flash
            transport = board.transport
            target = board.target

            # Boost speed with deferred transfers
            transport.setDeferredTransfer(True)

            # Write UICR
            if args.memwr is not None:
                target.writeMemory(NVMC_CONFIG, 1)
                target.writeMemory(args.memwr, args.val)
                target.writeMemory(NVMC_CONFIG, 0)

            # Read UICR
            if args.readuicr != None:
                uicr_size = flash.getPageInfo(UICR_ADDRESS).size
                data = bytearray(target.readBlockMemoryUnaligned8(UICR_ADDRESS, uicr_size))
                fake_file = StringIO(data)
                bin2hex(fake_file, args.readuicr, UICR_ADDRESS)

            # Erase everything to remove RBP
            if args.recover or args.eraseall:
                target.unlock()

            chip_erase = None
            if args.chip_erase:
                chip_erase = True
            elif args.sector_erase:
                chip_erase = False

            # Set file to program
            file_to_program = None
            if args.programs is not None:
                target.unlock()
                file_to_program = args.programs
            elif args.program is not None:
                file_to_program = args.program

            if file_to_program is not None:
                hex = IntelHex(file_to_program)
                addresses = hex.addresses()
                addresses.sort()

                flash_builder = flash.getFlashBuilder()

                highest_addr = 0
                data_list = list(ranges(addresses))
                for start, end in data_list:
                    size = end - start + 1
                    data = list(hex.tobinarray(start=start, size=size))
                    flash_builder.addData(start, data)
                    highest_addr = max(highest_addr, end)
                flash_builder.program(chip_erase=chip_erase, progress_cb=PROGRESS[args.progress], fast_verify=args.fast_program)

                # Set lock settings
                if args.programs is not None:
                    # Determine size to lock
                    page_size = flash.getPageInfo(highest_addr).size
                    size_to_lock = ((highest_addr + page_size) // page_size) * page_size
                    assert size_to_lock > highest_addr
                    assert size_to_lock % page_size == 0
                    logging.debug("Locking first %i bytes of flash" % size_to_lock)

                    # Write lock value to UICR
                    target.writeMemory(NVMC_CONFIG, 1)
                    target.writeMemory(UICR_CLENR0, size_to_lock)
                    target.writeMemory(NVMC_CONFIG, 0)

                    # Reset so the lock settings take effect
                    target.resetStopOnReset()

            # Reset
            if args.reset:
                target.resetStopOnReset()

if __name__ == '__main__':
    main()
