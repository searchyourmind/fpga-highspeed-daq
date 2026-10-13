from collections import deque
import random
import cocotb
from cocotb.triggers import Timer
from test_stream_fifo import reset, step

@cocotb.test()
async def depth_wrap_stability_and_concurrency(d):
    import os
    depth=int(os.environ['FIFO_DEPTH'])
    await reset(d); q=deque(); rng=random.Random(817+depth)
    for i in range(depth): assert (await step(d,q,1,i,0))[0]
    for _ in range(100):
        old=int(d.m_data.value)
        assert not (await step(d,q,1,65535,0))[0]
        assert int(d.m_data.value)==old
    pushed=popped=0; pending=65535
    for cycle in range(3000):
        if pending is None and rng.random()<0.8: pending=rng.randrange(65536)
        a,b=await step(d,q,int(pending is not None),pending or 0,int(rng.random()<0.7))
        pushed+=a; popped+=b
        if a: pending=None
    while pending is not None:
        accepted,_=await step(d,q,valid=1,data=pending,ready=1)
        if accepted: pending=None
    while q: await step(d,q,ready=1)
    assert pushed>500 and popped>500
    await reset(d)
    for _ in range(20):
        assert not (await step(d,deque(),ready=1))[1]
