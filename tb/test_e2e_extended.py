"""Actual RTL stress: page boundaries, large odd rings and delayed multi-job host."""
import os,json
from pathlib import Path
import cocotb
from test_end_to_end import Bench
from reference_model import records
ROOT=Path(__file__).resolve().parents[1]
RING=int(os.getenv('DAQ_RING_WORDS','32')); MEM=int(os.getenv('DAQ_MEM_BYTES','4096'));MAX=int(os.getenv('DAQ_MAX_WORDS','4'))
def bench(d,**kw):return Bench(d,capacity=MEM,max_words=MAX,**kw)
def capture_packets(b):
    packets=[];accept=b.link.accept
    def capture(cycle,**kw):
        accept(cycle,**kw)
        if kw['eop']:packets.append(b.link.pending[-1][1])
    b.link.accept=capture
    return packets

@cocotb.test()
async def packet_boundary_split(d):
    b=bench(d,seed=834,latency=2,stall=.25);await b.reset();packets=capture_packets(b)
    await b.issue(n=13,host=0x1ff8,frame=5,gain=7);await b.finish()
    assert b.host.records==records(13,5,7)
    assert packets[0].length==8,'First packet must end at the4KiB boundary'
    assert all((p.address&4095)+p.length<=4096 and p.length<=MAX*8 for p in packets)
    assert sum(p.length for p in packets)==13*8

@cocotb.test()
async def final_address_space_record(d):
    b=bench(d,seed=14);await b.reset()
    await b.issue(n=1,host=2**64-8,gain=3);await b.finish()
    assert b.completions==[(9,0)] and b.host.records==records(1,5,3)

@cocotb.test()
async def next_descriptor_before_previous_host_delivery(d):
    b=bench(d,seed=962,latency=1,stall=.1,link_latency=1500,link_capacity=4,multi_host=True)
    await b.reset();b.force_host_stall=1800
    contexts=[];completed_before_delivery=0
    for tag in range(4):
        await b.issue(n=3,frame=2,gain=tag+1,tag=tag,host=0x1ff8+tag*4096)
        contexts.append(b.host);await b.finish(wait_host=False,hold_completion=3)
        assert b.completions==[(tag,0)]
        completed_before_delivery+=not b.host.done
        # Wait-free consumer behavior must preserve the older tag's receive context.
    assert completed_before_delivery>=2 and len(b.router.contexts)==4
    for _ in range(10000):
        await b.step()
        if all(h.done for h in contexts):break
    else:raise AssertionError('Delayed multi-job host did not drain')
    for tag in range(4):assert b.router.take(tag)==records(3,2,tag+1)
    assert not b.router.contexts and not b.link.pending

@cocotb.test()
async def large_ring_stress_and_repeated_jobs(d):
    rows=[]
    for seed in (77,412,20261012):
        b=bench(d,seed=seed,latency=9,stall=.6);await b.reset()
        for job in range(3):
            n=RING-job;gain=(1,3,255)[job];start=RING-1-job;frame=(7,31,0)[job]
            before=len(b.memory.requests);packets=capture_packets(b)
            await b.issue(n=n,frame=frame,gain=gain,start=start,base=128,host=0x1ff8+4096*job,tag=job)
            elapsed=await b.finish(hold_completion=17)
            assert b.host.records==records(n,frame,gain)
            expected=[128+((start+i)%RING)*8 for i in range(n)]
            reqs=b.memory.requests[before:]
            assert [r[2] for r in reqs if r[1]]==expected
            assert [r[2] for r in reqs if not r[1]]==expected
            assert all((p.address&4095)+p.length<=4096 for p in packets)
            rows.append(dict(seed=seed,job=job,ring_words=RING,records=n,cycles=elapsed,packets=len(packets),max_fifo=b.max_fifo,status='MATCH'))
    (ROOT/'results/system-audit').mkdir(parents=True,exist_ok=True)
    (ROOT/f'results/system-audit/extended-ring-{RING}.json').write_text(json.dumps(rows,indent=2)+'\n')
