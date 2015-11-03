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

from pyOCD.transport.link import Link
import logging
from time import sleep

# !! This value are A[2:3] and not A[3:2]
DP_REG = {'IDCODE': Link.REG.DP_0x0,
          'ABORT': Link.REG.DP_0x0,
          'CTRL_STAT': Link.REG.DP_0x4,
          'SELECT': Link.REG.DP_0x8
          }
AP_REG = {'CSW' : 0x00,
          'TAR' : 0x04,
          'DRW' : 0x0C,
          'IDR' : 0xFC
          }

IDCODE = 0 << 2
AP_ACC = 1 << 0
DP_ACC = 0 << 0
READ = 1 << 1
WRITE = 0 << 1
VALUE_MATCH = 1 << 4
MATCH_MASK = 1 << 5

APBANKSEL = 0x000000f0

# AP Control and Status Word definitions
CSW_SIZE     =  0x00000007
CSW_SIZE8    =  0x00000000
CSW_SIZE16   =  0x00000001
CSW_SIZE32   =  0x00000002
CSW_ADDRINC  =  0x00000030
CSW_NADDRINC =  0x00000000
CSW_SADDRINC =  0x00000010
CSW_PADDRINC =  0x00000020
CSW_DBGSTAT  =  0x00000040
CSW_TINPROG  =  0x00000080
CSW_HPROT    =  0x02000000
CSW_MSTRTYPE =  0x20000000
CSW_MSTRCORE =  0x00000000
CSW_MSTRDBG  =  0x20000000
CSW_RESERVED =  0x01000000

CSW_VALUE = (CSW_RESERVED | CSW_MSTRDBG | CSW_HPROT | CSW_DBGSTAT | CSW_SADDRINC)

TRANSFER_SIZE = {8: CSW_SIZE8,
                 16: CSW_SIZE16,
                 32: CSW_SIZE32
                 }

COMMANDS_PER_DAP_TRANSFER = 12


class CMSIS_DAP(object):
    """
    This class implements the CMSIS-DAP protocol
    """
    def __init__(self, link):
        self.link = link
        self.csw = -1
        self.dp_select = -1

    def writeMem(self, addr, data, transfer_size=32):
        self.writeAP(AP_REG['CSW'], CSW_VALUE | TRANSFER_SIZE[transfer_size])
        if transfer_size == 8:
            data = data << ((addr & 0x03) << 3)
        elif transfer_size == 16:
            data = data << ((addr & 0x02) << 3)

        try:
            reg = Link.REG.ap_addr_to_reg(WRITE | AP_ACC | AP_REG['TAR'])
            self.link.write_reg(reg, addr)
            reg = Link.REG.ap_addr_to_reg(WRITE | AP_ACC | AP_REG['DRW'])
            self.link.write_reg(reg, data)
        except Link.Error:
            self._handle_error()
            raise

    def readMem(self, addr, transfer_size=32, mode=Link.MODE.NOW):
        res = None
        try:
            if mode in (Link.MODE.START, Link.MODE.NOW):
                self.writeAP(AP_REG['CSW'], CSW_VALUE | TRANSFER_SIZE[transfer_size])
                reg = Link.REG.ap_addr_to_reg(WRITE | AP_ACC | AP_REG['TAR'])
                self.link.write_reg(reg, addr)
                reg = Link.REG.ap_addr_to_reg(READ | AP_ACC | AP_REG['DRW'])
                self.link.read_reg(reg, mode=Link.MODE.START)

            if mode in (Link.MODE.NOW, Link.MODE.END):
                reg = Link.REG.ap_addr_to_reg(READ | AP_ACC | AP_REG['DRW'])
                res = self.link.read_reg(reg, mode=Link.MODE.END)

                if transfer_size == 8:
                    res = (res >> ((addr & 0x03) << 3) & 0xff)
                elif transfer_size == 16:
                    res = (res >> ((addr & 0x02) << 3) & 0xffff)
        except Link.Error:
            self._handle_error()
            raise

        return res

    # write aligned word ("data" are words)
    def writeBlock32(self, addr, data):
        # put address in TAR
        self.writeAP(AP_REG['CSW'], CSW_VALUE | CSW_SIZE32)
        self.writeAP(AP_REG['TAR'], addr)
        try:
            reg = Link.REG.ap_addr_to_reg(WRITE | AP_ACC | AP_REG['DRW'])
            self.link.reg_write_repeat(len(data), reg, data)
        except Link.Error:
            self._handle_error()
            raise

    # read aligned word (the size is in words)
    def readBlock32(self, addr, size):
        # put address in TAR
        self.writeAP(AP_REG['CSW'], CSW_VALUE | CSW_SIZE32)
        self.writeAP(AP_REG['TAR'], addr)
        try:
            reg = Link.REG.ap_addr_to_reg(READ | AP_ACC | AP_REG['DRW'])
            resp = self.link.reg_read_repeat(size, reg)
        except Link.Error:
            self._handle_error()
            raise
        return resp

    def readDP(self, addr, mode=Link.MODE.NOW):
        assert addr in Link.REG
        res = None

        try:
            if mode in (Link.MODE.START, Link.MODE.NOW):
                self.link.read_reg(addr, mode=Link.MODE.START)

            if mode in (Link.MODE.NOW, Link.MODE.END):
                res = self.link.read_reg(addr, mode=Link.MODE.END)

        except Link.Error:
            self._handle_error()
            raise

        return res

    def writeDP(self, addr, data):
        assert addr in Link.REG
        if addr == DP_REG['SELECT']:
            if data == self.dp_select:
                return
            self.dp_select = data

        try:
            self.link.write_reg(addr, data)
        except Link.Error:
            self._handle_error()
            raise
        return True

    def writeAP(self, addr, data):
        assert type(addr) in (int, long)
        ap_sel = addr & 0xff000000
        bank_sel = addr & APBANKSEL
        self.writeDP(DP_REG['SELECT'], ap_sel | bank_sel)

        if addr == AP_REG['CSW']:
            if data == self.csw:
                return
            self.csw = data

        ap_reg = Link.REG.ap_addr_to_reg(WRITE | AP_ACC | (addr & 0x0c))
        try:
            self.link.write_reg(ap_reg, data)

        except Link.Error:
            self._handle_error()
            raise

        return True

    def readAP(self, addr, mode=Link.MODE.NOW):
        assert type(addr) in (int, long)
        res = None
        ap_reg = Link.REG.ap_addr_to_reg(READ | AP_ACC | (addr & 0x0c))

        try:
            if mode in (Link.MODE.START, Link.MODE.NOW):
                ap_sel = addr & 0xff000000
                bank_sel = addr & APBANKSEL

                self.writeDP(DP_REG['SELECT'], ap_sel | bank_sel)
                self.link.read_reg(ap_reg, mode=Link.MODE.START)

            if mode in (Link.MODE.NOW, Link.MODE.END):
                res = self.link.read_reg(ap_reg, mode=Link.MODE.END)
        except Link.Error:
            self._handle_error()
            raise

        return res

    def _handle_error(self):
        # Invalidate cached registers
        self.csw = -1
        self.dp_select = -1
