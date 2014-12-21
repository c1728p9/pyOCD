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

from interface import Interface
import logging, os
import struct

try:
    import serial
except:
    logging.error("pyserial is required")
    isAvailable = False
else:
    isAvailable = True

class PySerial(Interface):
    """
    This class provides basic functions to access
    a USB HID device using pywinusb:
        - write/read an endpoint
    """
    vid = 0
    pid = 0
    
    isAvailable = isAvailable
    
    def __init__(self):
        # Set this to the serial port of the board you want to connect to.
        # On windows this value is one lower than the value in Device Manager.
        self.device = serial.Serial(12) # '12' shows up as COM13 on windows
        return
    
    def open(self):
        pass

    @staticmethod
    def getAllConnectedInterface(vid, pid):
        """
        returns all the connected devices which matches PyWinUSB.vid/PyWinUSB.pid.
        returns an array of PyWinUSB (Interface) objects
        """
        boards = []
        new_board = PySerial()
        new_board.vendor_name = '[Vendor goes here]'
        new_board.product_name = '[Product goes here]'
        boards.append(new_board)
        return boards
    
    def write(self, data):
        """
        write data on the OUT endpoint associated to the HID interface
        """
        for _ in range(64 - len(data)):
            data.append(0)
        data = struct.pack('<64B', *data)
        self.device.write(data)
        return
        
        
    def read(self, timeout = -1):
        """
        read data on the IN endpoint associated to the HID interface
        """
        data = self.device.read(64)
        data = struct.unpack('<64B', data)
        return data
    
    def close(self):
        """
        close the interface
        """
        logging.debug("closing interface")
        self.device.close()
