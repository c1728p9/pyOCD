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
        "384910b54944086038483749c1813849c1810188490849000180374835494844"
        "016001225204826000214160d202c2600522920642610122d202826102462032"
        "1170491e416200f03cf9002800d0012010bd00207047294a08b57a4449030092"
        "0a0c014624480023484400f0caf9002800d0012008bd08b5204979441e482039"
        "484400f0a4f800280ed11c4878441c4b32387b440090184804221a49484400f0"
        "6df9002800d0012008bd10b5134b7b44014611480122543b9202484400f0b9f8"
        "10bd38b50c460d4979446e3900910146094813462246484400f050f9002800d0"
        "012038bd0400000020c500000020054028d900000000024008000000ab000000"
        "6a0500000c04000070b504460068002503781b06fcd57023037000203ae00300"
        "00f060fa0c070b0f13171b1f23272b2f333626681378f3712ae026685378b371"
        "26e026689378737122e02668d37833711ee026681379f3721ae026685379b372"
        "16e026689379737212e02668d37933720ee02668137af3730ae02668537ab373"
        "06e02668937a737302e02668d37a3373401cc0b28842c2d921688020087003e0"
        "606a411c00d08047206800780006f7d520680078810601d5042506e0c10601d5"
        "082502e0c00700d01025284670bd08b50b46442269460a706a460021984708bd"
        "38b514468a0702d0ff20013038bd42688a4203d88368d3188b420dd8c3688b42"
        "03d802699a188a4201d8022038bd0122c91ad205891800e0891a08226b461a70"
        "0a0c5a700a0a9a70d9706a460321a04738bdffb581b01546019a012752680026"
        "4819bf028a4204d8019b9b68d31883420fd2019ad2688a4204d8019b1b69d318"
        "834201d2022629e0881a0121c905441800e08c1a3946204600f007f9002902d0"
        "ff2601361ae03946284600f0fef8002912d0012612e0092069460870200c4870"
        "200a8870cc70049b6a46032101989847060003d1ed1be419002decd1304605b0"
        "f0bdf0b5016800240a781206fcd570220a7002680321d171016880228a710368"
        "002159710568fc232b710368d97303681a70026813781b06fcd5557a127a1707"
        "01223f0fd20356103b0000f06bf910090b0e1009090909101f0e090909090911"
        "026105e003225203fae7066100e001612a07120f130000f055f9100c0c0c0f12"
        "15181b1d1f0c0c0c0c0c0c0d01225203e6e7c1612046f0bd0121c902f9e70121"
        "8902f6e701214902f3e7ff210131f0e78021eee74021ece72021eae7feb51646"
        "07461d4600208a198b0702d0ff200130febdb30701d00120febd7b688b4203d8"
        "bc681c1994420dd2fb688b4203d83c691c19944201d20220febd0122c91ad205"
        "8c181be0cc1a19e0062069460870200c4870200a8870cc70e8780871a8784871"
        "687888712878c871089b6a460721384698470028e0d1241d361f2d1d002ee3d1"
        "febdfeb5154604464268a80040181e468a4203d8a368d3188b4208d8e3688b42"
        "03d82769db198b4201d80220febd824205d8a368d318834201d38f1a0ae0e268"
        "824203d92369d3188342eed3881a0121c90547180421384600f017f8002902d0"
        "ff200130febd012069460870380c4870380a8870cf70280a08714d718e71089b"
        "6a46062120469847febd002203098b422cd3030a8b4211d300239c464ee00346"
        "0b433cd4002243088b4231d303098b421cd3030a8b4201d394463fe0c3098b42"
        "01d3cb01c01a524183098b4201d38b01c01a524143098b4201d34b01c01a5241"
        "03098b4201d30b01c01a5241c3088b4201d3cb00c01a524183088b4201d38b00"
        "c01a524143088b4201d34b00c01a5241411a00d201465241104670475de0ca0f"
        "00d04942031000d34042534000229c4603098b422dd3030a8b4212d3fc228901"
        "12ba030a8b420cd3890192118b4208d3890192118b4204d389013ad0921100e0"
        "8909c3098b4201d3cb01c01a524183098b4201d38b01c01a524143098b4201d3"
        "4b01c01a524103098b4201d30b01c01a5241c3088b4201d3cb00c01a52418308"
        "8b4201d38b00c01a5241d9d243088b4201d34b00c01a5241411a00d201466346"
        "52415b10104601d34042002b00d54942704763465b1000d3404201b50020c046"
        "c04602bd30b47446641e2578641cab4200d21d46635d5b00e31830bc18470000"
        "feffffff00000000fffffffffeffffff00000000000000000000000000000000"
        "0000000000000000000000000000000000000000000000000000000000000000",

    # Relative function addresses
    'pc_init': 0x1,
    'pc_unInit': 0x53,
    'pc_program_page': 0xc3,
    'pc_erase_sector': 0xab,
    'pc_eraseAll': 0x77,

    # Relative region addresses and sizes
    'ro_start': 0x0,
    'ro_size': 0x610,
    'rw_start': 0x610,
    'rw_size': 0x8,
    'zi_start': 0x618,
    'zi_size': 0x28,

    # Flash information
    'flash_start': 0x0,
    'flash_size': 0x20000,
    'page_size': 0x100,
    'sector_sizes': (
        (0x0, 0x400),
    )
}
