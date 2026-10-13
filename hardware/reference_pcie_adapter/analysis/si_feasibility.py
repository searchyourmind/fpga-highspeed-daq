"""Test whether simple line-width retuning closes the ORIGINAL broad process set."""
from pathlib import Path
import json
from field_solver import pair
O=Path(__file__).resolve().parents[1]/'outputs/engineering';rows=[]
for width in (.14,.15,.16,.17):
 bounds=[]
 for name,dw,dg,h,er in [('low',.015,-.015,.08946,4.3),('high',-.015,.015,.10934,3.9)]:
  r,_=pair(w=width+dw,g=.152+dg,h=h,er=er,step=.005);bounds.append(r['Zdiff_ohm'])
 rows.append({'nominal_width_mm':width,'fixed_nominal_gap_mm':.152,'process_low_Z_ohm':bounds[0],'process_high_Z_ohm':bounds[1],'lower_margin_ohm':bounds[0]-81,'upper_margin_ohm':99-bounds[1],'passes_both_original_bounds':bounds[0]>=81 and bounds[1]<=99})
(O/'si-width-feasibility.json').write_text(json.dumps({'scope':'Analysis candidates only. No PCB route change; no narrowed process tolerances.4 widths, same original etch+/-15um,h+/-10%,Er+/-0.2,mask fixed. Finite grid, not proof over all possible geometries.','candidates':rows},indent=2)+'\n');print(rows)
