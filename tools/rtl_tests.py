#!/usr/bin/env python3
import argparse, os, sys, signal
from pathlib import Path
from cocotb_tools.runner import get_runner
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.check_junit import require_pass

def run(top,module,name=None,params=None,env=None):
    name=name or top
    # A Verilator assertion abort can hang cocotb shutdown. Bound the isolated
    # container process so a real design failure never needs manual termination.
    timeout_seconds=int(os.environ.get('DAQ_SIM_TIMEOUT_S','180'))
    if timeout_seconds <= 0:
        raise ValueError('DAQ_SIM_TIMEOUT_S must be positive')
    def timed_out(signum,frame):
        os.write(2,f'REGRESSION_TIMEOUT {name}: {timeout_seconds}s wall limit; FAIL\n'.encode())
        os._exit(124)
    old_handler=signal.signal(signal.SIGALRM,timed_out)
    signal.alarm(timeout_seconds)
    (ROOT/'results/system-audit').mkdir(parents=True,exist_ok=True)
    runner=get_runner('verilator')
    sources=[ROOT/'rtl'/f'{top}.sv'] if top in ('counter','stream_fifo','stream_processor','dma_descriptor','tlp_packetizer') else sorted((ROOT/'rtl').glob('*.sv'))
    build=ROOT/'build'/name
    runner.build(sources=sources,hdl_toplevel=top,build_dir=build,parameters=params or {},
                 build_args=['--assert','--Wall','-Wno-PINCONNECTEMPTY'],waves=os.getenv('WAVES')=='1')
    result_path=ROOT/'results'/f'{name}.xml'
    result_path.unlink(missing_ok=True)
    runner.test(hdl_toplevel=top,test_module=module,test_dir=ROOT/'tb',build_dir=build,
                results_xml=ROOT/'results'/f'{name}.xml',extra_env=env or {},waves=os.getenv('WAVES')=='1')
    count=require_pass(result_path)
    signal.alarm(0)
    signal.signal(signal.SIGALRM,old_handler)
    print(f'REGRESSION_PASS {name}: {count} cases',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('suite',choices=['counter','fifo','streaming','e2e','extended','all']); a=p.parse_args()
    if a.suite in ('counter','all'): run('counter','test_counter')
    if a.suite in ('fifo','all'):
        run('stream_fifo','test_stream_fifo')
        for depth in (1,3,8,16): run('stream_fifo','test_fifo_extended',f'fifo_depth_{depth}',{'DEPTH':depth},{'FIFO_DEPTH':str(depth)})
    if a.suite in ('streaming','all'): run('streaming_top','test_streaming')
    if a.suite in ('e2e','all'): run('daq_top','test_end_to_end')

    if a.suite in ('extended','all'):
        for ring,depth,words,mem in ((32,8,4,4096),(257,3,8,8192)):
            run('daq_top','test_e2e_extended',f'e2e_extended_{ring}',
                {'RING_WORDS':ring,'FIFO_DEPTH':depth,'MAX_WORDS':words,'MEM_BYTES':mem},
                {'DAQ_RING_WORDS':str(ring),'DAQ_MAX_WORDS':str(words),'DAQ_MEM_BYTES':str(mem)})
