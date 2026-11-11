"""DMA throughput baseline versus memory latency.

The memory model may hold 64 commands and never refreshes, and the link never
stalls, so any shortfall from one word per cycle comes from the RTL itself.
"""
import json
from pathlib import Path
import cocotb
from test_end_to_end import Bench
from reference_model import records
ROOT=Path(__file__).resolve().parents[1]
LATENCIES=(1,2,4,8,16,32)
WORDS=32

@cocotb.test()
async def dma_words_per_cycle_vs_memory_latency(d):
    rows=[]
    for latency in LATENCIES:
        b=Bench(d,seed=5,latency=latency,stall=0,link_capacity=64); await b.reset()
        b.memory.queue_depth=64; b.memory.refresh_period=0
        await b.issue(n=WORDS,frame=8,gain=3); elapsed=await b.finish()
        assert b.host.records==records(WORDS,8,3)
        writes=[r[0] for r in b.memory.requests if r[1]]; reads=[r[0] for r in b.memory.requests if not r[1]]
        assert len(writes)==len(reads)==WORDS
        write_interval=(writes[-1]-writes[0])/(WORDS-1); read_interval=(reads[-1]-reads[0])/(WORDS-1)
        max_in_flight=max(sum(1 for r in b.memory.requests if r[0]<=c<r[0]+latency) for c in writes+reads)
        rows.append(dict(memory_latency=latency,words=WORDS,write_cycles_per_word=write_interval,
            read_cycles_per_word=read_interval,write_words_per_cycle=round(1/write_interval,4),
            read_words_per_cycle=round(1/read_interval,4),max_commands_in_flight=max_in_flight,
            job_cycles=elapsed))
        d._log.info('latency=%d write %.2f cyc/word, read %.2f cyc/word, in flight %d',
                    latency,write_interval,read_interval,max_in_flight)
    target=ROOT/'results'/'benchmark_csv'; target.mkdir(parents=True,exist_ok=True)
    (target/'dma_throughput.json').write_text(json.dumps(rows,indent=2)+'\n')
