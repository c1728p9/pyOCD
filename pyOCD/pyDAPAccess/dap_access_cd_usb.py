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
from .interface import INTERFACE, usb_backend
from .dap_access_cmsis_dap import DAPAccessCMSISDAP


class DAPAccessUSB(DAPAccessCMSISDAP):
    """
    An implementation of the DAPAccessIntf layer for DAPLINK boards
    """

    # ------------------------------------------- #
    #          Static Functions
    # ------------------------------------------- #
    @staticmethod
    def set_args(arg_list):
        # Do nothing
        pass

    @staticmethod
    def get_connected_devices():
        """
        Return an array of all mbed boards connected
        """
        """
        Return an array of all mbed boards connected
        """
        all_daplinks = []
        all_interfaces = INTERFACE[usb_backend].getAllConnectedInterface()
        for interface in all_interfaces:
            try:
                new_daplink = DAPAccessUSB(interface)
                all_daplinks.append(new_daplink)
            except DAPAccessCMSISDAP.TransferError:
                logger = logging.getLogger(__name__)
                logger.error('Failed to get unique id', exc_info=True)
        return all_daplinks

    @staticmethod
    def get_device(device_id):
        return INTERFACE[usb_backend].get_interface(device_id)
