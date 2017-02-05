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
        "0003400e072801d3c008c01d704770b556490d22494452064860904201d00120"
        "00e000208860534a5148d0625248534c08604c443120524e2060214618313268"
        "0d46204690470020a061362020603268294620469047a069002800d0012070bd"
        "00207047f8b5454c32204c4400260e27c1c43e4d21464d44a868206040480c31"
        "02683e480c3c484400919047a06900280fd13420c1c428682060a86860603848"
        "0c3c02683548009948449047a069002800d00120f8bdf8b5fff7a2ff2f4d0446"
        "32204d4411c5294e2c604e44b06868602b4f2946103129483a684844083d0091"
        "9047a86900280fd1342011c52c6030686860b068a86021483a684844083d0099"
        "9047a869002800d00120f8bdf7b582b00746fff775ff194c32214c4460602160"
        "124da0604d44a868154ee060214618313268204600919047a069002813d13320"
        "81c4049820600120800260602868a060a868e060094832684844083c00999047"
        "a069002800d0012005b0f0bd040000000008000140000540e02e000010000000"
        "0001401000000000000000000000000000000000000000000000000000000000"
        "0000000000000000000000000000000000000000000000000000000000000000",

    # Relative function addresses
    'pc_init': 0xf,
    'pc_unInit': 0x61,
    'pc_program_page': 0x10d,
    'pc_erase_sector': 0xb7,
    'pc_eraseAll': 0x65,

    # Relative region addresses and sizes
    'ro_start': 0x0,
    'ro_size': 0x184,
    'rw_start': 0x184,
    'rw_size': 0x10,
    'zi_start': 0x194,
    'zi_size': 0x2c,

    # Flash information
    'flash_start': 0x1a000000,
    'flash_size': 0x80000,
    'page_size': 0x400,
    'sector_sizes': (
        (0x0, 0x2000),
        (0x10000, 0x10000),
    )
}
