"""Actual RTL -> memory model -> RTL DMA -> packetizer -> delayed host."""
import csv, json, random, sys
from pathlib import Path
import cocotb
from cocotb.triggers import Timer
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from sim.ddr_behavioral.memory import Memory
from sim.pcie_transaction.transport import Link, ProtocolError
from sim.host_model.receiver import Host, HostRouter
from reference_model import records

class Bench:
    def __init__(self,d,seed=1,latency=3,stall=0.25,capacity=4096,max_words=4,
                 link_latency=7,link_capacity=2,multi_host=False):
        self.d=d; self.rng=random.Random(seed); self.seed=seed; self.stall=stall; self.cycle=0
        self.memory=Memory(capacity=capacity,latency=latency)
        self.link=Link(latency=link_latency,capacity=link_capacity,max_words=max_words)
        self.router=HostRouter(max_words=max_words) if multi_host else None
        self.host=None; self.completions=[]; self.fail_at=None
        self.max_fifo=0; self.link_stalls=0; self.mem_stalls=0
        self.previous={}; self.first_delivery=None; self.frame_latencies=[]
        self.job_start=0; self.force_link_stall=0; self.force_host_stall=0

    async def reset(self):
        d=self.d
        for name in ['clk','rst_n','desc_valid','desc_id','desc_start','desc_length','desc_base','desc_host','desc_owner','frame_len','gain','comp_ready','mem_cmd_ready','mem_rsp_valid','mem_rsp_error','mem_rsp_data','link_ready']:
            getattr(d,name).value=0
        self.memory.reset(); self.link.reset(); self.previous={}; self.host=None; self.completions=[]
        if self.router: self.router.reset()
        for _ in range(2):
            d.clk.value=1; await Timer(2,unit='ns'); d.clk.value=0; await Timer(2,unit='ns')
        d.rst_n.value=1; await Timer(1,unit='ns')
        assert int(d.desc_ready.value)==1 and not int(d.link_valid.value) and not int(d.comp_valid.value)

    async def step(self,comp_ready=1):
        d=self.d; now=self.cycle; rsp=self.memory.response(now)
        d.mem_cmd_ready.value=int(self.memory.ready(now) and self.rng.random()>=self.stall)
        d.mem_rsp_valid.value=int(rsp is not None)
        d.mem_rsp_error.value=int(rsp.error) if rsp else 0
        d.mem_rsp_data.value=(rsp.data[0] if rsp and rsp.data else 0)
        d.link_ready.value=int(now>=self.force_link_stall and self.link.ready() and self.rng.random()>=self.stall)
        d.comp_ready.value=comp_ready
        await Timer(1,unit='ns')
        get=lambda n:int(getattr(d,n).value)
        for name,valid,ready,fields in [
            ('memory','mem_cmd_valid','mem_cmd_ready',['mem_cmd_addr','mem_cmd_write','mem_cmd_data']),
            ('link','link_valid','link_ready',['link_data','link_addr','link_tag','link_length','link_sop','link_eop','link_last']),
            ('completion','comp_valid','comp_ready',['comp_id','comp_status'])]:
            payload=tuple(get(n) for n in fields)
            if name in self.previous: assert get(valid) and payload==self.previous[name], f'{name} changed under stall'
            if get(valid) and not get(ready): self.previous[name]=payload
            else: self.previous.pop(name,None)
        accepted=get('desc_valid') and get('desc_ready')
        if get('mem_rsp_valid') and get('mem_rsp_ready'): self.memory.consume(now)
        if get('mem_cmd_valid') and get('mem_cmd_ready'):
            failure=self.fail_at is not None and len(self.memory.requests)==self.fail_at
            self.memory.accept(now,bool(get('mem_cmd_write')),get('mem_cmd_addr'),
                               (get('mem_cmd_data'),) if get('mem_cmd_write') else (),inject_error=failure)
        if get('link_valid') and get('link_ready'):
            self.link.accept(now,data=get('link_data'),address=get('link_addr'),tag=get('link_tag'),
                length=get('link_length'),sop=get('link_sop'),eop=get('link_eop'),last=get('link_last'))
        if get('comp_valid') and comp_ready: self.completions.append((get('comp_id'),get('comp_status')))
        self.max_fifo=max(self.max_fifo,get('fifo_occupancy'))
        self.link_stalls+=bool(get('link_valid') and not get('link_ready'))
        self.mem_stalls+=bool(get('mem_cmd_valid') and not get('mem_cmd_ready'))
        d.clk.value=1; await Timer(2,unit='ns'); d.clk.value=0; await Timer(2,unit='ns')
        packet=self.link.deliver(now,now>=self.force_host_stall and self.rng.random()>=self.stall)
        if packet:
            assert self.host is not None
            (self.router or self.host).receive(packet)
            if self.first_delivery is None: self.first_delivery=now-self.job_start
            for value in packet.payload:
                if value>>48&1: self.frame_latencies.append(now-self.job_start)
        self.cycle+=1
        return accepted

    async def issue(self,n=16,frame=5,gain=3,start=0,base=0,host=0x1000,tag=9,owner=1):
        d=self.d
        for name,value in dict(desc_length=n,desc_start=start,desc_base=base,desc_host=host,
            desc_id=tag,desc_owner=owner,frame_len=frame,gain=gain,desc_valid=1).items():
            getattr(d,name).value=value
        self.host=self.router.register(tag,host,n) if self.router else Host(tag,host,n,self.link.max_words)
        self.completions=[]; self.first_delivery=None; self.frame_latencies=[]
        self.job_start=self.cycle
        for _ in range(100):
            if await self.step(comp_ready=0): break
        else: raise AssertionError('Descriptor acceptance timeout')
        d.desc_valid.value=0
        # Configuration must have been captured with the descriptor, not one cycle later.
        d.gain.value=0; d.frame_len.value=1

    async def finish(self,expected_status=0,hold_completion=0,wait_host=True):
        for _ in range(50000):
            await self.step(comp_ready=int(hold_completion==0))
            if int(self.d.comp_valid.value) and hold_completion: hold_completion-=1
            if self.completions and (expected_status or not wait_host or self.host.done): break
        else: raise AssertionError('DMA/host completion timeout')
        assert len(self.completions)==1 and self.completions[0][1]==expected_status
        return self.cycle-self.job_start

@cocotb.test()
async def e2e_fixed_seed_matrix(d):
    rows=[]
    cases=[(seed,n,frame,gain,latency,stall) for seed in (11,2026,99173)
           for n,frame,gain,latency,stall in [(1,1,0,1,0),(3,2,1,3,.2),(9,4,5,7,.6),(31,7,255,2,.35),(32,13,2,11,.5)]]
    for seed,n,frame,gain,latency,stall in cases:
        b=Bench(d,seed,latency,stall); await b.reset()
        await b.issue(n,frame,gain,start=29,base=128,tag=seed%65536)
        elapsed=await b.finish(hold_completion=15)
        expected=records(n,frame,gain)
        assert b.host.records==expected, f'seed={seed} n={n}'
        addresses=[128+((29+i)%32)*8 for i in range(n)]
        assert [r[2] for r in b.memory.requests if r[1]]==addresses
        assert [r[2] for r in b.memory.requests if not r[1]]==addresses
        assert len(b.memory.requests)==2*n
        rows.append(dict(seed=seed,records=n,frame_len=frame,gain=gain,memory_latency=latency,
            stall_probability=stall,cycles=elapsed,records_per_cycle=n/elapsed,first_host_cycles=b.first_delivery,
            final_host_cycles=max(b.frame_latencies),max_fifo=b.max_fifo,link_stall_cycles=b.link_stalls,
            memory_stall_cycles=b.mem_stalls,packets=b.link.packet_count,status='MATCH'))
        d._log.info('E2E seed=%d source=%d sink=%d cycles=%d DATA_MATCH',seed,n,len(b.host.records),elapsed)
    target=ROOT/'results'/'benchmark_csv'; target.mkdir(exist_ok=True,parents=True)
    (target/'e2e.json').write_text(json.dumps(rows,indent=2)+'\n')
    with (target/'e2e.csv').open('w') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    (ROOT/'results'/'golden_vectors.json').write_text(json.dumps({'count':32,'frame_len':13,'gain':2,'records':records(32,13,2)},indent=2)+'\n')

@cocotb.test()
async def invalid_descriptors_and_recovery(d):
    b=Bench(d,89); await b.reset()
    cases=[({'n':0},2),({'n':33},2),({'start':32},2),({'base':1},1),({'base':4096-248},1),
           ({'base':0xfffffff8},1),({'host':3},3),({'host':0xfffffffffffffff8,'n':2},3),({'owner':0},4)]
    for overrides,status in cases:
        before=len(b.memory.requests)
        await b.issue(**overrides); await b.finish(status,hold_completion=10)
        assert len(b.memory.requests)==before and not b.link.pending and not b.host.records
    await b.issue(n=17,frame=4,gain=2); await b.finish()
    assert b.host.records==records(17,4,2)

@cocotb.test()
async def long_backpressure_and_descriptor_order(d):
    b=Bench(d,923,latency=1,stall=.1); await b.reset()
    for tag in range(5):
        await b.issue(n=32,frame=3,gain=tag,start=tag*7%32,tag=tag)
        b.force_link_stall=b.cycle+500
        await b.finish(hold_completion=25)
        assert b.completions==[(tag,0)] and b.host.records==records(32,3,tag)

@cocotb.test()
async def memory_faults_abort_and_next_job(d):
    for fail_index in (0,7,16,23):
        b=Bench(d,62); await b.reset(); b.fail_at=fail_index
        await b.issue(n=16); await b.finish(5)
        # Error may leave an incomplete transport packet: host/link are explicitly aborted.
        b.link.reset(); b.fail_at=None
        await b.issue(n=8,frame=2,gain=4,tag=77); await b.finish()
        assert b.host.records==records(8,2,4)

@cocotb.test()
async def reset_inflight_at_multiple_stages(d):
    for delay in (2,17,90,190,300):
        b=Bench(d,440,latency=2,stall=.1); await b.reset(); await b.issue(n=32)
        for _ in range(delay): await b.step(comp_ready=0)
        await b.reset()
        for _ in range(20):
            await b.step(); assert not b.completions and not int(d.link_valid.value)
        await b.issue(n=13,frame=4,gain=7,tag=55); await b.finish()
        assert b.host.records==records(13,4,7)

@cocotb.test()
async def transport_corruption_is_detected(d):
    b=Bench(d,731); await b.reset(); await b.issue(n=13); b.link.corrupt_next=True
    try:
        await b.finish()
    except ProtocolError as exc:
        assert 'CRC' in str(exc)
    else: raise AssertionError('Corrupted payload was accepted')
    await b.reset()
