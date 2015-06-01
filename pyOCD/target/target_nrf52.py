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

from cortex_m import CortexM, DHCSR, DBGKEY, C_DEBUGEN, C_MASKINTS, C_STEP, DEMCR, VC_CORERESET, NVIC_AIRCR, NVIC_AIRCR_VECTKEY, NVIC_AIRCR_SYSRESETREQ
from .memory_map import (FlashRegion, RamRegion, MemoryMap)
from pyOCD.target.target import TARGET_RUNNING, TARGET_HALTED
import logging

# NRF52 specific registers
RESET = 0x40000544
RESET_ENABLE = (1 << 0)

NVMC_READY      = 0x4001E400
NVMC_CONFIG     = 0x4001E504
NVMC_ERASEPAGE  = 0x4001E508
NVMC_ERASEALL   = 0x4001E50C
NVMC_ERASEUIR   = 0x4001E514

class NRF52(CortexM):

    memoryMap = MemoryMap(
        FlashRegion(    start=0x0,         length=0x80000,      blocksize=0x1000, isBootMemory=True),
        RamRegion(      start=0x20000000,  length=0x10000)
        )
    
    def __init__(self, transport):
        super(NRF52, self).__init__(transport, self.memoryMap)

    def resetn(self):
        """
        reset a core. After a call to this function, the core
        is running
        """
        #Regular reset will kick NRF out of DBG mode
        logging.debug("target_nrf52.reset: enable reset pin")
        self.writeMemory(RESET, RESET_ENABLE)
        #reset
        logging.debug("target_nrf52.reset: trigger nRST pin")
        CortexM.reset(self)

    def unlock(self, reset=True):
        prev_config = self.readMemory(NVMC_CONFIG)
        self.writeMemory(NVMC_CONFIG, 2)
        self.writeMemory(NVMC_ERASEALL, 1)
        while self.readMemory(NVMC_READY) == 0:
            pass
        self.writeMemory(NVMC_CONFIG, prev_config)
        if reset:
            self.resetStopOnReset()
