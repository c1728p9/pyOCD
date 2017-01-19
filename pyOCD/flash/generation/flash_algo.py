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
import os
import struct
import binascii
import argparse
import logging
import StringIO
import jinja2

from elftools.common.py3compat import bytes2str
from elftools.elf.elffile import ELFFile
from elftools.elf.sections import SymbolTableSection

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def main():
    parser = argparse.ArgumentParser(description="Algo Extracter")
    parser.add_argument("input", help="File to extract flash algo from")
    parser.add_argument("template", default="py_blob.tmpl",
                        help="Template to use")
    parser.add_argument("output", help="Output file")
    args = parser.parse_args()

    with open(args.input, "rb") as file_handle:
        data = file_handle.read()
    algo = PackFlashAlgo(data)
    algo.process_template("py_blob.tmpl",
                          os.path.join(args.output, "py_blob.py"))


class PackFlashAlgo(object):
    """
    Class to wrap a flash algo

    This class is intended to provide easy access to the information
    provided by a flash algorithm, such as symbols and the flash
    algorithm itself.
    """

    REQUIRED_SYMBOLS = set([
        "Init",
        "UnInit",
        "EraseSector",
        "ProgramPage",
    ])

    EXTRA_SYMBOLS = set([
        "BlankCheck",
        "EraseChip",
        "Verify",
    ])

    def __init__(self, data):
        """Construct a PackFlashAlgorithm from an ElfFileSimple"""
        elf_simple = ElfFileSimple(data)
        self.flash_info = PackFlashInfo(elf_simple)
        self.algo_data = None
        self.symbols = None

        self.ro_start = None
        self.ro_size = None
        self.rw_start = None
        self.rw_size = None
        self.zi_start = None
        self.zi_size = None

        self.flash_start = self.flash_info.start
        self.flash_size = self.flash_info.size
        self.page_size = self.flash_info.page_size
        self.sector_sizes = self.flash_info.sector_info_list

        ro_section = None
        rw_section = None
        zi_section = None

        symbols = {}
        for symbol in self.REQUIRED_SYMBOLS:
            if symbol not in elf_simple.symbols:
                raise Exception("Missing symbol %s" % symbol)
            symbols[symbol] = elf_simple.symbols[symbol].value
        for symbol in self.EXTRA_SYMBOLS:
            if symbol not in elf_simple.symbols:
                symbols[symbol] = 0xFFFFFFFF
            else:
                symbols[symbol] = elf_simple.symbols[symbol].value
        self.symbols = symbols

        # Find required sections
        for section in elf_simple.elf.iter_sections():
            if bytes2str(section.name) == "PrgCode":
                if section["sh_type"] == "SHT_PROGBITS":
                    if ro_section is None:
                        ro_section = section
                    else:
                        raise Exception("Extra ro section")
                else:
                    raise Exception("Unexpected section type in PrgCode")
            if bytes2str(section.name) == "PrgData":
                if section["sh_type"] == "SHT_PROGBITS":
                    if rw_section is None:
                        rw_section = section
                    else:
                        raise Exception("Extra rw section")
                elif section["sh_type"] == "SHT_NOBITS":
                    if zi_section is None:
                        zi_section = section
                    else:
                        raise Exception("Extra zi section")
                else:
                    raise Exception("Unexpected section type in PrgData")

        # Make sure all required sections are present
        if ro_section is None:
            raise Exception("Missing ro section")
        if rw_section is None:
            raise Exception("Missing rw section")
        if zi_section is None:
            zi_section = {
                "sh_addr": rw_section["sh_addr"] + rw_section["sh_size"],
                "sh_size": 0,
            }
            logger.info("Missing zi section")

        # Build the algo
        self.ro_start = ro_section["sh_addr"]
        self.ro_size = ro_section["sh_size"]
        self.rw_start = rw_section["sh_addr"]
        self.rw_size = rw_section["sh_size"]
        self.zi_start = zi_section["sh_addr"]
        self.zi_size = zi_section["sh_size"]

        # Check section ordering
        if self.ro_start != 0:
            raise Exception("RO section does not start at address 0")
        if self.ro_start + self.ro_size != self.rw_start:
            raise Exception("RW section does not follow RO section")
        if self.rw_start + self.rw_size != self.zi_start:
            raise Exception("ZI section does not follow RW section")

        # Attach data to the flash algo
        algo_size = self.ro_size + self.rw_size + self.zi_size
        algo_data = bytearray(algo_size)
        ro_data = ro_section.data()
        algo_data[self.ro_start:self.ro_start + self.ro_size] = ro_data
        rw_data = rw_section.data()
        algo_data[self.rw_start:self.rw_start + self.rw_size] = rw_data
        # Note - ZI is already zeroed
        self.algo_data = algo_data

    def format_algo_data(self, spaces, group_size, fmt):
        """"
        Return a string representing algo_data suitable for use in a template

        The string is intended for use in a template.

        :param spaces: The number of leading spaces for each line
        :param group_size: number of elements per line (element type
            depends of format)
        :param fmt: - format to create - can be either "hex" or "c"
        """
        padding = " " * spaces
        if fmt == "hex":
            blob = binascii.b2a_hex(self.algo_data)
            line_list = []
            for i in xrange(0, len(blob), group_size):
                line_list.append('"' + blob[i:i + group_size] + '"')
            return ("\n" + padding).join(line_list)
        elif fmt == "c":
            blob = self.algo_data[:]
            pad_size = 0 if len(blob) % 4 == 0 else 4 - len(blob) % 4
            blob = blob + "\x00" * pad_size
            integer_list = struct.unpack("<" + "L" * (len(blob) / 4), blob)
            line_list = []
            for pos in range(0, len(integer_list), group_size):
                group = ["0x%08x" % value for value in
                         integer_list[pos:pos + group_size]]
                line_list.append(", ".join(group))
            return (",\n" + padding).join(line_list)
        else:
            raise Exception("Unsupported format %s" % fmt)

    def process_template(self, template_path, output_path, data_dict=None):
        """
        Generate output from the supplied template

        All the public methods and fields of this class can be accessed from
        the template via "algo".

        :param template_path: Relative or absolute file path to the template
        :param output_path: Relative or absolute file path to create
        :param data_dict: Additional data to use when generating
        """
        if data_dict is None:
            data_dict = {}
        else:
            assert isinstance(data_dict, dict)
            data_dict = dict(data_dict)
        assert "algo" not in data_dict, "algo already set by user data"
        data_dict["algo"] = self

        with open(template_path) as file_handle:
            template_text = file_handle.read()

        template = jinja2.Template(template_text)
        target_text = template.render(data_dict)

        with open(output_path, "wb") as file_handle:
            file_handle.write(target_text)


class PackFlashInfo(object):
    """Wrapper class for the non-executable information in an FLM file"""

    FLASH_DEVICE_STRUCT = "<H128sHLLLLBxxxLL"
    FLASH_SECTORS_STRUCT = "<LL"
    SECTOR_END = 0xFFFFFFFF

    def __init__(self, elf_simple):
        dev_info = elf_simple.symbols["FlashDevice"]
        info_start = dev_info.value
        info_size = struct.calcsize(self.FLASH_DEVICE_STRUCT)
        data = elf_simple.read(info_start, info_size)
        values = struct.unpack(self.FLASH_DEVICE_STRUCT, data)

        self.version = values[0]
        self.name = values[1].strip("\x00")
        self.type = values[2]
        self.start = values[3]
        self.size = values[4]
        self.page_size = values[5]
        self.value_empty = values[7]
        self.prog_timeout_ms = values[8]
        self.erase_timeout_ms = values[9]

        sector_entry_size = struct.calcsize(self.FLASH_SECTORS_STRUCT)
        index = 0
        sector_size, sector_start = 0, 0
        sector_info_list = []
        while True:
            sector_info_start = (info_start + info_size +
                                 index * sector_entry_size)
            data = elf_simple.read(sector_info_start, sector_entry_size)
            sector_size, sector_start = struct.unpack(self.FLASH_SECTORS_STRUCT, data)
            if (sector_size == self.SECTOR_END and
               sector_start == self.SECTOR_END):
                break
            sector_info_list.append((sector_start, sector_size))
            index += 1
        self.sector_info_list = sector_info_list

    def __str__(self):
        desc = ""
        desc += "Flash Device:" + os.linesep
        desc += "  name=%s" % self.name + os.linesep
        desc += "  version=0x%x" % self.version + os.linesep
        desc += "  type=%i" % self.type + os.linesep
        desc += "  start=0x%x" % self.start + os.linesep
        desc += "  size=0x%x" % self.size + os.linesep
        desc += "  page_size=0x%x" % self.page_size + os.linesep
        desc += "  value_empty=0x%x" % self.value_empty + os.linesep
        desc += "  prog_timeout_ms=%i" % self.prog_timeout_ms + os.linesep
        desc += "  erase_timeout_ms=%i" % self.erase_timeout_ms + os.linesep
        desc += "  sectors:" + os.linesep
        for sector_start, sector_size in self.sector_info_list:
            desc += ("    start=0x%x, size=0x%x" %
                     (sector_start, sector_size) + os.linesep)
        return desc


class SymbolSimple(object):
    """Wrapper for symbol object"""

    def __init__(self, name, value, size):
        self.name = name
        self.value = value
        self.size = size


class ElfFileSimple(object):
    """Wrapper for elf object which allows easy access to symbols and rom"""

    def __init__(self, data):
        """Construct a ElfFileSimple from bytes or a bytearray"""
        self.symbols = None
        self.elf = ELFFile(StringIO.StringIO(data))
        self._read_symbol_table()

    def _read_symbol_table(self):
        """Read the symbol table into the field "symbols" for easy use"""
        section = self.elf.get_section_by_name(b".symtab")
        if not section:
            raise Exception("Missing symbol table")

        if not isinstance(section, SymbolTableSection):
            raise Exception("Invalid symbol table section")

        symbols = {}
        for symbol in section.iter_symbols():
            name_str = bytes2str(symbol.name)
            if name_str in symbols:
                logging.debug("Duplicate symbol %s", name_str)
            symbols[name_str] = SymbolSimple(name_str, symbol["st_value"],
                                             symbol["st_size"])
        self.symbols = symbols

    def read(self, addr, size):
        """Read program data from the elf file

        :param addr: physical address (load address) to read from
        :param size: number of bytes to read
        :return: Requested data or None if address is unmapped
        """
        for segment in self.elf.iter_segments():
            seg_addr = segment["p_paddr"]
            seg_size = min(segment["p_memsz"], segment["p_filesz"])
            if addr >= seg_addr + seg_size:
                continue
            if addr + size <= seg_addr:
                continue
            # There is at least some overlap

            if addr >= seg_addr and addr + size <= seg_addr + seg_size:
                # Region is fully contained
                data = segment.data()
                start = addr - seg_addr
                return data[start:start + size]


if __name__ == '__main__':
    main()
