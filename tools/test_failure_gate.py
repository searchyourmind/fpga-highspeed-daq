"""Exercise an actual deliberately failing cocotb test and require a failed runner."""
from pathlib import Path
import subprocess,sys,json,uuid,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[1]
# This probe also runs on a clean checkout, before any log writer has run.
(R/'results/simulation_logs').mkdir(parents=True,exist_ok=True)
(R/'results/system-audit').mkdir(parents=True,exist_ok=True)
module='failure_probe_'+uuid.uuid4().hex
fixture=R/'tb'/f'{module}.py'
proof=R/'results/runner_failure_probe.xml'
try:
 with fixture.open('x') as f:
  f.write('import cocotb\n@cocotb.test()\nasync def deliberate_failure(dut):\n    assert False, "intentional runner gate probe"\n')
 source='from tools.rtl_tests import run; import sys; run("counter",sys.argv[1],"runner_failure_probe")'
 r=subprocess.run([sys.executable,'-c',source,module],cwd=R,capture_output=True,text=True)
 (R/'results/simulation_logs/runner-failure-gate-probe.log').write_text(r.stdout+r.stderr)
 assert r.returncode!=0 and 'intentional runner gate probe' in r.stdout+r.stderr,(r.returncode,r.stdout,r.stderr)
 tree=ET.parse(proof)
 assert len(list(tree.iter('testcase')))==1 and len(list(tree.iter('failure')))==1
 proof.replace(R/'results/system-audit/runner-failure-probe.xml')
 (R/'results/system-audit/runner-failure-gate.json').write_text(json.dumps({'actual_cocotb_failure_returns_nonzero':True,'exit_code':r.returncode,'intentional_test':'temporary fixture: deliberate_failure','scope':'Generated temporary fixture, removed afterward. Excluded from passing production test counts.'},indent=2)+'\n')
 print('PASS: actual failing cocotb test produced nonzero runner exit')
finally:
 fixture.unlink(missing_ok=True)
