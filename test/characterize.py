from pyOCD.board import MbedBoard
from pyOCD.coresight.dap import DebugPort
from pyOCD.pyDAPAccess import DAPAccess
import time


# nrf51
#    - minimum clock frequency
#    - behavior after a reset
# onsemi
# lpc1768
# QSB
# K64F
#    - See why there is a failure on first connect

DP_IDCODE = DAPAccess.REG.DP_0x0
DP_ABORT = DAPAccess.REG.DP_0x0
DP_CTRL_STAT = DAPAccess.REG.DP_0x4
DP_SELECT = DAPAccess.REG.DP_0x8

CSYSPWRUPACK = 0x80000000
CDBGPWRUPACK = 0x20000000
CSYSPWRUPREQ = 0x40000000
CDBGPWRUPREQ = 0x10000000
TRNNORMAL = 0x00000000
MASKLANE = 0x00000f00

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
        link = board.link

        link.set_clock(1000000)
        link.connect()
        link.swj_sequence()
        print("Connected to board")

        # IDCODE must be the first read performed
        idr = link.read_reg(DP_IDCODE)
        print("IDR: 0x%x" % idr)

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

        # Check the initial state of debug power
        link.write_reg(DP_SELECT, 0)
        ctrl_stat = link.read_reg(DP_CTRL_STAT)
        resp = "yes" if ctrl_stat & CDBGPWRUPACK else "no"
        print("Debug powered on initial connect: %s" % resp)
        resp = "yes" if ctrl_stat & CSYSPWRUPACK else "no"
        print("System powered on initial connect: %s" % resp)

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

        # See if SWJ affect power state
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
        print("Debug powered after during hardware reset: %s" % resp)
        resp = "yes" if ctrl_stat & CSYSPWRUPACK else "no"
        print("System powered after during hardware reset: %s" % resp)

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

        link.set_clock(1000000)

        # Check that all frequencies work normally
        print("Supported frequencies 2:")
        for frequency in TEST_FREQUENCIES:

            # Verify the IDR can be read
            link.set_clock(frequency)
            idr = link.read_reg(DP_IDCODE)#dp.read_id_code()
            print("    %s" % frequency)
            #print("IDR: 0x%x" % idr)

        link.set_clock(1000000)

        board.uninit(False)


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
