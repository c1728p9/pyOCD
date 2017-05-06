"""
 mbed CMSIS-DAP debugger
 Copyright (c) 2017 ARM Limited

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
from pyOCD.board import MbedBoard
from pyOCD.rtos.provider import (TargetThread, ThreadProvider)
from pyOCD.rtos.common import (read_c_string, HandlerModeThread)
from pyOCD.debug.context import DebugContext
from pyOCD.pyDAPAccess import DAPAccess
import logging
from collections import namedtuple

RTX2_osRtxInfo_t = {
    "kernel.state": 8,
    "run.curr": 28,
    "ready.thread_list": 44,
    "delay_list": 52,
    "wait_list": 56
}

RTX2_osRtxThread_t = {
    "name": 4,
    "thread_next": 8,
    "thread_prev": 12,
    "delay_next": 16,
    "delay_prev": 20,
    "stack_frame": 34,
    "stack_mem": 48,
    "stack_size": 52,
    "sp": 56,
    "thread_addr": 60,
}

RTX2_osKernelState_t = {
    "osKernelInactive": 0,
    "osKernelReady": 1,
    "osKernelRunning": 2,
    "osKernelLocked": 3,
    "osKernelSuspended": 4,
    "osKernelError": 0xFFFFFFFF,
}

log = logging.getLogger("rtx2")


def list_to_stack_offsets(regs):
    return {reg: idx * 4 for idx, reg in enumerate(regs)}


class RTX2ThreadContext(DebugContext):

    _REGS_AUTO_FPU = (range(0x40, 0x40 + 16) +  # S0-S15
                      [33, None]  # fpscr and reserved
                      )
    _REGS_AUTO = [
        0, 1, 2, 3,  # R0-R3
        12,  # R12
        14,  # LR
        15,  # PC
        16,  # XPSR
    ]
    _REGS_SAVED = range(4, 12)  # R4-R11
    _REGS_SAVED_FPU = range(0x50, 0x50 + 16)  # S16-S31

    ISR_OFFSETS = list_to_stack_offsets(_REGS_AUTO)
    ISR_OFFSETS_FPU = list_to_stack_offsets(_REGS_AUTO + _REGS_AUTO_FPU)
    CONTEXT_OFFSETS = list_to_stack_offsets(_REGS_SAVED + _REGS_AUTO)
    CONTEXT_OFFSETS_FPU = list_to_stack_offsets(_REGS_SAVED_FPU + _REGS_SAVED +
                                                _REGS_AUTO + _REGS_AUTO_FPU)

    def __init__(self, parentContext, thread):
        super(RTX2ThreadContext, self).__init__(parentContext.core)
        self._parent = parentContext
        self._thread = thread
        self._has_fpu = parentContext.core.has_fpu

    def readCoreRegistersRaw(self, reg_list):
        reg_list = [self.registerNameToIndex(reg) for reg in reg_list]
        reg_vals = []

        in_exception = self._get_ipsr() > 0
        is_current = self._thread.is_current

        # If this is the current thread and we're not in an exception so
        # just read the live registers.
        if is_current and not in_exception:
            return self._parent.readCoreRegistersRaw(reg_list)

        sp, sf = self._thread.get_stack_and_fame()
        assert (sf is not None) or is_current, ("Frame should be 'None' for"
                                                " current thread only")
        # Note - stack frame is the 8 least
        # signification bits of the link register
        fpu_active = False if sf is None else sf & (1 << 4) == 0

        if is_current and in_exception:
            reg_offsets = (self.ISR_OFFSETS_FPU if fpu_active
                           else self.ISR_OFFSETS)
        else:
            reg_offsets = (self.CONTEXT_OFFSETS_FPU if fpu_active
                           else self.CONTEXT_OFFSETS)
        real_sp_offset = len(reg_offsets) * 4

        for reg in reg_list:
            if reg == 18 or reg == 13:  # PSP and SP
                reg_vals.append(sp + real_sp_offset)
                continue
            if reg not in reg_offsets:
                log.debug("Register %s cannot be read", reg)
                reg_vals.append(0xDEADBEEF)
                continue
            try:
                reg_vals.append(self._parent.read32(sp + reg_offsets[reg]))
            except DAPAccess.TransferError:
                log.debug("Transfer error while reading register %s", reg)
                reg_vals.append(0xDEADBEEF)

        return reg_vals

    def _get_ipsr(self):
        return self._parent.readCoreRegister('xpsr') & 0xff

    def writeCoreRegistersRaw(self, reg_list, data_list):
        self._parent.writeCoreRegistersRaw(reg_list, data_list)


class RTX2TargetThread(TargetThread):
    """Class representing a thread in RTX2"""

    RUNNING = 1
    READY = 2
    DELAYED = 3
    WAITING = 4

    STATE_NAMES = {
        RUNNING: "Running",
        READY: "Ready",
        DELAYED: "Delayed",
        WAITING: "Waiting",
    }

    def __init__(self, targetContext, provider, base, state):
        super(RTX2TargetThread, self).__init__()
        self._target_context = targetContext
        self._provider = provider
        self._base = base
        self._thread_context = RTX2ThreadContext(targetContext, self)
        self._state = state

        try:
            name_tcb_addr = self._base + RTX2_osRtxThread_t["name"]
            name_addr = self._target_context.read32(name_tcb_addr)
            name = read_c_string(self._target_context, name_addr)
        except DAPAccess.TransferError:
            log.debug("Transfer error while reading thread's name")
            name = ""
        self._name = "Unnamed" if len(name) == 0 else name

    def get_stack_and_fame(self):
        """
        Get this threads stack pointer and stack frame

        Note - the stack frame is the last 8 bits of the link register
        """
        if self.is_current:
            # Read live process stack.
            sp = self._target_context.readCoreRegister('psp')
            frame = None
        else:
            # Get stack pointer saved in thread struct.
            try:
                sp = self._target_context.read32(self._base +
                                                 RTX2_osRtxThread_t["sp"])
                frame = self._target_context.read8(self._base +
                                                   RTX2_osRtxThread_t["stack_frame"])
            except DAPAccess.TransferError:
                log.debug("Transfer error while reading thread's "
                          "stack pointer @ 0x%08x",
                          self._base + RTX2_osRtxThread_t["sp"])
        return sp, frame

    @property
    def unique_id(self):
        return self._base

    @property
    def name(self):
        return self._name

    @property
    def description(self):
        return self.STATE_NAMES[self._state]

    @property
    def is_current(self):
        return self._provider._get_actual_current_thread_id() == self.unique_id

    @property
    def context(self):
        return self._thread_context

    def __str__(self):
        return "<RTX2Thread@0x%08x id=%x name=%s>" % (id(self), self.unique_id, self.name)

    def __repr__(self):
        return str(self)


class RTX2ThreadProvider(ThreadProvider):

    """Required RTX2 Symbols"""
    REQUIRED_SYMBOLS = [
        "osRtxInfo",
        ]

    def __init__(self, target):
        super(RTX2ThreadProvider, self).__init__(target)
        self._threads = {}
        self._os_rtx_info = None
        self._current_thread = None

    def init(self, symbolProvider):
        symbols = self._lookup_symbols(self.REQUIRED_SYMBOLS, symbolProvider)
        if symbols is None:
            return False
        self._os_rtx_info = symbols['osRtxInfo']
        return True

    def _build_thread_list(self):
        ThreadLinkedList = namedtuple("ThreadLinkedList",
                                      "state address next_offset")
        lists_info = (
            ThreadLinkedList(
                state=RTX2TargetThread.READY,
                address=self._os_rtx_info + RTX2_osRtxInfo_t["ready.thread_list"],
                next_offset=RTX2_osRtxThread_t["thread_next"]
            ),
            ThreadLinkedList(
                state=RTX2TargetThread.DELAYED,
                address=self._os_rtx_info + RTX2_osRtxInfo_t["delay_list"],
                next_offset=RTX2_osRtxThread_t["delay_next"]
            ),
            ThreadLinkedList(
                state=RTX2TargetThread.WAITING,
                address=self._os_rtx_info + RTX2_osRtxInfo_t["wait_list"],
                next_offset=RTX2_osRtxThread_t["delay_next"]
            ),
        )
        self._current_thread = None
        self._threads = {}
        threads = {}
        current_thread = None
        try:
            for state, address, next_offset in lists_info:
                for base in _iter_linked_list(self._target_context,
                                              address, next_offset):
                    if base in self._threads:
                        log.error("Thread base 0x%x in multiple lists", base)
                        break
                    threads[base] = RTX2TargetThread(self._target_context,
                                                     self, base, state)
        except DAPAccess.TransferError:
            log.debug("Error retrieving thread list")

        # Create fake handler mode thread.
        if self.get_ipsr() > 0:
            log.debug("RTX2: creating handler mode thread")
            handler_thread = HandlerModeThread(self._target_context, self)
            threads[handler_thread.unique_id] = handler_thread
            current_thread = handler_thread

        try:
            run_state = RTX2TargetThread.RUNNING
            run_base = self._target_context.read32(self._os_rtx_info +
                                                   RTX2_osRtxInfo_t["run.curr"])
            run_thread = RTX2TargetThread(self._target_context,
                                          self, run_base, run_state)
            threads[run_base] = run_thread
            if current_thread is None:
                current_thread = run_thread
        except DAPAccess.TransferError:
            log.debug("Error retrieving current thread info")
        self._threads = threads
        self._current_thread = current_thread

    def get_threads(self):
        if not self.is_enabled:
            return []
        self.update_threads()
        return self._threads.values()

    def get_thread(self, threadId):
        if not self.is_enabled:
            return None
        self.update_threads()
        return self._threads.get(threadId, None)

    @property
    def is_enabled(self):
        """Return True if the rtos is active, false otherwise"""
        if self._os_rtx_info is None:
            return False
        try:
            state = self._target_context.read32(self._os_rtx_info +
                                                RTX2_osRtxInfo_t["kernel.state"])
        except DAPAccess.TransferError:
            log.debug("Failed to read kernel state")
            return False
        if state == RTX2_osKernelState_t["osKernelInactive"]:
            return False
        return True

    @property
    def current_thread(self):
        if not self.is_enabled:
            return None
        self.update_threads()
        return self._current_thread

    def is_valid_thread_id(self, threadId):
        if not self.is_enabled:
            return False
        self.update_threads()
        return threadId in self._threads

    def get_current_thread_id(self):
        if not self.is_enabled:
            return None
        if self.get_ipsr() > 0:
            return 2  # Handler mode thread ID
        return self._get_actual_current_thread_id()

    def _get_actual_current_thread_id(self):
        if not self.is_enabled:
            return None
        try:
            return self._target_context.read32(self._os_rtx_info +
                                               RTX2_osRtxInfo_t["run.curr"])
        except DAPAccess.TransferError:
            return None


def _iter_linked_list(target, list_addr, next_offset):
    """Given the address of a list pointer walk the list"""
    node = target.readMemory(list_addr)
    while node != 0:
        yield node
        node = target.readMemory(node + next_offset)
