import pyOCD
from pyOCD.board import MbedBoard
from pyOCD.coresight.dap import DebugPort
from pyOCD.pyDAPAccess import DAPAccess
import time
import traceback
from warnings import catch_warnings


# nrf51
#    - minimum clock frequency
#    - behavior after a reset
# onsemi
# lpc1768
# QSB
# K64F
#    - See why there is a failure on first connect - stikyerr is set
#
# - See if IDR can always be read (regardless of core clock dividers)
#    -Deep sleep mode
#    -Large clock divisors

# Anomalies:
# -nrf51 has a minimum initial connect frequency of 125KHz
# -NCS36510 resets debug power bits when hardware reset is asserted

# TODO
# -try the K64F with greatly divided system clock
# -try the K64F in sleep mode
# -try the K64F constantly resetting
# -K64F slow clock bit
# -TODO - see under which circumstances the NRF51 clock has special requirements - when first swd init only?

# Current sequence
# -Connect with fast clock (Need to determine that this is independent of core clock)
# -

# Notes
# NCS36510 - no minimum initial connect clock
# K64F - no minimum initial connect clock
# NRF51 - Initial connect clock of 125KHz
# LPC 1768 - ?
#
# NCS36510 is having problems with hardware reset because debug power bits aren't set properly


# Metrics
# - Can connect while held in reset?
# - Clock frequency when vector catch on
# - side effect of various reset types

# Structural
# - SWD sequence clocked by core clock?

DEFAULT_TEST_FREQUENCY = 1000000

DP_IDCODE = DAPAccess.REG.DP_0x0
DP_ABORT = DAPAccess.REG.DP_0x0
DP_CTRL_STAT = DAPAccess.REG.DP_0x4
DP_SELECT = DAPAccess.REG.DP_0x8

ABORT_ORUNERRCLR = (1 << 4)
ABORT_WDERRCLR = (1 << 3)
ABORT_STKERRCLR = (1 << 2)
ABORT_STKCMPCLR = (1 << 1)
ABORT_ERR_MASK = (ABORT_ORUNERRCLR | ABORT_WDERRCLR |
                  ABORT_STKERRCLR | ABORT_STKCMPCLR)

CSYSPWRUPACK = 0x80000000
CDBGPWRUPACK = 0x20000000
CSYSPWRUPREQ = 0x40000000
CDBGPWRUPREQ = 0x10000000
TRNNORMAL = 0x00000000
MASKLANE = 0x00000f00

NVIC_AIRCR = (0xE000ED0C)
NVIC_AIRCR_VECTKEY = (0x5FA << 16)
NVIC_AIRCR_VECTRESET = (1 << 0)
NVIC_AIRCR_SYSRESETREQ = (1 << 2)

# Debug Exception and Monitor Control Register
DEMCR = 0xE000EDFC
# DWTENA in armv6 architecture reference manual
DEMCR_TRCENA = (1 << 24)
DEMCR_VC_HARDERR = (1 << 10)
DEMCR_VC_BUSERR = (1 << 8)
DEMCR_VC_CORERESET = (1 << 0)

DHCSR = 0xE000EDF0
C_DEBUGEN = (1 << 0)
C_HALT = (1 << 1)
DBGKEY = (0xA05F << 16)

TEST_FREQUENCIES = [
    100,                # 100 Hz
    1000,               # 1 KHz
    10000,              # 10 KHz
    100000,             # 100 Khz
    1000000,            # 1 MHz
    10000000,           # 10 MHz
]


def main():
    with MbedBoard.chooseBoard(init_board=False, target_override="cortex_m") as board:
        try:
            initial_connect(board)
            mem_test(board)
        finally:
            try:
                board.uninit(False)
            except DAPAccess.Error:
                pass

#TODO - test when held in reset
def mem_test(board):
    link = board.link
    link.set_deferred_transfer(False)

    link.set_clock(DEFAULT_TEST_FREQUENCY)
    # Create the DP and turn on debug.

    dp = pyOCD.coresight.dap.DebugPort(link)
    dp.init()
    dp.power_up_debug()

    # Create an AHB-AP for the CPU.
    ap = pyOCD.coresight.ap.AHB_AP(dp, 0)
    ap.init(True)
    cpu_id = ap.read32(0xE000ED00)
    print("CPU ID: 0x%x" % cpu_id)

    # Read from bus while under reset
    link.assert_reset(True)
    try:
        cpu_id = ap.read32(0xE000ED00)
        print("CPU ID under reset: 0x%x" % cpu_id)
    except DAPAccess.TransferError:
        print("Could not read memory under reset")
    link.assert_reset(False)
    # Re-init
    dp = pyOCD.coresight.dap.DebugPort(link)
    dp.init()
    dp.power_up_debug()
    ap = pyOCD.coresight.ap.AHB_AP(dp, 0)
    ap.init(True)
    cpu_id = ap.read32(0xE000ED00)
    print("CPU ID after re-init: 0x%x" % cpu_id)

    # Try a system reset
    try:
        ap.write32(NVIC_AIRCR, NVIC_AIRCR_VECTKEY | NVIC_AIRCR_SYSRESETREQ)
    except DAPAccess.TransferError:
        pass
    #dp.init()
    cpu_id = ap.read32(0xE000ED00)
    print("CPU ID after SYSRESETREQ: 0x%x" % cpu_id)

    # Try a vector reset
    ap.write32(NVIC_AIRCR, NVIC_AIRCR_VECTKEY | NVIC_AIRCR_VECTRESET)
    cpu_id = ap.read32(0xE000ED00)
    print("CPU ID after VECTRESET: 0x%x" % cpu_id)

#     link.set_clock(DEFAULT_TEST_FREQUENCY)
#     dp = pyOCD.coresight.dap.DebugPort(link)
#     dp.init()
#     dp.power_up_debug()
# 
#     ap = pyOCD.coresight.ap.AHB_AP(dp, 0)
#     ap.init(True)

    print("Supported frequencies:")
    for frequency in TEST_FREQUENCIES:

        try:
            link.set_clock(frequency)
            ap.read32(0xE000ED00)
            print("    %s" % frequency)
        except DAPAccess.TransferError as e:
            print("Exception: %s" % type(e))
            #traceback.print_exc()
            pass

    link.set_clock(DEFAULT_TEST_FREQUENCY)
    # Re-init
    dp = pyOCD.coresight.dap.DebugPort(link)
    dp.init()
    dp.power_up_debug()
    ap = pyOCD.coresight.ap.AHB_AP(dp, 0)
    ap.init(True)

    ap.write32(DHCSR, DBGKEY | C_DEBUGEN)
    # enable the vector catch
    ap.writeMemory(DEMCR, DEMCR_VC_CORERESET)
#     link.assert_reset(True)
#     link.assert_reset(False)
    ap.write32(NVIC_AIRCR, NVIC_AIRCR_VECTKEY | NVIC_AIRCR_SYSRESETREQ)

    dp = pyOCD.coresight.dap.DebugPort(link)
    dp.init()
    dp.power_up_debug()
    ap = pyOCD.coresight.ap.AHB_AP(dp, 0)
    ap.init(True)

    val = ap.readMemory(DHCSR)
    print("DHCSR 0x%x, expected 0x%x" % (val, C_DEBUGEN))
    val = ap.readMemory(DEMCR)
    print("Read 0x%x, expected 0x%x" % (val, DEMCR_VC_CORERESET))
    print("Supported frequencies held in vector catch:")
    for frequency in TEST_FREQUENCIES:

        try:
            link.set_clock(frequency)
            ap.read32(0xE000ED00)
            print("    %s" % frequency)
        except DAPAccess.TransferError as e:
            print("Exception: %s" % type(e))
            traceback.print_exc()
            pass


def lpc_test(board):
    link = board.link
    link.set_deferred_transfer(False)

    dp = pyOCD.coresight.dap.DebugPort(link)
    dp.init()
    dp.power_up_debug()
    ap = pyOCD.coresight.ap.AHB_AP(dp, 0)
    ap.init(True)

    print("DHCSR: 0x%x" % ap.read32(DHCSR))
    ap.write32(DHCSR, DBGKEY | C_DEBUGEN | C_HALT)
    print("DHCSR2: 0x%x" % ap.read32(DHCSR))
    ap.write32(DHCSR, DBGKEY | C_HALT)
    print("DHCSR3: 0x%x" % ap.read32(DHCSR))
    dp.power_down_debug()
    time.sleep(50)
    dp.init()
    dp.power_up_debug()
    print("DHCSR: 0x%x" % ap.read32(DHCSR))
    while True:
        print("DHCSR: 0x%x" % ap.read32(DHCSR))
        time.sleep(1)

    time.sleep(1000)
    exit(0)

# Need to determine (per target)
# -Can target be reset via hardware when DP is powered down?
#

# SWD uninit
# -Need a way for both hardware and software reset to coexist
#    -Software reset - keep debug logic on until target no longer needs to be halted
#    -Hardware reset - turn debug logic off after programming, use reset to hold?
# -

# Hardware cases
# -Reset button goes directly to the target
# -Normal software reset
# -Target specific reset sequence

# 


def initial_connect(board):
    #lpc_test(board)

    link = board.link
    link.set_deferred_transfer(False)

    link.set_clock(1000)#DEFAULT_TEST_FREQUENCY)
    link.connect()
    link.swj_sequence()
    print("Connected to board")

    # IDCODE must be the first read performed
    idr = link.read_reg(DP_IDCODE)
    print("IDR: 0x%x" % idr)
    # Clear any errors that might have occurred
    link.write_reg(DP_ABORT, ABORT_ERR_MASK)

    # Check the initial state of debug power
    link.write_reg(DP_SELECT, 0)
    ctrl_stat = link.read_reg(DP_CTRL_STAT)
    resp = "yes" if ctrl_stat & CDBGPWRUPACK else "no"
    print("Debug powered on initial connect: %s" % resp)
    resp = "yes" if ctrl_stat & CSYSPWRUPACK else "no"
    print("System powered on initial connect: %s" % resp)

    # Check if ID code can be read under reset
    link.assert_reset(True)
    try:
        idr = link.read_reg(DP_IDCODE)
        print("IDCODE accessable under reset: Yes")
    except DAPAccess.TransferError:
        print("IDCODE accessable under reset: No")
    link.assert_reset(False)
    # Reinit
    link.swj_sequence()
    link.read_reg(DP_IDCODE)

    # Check that debug powers on correctly
    power_up_debug(link)
    link.write_reg(DP_SELECT, 0)
    ctrl_stat = link.read_reg(DP_CTRL_STAT)
    if ctrl_stat & CDBGPWRUPACK:
        print("Debug powered on correctly")
    if ctrl_stat & CSYSPWRUPACK:
        print("System powered on correctly")

    # Check that debug powers off correctly
    power_down_debug(link)
    link.write_reg(DP_SELECT, 0)
    ctrl_stat = link.read_reg(DP_CTRL_STAT)
    if not (ctrl_stat & CDBGPWRUPACK):
        print("Debug powered off correctly")
    if not (ctrl_stat & CSYSPWRUPACK):
        print("System powered off correctly")

    # See if SWJ affects power state
    power_up_debug(link)
    link.swj_sequence()
    link.read_reg(DP_IDCODE)
    link.write_reg(DP_SELECT, 0)
    ctrl_stat = link.read_reg(DP_CTRL_STAT)
    resp = "yes" if ctrl_stat & CDBGPWRUPACK else "no"
    print("Debug left on after swj: %s" % resp)
    resp = "yes" if ctrl_stat & CSYSPWRUPACK else "no"
    print("System left on after swj: %s" % resp)

    # See if power is disabled under reset
    power_up_debug(link)
    try:
        link.assert_reset(True)
        link.write_reg(DP_SELECT, 0)
        ctrl_stat = link.read_reg(DP_CTRL_STAT)
        resp = "yes" if ctrl_stat & CDBGPWRUPACK else "no"
        print("Debug powered on during hardware reset: %s" % resp)
        resp = "yes" if ctrl_stat & CSYSPWRUPACK else "no"
        print("System powered on during hardware reset: %s" % resp)
    except DAPAccess.TransferError:
        pass
    link.assert_reset(False)
    link.swj_sequence()
    link.read_reg(DP_IDCODE)

    # Check after reset
    link.write_reg(DP_SELECT, 0)
    ctrl_stat = link.read_reg(DP_CTRL_STAT)
    resp = "yes" if ctrl_stat & CDBGPWRUPACK else "no"
    print("Debug powered after hardware reset: %s" % resp)
    resp = "yes" if ctrl_stat & CSYSPWRUPACK else "no"
    print("System powered after hardware reset: %s" % resp)

    # Check that all frequencies work for connect sequence
    print("Supported frequencies:")
    for frequency in TEST_FREQUENCIES:

        link.assert_reset(True)
        link.assert_reset(False)

        # Verify the IDR can be read
        link.set_clock(frequency)
        link.swj_sequence()
        idr = link.read_reg(DP_IDCODE)#dp.read_id_code()
        print("    %s" % frequency)
        #print("IDR: 0x%x" % idr)

    link.set_clock(DEFAULT_TEST_FREQUENCY)

    # Check that all frequencies work normally
    print("Supported frequencies 2:")
    for frequency in TEST_FREQUENCIES:

        # Verify the IDR can be read
        link.set_clock(frequency)
        idr = link.read_reg(DP_IDCODE)#dp.read_id_code()
        print("    %s" % frequency)
        #print("IDR: 0x%x" % idr)

    link.set_clock(DEFAULT_TEST_FREQUENCY)


def power_up_debug(link):
    # select bank 0 (to access DRW and TAR)
    link.write_reg(DP_SELECT, 0)
    link.write_reg(DP_CTRL_STAT, CSYSPWRUPREQ | CDBGPWRUPREQ)

    while True:
        r = link.read_reg(DP_CTRL_STAT)
        if (r & (CDBGPWRUPACK | CSYSPWRUPACK)) == (CDBGPWRUPACK | CSYSPWRUPACK):
            break

    link.write_reg(DP_CTRL_STAT, CSYSPWRUPREQ | CDBGPWRUPREQ | TRNNORMAL | MASKLANE)
    link.write_reg(DP_SELECT, 0)


def power_down_debug(link):
    # select bank 0 (to access DRW and TAR)
    link.write_reg(DP_SELECT, 0)
    link.write_reg(DP_CTRL_STAT, 0)


if __name__ == "__main__":
    main()
