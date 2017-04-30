"""
 mbed CMSIS-DAP debugger
 Copyright (c) 2016 ARM Limited

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
from .provider import (TargetThread, ThreadProvider)
import logging

## @brief Base class representing a thread on the target.
class RTX2TargetThread(TargetThread):

    def __init__(self, targetContext, provider, base):
        super(RTX2TargetThread, self).__init__()
        self._target_context = targetContext
        self._provider = provider
        self._base = base
        #TODO - create a new context
        self._thread_context = targetContext

    @property
    def unique_id(self):
        return self._base

    @property
    def name(self):
        #TODO
        return "Russ's thread name (0x%x)" % self._base

    @property
    def description(self):
        #todo
        return "Russ's thread description"

    @property
    def is_current(self):
        return self._provider.get_actual_current_thread_id() == self.unique_id

    @property
    def context(self):
        return self._thread_context


class RTX2ThreadProvider(ThreadProvider):

    def __init__(self, target):
        super(RTX2ThreadProvider, self).__init__(target)
        self._target_context = self._target.getTargetContext()
        self._threads = {}
        #todo

    def init(self, symbolProvider):
        #todo - check symbol provider for required symbols
        return True

    def _build_thread_list(self):
        threads = {}
        # Read from target to get all the threads
        for i in range(5):
            threads[i] = RTX2TargetThread(self._target_context, self, i)
        self._threads = threads

    def get_threads(self):
        if not self.is_enabled:
            return []
        self.update_threads()
        return self._threads.values()

    def get_thread(self, threadId):
        self.update_threads()
        return self._threads.get(threadId, None)

    @property
    def is_enabled(self):
        """Return True if the rtos is active, false otherwise"""
        return True

    @property
    def current_thread(self):
        if not self.is_enabled:
            return None
        self.update_threads()
        id = self.get_current_thread_id()
        try:
            return self._threads[id]
        except KeyError:
            return None

    def is_valid_thread_id(self, threadId):
        if not self.is_enabled:
            return False
        self.update_threads()
        return threadId in self._threads

    def get_current_thread_id(self):
        if not self.is_enabled:
            return None
        if self.get_ipsr() > 0:
            #TODO - not sure what thread ID should be used here
            return 2
        return self._get_actual_current_thread_id()

    def get_ipsr(self):
        return self._target_context.readCoreRegister('xpsr') & 0xff

    def _get_actual_current_thread_id(self):
        if not self.is_enabled:
            return None
        #TODO
        return 0#self._target_context.read32(self._symbols['pxCurrentTCB'])

