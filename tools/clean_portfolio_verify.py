"""Verify the proposed files via an isolated local commit and clean Git clone.

No remote is contacted by Git. Existing directories/evidence are never removed.
Docker must already contain the selected core tools image.
"""
from pathlib import Path
import argparse, datetime, hashlib, json, os, subprocess, time
R=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('destination');p.add_argument('--assets',action='store_true');p.add_argument('--check',action='store_true');a=p.parse_args()
D=Path(a.destination).resolve();assert not D.exists(),'Use a new path to preserve earlier evidence';D.mkdir(parents=True)
S=D/'source';C=D/'checkout';O=D/'logs';O.mkdir()
env=os.environ.copy();env['DAQ_TOOLS_IMAGE']=env.get('DAQ_TOOLS_IMAGE','fpga-daq-tools:release-audit')
records=[]
def run(label,command,cwd):
    start=datetime.datetime.now(datetime.timezone.utc).isoformat();timer=time.monotonic()
    with (O/(label+'.log')).open('w') as f:r=subprocess.run(command,cwd=cwd,env=env,stdout=f,stderr=subprocess.STDOUT)
    row={'label':label,'command':command,'cwd':str(cwd),'environment':{'DAQ_TOOLS_IMAGE':env['DAQ_TOOLS_IMAGE']},'start_UTC':start,'elapsed_s':round(time.monotonic()-timer,3),'return_code':r.returncode,'log':label+'.log'}
    records.append(row);(O/'commands.json').write_text(json.dumps(records,indent=2)+'\n');print(label,'exit',r.returncode,flush=True)
    if r.returncode:raise SystemExit(r.returncode)
run('snapshot',['python3','tools/portfolio_release.py','snapshot',str(S)],R)
run('git-init',['git','init','-b','portfolio-candidate'],S)
run('git-add',['git','add','--pathspec-from-file=release/tracked-files.txt'],S)
run('git-commit',['git','-c','user.name=Local verification','-c','user.email=verification@example.invalid','commit','-m','Portfolio verification snapshot'],S)
run('git-clone',['git','clone','--local',str(S),str(C)],D)
assert all(not (C/x).exists() for x in ('results','build','synthesis/reports','hardware/power_tree/vendor'))
files=subprocess.check_output(['git','ls-files'],cwd=C,text=True).splitlines()
assert files==(C/'release/tracked-files.txt').read_text().splitlines()
inputs={f:hashlib.sha256((C/f).read_bytes()).hexdigest() for f in files}
core={f:h for f,h in inputs.items() if f.startswith(('rtl/','sim/','tb/','tests/','tools/','synthesis/')) or f in ('Makefile','requirements.txt','.dockerignore')}
(O/'checkout.json').write_text(json.dumps({'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=C,text=True).strip(),'initial_git_status':subprocess.check_output(['git','status','--porcelain'],cwd=C,text=True),'git_remotes':subprocess.check_output(['git','remote','-v'],cwd=C,text=True),'clone_type':'Local only; origin points at isolated source snapshot, no GitHub remote','preexisting_generated_directories':False,'file_count':len(files),'tracked_file_sha256':inputs,'reproduction_input_sha256':core},indent=2)+'\n')
run('versions',['./tools/run','bash','tools/versions.sh'],C)
run('image',['docker','image','inspect',env['DAQ_TOOLS_IMAGE'],'--format','{{.Id}} {{.Os}}/{{.Architecture}}'],C)
run('verify',['make','verify'],C)
run('timing',['make','timing'],C)
run('oracles',['./tools/run','python','tools/independence_audit.py'],C)
run('failure-gate',['./tools/run','python','tools/test_failure_gate.py'],C)
run('mutations',['python3','tools/mutation_audit.py'],C)
if a.assets:
    run('waveform',['env','WAVES=1','make','e2e'],C)
    run('assets',['make','release-assets'],C)
if a.check:run('integrity',['python3','tools/portfolio_check.py','--generated'],C)
run('git-status',['git','status','--porcelain'],C)
if not a.assets:assert not (O/'git-status.log').read_text().strip(),'Tracked files changed during verification'
for f,h in core.items():assert hashlib.sha256((C/f).read_bytes()).hexdigest()==h,f
print('CLEAN_CHECKOUT_PASS',C,flush=True)
