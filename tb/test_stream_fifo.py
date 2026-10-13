"""Week 1 exercises: scoreboard and backpressure tests for an 8 x 16 FIFO.

These tests are deliberately included BEFORE the RTL is finished, so
`make fifo` should initially FAIL. The tests model transfers at rising edges.
"""
from collections import deque
import random

import cocotb
from cocotb.triggers import Timer


async def reset(dut):
    dut.clk.value = 0
    dut.rst_n.value = 0
    dut.s_valid.value = 0
    dut.s_data.value = 0
    dut.m_ready.value = 0
    await Timer(2, unit="ns")
    for _ in range(2):
        dut.clk.value = 1
        await Timer(2, unit="ns")
        dut.clk.value = 0
        await Timer(2, unit="ns")
    assert int(dut.occupancy.value) == 0
    dut.rst_n.value = 1
    await Timer(2, unit="ns")


async def step(dut, expected, valid=0, data=0, ready=0):
    """Drive before the edge, sample handshakes, check FIFO and Python model."""
    dut.clk.value = 0
    dut.s_valid.value = valid
    dut.s_data.value = data
    dut.m_ready.value = ready
    await Timer(2, unit="ns")

    accepted_input = bool(valid and int(dut.s_ready.value))
    accepted_output = bool(ready and int(dut.m_valid.value))
    if accepted_output:
        assert expected, "DUT output a word with no corresponding input"
        observed = int(dut.m_data.value)
        wanted = expected.popleft()
        assert observed == wanted, f"Data corruption/reorder: got {observed:#06x}, expected {wanted:#06x}"
    if accepted_input:
        expected.append(data)

    dut.clk.value = 1
    await Timer(2, unit="ns")
    observed_count = int(dut.occupancy.value)
    assert observed_count == len(expected), (
        f"FIFO occupancy {observed_count}, reference queue {len(expected)}"
    )
    dut.clk.value = 0
    await Timer(1, unit="ns")
    return accepted_input, accepted_output


@cocotb.test()
async def basic_order(dut):
    q = deque()
    await reset(dut)
    # Send a handful of words with output initially paused.
    for word in (0x1234, 0xABCD, 0x0000, 0xFFFF):
        accepted, _ = await step(dut, q, valid=1, data=word, ready=0)
        assert accepted
    # Then drain and check the entire sequence.
    for _ in range(4):
        _, transferred = await step(dut, q, ready=1)
        assert transferred
    assert not q
    assert int(dut.m_valid.value) == 0


@cocotb.test()
async def full_then_resume(dut):
    q = deque()
    await reset(dut)
    for i in range(8):
        accepted, _ = await step(dut, q, valid=1, data=i + 100, ready=0)
        assert accepted
    assert int(dut.s_ready.value) == 0
    # Hold the ninth word unchanged while the FIFO is full.
    accepted, _ = await step(dut, q, valid=1, data=999, ready=0)
    assert not accepted
    # Free one entry. This simple RTL deliberately doesn't accept on a full cycle.
    accepted, transferred = await step(dut, q, valid=1, data=999, ready=1)
    assert not accepted and transferred
    accepted, _ = await step(dut, q, valid=1, data=999, ready=1)
    assert accepted
    for _ in range(20):
        if not q:
            break
        await step(dut, q, ready=1)
    assert not q


@cocotb.test()
async def random_backpressure(dut):
    q = deque()
    await reset(dut)
    rng = random.Random(2026)
    total_words = 200
    next_word = 0
    pending = None
    for _ in range(4000):
        if pending is None and next_word < total_words and rng.random() < 0.85:
            pending = ((next_word * 91) ^ 0xA55A) & 0xFFFF
        accepted, _ = await step(
            dut, q,
            valid=int(pending is not None),
            data=pending or 0,
            ready=int(rng.random() < 0.60),
        )
        if accepted:
            next_word += 1
            pending = None
        if next_word == total_words and pending is None and not q:
            break
    else:
        assert False, "Timeout: FIFO did not drain all accepted words"
    assert next_word == total_words


@cocotb.test()
async def reset_flushes_pending_words(dut):
    q = deque()
    await reset(dut)
    for word in (1, 2, 3):
        await step(dut, q, valid=1, data=word, ready=0)
    assert q
    await reset(dut)
    assert int(dut.m_valid.value) == 0
    assert int(dut.occupancy.value) == 0
