"""Generic technology-independent Yosys synthesis, no FPGA timing claims."""
from pathlib import Path
import subprocess,json
root=Path(__file__).resolve().parents[1]
reports=root/'synthesis/reports'; reports.mkdir(exist_ok=True,parents=True)
sources=' '.join(str(p.relative_to(root)) for p in sorted((root/'rtl').glob('*.sv')))
script=f'''read_verilog -sv -DSYNTHESIS {sources}
hierarchy -check -top daq_top
synth -top daq_top -noabc
check -assert
tee -o synthesis/reports/generic-stat.json stat -json
write_json synthesis/reports/daq_top.json
write_verilog -noattr synthesis/reports/daq_top_netlist.v
'''
(root/'synthesis/scripts/generic.ys').write_text(script)
subprocess.run(['yosys','-l',str(reports/'yosys.log'),'-s','synthesis/scripts/generic.ys'],cwd=root,check=True)
netlist=json.loads((reports/'daq_top.json').read_text())
counts={name:len(mod.get('cells',{})) for name,mod in netlist['modules'].items()}
assert counts.get('daq_top',0)>0
assert not any('latch' in cell['type'].lower() for mod in netlist['modules'].values() for cell in mod.get('cells',{}).values())
(reports/'summary.json').write_text(json.dumps({'scope':'Generic synthesis only; no target, timing closure, LUT or Fmax claim','cells_by_module':counts},indent=2)+'\n')
print('SYNTHESIS_PASS: hierarchy checked, no inferred latch, generic reports written')
