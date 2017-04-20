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
from struct import unpack
from collections import namedtuple
from ArmPackManager import Cache
from .flash_algo import PackFlashAlgo
from ..family.flash_cortex_m import Flash_cortex_m
from ...core.memory_map import MemoryMap, RamRegion, FlashRegion
from ...flash.flash import Flash
from .. import CoreSightTarget

BLOB_HEADER = (
    0xE00ABE00, 0x062D780D, 0x24084068, 0xD3000040,
    0x1E644058, 0x1C49D1FA, 0x2A001E52, 0x04770D1F
)
HEADER_SIZE = len(BLOB_HEADER) * 4


FlashInfo = namedtuple("FlashInfo", ["start", "size", "sector_sizes"])


def get_supported_targets():
    """Return a list containing the names of all supported targets"""
    cache = Cache(True, True)
    return sorted([name for name, dev in cache.index.items()
                   if name != "version" and
                   _get_cache_device_errors(dev) is None])


def get_target_and_flash(device_name, link):
    """Return an instance of the target and flash classes for the given name"""
    cache = Cache(True, True)
    if device_name not in cache.index:
        raise Exception("Unsupported device '%s'" % device_name)
    dev = cache.index[device_name]
    binaries = cache.get_flash_algorthim_binary(device_name, all=True)
    algos = [PackFlashAlgo(binary.read()) for binary in binaries]
    pack_algo = _filter_algos(dev, algos)[0]
    flash_block = FlashInfo(pack_algo.flash_start, pack_algo.flash_size,
                            pack_algo.sector_sizes)
    memory_map = get_memory_map(dev, flash_block)
    target = CoreSightTarget(link, memory_map)
    pyocd_algo = get_pyocd_flash_algo(pack_algo, memory_map)
    flash = (Flash_cortex_m(target) if pyocd_algo is None
             else Flash(target, pyocd_algo))
    return target, flash


def get_memory_map(dev, flash_info):
    """Create a pyOCD memory map based on the pack device and flash_info"""
    memory_map = MemoryMap()
    for name, info in dev["memory"].items():
        start = int(info["start"], 0)
        length = int(info["size"], 0)
        is_rom = name.find("IROM") >= 0
        if is_rom:
            is_boot_memory = name.find("IROM1") >= 0
            for split_start, split_length in _split_on_blocksize(start, length,
                                                                 flash_info):
                blocksize = _get_sector_size(flash_info, split_start)
                region = FlashRegion(start=split_start,
                                     length=split_length,
                                     blocksize=blocksize,
                                     isBootMemory=is_boot_memory)
                memory_map.addRegion(region)
        else:
            region = RamRegion(start=start, length=length)
            memory_map.addRegion(region)
    return memory_map


def get_pyocd_flash_algo(pack_algo, memory_map):
    """Return a dictionary representing a pyOCD flash algorithm or None"""
    ram_region = [region for region in memory_map if region.type == "ram"][0]
    sector_sizes = [region.blocksize for region in memory_map if
                    (region.type == "rom" or region.type == "flash")]
    largest_sector = reduce(max, sector_sizes)
    instructions = BLOB_HEADER + _bytes_to_words(pack_algo.algo_data)

    offset = 0

    # Data buffers
    addr_data = ram_region.start + offset
    offset += largest_sector

    # Stack
    offset += 512
    addr_stack = ram_region.start + offset

    # Load address
    addr_load = ram_region.start + offset
    offset += len(instructions) * 4

    if offset > ram_region.length:
        # Not enough space for flash algorithm
        return None

    # TODO - analyzer support
    # TODO - double buffering

    code_start = addr_load + HEADER_SIZE
    flash_algo = {
       "load_address": addr_load,
       "instructions": instructions,
       "pc_init": code_start + pack_algo.symbols["Init"],
       "pc_uninit": code_start + pack_algo.symbols["UnInit"],
       "pc_eraseAll": code_start + pack_algo.symbols["EraseChip"],
       "pc_erase_sector": code_start + pack_algo.symbols["EraseSector"],
       "pc_program_page": code_start + pack_algo.symbols["ProgramPage"],
       "begin_data": addr_data,
       "begin_stack": addr_stack,
       "static_base": code_start + pack_algo.rw_start,
       "min_program_length": pack_algo.page_size,
       "analyzer_supported": False
    }
    return flash_algo


def _split_on_blocksize(start, length, flash_info):
    """Split the region given by start and length where sector size changes"""
    split_addrs = [flash_info.start + addr for addr, _
                   in flash_info.sector_sizes]
    splits_inrange = [addr for addr in split_addrs
                      if start < addr < start + length]
    segments = [start] + splits_inrange + [start + length]
    for start, stop in zip(segments, segments[1:]):
        yield start, stop - start


def _get_sector_size(flash_info, addr):
    """Return the sector size at addr based on the flash_info provided"""
    start, size, sector_sizes = flash_info
    if addr >= start + size:
        return
    for offset, sector_size in reversed(sector_sizes):
        if addr >= start + offset:
            return sector_size


def _bytes_to_words(data, pad="\x00"):
    """Convert a string or byte array to a list of words"""
    assert len(pad) == 1
    pad_size = _align_up(len(data), 4) - len(data)
    data_padded = data + pad * pad_size
    return unpack("<" + "I" * (len(data_padded) // 4), data_padded)


def _align_up(value, multiple):
    """Return value aligned up to multiple"""
    remainder = value % multiple
    return value if remainder == 0 else value + multiple - remainder


def _get_cache_device_errors(dev):
    """Return a list of errors with the device or None if valid"""
    if "memory" not in dev:
        return ["Device does not have a memory layout"]

    def valid_hex(num_str):
        """Return true if the string is a valid hex number, false otherwise"""
        try:
            int(num_str, 0)
            return True
        except ValueError:
            return False
    key_validator_pairs = (
        ("start", valid_hex),
        ("size", valid_hex),
    )

    problems = []
    for region_name, info in list(dev["memory"].items()):
        for key, valid in key_validator_pairs:
            if key not in info:
                problems.append("Device region '%s' missing key '%s'" %
                                (region_name, key))
                continue
            if not valid(info[key]):
                problems.append("Device region '%s' key '%s' has invalid "
                                "value '%s'" % (region_name, key, info[key],))
    return None if len(problems) == 0 else problems


def _filter_algos(dev, algos):
    """Filter out algos not for the ROM/Flash of the device"""
    if "memory" not in dev:
        return algos
    if "IROM1" not in dev["memory"]:
        return algos
    if "IROM2" in dev["memory"]:
        return algos

    rom_rgn = dev["memory"]["IROM1"]
    try:
        start = int(rom_rgn["start"], 0)
        size = int(rom_rgn["size"], 0)
    except ValueError:
        return algos

    matching_algos = [algo for algo in algos if
                      algo.flash_start == start and algo.flash_size == size]
    return matching_algos if len(matching_algos) == 1 else algos

