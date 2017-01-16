"""
 mbed CMSIS-DAP debugger
 Copyright (c) 2006-2015 ARM Limited

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

from pyOCD.target.target import Target
import logging
from struct import unpack
from time import time
from binascii import crc32

# Number of bytes in a sector to read to quickly determine if the sector has the same data
SECTOR_ESTIMATE_SIZE = 32
SECTOR_READ_WEIGHT = 0.3
DATA_TRANSFER_B_PER_S = 40 * 1000 # ~40KB/s, depends on clock speed, theoretical limit for HID is 56,000 B/s

class ProgrammingInfo(object):
    def __init__(self):
        self.program_type = None                # Type of programming performed - FLASH_SECTOR_ERASE or FLASH_CHIP_ERASE
        self.program_time = None                # Total programming time
        self.analyze_type = None                # Type of flash analysis performed - FLASH_ANALYSIS_CRC32 or FLASH_ANALYSIS_PARTIAL_SECTOR_READ
        self.analyze_time = None                # Time to analyze flash contents

def _same(d1, d2):
    assert len(d1) == len(d2)
    for i in range(len(d1)):
        if d1[i] != d2[i]:
            return False
    return True

def _erased(d):
    for i in range(len(d)):
        if d[i] != 0xFF:
            return False
    return True

def _stub_progress(percent):
    pass

class flash_sector(object):
    def __init__(self, addr, size, data, erase_weight, program_weight):
        self.addr = addr
        self.size = size
        self.data = data
        self.erase_weight = erase_weight
        self.program_weight = program_weight
        self.erased = None
        self.same = None

    def getProgramWeight(self):
        """
        Get time to program a sector including the data transfer
        """
        return self.program_weight + \
            float(len(self.data)) / float(DATA_TRANSFER_B_PER_S)

    def getEraseProgramWeight(self):
        """
        Get time to erase and program a sector including data transfer time
        """
        return self.erase_weight + self.program_weight + \
            float(len(self.data)) / float(DATA_TRANSFER_B_PER_S)

    def getVerifyWeight(self):
        """
        Get time to verify a sector
        """
        return float(self.size) / float(DATA_TRANSFER_B_PER_S)

class flash_operation(object):
    def __init__(self, addr, data):
        self.addr = addr
        self.data = data

class FlashBuilder(object):

    # Type of flash operation
    FLASH_SECTOR_ERASE = 1
    FLASH_CHIP_ERASE = 2

    # Type of flash analysis
    FLASH_ANALYSIS_CRC32 = "CRC32"
    FLASH_ANALYSIS_PARTIAL_SECTOR_READ = "SECTOR_READ"

    def __init__(self, flash, base_addr=0):
        self.flash = flash
        self.flash_start = base_addr
        self.flash_operation_list = []
        self.sector_list = []
        self.perf = ProgrammingInfo()
        self.enable_double_buffering = True
        self.max_errors = 10

    def enableDoubleBuffer(self, enable):
        self.enable_double_buffering = enable

    def setMaxErrors(self, count):
        self.max_errors = count

    def addData(self, addr, data):
        """
        Add a block of data to be programmed

        Note - programming does not start until the method
        program is called.
        """
        # Sanity check
        if addr < self.flash_start:
            raise Exception("Invalid flash address 0x%x is before flash start 0x%x" % (addr, self.flash_start))

        # Add operation to list
        self.flash_operation_list.append(flash_operation(addr, data))

        # Keep list sorted
        self.flash_operation_list = sorted(self.flash_operation_list, key=lambda operation: operation.addr)
        # Verify this does not overlap
        prev_flash_operation = None
        for operation in self.flash_operation_list:
            if prev_flash_operation != None:
                if prev_flash_operation.addr + len(prev_flash_operation.data) > operation.addr:
                    raise ValueError("Error adding data - Data at 0x%x..0x%x overlaps with 0x%x..0x%x"
                            % (prev_flash_operation.addr, prev_flash_operation.addr + len(prev_flash_operation.data),
                               operation.addr, operation.addr + len(operation.data)))
            prev_flash_operation = operation

    def program(self, chip_erase=None, progress_cb=None, smart_flash=True, fast_verify=False):
        """
        Determine fastest method of flashing and then run flash programming.

        Data must have already been added with addData
        """

        # Assumptions
        # 1. Sector erases must be on sector boundaries ( sector_erase_addr % sector_size == 0 )
        # 2. Sector erase can have a different size depending on location
        # 3. It is safe to program a sector with less than a sector of data

        # Examples
        # - lpc4330     -Non 0 base address
        # - nRF51       -UICR location far from flash (address 0x10001000)
        # - LPC1768     -Different sized sectors
        program_start = time()

        if progress_cb is None:
            progress_cb = _stub_progress

        # There must be at least 1 flash operation
        if len(self.flash_operation_list) == 0:
            logging.warning("No sectors were programmed")
            return

        # Convert the list of flash operations into flash sectors
        program_byte_count = 0
        flash_addr = self.flash_operation_list[0].addr
        info = self.flash.getSectorInfo(flash_addr)
        sector_addr = flash_addr - (flash_addr % info.size)
        current_sector = flash_sector(sector_addr, info.size, [], info.erase_weight, info.program_weight)
        self.sector_list.append(current_sector)
        for flash_operation in self.flash_operation_list:
            pos = 0
            while pos < len(flash_operation.data):

                # Check if operation is in next sector
                flash_addr = flash_operation.addr + pos
                if flash_addr >= current_sector.addr + current_sector.size:
                    info = self.flash.getSectorInfo(flash_addr)
                    sector_addr = flash_addr - (flash_addr % info.size)
                    current_sector = flash_sector(sector_addr, info.size, [], info.erase_weight, info.program_weight)
                    self.sector_list.append(current_sector)

                # Fill the sector gap if there is one
                sector_data_end = current_sector.addr + len(current_sector.data)
                if flash_addr != sector_data_end:
                    old_data = self.flash.target.readBlockMemoryUnaligned8(sector_data_end, flash_addr - sector_data_end)
                    current_sector.data.extend(old_data)

                # Copy data to sector and increment pos
                space_left_in_sector = info.size - len(current_sector.data)
                space_left_in_data = len(flash_operation.data) - pos
                amount = min(space_left_in_sector, space_left_in_data)
                current_sector.data.extend(flash_operation.data[pos:pos + amount])
                program_byte_count += current_sector.size

                #increment position
                pos += amount

        # If smart flash was set to false then mark all sectors
        # as requiring programming
        if not smart_flash:
            self._mark_all_sectors_for_programming()

        # If the first sector being programmed is not the first sector
        # in ROM then don't use a chip erase
        if self.sector_list[0].addr > self.flash_start:
            if chip_erase is None:
                chip_erase = False
            elif chip_erase is True:
                logging.warning('Chip erase used when flash address 0x%x is not the same as flash start 0x%x', self.sector_list[0].addr, self.flash_start)

        self.flash.init()

        chip_erase_count, chip_erase_program_time = self._compute_chip_erase_sectors_and_weight()
        sector_erase_min_program_time = self._compute_sector_erase_sectors_weight_min()

        # If chip_erase hasn't been specified determine if chip erase is faster
        # than sector erase regardless of contents
        if (chip_erase is None) and (chip_erase_program_time < sector_erase_min_program_time):
            chip_erase = True

        # If chip erase isn't True then analyze the flash
        if chip_erase != True:
            analyze_start = time()
            if self.flash.getFlashInfo().crc_supported:
                sector_erase_count, sector_program_time = self._compute_sector_erase_sectors_and_weight_crc32(fast_verify)
                self.perf.analyze_type = FlashBuilder.FLASH_ANALYSIS_CRC32
            else:
                sector_erase_count, sector_program_time = self._compute_sector_erase_sectors_and_weight_sector_read()
                self.perf.analyze_type = FlashBuilder.FLASH_ANALYSIS_PARTIAL_SECTOR_READ
            analyze_finish = time()
            self.perf.analyze_time = analyze_finish - analyze_start
            logging.debug("Analyze time: %f" % (analyze_finish - analyze_start))

        # If chip erase hasn't been set then determine fastest method to program
        if chip_erase is None:
            logging.debug("Chip erase count %i, Sector erase est count %i" % (chip_erase_count, sector_erase_count))
            logging.debug("Chip erase weight %f, Sector erase weight %f" % (chip_erase_program_time, sector_program_time))
            chip_erase = chip_erase_program_time < sector_program_time

        if chip_erase:
            if self.flash.isDoubleBufferingSupported() and self.enable_double_buffering:
                logging.debug("Using double buffer chip erase program")
                flash_operation = self._chip_erase_program_double_buffer(progress_cb)
            else:
                flash_operation = self._chip_erase_program(progress_cb)
        else:
            if self.flash.isDoubleBufferingSupported() and self.enable_double_buffering:
                logging.debug("Using double buffer sector erase program")
                flash_operation = self._sector_erase_program_double_buffer(progress_cb)
            else:
                flash_operation = self._sector_erase_program(progress_cb)

        self.flash.target.resetStopOnReset()

        program_finish = time()
        self.perf.program_time = program_finish - program_start
        self.perf.program_type = flash_operation

        logging.info("Programmed %d bytes (%d sectors) at %.02f kB/s", program_byte_count, len(self.sector_list), ((program_byte_count / 1024) / self.perf.program_time))

        return self.perf

    def getPerformance(self):
        return self.perf

    def _mark_all_sectors_for_programming(self):
        for sector in self.sector_list:
            sector.erased = False
            sector.same = False

    def _compute_chip_erase_sectors_and_weight(self):
        """
        Compute the number of erased sectors.

        Determine how many sectors in the new data are already erased.
        """
        chip_erase_count = 0
        chip_erase_weight = 0
        chip_erase_weight += self.flash.getFlashInfo().erase_weight
        for sector in self.sector_list:
            if sector.erased is None:
                sector.erased = _erased(sector.data)
            if not sector.erased:
                chip_erase_count += 1
                chip_erase_weight += sector.getProgramWeight()
        self.chip_erase_count = chip_erase_count
        self.chip_erase_weight = chip_erase_weight
        return chip_erase_count, chip_erase_weight

    def _compute_sector_erase_sectors_weight_min(self):
        sector_erase_min_weight = 0
        for sector in self.sector_list:
            sector_erase_min_weight += sector.getVerifyWeight()
        return sector_erase_min_weight

    def _compute_sector_erase_sectors_and_weight_sector_read(self):
        """
        Estimate how many sectors are the same.

        Quickly estimate how many sectors are the same.  These estimates are used
        by sector_erase_program so it is recommended to call this before beginning programming
        This is done automatically by smart_program.
        """
        # Quickly estimate how many sectors are the same
        sector_erase_count = 0
        sector_erase_weight = 0
        for sector in self.sector_list:
            # Analyze sectors that haven't been analyzed yet
            if sector.same is None:
                size = min(SECTOR_ESTIMATE_SIZE, len(sector.data))
                data = self.flash.target.readBlockMemoryUnaligned8(sector.addr, size)
                sector_same = _same(data, sector.data[0:size])
                if sector_same is False:
                    sector.same = False

        # Put together sector and time estimate
        for sector in self.sector_list:
            if sector.same is False:
                sector_erase_count += 1
                sector_erase_weight += sector.getEraseProgramWeight()
            elif sector.same is None:
                # sector is probably the same but must be read to confirm
                sector_erase_weight += sector.getVerifyWeight()
            elif sector.same is True:
                # sector is confirmed to be the same so no programming weight
                pass

        self.sector_erase_count = sector_erase_count
        self.sector_erase_weight = sector_erase_weight
        return sector_erase_count, sector_erase_weight

    def _compute_sector_erase_sectors_and_weight_crc32(self, assume_estimate_correct=False):
        """
        Estimate how many sectors are the same.

        Quickly estimate how many sectors are the same.  These estimates are used
        by sector_erase_program so it is recommended to call this before beginning programming
        This is done automatically by smart_program.

        If assume_estimate_correct is set to True, then sectors with matching CRCs
        will be marked as the same.  There is a small chance that the CRCs match even though the
        data is different, but the odds of this happing are low: ~1/(2^32) = ~2.33*10^-8%.
        """
        # Build list of all the sectors that need to be analyzed
        crc_cmd_list = []
        sector_list = []
        for sector in self.sector_list:
            if sector.same is None:
                # Add sector to computeCrcs
                crc_cmd_list.append((sector.addr, sector.size))
                sector_list.append(sector)
                # Compute CRC of data (Padded with 0xFF)
                data = list(sector.data)
                pad_size = sector.size - len(sector.data)
                if pad_size > 0:
                    data.extend([0xFF] * pad_size)
                sector.crc = crc32(bytearray(data)) & 0xFFFFFFFF

        # Analyze sectors
        sector_erase_count = 0
        sector_erase_weight = 0
        if len(sector_list) > 0:
            crc_list = self.flash.computeCrcs(crc_cmd_list)
            for sector, crc in zip(sector_list, crc_list):
                sector_same = sector.crc == crc
                if assume_estimate_correct:
                    sector.same = sector_same
                elif sector_same is False:
                    sector.same = False

        # Put together sector and time estimate
        for sector in self.sector_list:
            if sector.same is False:
                sector_erase_count += 1
                sector_erase_weight += sector.getEraseProgramWeight()
            elif sector.same is None:
                # sector is probably the same but must be read to confirm
                sector_erase_weight += sector.getVerifyWeight()
            elif sector.same is True:
                # sector is confirmed to be the same so no programming weight
                pass

        self.sector_erase_count = sector_erase_count
        self.sector_erase_weight = sector_erase_weight
        return sector_erase_count, sector_erase_weight

    def _chip_erase_program(self, progress_cb=_stub_progress):
        """
        Program by first performing a chip erase.
        """
        logging.debug("Smart chip erase")
        logging.debug("%i of %i sectors already erased", len(self.sector_list) - self.chip_erase_count, len(self.sector_list))
        progress_cb(0.0)
        progress = 0
        self.flash.eraseAll()
        progress += self.flash.getFlashInfo().erase_weight
        for sector in self.sector_list:
            if not sector.erased:
                self.flash.programPage(sector.addr, sector.data)
                progress += sector.getProgramWeight()
                progress_cb(float(progress) / float(self.chip_erase_weight))
        progress_cb(1.0)
        return FlashBuilder.FLASH_CHIP_ERASE

    def _next_unerased_sector(self, i):
        if i >= len(self.sector_list):
            return None, i
        sector = self.sector_list[i]
        while sector.erased:
            i += 1
            if i >= len(self.sector_list):
                return None, i
            sector = self.sector_list[i]
        return sector, i + 1

    def _chip_erase_program_double_buffer(self, progress_cb=_stub_progress):
        """
        Program by first performing a chip erase.
        """
        logging.debug("Smart chip erase")
        logging.debug("%i of %i sectors already erased", len(self.sector_list) - self.chip_erase_count, len(self.sector_list))
        progress_cb(0.0)
        progress = 0
        self.flash.eraseAll()
        progress += self.flash.getFlashInfo().erase_weight

        # Set up sector and buffer info.
        error_count = 0
        current_buf = 0
        next_buf = 1
        sector, i = self._next_unerased_sector(0)
        assert sector is not None

        # Load first sector buffer
        self.flash.loadPageBuffer(current_buf, sector.addr, sector.data)

        while sector is not None:
            # Kick off this sector program.
            current_addr = sector.addr
            current_weight = sector.getProgramWeight()
            self.flash.startProgramPageWithBuffer(current_buf, current_addr)

            # Get next sector and load it.
            sector, i = self._next_unerased_sector(i)
            if sector is not None:
                self.flash.loadPageBuffer(next_buf, sector.addr, sector.data)

            # Wait for the program to complete.
            result = self.flash.waitForCompletion()

            # check the return code
            if result != 0:
                logging.error('programPage(0x%x) error: %i', current_addr, result)
                error_count += 1
                if error_count > self.max_errors:
                    logging.error("Too many sector programming errors, aborting program operation")
                    break

            # Swap buffers.
            temp = current_buf
            current_buf = next_buf
            next_buf = temp

            # Update progress.
            progress += current_weight
            progress_cb(float(progress) / float(self.chip_erase_weight))

        progress_cb(1.0)
        return FlashBuilder.FLASH_CHIP_ERASE

    def _sector_erase_program(self, progress_cb=_stub_progress):
        """
        Program by performing sector erases.
        """
        actual_sector_erase_count = 0
        actual_sector_erase_weight = 0
        progress = 0

        progress_cb(0.0)

        for sector in self.sector_list:

            # If the sector is not the same
            if sector.same is False:
                progress += sector.getEraseProgramWeight()

            # Read sector data if unknown - after this sector.same will be True or False
            if sector.same is None:
                data = self.flash.target.readBlockMemoryUnaligned8(sector.addr, len(sector.data))
                sector.same = _same(sector.data, data)
                progress += sector.getVerifyWeight()

            # Program sector if not the same
            if sector.same is False:
                self.flash.eraseSector(sector.addr)
                self.flash.programPage(sector.addr, sector.data)
                actual_sector_erase_count += 1
                actual_sector_erase_weight += sector.getEraseProgramWeight()

            # Update progress
            if self.sector_erase_weight > 0:
                progress_cb(float(progress) / float(self.sector_erase_weight))

        progress_cb(1.0)

        logging.debug("Estimated sector erase count: %i", self.sector_erase_count)
        logging.debug("Actual sector erase count: %i", actual_sector_erase_count)

        return FlashBuilder.FLASH_SECTOR_ERASE

    def _scan_sectors_for_same(self, progress_cb=_stub_progress):
        """
        Program by performing sector erases.
        """
        progress = 0
        count = 0
        same_count = 0

        for sector in self.sector_list:
            # Read sector data if unknown - after this sector.same will be True or False
            if sector.same is None:
                data = self.flash.target.readBlockMemoryUnaligned8(sector.addr, len(sector.data))
                sector.same = _same(sector.data, data)
                progress += sector.getVerifyWeight()
                count += 1
                if sector.same:
                    same_count += 1

                # Update progress
                progress_cb(float(progress) / float(self.sector_erase_weight))
        return progress

    def _next_nonsame_sector(self, i):
        if i >= len(self.sector_list):
            return None, i
        sector = self.sector_list[i]
        while sector.same:
            i += 1
            if i >= len(self.sector_list):
                return None, i
            sector = self.sector_list[i]
        return sector, i + 1

    def _sector_erase_program_double_buffer(self, progress_cb=_stub_progress):
        """
        Program by performing sector erases.
        """
        actual_sector_erase_count = 0
        actual_sector_erase_weight = 0
        progress = 0

        progress_cb(0.0)

        # Fill in same flag for all sectors. This is done up front so we're not trying
        # to read from flash while simultaneously programming it.
        progress = self._scan_sectors_for_same(progress_cb)

        # Set up sector and buffer info.
        error_count = 0
        current_buf = 0
        next_buf = 1
        sector, i = self._next_nonsame_sector(0)

        # Make sure there are actually sectors to program differently from current flash contents.
        if sector is not None:
            # Load first sector buffer
            self.flash.loadPageBuffer(current_buf, sector.addr, sector.data)

            while sector is not None:
                assert sector.same is not None

                # Kick off this sector program.
                current_addr = sector.addr
                current_weight = sector.getEraseProgramWeight()
                self.flash.eraseSector(current_addr)
                self.flash.startProgramPageWithBuffer(current_buf, current_addr) #, erase_sector=True)
                actual_sector_erase_count += 1
                actual_sector_erase_weight += sector.getEraseProgramWeight()

                # Get next sector and load it.
                sector, i = self._next_nonsame_sector(i)
                if sector is not None:
                    self.flash.loadPageBuffer(next_buf, sector.addr, sector.data)

                # Wait for the program to complete.
                result = self.flash.waitForCompletion()

                # check the return code
                if result != 0:
                    logging.error('programPage(0x%x) error: %i', current_addr, result)
                    error_count += 1
                    if error_count > self.max_errors:
                        logging.error("Too many sector programming errors, aborting program operation")
                        break

                # Swap buffers.
                temp = current_buf
                current_buf = next_buf
                next_buf = temp

                # Update progress
                progress += current_weight
                if self.sector_erase_weight > 0:
                    progress_cb(float(progress) / float(self.sector_erase_weight))

        progress_cb(1.0)

        logging.debug("Estimated sector erase count: %i", self.sector_erase_count)
        logging.debug("Actual sector erase count: %i", actual_sector_erase_count)

        return FlashBuilder.FLASH_SECTOR_ERASE
