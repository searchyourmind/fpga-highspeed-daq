"""Heavy whole-project regeneration; stop on failure and preserve actual return codes."""
import subprocess,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];(R/'results/simulation_logs').mkdir(parents=True,exist_ok=True);status={}
stages=[('verify',['make','verify']),('timing',['make','timing']),('power',['make','power']),('pcb-rebuild',['make','pcb-rebuild']),('pcb-draft',['make','pcb-draft']),('pcb-engineering',['make','pcb-engineering']),('pcb-independent',['make','pcb-independent']),('waveform',['env','WAVES=1','make','e2e']),('release-assets',['make','release-assets']),('portfolio',['make','portfolio'])]
for name,command in stages:
 with (R/f'results/simulation_logs/final-{name}.log').open('w') as f:r=subprocess.run(command,cwd=R,stdout=f,stderr=subprocess.STDOUT)
 status[name]={'command':command,'return_code':r.returncode}
 (R/'results/full-check.json').write_text(json.dumps(status,indent=2)+'\n');print(name,r.returncode,flush=True)
 if r.returncode:raise SystemExit(r.returncode)
print('Model/visual regeneration complete; inspect independent designFAIL/BLOCKED gates.')
