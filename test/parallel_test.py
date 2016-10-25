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


def run_in_parallel(function, args_list):\
    # TODO - handle error codes
    thread_list = []
    for args in args_list:
        thread = threading.Thread(target=function, args=args)
        thread.start()
        thread_list.append(thread)

    for thread in thread_list:
        thread.join()

#        code = []
#        for threadId, stack in sys._current_frames().items():
#            code.append("\n# ThreadID: %s" % threadId)
#            for filename, lineno, name, line in traceback.extract_stack(stack):
#                code.append('File: "%s", line %d, in %s' % (filename,
#                                                            lineno, name))
#                if line:
#                    code.append("  %s" % (line.strip()))
#        for line in code:
#            print(line)
#        print("\n*** STACKTRACE - END ***\n")


def list_boards(id_list):
    for _ in range(0, 20):
        device_list = DAPAccess.get_connected_devices()
        found_id_list = [device.get_unique_id() for device in device_list]
        found_id_list.sort()
        assert id_list == found_id_list, "Expected %s, got %s" % \
            (id_list, found_id_list)


def search_and_lock(board_id):
    for _ in range(0, 200):
        device = DAPAccess.get_device(board_id)
        device.open()
        device.close()
        with MbedBoard.chooseBoard(board_id=board_id) as board:
            pass


def open_already_opened(board_id):
    device = DAPAccess.get_device(board_id)
    try:
        device.open()
        assert False
    except DAPAccess.DeviceError:
        pass


def parallel_test():
    device_list = DAPAccess.get_connected_devices()
    id_list = [device.get_unique_id() for device in device_list]
    id_list.sort()

    if len(id_list) < 2:
        print("Need at least 2 boards to run the parallel test")
        exit(-1)

    # -The process of listing available boards does not interfere
    #  with other processes enumerating, opening, or using boards
    # -Opening and using a board does not interfere with another process
    #  processes which is enumerating, opening, or using boards as
    # long as that is not the current board

    # List boards in multple threads
    args_list = [(id_list,) for _ in range(5)]
    run_in_parallel(list_boards, args_list)

    # List boards in multiple processes

    # Open same board in multiple threads - make sure error is graceful
    device = DAPAccess.get_device(id_list[0])
    device.open()
    open_already_opened(id_list[0])
    args_list = [(id_list[0],) for _ in range(5)]
    run_in_parallel(open_already_opened, args_list)
    device.close()


    # Open same board in multiple processes - make sure error is graceful

    # Repeatedly open an close one board per thread - make sure there are no collisions
    args_list = [(board_id,) for board_id in id_list]
    run_in_parallel(search_and_lock, args_list)

    # Repeately open and close one board per process -  make sure there are no collisions


if __name__ == "__main__":
    parallel_test()
