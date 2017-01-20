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
        "40ba7047c0ba704755480123012a05d0022a05d0032a05d001207047022102e0"
        "436001e0002141604e4801680029fcd04d488360002070474949002048604948"
        "01680029fcd00020704745490120c860444801680029fcd00020704770b50125"
        "2d070446296900f081f8002904d1286969694843a04201d8012070bd38488460"
        "384801680029fcd0002070bd70b5830716d18b0714d101231b071c695d696c43"
        "84420dd91c695b695c4343189c4207d300232c4c8d080be099004658761c01d0"
        "012070bd5658465021680029fcd05b1c9d42f1d8002070bd70b50446830711d1"
        "8b070fd101231b071d695e697543854208d91d695e6940187543854203d21869"
        "5969484370bd00238d0808e09900665851588e4202d09800001970bd5b1c9d42"
        "f4d870bd30b5830713d18b0711d101231b071c695d696c4384420ad91c695b69"
        "5c4343189c4204d3002305e0c45c944201d0012030bd5b1c8b42f7d3002030bd"
        "00e5014000e4014000060040002203098b422cd3030a8b4211d300239c464ee0"
        "03460b433cd4002243088b4231d303098b421cd3030a8b4201d394463fe0c309"
        "8b4201d3cb01c01a524183098b4201d38b01c01a524143098b4201d34b01c01a"
        "524103098b4201d30b01c01a5241c3088b4201d3cb00c01a524183088b4201d3"
        "8b00c01a524143088b4201d34b00c01a5241411a00d201465241104670475de0"
        "ca0f00d04942031000d34042534000229c4603098b422dd3030a8b4212d3fc22"
        "890112ba030a8b420cd3890192118b4208d3890192118b4204d389013ad09211"
        "00e08909c3098b4201d3cb01c01a524183098b4201d38b01c01a524143098b42"
        "01d34b01c01a524103098b4201d30b01c01a5241c3088b4201d3cb00c01a5241"
        "83088b4201d38b00c01a5241d9d243088b4201d34b00c01a5241411a00d20146"
        "634652415b10104601d34042002b00d54942704763465b1000d3404201b50020"
        "c046c04602bd000000000000",

    # Relative function addresses
    'pc_init': 0x9,
    'pc_unInit': 0x39,
    'pc_program_page': 0x8d,
    'pc_erase_sector': 0x5d,
    'pc_eraseAll': 0x4b,

    # Relative region addresses and sizes
    'ro_start': 0x0,
    'ro_size': 0x2c8,
    'rw_start': 0x2c8,
    'rw_size': 0x4,
    'zi_start': 0x2cc,
    'zi_size': 0x0,

    # Flash information
    'flash_start': 0x0,
    'flash_size': 0x200000,
    'page_size': 0x400,
    'sector_sizes': (
        (0x0, 0x400),
    )
}
