"""Isolated deliberate defects: prove selected checkers detect bad designs/models."""
from pathlib import Path
import shutil,subprocess,json,xml.etree.ElementTree as ET,time,tempfile
R=Path(__file__).resolve().parents[1];O=R/'results/release-audit';B=R/'build/mutation-audit';B.mkdir(exist_ok=True,parents=True);B=Path(tempfile.mkdtemp(prefix='run-',dir=B));O.mkdir(parents=True,exist_ok=True)
specs=[
 ('sample_stride','rtl/sensor_source.sv',"32'd73","32'd74",'rtl','daq_top','test_end_to_end'),
 ('saturation','rtl/stream_processor.sv',"16'hffff","16'hfffe",'rtl','streaming_top','test_streaming'),
 ('ring_wrap','rtl/dma_writer.sv','RING_WORDS-1','RING_WORDS-2','rtl','daq_top','test_end_to_end'),
 ('packet_boundary','rtl/tlp_packetizer.sv','(bounded < page_words) ? bounded : page_words','bounded + (page_words & 16\'d0)','rtl','daq_top','test_e2e_extended'),
 ('host_crc','sim/pcie_transaction/transport.py','if self.crc != checksum:','if False and self.crc != checksum:','python','',''),
 ('memory_bounds','sim/ddr_behavioral/memory.py','address + length * 8 > self.capacity','address + length * 8 > self.capacity + 64','python','',''),
]
rows=[]
for label,filename,old,new,kind,top,module in specs:
 d=B/label;assert not d.exists(),f'Preserve prior mutation run: {d}'
 d.mkdir()
 for folder in ('rtl','sim','tb','tests','tools'):
  shutil.copytree(R/folder,d/folder,ignore=shutil.ignore_patterns('__pycache__','*.vcd'))
 (d/'results/system-audit').mkdir(parents=True);p=d/filename;s=p.read_text();assert old in s;p.write_text(s.replace(old,new,1))
 if kind=='rtl':cmd=['./tools/run','timeout','--kill-after=5','60','env','DAQ_SIM_TIMEOUT_S=15','python','-c',f'from tools.rtl_tests import run;run({top!r},{module!r},"mutation")']
 else:cmd=['./tools/run','timeout','--kill-after=5','60','env','DAQ_SIM_TIMEOUT_S=15','python','-m','pytest','-q','tests/test_models.py','--junitxml=results/mutation.xml']
 start=time.monotonic()
 with (O/f'mutation-{label}.log').open('w') as f:r=subprocess.run(cmd,cwd=d,stdout=f,stderr=subprocess.STDOUT)
 xml=d/'results/mutation.xml';failures=[]
 if xml.exists():
  tree=ET.parse(xml);failures=[(x.get('name'),x.find('failure').get('message')) for x in tree.iter('testcase') if x.find('failure') is not None]
 text=(O/f'mutation-{label}.log').read_text();detected=r.returncode!=0 and (bool(failures) or 'Assertion failed' in text)
 row=dict(mutation=label,file=filename,original=old,modified=new,return_code=r.returncode,watchdog_used=r.returncode in (124,137),detected_by_runtime_checks=detected,failed_cases=failures,elapsed_s=round(time.monotonic()-start,2))
 rows.append(row);(O/'mutation-summary.json').write_text(json.dumps({'scope':'Selected deliberate defects, isolated copies only; not a coverage percentage or production tests. No production RTL/model files modified.','cases':rows},indent=2)+'\n');print(label,r.returncode,detected,flush=True)
 assert detected,row
