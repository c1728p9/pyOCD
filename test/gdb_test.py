"""
 mbed CMSIS-DAP debugger
 Copyright (c) 2015-2015 ARM Limited

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

# Note
#  To run this script GNU Tools ARM Embedded must be installed,
#  along with python for the same architecture.  The program
#  "arm-none-eabi-gdb-py.exe" requires python for the same
#  architecture (x86 or 64) to work correctly. Also, on windows
#  the GNU Tools ARM Embedded bin directory needs to be added to
#  your path.

import os
import json
import sys
from subprocess import Popen, STDOUT, PIPE

from pyOCD.tools.gdb_server import GDBServerTool
from pyOCD.board import MbedBoard
from test_util import Test, TestResult
from threading import Lock

# TODO, c1728p9 - run script several times with
#       with different command line parameters

TEST_PARAM_FILE = "test_params.txt"
TEST_RESULT_FILE = "test_results.txt"
PYTHON_GDB_FOR_OS = {
    "linux": "arm-none-eabi-gdb",
    "darwin": "arm-none-eabi-gdb-py",
    "win": "arm-none-eabi-gdb-py",
}
PYTHON_GDB = None
STARTING_TEST_PORT = 3334
for prefix, program in PYTHON_GDB_FOR_OS.iteritems():
    if sys.platform.startswith(prefix):
        PYTHON_GDB = program
        break
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class GdbTestResult(TestResult):
    def __init__(self):
        super(self.__class__, self).__init__(None, None, None)


class GdbTest(Test):
    def __init__(self):
        super(self.__class__, self).__init__("Gdb Test", test_gdb)

    def print_perf_info(self, result_list, output_file=None):
        pass

    def run(self, board, log_func):
        try:
            result = self.test_function(board.getUniqueID(), log_func)
        except Exception as e:
            result = GdbTestResult()
            result.passed = False
            print("Exception %s when testing board %s" %
                  (e, board.getUniqueID()))
            raise
        result.board = board
        result.test = self
        return result

TEST_RESULT_KEYS = [
    "breakpoint_count",
    "watchpoint_count",
    "step_time_si",
    "step_time_s",
    "step_time_n",
    "fail_count",
]


class PortLock(object):
    _port_lock = Lock()
    _ports_in_use = set()

    def __init__(self):
        self._port = None

    def __enter__(self):
        print("enter 1")
        with PortLock._port_lock:
            free_port = STARTING_TEST_PORT
            while free_port in PortLock._ports_in_use:
                free_port += 1
            PortLock._ports_in_use.add(free_port)
        self._port = free_port
        print("enter 2")
        return free_port

    def __exit__(self, exptn_type, value, traceback):
        print("exit 1")
        with PortLock._port_lock:
            assert self._port in PortLock._ports_in_use
            PortLock._ports_in_use.remove(self._port)
        print("exit 2")
        return False


def default_log(message):
    print(message)


def test_gdb(board_id=None, log_func=default_log):
    result = GdbTestResult()
    with MbedBoard.chooseBoard(board_id=board_id) as board:
        memory_map = board.target.getMemoryMap()
        ram_regions = [region for region in memory_map if region.type == 'ram']
        ram_region = ram_regions[0]
        rom_region = memory_map.getBootMemory()
        target_type = board.getTargetType()
        binary_file = os.path.join(parentdir, 'binaries',
                                   board.getTestBinary())
        if board_id is None:
            board_id = board.getUniqueID()
        test_clock = 10000000
        error_on_invalid_access = True
        # Hardware breakpoints are not supported above 0x20000000 on
        # CortexM devices
        ignore_hw_bkpt_result = 1 if ram_region.start >= 0x20000000 else 0
        if target_type == "nrf51":
            # Override clock since 10MHz is too fast
            test_clock = 1000000
            # Reading invalid ram returns 0 or nrf51
            error_on_invalid_access = False

        # Program with initial test image
        board.flash.flashBinary(binary_file, rom_region.start)
        board.uninit(False)

    with PortLock() as test_port:

        # Write out the test configuration
        test_params = {}
        test_params['test_port'] = test_port
        test_params["rom_start"] = rom_region.start
        test_params["rom_length"] = rom_region.length
        test_params["ram_start"] = ram_region.start
        test_params["ram_length"] = ram_region.length
        test_params["invalid_start"] = 0xffff0000
        test_params["invalid_length"] = 0x1000
        test_params["expect_error_on_invalid_access"] = error_on_invalid_access
        test_params["ignore_hw_bkpt_result"] = ignore_hw_bkpt_result
        with open(TEST_PARAM_FILE, "wb") as f:
            f.write(json.dumps(test_params))

        # Run the test
        gdb = [PYTHON_GDB, "--command=gdb_script.py"]
        with open("output.txt", "wb") as f:
            program = Popen(gdb, stdin=PIPE, stdout=f, stderr=STDOUT)
            args = ['-p=%i' % test_port, "-f=%i" % test_clock, "-b=%s" % board_id]
            server = GDBServerTool()
            server.run(args)
            program.wait()

    # Read back the result
    with open(TEST_RESULT_FILE, "rb") as f:
        test_result = json.loads(f.read())

    # Print results
    if set(TEST_RESULT_KEYS).issubset(test_result):
        log_func("----------------Test Results----------------")
        log_func("HW breakpoint count: %s" % test_result["breakpoint_count"])
        log_func("Watchpoint count: %s" % test_result["watchpoint_count"])
        log_func("Average instruction step time: %s" %
              test_result["step_time_si"])
        log_func("Average single step time: %s" % test_result["step_time_s"])
        log_func("Average over step time: %s" % test_result["step_time_n"])
        log_func("Failure count: %i" % test_result["fail_count"])
        result.passed = test_result["fail_count"] == 0
    else:
        result.passed = False

    # Cleanup
    os.remove(TEST_RESULT_FILE)
    os.remove(TEST_PARAM_FILE)

    return result

if __name__ == "__main__":
    test_gdb()
