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
        "800a704746494548494408604548002202630121416342634163816341490220"
        "403908701046704700207047f8b53e4c32204c4400250f26224661c221461431"
        "3a4f20460091b847606900280cd13420214661c1324848440068e06020460099"
        "b8476069002800d00120f8bdf8b52e4d840a4d4432206c602946ac6014312860"
        "2a4e0f462846b047686900280dd16c603420ac6028602248394648440068e860"
        "2846b0476869002800d00120f8bdf8b5144606000ed161682068e2684018a168"
        "891840182169401861694018a16940184042e061144db00a4d44322168602960"
        "a86029461431114f28460091b8476869002810d16e603320ac602860ff200130"
        "e860074848440068286128460099b8476869002800d00120f8bd0000e02e0000"
        "040000004080044008000000f11fff1f00000000000000000000000000000000"
        "000000000000000000000000000000000000000000000000",

    # Relative function addresses
    'pc_init': 0x5,
    'pc_unInit': 0x29,
    'pc_program_page': 0xaf,
    'pc_erase_sector': 0x6d,
    'pc_eraseAll': 0x2d,

    # Relative region addresses and sizes
    'ro_start': 0x0,
    'ro_size': 0x130,
    'rw_start': 0x130,
    'rw_size': 0x8,
    'zi_start': 0x138,
    'zi_size': 0x20,

    # Flash information
    'flash_start': 0x0,
    'flash_size': 0x4000,
    'page_size': 0x100,
    'sector_sizes': (
        (0x0, 0x400),
    )
}