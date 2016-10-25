"""
 mbed CMSIS-DAP debugger
 Copyright (c) 2015 ARM Limited

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
from __future__ import print_function

import os, sys
from time import sleep, time
from random import randrange
import traceback
import argparse

parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parentdir)

import pyOCD
from pyOCD.board import MbedBoard
from test_util import Test, TestResult
import logging
from pyOCD.pyDAPAccess import DAPAccess
import threading


def run_in_parallel(function, args, count):
    thread_list = []
    for _ in range(count):
        thread = threading.Thread(target=function, args=args)
        thread.start()
        thread_list.append(thread)
    for thread in thread_list:
        thread.join()


def list_boards(id_list):
    for _ in range(0, 20):
        device_list = DAPAccess.get_connected_devices()
        found_id_list = [device.get_unique_id() for device in device_list]
        found_id_list.sort()
        assert id_list == found_id_list, "Expected %s, got %s" % (id_list, found_id_list)


def parallel_test():
    device_list = DAPAccess.get_connected_devices()

    print("Devices: %s" % device_list)
    for _ in range(0, 10):
        device_list[0].open()
        device_list[0].close()

    id_list = [device.get_unique_id() for device in device_list]
    id_list.sort()
    
    # List boards in multple threads
    run_in_parallel(list_boards, (id_list,), 5)

    # List boards in multiple processes

    # Open same board in multiple threads - make sure error is graceful

    # Open same board in multiple processes - make sure error is graceful

    # Repeatedly open an close one board per thread - make sure there are no collisions
    
    # Repeately open and close one board per process -  make sure there are no collisions

#     
#     with MbedBoard.chooseBoard(board_id=board_id, frequency=1000000) as board:
#         target_type = board.getTargetType()
# 
#         test_clock = 10000000
#         if target_type == "nrf51":
#             # Override clock since 10MHz is too fast
#             test_clock = 1000000
#         if target_type == "ncs36510":
#             # Override clock since 10MHz is too fast
#             test_clock = 1000000
# 
#         memory_map = board.target.getMemoryMap()
#         ram_regions = [region for region in memory_map if region.type == 'ram']
#         ram_region = ram_regions[0]
#         rom_region = memory_map.getBootMemory()
# 
#         ram_start = ram_region.start
#         ram_size = ram_region.length
#         rom_start = rom_region.start
#         rom_size = rom_region.length
# 
#         target = board.target
#         link = board.link
# 
#         test_pass_count = 0
#         test_count = 0
#         result = SpeedTestResult()
# 
#         link.set_clock(test_clock)
#         link.set_deferred_transfer(True)
# 
#         print("\r\n\r\n------ TEST RAM READ / WRITE SPEED ------")
#         test_addr = ram_start
#         test_size = ram_size
#         data = [randrange(1, 50) for x in range(test_size)]
#         start = time()
#         target.writeBlockMemoryUnaligned8(test_addr, data)
#         target.flush()
#         stop = time()
#         diff = stop - start
#         result.write_speed = test_size / diff
#         print("Writing %i byte took %s seconds: %s B/s" % (test_size, diff, result.write_speed))
#         start = time()
#         block = target.readBlockMemoryUnaligned8(test_addr, test_size)
#         target.flush()
#         stop = time()
#         diff = stop - start
#         result.read_speed = test_size / diff
#         print("Reading %i byte took %s seconds: %s B/s" % (test_size, diff, result.read_speed))
#         error = False
#         for i in range(len(block)):
#             if (block[i] != data[i]):
#                 error = True
#                 print("ERROR: 0x%X, 0x%X, 0x%X!!!" % ((addr + i), block[i], data[i]))
#         if error:
#             print("TEST FAILED")
#         else:
#             print("TEST PASSED")
#             test_pass_count += 1
#         test_count += 1
# 
#         print("\r\n\r\n------ TEST ROM READ SPEED ------")
#         test_addr = rom_start
#         test_size = rom_size
#         start = time()
#         block = target.readBlockMemoryUnaligned8(test_addr, test_size)
#         target.flush()
#         stop = time()
#         diff = stop - start
#         print("Reading %i byte took %s seconds: %s B/s" % (test_size, diff, test_size / diff))
#         print("TEST PASSED")
#         test_pass_count += 1
#         test_count += 1
# 
#         target.reset()
# 
#         result.passed = test_count == test_pass_count
#         return result

if __name__ == "__main__":
    parallel_test()
