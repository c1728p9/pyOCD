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
        "800a704748494748494408604748002202630121416342634163816343490220"
        "403908701046704700207047f8b5404c32204c44214600251f2661c414313c48"
        "3c4f48440c3c0091b847606900280dd1342061c4344848440068206034480c3c"
        "48440099b8476069002800d00120f8bdf8b52f4d840a32204d4411c529460c31"
        "2b482c4e2c600f464844083db047686900280ed1342011c523482c6048440068"
        "6860234839464844083db0476869002800d00120f8bdf8b5144606000ed103cc"
        "62684018216889184018a1684018e16840182169401840426061083c144db00a"
        "4d44322168602960a86029461431114f28460091b8476869002811d13320ac60"
        "41c5ff2001306860074848440068a8600748083d48440099b8476869002800d0"
        "0120f8bde02e0000040000004080044008000000f11fff1f0000000000000000"
        "0000000000000000000000000000000000000000000000000000000000000000",

    # Relative function addresses
    'pc_init': 0x5,
    'pc_unInit': 0x29,
    'pc_program_page': 0xb7,
    'pc_erase_sector': 0x71,
    'pc_eraseAll': 0x2d,

    # Relative region addresses and sizes
    'ro_start': 0x0,
    'ro_size': 0x138,
    'rw_start': 0x138,
    'rw_size': 0x8,
    'zi_start': 0x140,
    'zi_size': 0x20,

    # Flash information
    'flash_start': 0x0,
    'flash_size': 0x8000,
    'page_size': 0x100,
    'sector_sizes': (
        (0x0, 0x400),
    )
}
