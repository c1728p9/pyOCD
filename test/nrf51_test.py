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

import os, sys
from time import sleep
from random import randrange
import math

parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parentdir)

import pyOCD
from pyOCD.board import MbedBoard
import logging

from pyOCD.target.target import TARGET_RUNNING
from pyOCD.target.target_nrf51 import NVMC_CONFIG

logging.basicConfig(level=logging.INFO)

# nrf51:
UCIR_BASE = 0x10001000
UICR_RBPCONF = UCIR_BASE + 0x004
UICR_USER_START = UCIR_BASE + 0x80

UICR_LOCK_VALUE = 0xFFFF0000

def same(d1, d2):
    if len(d1) != len(d2):
        return False
    for i in range(len(d1)):
        if d1[i] != d2[i]:
            return False
    return True
    
def zero(d):
    for val in d:
        if val != 0:
            return False
    return True

print "\r\n\r\n------ Test nrf51 ------"
with MbedBoard.chooseBoard() as board:
    flash = board.flash
    target = board.target
    transport = board.transport


    transport.setDeferredTransfer(True)
    transport.setClock(1000000)
    # Get test binary for board
    target_type = board.getTargetType()
    binary_file = os.path.join(parentdir, 'binaries', board.getTestBinary())
    with open(binary_file, "rb") as f:
        data = f.read()
    test_binary = list(bytearray(data))

    flash.setFlashAlgoDebug(True)
    
    # Unlock and program initial image
    target.unlock()
    flash.flashBlock(0, test_binary)
    data_read = target.readBlockMemoryUnaligned8(0, len(test_binary))
    if same(test_binary, data_read):
        print("Flash programmed successfully")
    else:
        print("Error! data does not match")
    
    # Write lock settings to UICR
    target.writeMemory(NVMC_CONFIG, 1)
    target.writeMemory(UICR_RBPCONF, UICR_LOCK_VALUE) 
    target.writeMemory(NVMC_CONFIG, 0)
    
    # Verify rom can still be read
    data_read = target.readBlockMemoryUnaligned8(0, len(test_binary))
    if not same(test_binary, data_read):
        print("Error! data does not match")

    # Reset so lock setting take effect
    target.resetStopOnReset()
    
    # Verify rom is locked and reads as 0
    data_read = target.readBlockMemoryUnaligned8(0, len(test_binary))
    if zero(data_read):
        print("Lock successful")
    else:
        print("Error! Lock failed")
        
    # Verify UICR can still be read
    if UICR_LOCK_VALUE == target.readMemory(UICR_RBPCONF):
        print("UICR read successfully")
    else:
        print("UICR cannot be read")
        
    # Verify UICR does not change if written to when locked
    target.writeMemory(NVMC_CONFIG, 0)
    uicr_write_value = 0x33 # Random value
    target.writeMemory(UICR_USER_START, uicr_write_value)
    value_read = target.readMemory(UICR_USER_START)
    if 0xFFFFFFFF == value_read:
        print("UICR protection worked")
    else:
        print("UICR protection failed")

    # Verify UICR can still be written
    uicr_write_value = 0x27 # Random value
    if 0xFFFFFFFF != target.readMemory(UICR_USER_START):
        print("Unexpected UICR user value")
    target.writeMemory(NVMC_CONFIG, 1)
    target.writeMemory(UICR_USER_START, uicr_write_value)
    target.writeMemory(NVMC_CONFIG, 0)
    value_read = target.readMemory(UICR_USER_START)
    if uicr_write_value == value_read:
        print("UICR can be written: 0x%x" % value_read)
    else:
        print("Failed to write UICR")
    
    # Verify programming fails
    try:
        # Flash algo debug must be turned on for this to fail
        flash.flashBlock(0, test_binary)
        print("Error! Programming should not work when locked")
    except Exception:
        print("Programming failed as expected when locked")
    
    # Verify programming succeeds after unlocking
    target.unlock()
    flash.flashBlock(0, test_binary)
    print("Programming succeeded after unlocking")
