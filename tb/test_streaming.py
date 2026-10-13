import random
import cocotb
from cocotb.triggers import Timer
from reference_model import records

async def tick(d):
    d.clk.value=1; await Timer(2,unit='ns')
    d.clk.value=0; await Timer(2,unit='ns')

@cocotb.test()
async def streaming_frames_gain_stalls_and_reset(d):
    rng=random.Random(284)
    for count,frame,gain in [(1,1,0),(73,7,1),(1001,13,255),(80,0,2),(500,16,4)]:
        d.clk.value=0; d.rst_n.value=0; d.start.value=0; d.m_ready.value=0
        d.sample_count.value=count; d.frame_len.value=frame; d.gain.value=gain
        await tick(d); await tick(d)
        d.rst_n.value=1; d.start.value=1; await tick(d); d.start.value=0
        expected=records(count,frame,gain); seen=[]; stalled=None
        for cycle in range(count*10+300):
            ready=int(cycle>50 and rng.random()<0.65)
            d.m_ready.value=ready; await Timer(1,unit='ns')
            valid=int(d.m_valid.value); value=int(d.m_data.value)
            if stalled is not None: assert valid and value==stalled
            stalled=value if valid and not ready else None
            if valid and ready: seen.append(value)
            assert int(d.occupancy.value)<=8
            await tick(d)
            if len(seen)==count: break
        assert seen==expected, f'count={count}, frame={frame}, gain={gain}'
        for _ in range(10):
            assert not int(d.m_valid.value); await tick(d)
    # Abort a live pipeline, then ensure no stale record survives.
    d.sample_count.value=100; d.start.value=1; await tick(d); d.start.value=0; d.m_ready.value=0
    for _ in range(15): await tick(d)
    d.rst_n.value=0; await tick(d); d.rst_n.value=1; d.m_ready.value=1
    for _ in range(20):
        assert not int(d.m_valid.value); await tick(d)
