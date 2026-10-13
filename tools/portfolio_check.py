"""Check release links, preserved failures, source identity and real test outputs."""
from pathlib import Path
import argparse, gzip, hashlib, json, re, xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--generated',action='store_true');args=p.parse_args()
base=R/'results' if args.generated else R/'evidence/core'
xmls=sorted(base.glob('*.xml')) if args.generated else sorted((base/'junit').glob('*.xml'))
counts={}
for x in xmls:
    tree=ET.parse(x);cases=list(tree.iter('testcase'))
    assert cases and not any(list(tree.iter(k)) for k in ('failure','error','skipped')), x
    counts[x.name]=len(cases)
assert counts.get('models.xml')==39 and sum(counts.values())==63, counts
if args.generated:
    paths=[base/'benchmark_csv/e2e.json',base/'system-audit/extended-ring-32.json',base/'system-audit/extended-ring-257.json']
else:paths=[base/'scenarios'/n for n in ('e2e.json','extended-ring-32.json','extended-ring-257.json')]
rows=[json.loads(p.read_text()) for p in paths]
assert list(map(len,rows))==[15,9,9] and all(x['status']=='MATCH' for group in rows for x in group)
syn=R/'synthesis/reports' if args.generated else base/'synthesis'
timing=json.loads((syn/'timing-audit.json').read_text())
assert timing['generic_flip_flops']==1447 and timing['longest_path_cells']==42 and timing['nanosecond_STA_executed'] is False
for path,h in timing['source_sha256'].items():assert hashlib.sha256((R/path).read_bytes()).hexdigest()==h,path
original=json.loads((R/'evidence/original-evidence-map.json').read_text())
for f,meta in original.items():assert hashlib.sha256((R/f).read_bytes()).hexdigest()==meta['sha256'], f
board=R/'evidence/pcb/engineering'
v=json.loads((board/'voltage-root-cause.json').read_text());assert v['status']=='FAIL_REQUIREMENTS' and all(x['margin_mV']<0 for x in v['cases'])
t=json.loads((board/'thermal-independent-review.json').read_text());assert t['worst_corrected_fine']['estimated_regulator_junction_C']>160
assert t['status']=='FAIL_REQUIREMENTS' and t['corrected_failing_count']==6
assert len(t['corrected_minimum_outer_copper_cases'])==24 and len(t['original_failing_case_refinement'])==5
si=json.loads((board/'si-independent-review.json').read_text())
assert si['status']=='FAIL_OR_UNQUALIFIED' and len(si['sensitivity_cases'])==31 and not si['fabrication_released']
assert not json.loads((board/'field-solver.json').read_text())['all_screened_corners_in_target']
history=json.loads((R/'evidence/review/reproduction-summary.json').read_text())
for f,h in history['production_source_unchanged_sha256'].items():assert hashlib.sha256((R/f).read_bytes()).hexdigest()==h,f
preserved=json.loads((R/'evidence/engineering-preservation.json').read_text())
for group in preserved['core_and_board_inputs'].values():
    for f,h in group.items():assert hashlib.sha256((R/f).read_bytes()).hexdigest()==h,f
meta=json.loads((R/'portfolio/assets/evidence.json').read_text())
assert hashlib.sha256(gzip.decompress((R/'evidence/core/daq_top.vcd.gz').read_bytes())).hexdigest()==meta['raw_sha256']
files=(R/'release/tracked-files.txt').read_text().splitlines();known=set(files)
missing=[]
for f in files:
    if not f.endswith('.md'):continue
    text=re.sub(r'```.*?```','', (R/f).read_text(),flags=re.S)
    for link in re.findall(r'\]\(([^)]+)\)',text):
        if re.match(r'(?:https?://|mailto:|#)',link):continue
        link=link.split('#')[0].strip('<>');dest=((R/f).parent/link).resolve()
        try: rel=dest.relative_to(R).as_posix()
        except ValueError:missing.append((f,link));continue
        if rel not in known and not any(s.startswith(rel.rstrip('/')+'/') for s in known):missing.append((f,link))
assert not missing,missing
out={'production_tests':sum(counts.values()),'pytest':39,'cocotb':24,'failures':0,'skips':0,'matrix_scenarios':sum(map(len,rows)),'scenario_status':'MATCH','junit_counts':counts,'generic_flip_flops':1447,'topological_path_cells':42,'device_STA':'NOT_EXECUTED','preserved_original_evidence_files':len(original),'production_source_unchanged':True,'markdown_links':'PASS','source':'generated outputs' if args.generated else 'curated evidence'}
print(json.dumps(out,indent=2))
