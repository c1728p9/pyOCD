"""
 Flash OS Routines (Automagically Generated)
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

flash_algo = {

    # Flash algorithm as a hex string
    'instructions':
        "10b503460020444c206044486060444860602046c06910f0040f08d145f25550"
        "404c20600620606040f6ff70a060002010bd01463848006940f08000364a1061"
        "002070473448006940f00400324908610846006940f04000086103e04af6aa20"
        "304908602c48c06810f0010ff6d12a48006920f0040028490861002070470146"
        "2548006940f00200234a106110464161006940f04000106103e04af6aa20214a"
        "10601d48c06810f0010ff6d11a48006920f00200184a10610020704710b50346"
        "481c20f0010122e01348006940f00100114c20611088188000bf0f48c06810f0"
        "010ffad10c48006920f001000a4c20612046c06810f0140f06d02046c06840f0"
        "1400e060012010bd9b1c921c891e0029dad10020f7e700000020024023016745"
        "ab89efcd0030004000000000",

    # Relative function addresses
    'pc_init': 0x1,
    'pc_unInit': 0x33,
    'pc_program_page': 0xbd,
    'pc_erase_sector': 0x7f,
    'pc_eraseAll': 0x45,

    # Relative region addresses and sizes
    'ro_start': 0x0,
    'ro_size': 0x128,
    'rw_start': 0x128,
    'rw_size': 0x4,
    'zi_start': 0x12c,
    'zi_size': 0x0,

    # Flash information
    'flash_start': 0x8000000,
    'flash_size': 0x80000,
    'page_size': 0x400,
    'sector_sizes': (
        (0x0, 0x800),
    )
}
