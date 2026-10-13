"""Executed structural timing audit; deliberately no fabricated delay or Fmax."""
from pathlib import Path
import subprocess,json,re,hashlib
R=Path(__file__).resolve().parents[1];O=R/'synthesis/reports';O.mkdir(exist_ok=True,parents=True)
script='''read_json synthesis/reports/daq_top.json
hierarchy -check -top daq_top
flatten
clean
check -assert
scc -expect 0
tee -o synthesis/reports/longest-path.txt ltp -noff
tee -o synthesis/reports/flattened-stat.json stat -json
write_json synthesis/reports/flattened.json
'''
(R/'synthesis/scripts/structural-timing.ys').write_text(script)
subprocess.run(['yosys','-l',str(O/'structural-timing.log'),'-s','synthesis/scripts/structural-timing.ys'],cwd=R,check=True)
n=json.loads((O/'flattened.json').read_text())['modules']['daq_top'];clock=n['ports']['clk']['bits'];ffs=[c for c in n['cells'].values() if 'DFF' in c['type'].upper()]
assert ffs and all(c['connections'].get('C')==clock for c in ffs),'Unexpected register clock domain'
p=(O/'longest-path.txt').read_text();m=re.search(r'length[= ]+(\d+)',p);assert m,p
result={'status':'PARTIAL','completed':['Generic synthesis and hierarchy checks','Flattened combinational-loop count zero','All mapped generic flip-flops use top clk','Longest combinational topological path with FFs excluded'], 'longest_path_cells':int(m.group(1)),'generic_flip_flops':len(ffs),'clock_domains_seen':1,'nanosecond_STA_executed':False,'setup_hold_slack':None,'fmax_MHz':None,'remaining':'A selected FPGA/device/speed grade, vendor delay models and placement/routing are absent. Example SDC is an unapproved100MHz scenario, not a timing result.','source_sha256':{p.relative_to(R).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((R/'rtl').glob('*.sv'))}}
(O/'timing-audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
