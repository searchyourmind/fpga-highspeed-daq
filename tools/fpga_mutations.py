"""Deliberate board-top defects in isolated copies: prove test_fpga_top detects each one."""
from pathlib import Path
import json,shutil,subprocess,tempfile
R=Path(__file__).resolve().parents[1];O=R/'results/fpga';O.mkdir(parents=True,exist_ok=True)
B=R/'build/fpga-mutations';B.mkdir(parents=True,exist_ok=True);B=Path(tempfile.mkdtemp(prefix='run-',dir=B))
specs=[
 ('addr_upper','fpga/rtl/fpga_top.sv',' ^ link_addr[63:32]',''),
 ('addr_lower','fpga/rtl/fpga_top.sv','^ link_addr[31:0] ',''),
 ('tag_length_swap','fpga/rtl/fpga_top.sv','^ {link_tag, link_length}','^ {link_length, link_tag}'),
 ('sop_eop_swap','fpga/rtl/fpga_top.sv',"5'b11010, link_last, link_eop, link_sop}","5'b11010, link_last, link_sop, link_eop}"),
 ('bram_index','fpga/rtl/bram_memory.sv','rsp_data       <= storage[index];','rsp_data       <= storage[index ^ 1];'),
 ('uart_rx_bit_order','fpga/rtl/uart_rx.sv','shift <= {rx_sync, shift[7:1]};','shift <= {shift[6:0], rx_sync};'),
]
rows=[]
for label,filename,old,new in specs:
    d=B/label
    for folder in ('rtl','fpga','sim','tb','tools'):
        shutil.copytree(R/folder,d/folder,ignore=shutil.ignore_patterns('__pycache__','*.vcd'))
    p=d/filename;s=p.read_text();assert s.count(old)==1,(label,old);p.write_text(s.replace(old,new))
    with (O/f'mutation-{label}.log').open('w') as f:
        r=subprocess.run(['./tools/run','python','tools/rtl_tests.py','fpga'],cwd=d,stdout=f,stderr=subprocess.STDOUT)
    rows.append(dict(mutation=label,file=filename,original=old,modified=new,detected=r.returncode!=0))
    print(label,'detected' if r.returncode else 'MISSED',flush=True)
(O/'mutation-summary.json').write_text(json.dumps({'scope':'Deliberate board-top defects in isolated copies; production files unchanged','cases':rows},indent=2)+'\n')
assert all(r['detected'] for r in rows),rows
print(f'FPGA_MUTATIONS_PASS: {len(rows)}/{len(rows)} detected')
