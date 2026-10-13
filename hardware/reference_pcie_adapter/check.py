"""Actual KiCad checks: generate evidence, then FAIL if any release gate is open."""
from pathlib import Path
import subprocess,json,collections,sys,xml.etree.ElementTree as ET
H=Path(__file__).resolve().parent;K=H/'kicad';O=H/'outputs'
O.mkdir(parents=True,exist_ok=True)
for kind,src in [('sch',K/'pi5_m2_reference.kicad_sch'),('pcb',K/'pi5_m2_reference.kicad_pcb')]:
 args=['kicad-cli',kind,'erc' if kind=='sch' else 'drc','--format','json','-o',str(O/('erc.json' if kind=='sch' else 'drc.json'))]
 if kind=='pcb':args+=['--schematic-parity','--all-track-errors']
 subprocess.run(args+[str(src)],check=True)
subprocess.run(['kicad-cli','sch','export','netlist','--format','kicadxml','-o',str(O/'reference.net'),str(K/'pi5_m2_reference.kicad_sch')],check=True)
# Independent critical pin map checks against KiCad's exported connectivity.
tree=ET.parse(O/'reference.net');pins={}
for net in tree.findall('.//nets/net'):
 for node in net.findall('node'):pins[(node.get('ref'),node.get('pin'))]=net.get('name')
for pin,net in {'4':'CLK_P','5':'CLK_N','7':'RX_P','8':'RX_N','10':'TX_P','11':'TX_N','13':'PWR_EN','14':'DET_WAKE'}.items():assert pins['J1',pin]=='/'+net
for pin,net in {'43':'RX_P','41':'RX_N','49':'TX_P','47':'TX_N','55':'CLK_P','53':'CLK_N','69':'GND','50':'RESET_SSD','52':'CLKREQ_SSD'}.items():assert pins['J2',pin]=='/'+net
assert pins['J1','1']!=pins['J3','1'] and pins['J3','1']=='/EXT_5V'
assert pins['U1','13']=='/PWR_EN' and pins['U2','6']==pins['Q1','1']=='/PG'
erc=json.loads((O/'erc.json').read_text());drc=json.loads((O/'drc.json').read_text())
summary={'native_pin_contracts':'PASS','erc_violations':sum(len(s['violations']) for s in erc['sheets']),
 'drc_geometric_violations':len(drc['violations']),'drc_unconnected_items':len(drc['unconnected_items']),
 'schematic_parity_issues':len(drc['schematic_parity']),'fabrication_released':False}
summary['cad_checks']='FAIL' if any(summary[k] for k in ('erc_violations','drc_geometric_violations','drc_unconnected_items','schematic_parity_issues')) else 'PASS'
summary['release_gate']='FAIL' if summary['cad_checks']=='FAIL' else 'REVIEW_REQUIRED'
(O/'check-summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
sys.exit(1 if summary['release_gate']=='FAIL' else 0)
