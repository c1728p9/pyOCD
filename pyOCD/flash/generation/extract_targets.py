#!/usr/bin/env python
"""
 mbed
 Copyright (c) 2017-2017 ARM Limited

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
import argparse
from flash_algo import PackFlashAlgo
from ArmPackManager import Cache
from pyOCD.board.mbed_board import BOARD_ID_TO_INFO
import zipfile


def main():
    """Regenerate all flash algorithms"""
    parser = argparse.ArgumentParser(description='Flash generator')
    parser.add_argument("--rebuild_cache", action="store_true",
                        help="Rebuild entire cache")
    args = parser.parse_args()

    cache = Cache(True, True)
    if args.rebuild_cache:
        cache.cache_everything()
        print("Cache rebuilt")
        return

    unsupported_list = []
    count_target = 0
    for _, board_info in BOARD_ID_TO_INFO.iteritems():
        device_name = board_info.target
        count_target += 1
        try:
            algo_binary = cache.get_flash_algorthim_binary(device_name)
        except zipfile.BadZipfile:
            unsupported_list.append(device_name)
            continue

        device_name = device_name.replace("/", "_")
        algo = PackFlashAlgo(algo_binary.read())
        algo.process_template("py_blob.tmpl", "../flash_" +
                              device_name + ".py")

    print("%s of %s supported" % (count_target - len(unsupported_list),
                                  count_target))
    if unsupported_list:
        print("Unsupported devices: %s" % unsupported_list)

if __name__ == '__main__':
    main()
