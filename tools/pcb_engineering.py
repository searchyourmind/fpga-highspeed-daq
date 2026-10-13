"""Re-execute PCB review models. Numerical PASS does not release a board."""
from pathlib import Path
import subprocess,time,json,argparse,hashlib,shutil
R=Path(__file__).resolve().parents[1];A='hardware/reference_pcie_adapter/analysis/';(R/'build/review-r03').mkdir(parents=True,exist_ok=True)
(R/'results/simulation_logs').mkdir(parents=True,exist_ok=True)
stages=[('cad',['make','pcb']),('views',['./tools/run-eda','sh','tools/pcb-views.sh']),('model-fetch',['./tools/run','python','hardware/power_tree/fetch_models.py'])]
for script in ('export_geometry','component_selection','dc_network','dc_analytic_tests','geometry_checks','field_solver','process_window','si_feasibility','thermal','thermal_exit_requirement'):
 stages.append((script,['./tools/run-analysis','python3',A+script+'.py']))
stages += [('power-corners',['./tools/run','python',A+'power_corners.py']),('A-transient',['./tools/run','bash','-c','cd '+A+'; timeout 1800 ngspice -b adapter_transient.cir']),('transient-evidence',['./tools/run','python',A+'transient_evidence.py']),('loaded-corner',['./tools/run','bash','-c','cd '+A+'; timeout 1800 ngspice -b adapter_loaded_corner.cir']),('loaded-evidence',['./tools/run','python',A+'loaded_transient_evidence.py']),('voltage-feasibility',['./tools/run','python',A+'voltage_feasibility.py']),('margin-audit',['./tools/run-analysis','python3',A+'review_margins.py']),('evidence-check',['./tools/run-analysis','python3',A+'check_evidence.py']),('review-Markdown',['./tools/run-analysis','python3',A+'write_review.py']),('review-PDF',['./tools/run-analysis','python3',A+'report.py'])]
ap=argparse.ArgumentParser();ap.add_argument('--resume-reports',action='store_true');args=ap.parse_args()
rows=[];log_prefix='engineering-rerun-'
if args.resume_reports:
 # Resume only presentation stages after successful numeric evidence checking.
 # Validate the exact upstream engineering input snapshot; only report sources may change.
 check=json.loads((R/'results/engineering-check-summary.json').read_text())
 assert check['software_evidence_checks']=='PASS'
 permitted={A+'write_review.py',A+'report.py'}
 for path,digest in check['input_sha256'].items():
  if path not in permitted:assert hashlib.sha256((R/path).read_bytes()).hexdigest()==digest,'Upstream input changed: '+path
 saved=R/'results/engineering-rerun.json';prior=json.loads(saved.read_text())
 stop=next(i for i,x in enumerate(prior) if x['stage']=='review-Markdown')
 rows=prior[:stop];assert rows[-1]['stage']=='evidence-check' and all(x['exit_code']==0 for x in rows)
 backup=R/'results/engineering-before-report-repair.json'
 if not backup.exists():shutil.copy2(saved,backup)
 stages=stages[-2:];log_prefix='engineering-resume-'
 (R/'results/engineering-report-resume.json').write_text(json.dumps({'mode':'Resume only two reporting stages after upstream input SHA256 validation','preserved_failed_run':'results/engineering-before-report-repair.json','upstream_stages':len(rows),'upstream_input_hashes_valid':True},indent=2)+'\n')
for name,command in stages:
 log=R/'results/simulation_logs'/(log_prefix+name+'.log');start=time.time()
 with log.open('w') as f:r=subprocess.run(command,cwd=R,stdout=f,stderr=subprocess.STDOUT)
 rows.append({'stage':name,'command':command,'exit_code':r.returncode,'seconds':time.time()-start,'log':log.relative_to(R).as_posix()})
 (R/'results/engineering-rerun.json').write_text(json.dumps(rows,indent=2)+'\n');print(name,r.returncode,flush=True)
 if r.returncode:raise SystemExit(r.returncode)
print('Numerical evidence complete. Inspect design gates; this is not a hardware release.')
