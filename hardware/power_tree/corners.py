"""Run independent operating-point cases using original TI CCM average model."""
from pathlib import Path
import subprocess,json,re
H=Path(__file__).resolve().parent;O=H.parents[1]/'results/power';results=[]
for vin in (5.,12.,16.):
 for current in (.5,1.,2.):
  source=(H/'tps62130_average.cir').read_text().split('.control')[0]
  source=source.replace('Vinput vin 0 12',f'Vinput vin 0 {vin}').replace('Rload out 0 3.3',f'Rload out 0 {3.3/current}')
  source+='\n.control\nop\nprint v(out)\nquit\n.endc\n.end\n'
  path=H/'corner.cir';path.write_text(source)
  run=subprocess.run(['ngspice','-b',path.name],cwd=H,capture_output=True,text=True,timeout=20)
  out=run.stdout+run.stderr;(O/f'corner-{vin:g}V-{current:g}A.log').write_text(out)
  assert run.returncode==0,out
  v=float(re.search(r'v\(out\)\s*=\s*(\S+)',out).group(1));assert 3.15<v<3.45
  results.append({'Vin_V':vin,'nominal_load_A':current,'simulated_Vout_V':v,'status':'PASS'})
path.unlink();(O/'dc-corners.json').write_text(json.dumps(results,indent=2)+'\n');print('PASS: 9 TI average-model voltage/load operating points; no thermal, efficiency or stability guarantee')
