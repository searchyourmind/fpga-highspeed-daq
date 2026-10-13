"""Day 1: complete test, designed to PASS before you touch stream_fifo.sv."""
import cocotb
from cocotb.triggers import Timer


@cocotb.test()
async def counter_increments_and_holds(dut):
    dut.clk.value = 0
    dut.rst_n.value = 0
    dut.enable.value = 0
    await Timer(2, unit="ns")
    dut.clk.value = 1
    await Timer(2, unit="ns")
    assert int(dut.count.value) == 0
    dut.clk.value = 0
    await Timer(2, unit="ns")
    dut.rst_n.value = 1

    expected = 0
    for enable in (1, 1, 0, 1, 0, 1, 1, 1):
        dut.enable.value = enable
        await Timer(2, unit="ns")
        dut.clk.value = 1
        await Timer(2, unit="ns")
        expected += enable
        assert int(dut.count.value) == expected
        dut.clk.value = 0
        await Timer(2, unit="ns")
