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
        "5348524a4260534941608260816000210160c16814221143c160c069400706d4"
        "4e484d490160062141604d498160002070474748016980221143016101698215"
        "914301610020704770b54148c16814231943c160016920242143016101694022"
        "114301613f493d4a00e01160c568ed07fbd10569a54305610569102425430561"
        "354d394e5535358000e01160c568ed07fbd10169a1430161c168194204d0c168"
        "1943c160012070bd002070bd30b52848c16814242143c1600169202529430161"
        "01694022114301612649244a00e01160c368db07fbd10169a9430161c1682142"
        "04d0c1682143c160012030bd002030bd01207047f0b5164d491c4908eb684900"
        "04242343eb601026164b1ae02c6934432c6114880480114c00e02360ef68ff07"
        "fbd12c69b4432c61ec6814273c4205d0e86814210843e8600120f0bd801c921c"
        "891e0029e2d10020f0bd00002301674500200240ab89efcd5555000000300040"
        "ff0f0000aaaa000000f8ff1f00000000",

    # Relative function addresses
    'pc_init': 0x1,
    'pc_unInit': 0x33,
    'pc_program_page': 0xf5,
    'pc_erase_sector': 0xad,
    'pc_eraseAll': 0x49,

    # Relative region addresses and sizes
    'ro_start': 0x0,
    'ro_size': 0x16c,
    'rw_start': 0x16c,
    'rw_size': 0x4,
    'zi_start': 0x170,
    'zi_size': 0x0,

    # Flash information
    'flash_start': 0x1ffff800,
    'flash_size': 0x10,
    'page_size': 0x10,
    'sector_sizes': (
        (0x0, 0x10),
    )
}
