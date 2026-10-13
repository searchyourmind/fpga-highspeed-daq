"""Run a command with durable start/end, actual return code and source snapshot."""
from pathlib import Path
import argparse,datetime,hashlib,json,subprocess,time
R=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('label');p.add_argument('command',nargs=argparse.REMAINDER);a=p.parse_args();cmd=a.command
if cmd and cmd[0]=='--':cmd=cmd[1:]
assert cmd and '/' not in a.label
O=R/'results/release-audit';O.mkdir(exist_ok=True,parents=True)
start=datetime.datetime.now(datetime.timezone.utc).isoformat();timer=time.monotonic()
S=(R/cmd[cmd.index('-C')+1]).resolve() if '-C' in cmd else R
inputs={p.relative_to(S).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for folder in ('rtl','sim','tb','tests','tools','hardware') for p in sorted((S/folder).rglob('*')) if p.is_file() and p.suffix in ('.sv','.py','.sh','.cir','.kicad_pcb','.kicad_sch','.kicad_pro','.json','.csv') and not any(x in p.parts for x in ('__pycache__','outputs','vendor'))}
receipt={'command':cmd,'cwd':str(R),'start_UTC':start,'status':'RUNNING','source_root':str(S),'source_sha256':inputs}
out=O/(a.label+'.json');out.write_text(json.dumps(receipt,indent=2)+'\n')
with (O/(a.label+'.log')).open('w') as f:
 r=subprocess.run(cmd,cwd=R,stdout=f,stderr=subprocess.STDOUT)
receipt.update(status='PASS' if r.returncode==0 else 'FAIL',return_code=r.returncode,elapsed_s=round(time.monotonic()-timer,3),end_UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),log=f'results/release-audit/{a.label}.log')
out.write_text(json.dumps(receipt,indent=2)+'\n');print(a.label,receipt['status'],'exit',r.returncode,flush=True);raise SystemExit(r.returncode)
