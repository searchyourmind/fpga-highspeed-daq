"""Proposed tighter process window; no fabricator acceptance is implied."""
import json
from pathlib import Path
from field_solver import pair
O=Path(__file__).resolve().parents[1]/'outputs/engineering'
rows=[]
for name,w,g,h,er in [('controlled_low',.145,.147,.0994*.97,4.2),('controlled_high',.135,.157,.0994*1.03,4.0)]:
 r,_=pair(w=w,g=g,h=h,er=er,step=.0025);r['case']=name;rows.append(r)
(O/'process-window.json').write_text(json.dumps({'scope':'Proposed tolerance acceptance only, not vendor commitment: trace etch +/-5um with gap changing oppositely, dielectric height +/-3%, er+/-0.1, same fixed mask model. Other tolerances omitted.','cases':rows,'both_within_81_to_99':all(81<=r['Zdiff_ohm']<=99 for r in rows)},indent=2)+'\n')
print(rows)
