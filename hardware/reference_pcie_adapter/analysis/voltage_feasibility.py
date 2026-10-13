"""Solve divider limits against the unchanged conservative voltage budgets."""
from pathlib import Path
import json
O=Path(__file__).resolve().parents[1]/'outputs/engineering'
b=json.loads((O/'power-corners.json').read_text())['budget'];t=b['temp_tolerance_resistors'];rb=10000.;ileak=b['FB_leakage_max_A'];res=b['explicit_unverified_reserves']
vfblo=.7856;vfbhi=.8224
rtmin=(3.135+b['copper_drop_V']+sum(res.values())-vfblo)/(vfblo*(1-t)/(rb*(1+t))-ileak*(1+t))
rtmax=(3.465-res['ripple_transient_peak_V']-res['line_load_regulation_V']-vfbhi)/(vfbhi*(1+t)/(rb*(1-t))+ileak*(1+t))
r={'scope':'Fixed 10kohm bottom resistor, original FB/temperature/leakage and all voltage/drop reserves. Algebraic feasible interval, not another SPICE model.','lower_bound_required_Rtop_ohm':rtmin,'upper_bound_allowed_Rtop_ohm':rtmax,'overlap_ohm':rtmax-rtmin,'divider_only_solution_exists':rtmin<=rtmax,'requirements_relaxed':False,'decision':'Retain divider; do not retarget one rail bound at the expense of the other. Jointly qualified dynamic/regulation limits or power topology changes are required.'}
(O/'voltage-feasibility.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
