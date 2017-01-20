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
        "40ba7047c0ba70473048012a05d0022a05d0032a0bd001207047022100e00121"
        "01602b4801680029fcd0002070470021f6e7264900200860254801680029fcd0"
        "002070472149012010310860204801680029fcd000207047f4e730b500231c4c"
        "0de050f823506d1c01d0012030bd52f8235040f823502568002dfcd05b1cb3eb"
        "910feed3002030bd70b50446002309e050f8235052f82360b54202d004eb8300"
        "70bd5b1c0d46b3eb910ff1d3284470bd10b5002305e0c45c944201d0012010bd"
        "5b1c8b42f7d3002010bd000004e5014000e4014000000000",

    # Relative function addresses
    'pc_init': 0x9,
    'pc_unInit': 0x33,
    'pc_program_page': 0x5b,
    'pc_erase_sector': 0x59,
    'pc_eraseAll': 0x45,

    # Relative region addresses and sizes
    'ro_start': 0x0,
    'ro_size': 0xd4,
    'rw_start': 0xd4,
    'rw_size': 0x4,
    'zi_start': 0xd8,
    'zi_size': 0x0,

    # Flash information
    'flash_start': 0x10001000,
    'flash_size': 0x1000,
    'page_size': 0x1000,
    'sector_sizes': (
        (0x0, 0x1000),
    )
}
