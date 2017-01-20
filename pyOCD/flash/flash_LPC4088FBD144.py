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
        "000b102801d3c0080e30704770b5604c00254c4436206561214620605d4a1431"
        "204690476069002801d0012070bda0697d225949000e5201494427281cd002dc"
        "202806d118e0282816d0472814d0482812d00a605149cd60504a803a1560aa23"
        "d3605523d3600122282811d006dc20280ed0272806d10be0494aeae7472807d0"
        "482805d04d604548c0380260002070bd4a60f8e700207047f8b53d4c32204c44"
        "00251d26224661c221461431394f20460091b847606900280cd13420214661c1"
        "354848440068e06020460099b8476069002800d00120f8bdf8b5fff791ff2c4d"
        "04464d4432206c602946ac6014312860284e0f462846b047686900280dd16c60"
        "3420ac6028602448394648440068e8602846b0476869002800d00120f8bdf8b5"
        "060014460ed161682068e2684018a168891840182169401861694018a1694018"
        "4042e0613046fff75bff114d32214d4468602960a860294614310e4f28460091"
        "b8476869002810d16e603320ac60286001208002e86008484844006828612846"
        "0099b8476869002800d00120f8bd000008000000f11fff1f0400000000c10f40"
        "e02e000000000000000000000000000000000000000000000000000000000000"
        "000000000000000000000000",

    # Relative function addresses
    'pc_init': 0xd,
    'pc_unInit': 0x95,
    'pc_program_page': 0x11f,
    'pc_erase_sector': 0xd9,
    'pc_eraseAll': 0x99,

    # Relative region addresses and sizes
    'ro_start': 0x0,
    'ro_size': 0x1a4,
    'rw_start': 0x1a4,
    'rw_size': 0x8,
    'zi_start': 0x1ac,
    'zi_size': 0x20,

    # Flash information
    'flash_start': 0x0,
    'flash_size': 0x80000,
    'page_size': 0x400,
    'sector_sizes': (
        (0x0, 0x1000),
        (0x10000, 0x8000),
    )
}
