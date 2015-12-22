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
from __future__ import absolute_import

import logging
from .interface import INTERFACE
from .dap_access_cd_usb import DAPAccessUSB
from .dap_access_cd_ws import DAPAccessWS
from pyOCD.pyDAPAccess.dap_access_api import DAPAccessIntf


DAPAccessList = [DAPAccessUSB, DAPAccessWS]


class DAPAccessAll(DAPAccessIntf):
    """
    An implementation of the DAPAccessIntf layer for DAPLINK boards using websockets as interface
    """

    @staticmethod
    def set_args(arg_list):
        for access in DAPAccessList:
            access.set_args(arg_list)

    # ------------------------------------------- #
    #          Static Functions
    # ------------------------------------------- #
    @staticmethod
    def get_connected_devices():
        """
        Return an array of all mbed boards connected
        """
        all_devices = []
        for access in DAPAccessList:
            all_devices.extend(access.get_connected_devices())
        return all_devices

    @staticmethod
    def get_device(device_id):
        for access in DAPAccessList:
            if access.get_device(device_id):
                return device_id
