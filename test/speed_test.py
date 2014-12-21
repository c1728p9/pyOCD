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

import argparse, os, sys
from time import sleep, time
from random import randrange
import math
import struct

parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parentdir)

import pyOCD
from pyOCD.board import MbedBoard
from pyOCD.target.cortex_m import float2int

addr = 0
size = 0

interface = None
board = None

import logging

logging.basicConfig(level=logging.INFO)


with MbedBoard.chooseBoard(frequency = 10000000) as board:
    target_type = board.getTargetType()

    if target_type == "kl25z":
        ram_start = 0x1ffff000
        ram_size = 0x4000
        rom_start = 0x00000000
        rom_size = 0x20000
    else:
        raise Exception("A board is not supported by this test script.")

    target = board.target
    transport = board.transport
    flash = board.flash
    interface = board.interface
    
    print "\r\n\r\n------ TEST READ / WRITE SPEED ------"
    test_addr = ram_start
    test_size = ram_size
    data = [randrange(1, 50) for x in range(test_size)]
    start = time()
    target.writeBlockMemoryUnaligned8(test_addr, data)
    stop = time()
    diff = stop-start
    print("Writing %i byte took %s seconds: %s B/s" % (test_size, diff,  test_size / diff))
    start = time()
    block = target.readBlockMemoryUnaligned8(test_addr, test_size)
    stop = time()
    diff = stop-start
    print("Reading %i byte took %s seconds: %s B/s" % (test_size, diff,  test_size / diff))
    error = False
    for i in range(len(block)):
        if (block[i] != data[i]):
            error = True
            print "ERROR: 0x%X, 0x%X, 0x%X!!!" % ((addr + i), block[i], data[i])
    if error:
        print "TEST FAILED"
    else:
        print "TEST PASSED"

    test_addr = rom_start
    test_size = rom_size
    start = time()
    block = target.readBlockMemoryUnaligned8(test_addr, test_size)
    stop = time()
    diff = stop-start
    print("Reading %i byte took %s seconds: %s B/s" % (test_size, diff,  test_size / diff))

    target.reset()
