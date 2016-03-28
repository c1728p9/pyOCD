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
import argparse
import os
import sys

DIR_PARENT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, DIR_PARENT)

import pyOCD
from pyOCD.pyDAPAccess import DAPAccess
from test_util import Test, TestResult
import logging
from random import randrange


def main():
    parser = argparse.ArgumentParser(description='pyOCD cpu test')
    parser.add_argument('-d', '--debug', action="store_true",
                        help='Enable debug logging')
    args = parser.parse_args()
    level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=level)
    thread_test()


def thread_test():

    device_list = DAPAccess.get_connected_devices()

    # Make sure open and close work as expected
    for device in device_list:
        device.open()
        device.close()

    # Make sure an error is thrown when a closed device is closed again
    device_list = DAPAccess.get_connected_devices()
    for device in device_list:
        try:
            device.close()
            raise Exception("Test failed to throw exception")
        except DAPAccess.Error:
            pass

    # Make sure an error is thrown when a closed device is opened twice
    device_list = DAPAccess.get_connected_devices()
    for device in device_list:
        device.open()
        try:
            device.open()
            raise Exception("Test failed to throw exception")
        except DAPAccess.Error:
            pass

    # Make sure there is not a problem with getting devices repeatedly
    for _ in range(100):
        DAPAccess.get_connected_devices()

    # Make sure there is not a problem with getting devices repeatedly
    # on two threads
    thread_list = []
    for 

    # Make sure there is not a problem with getting devices repeatedly
    # on two processes
    
    #TODO
    #-list board repeatedly
    #-list boards on multiple threads repeatedly
    #-list boards on multiple processes repeatedly
    
    #-Lock board
    #-list boards on multiple threads repeatedly
    #-list boards on multiple processes repeatedly


if __name__ == "__main__":
    main()
