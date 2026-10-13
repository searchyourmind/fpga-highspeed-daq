"""Enumerate every failing retained corner against unchanged acceptance limits."""
from pathlib import Path
import json,csv
R=Path(__file__).resolve().parents[3];O=Path(__file__).resolve().parents[1]/'outputs/engineering'
def audit(folder):
 read=lambda n:json.loads((folder/(n+'.json')).read_text())
 p,t,s=read('power-corners'),read('thermal'),read('field-solver');b=p['budget']
 voltage=[{'case':'full-load lower composite','actual_V':b['loaded_min_V'],'limit_V':3.135,'margin_mV':1000*(b['loaded_min_V']-3.135),'root_cause':'Reference/resistor errors plus output copper, ground, contact, dynamic and line/load budgets'}, {'case':'PSM upper plus dynamic composite','actual_V':b['idle_max_V'],'limit_V':3.465,'margin_mV':1000*(3.465-b['idle_max_V']),'root_cause':'PSM feedback upper bound plus resistor/leakage and dynamic allowance; simultaneous occurrence is not established'}]
 thermal=[]
 for i,x in enumerate(t['cases']):
  thermal.append(dict(case_id=i,**{k:x[k] for k in ('ambient_C','h_each_side_W_m2K','assumed_regulator_loss_W','assumed_SSD_heat_into_carrier_W','estimated_regulator_junction_C')},limit_C=125,margin_C=125-x['estimated_regulator_junction_C'],result='PASS_SCREEN' if x['within_125C'] else 'FAIL'))
 si=[]
 for x in s['cases']:
  if x['case'] in ('low_Z','high_Z','no_mask','wide_fanout'):
   z=x['Zdiff_ohm'];si.append(dict(case=x['case'],width_mm=x.get('w',.14),gap_mm=x.get('g',.152),dielectric_mm=x.get('h',.0994),er=x.get('er',4.1),Zdiff_ohm=z,lower_margin_ohm=z-81,upper_margin_ohm=99-z,result='PASS_SCREEN' if 81<=z<=99 else 'FAIL_LOCAL_CROSS_SECTION'))
 return {'voltage':voltage,'thermal_cases':thermal,'thermal_failing_count':sum(x['result']=='FAIL' for x in thermal),'impedance':si}
r={'scope':'Unchanged limits3.135..3.465V,125C,81..99ohm. All thermal rows and both voltage bounds are explicit. Wide fanout/no-mask are local sensitivity cases, not a full channel result.','baseline_rev03':audit(R/'provenance/pcb-rev03-baseline'),'corrected_copper_rev03_1':audit(O),'remaining_gates':['Composite voltage budget, not vendor-guaranteed transient/MLCC bounds','Weak-convection thermal limits and SSD temperature','Broad-process and fanout impedance, cable/connector3D channel','Full part/assembly/mating approval'],'requirements_relaxed':False}
(O/'failure-margins.json').write_text(json.dumps(r,indent=2)+'\n')
for n,a in [('before',r['baseline_rev03']),('after',r['corrected_copper_rev03_1'])]:
 with (O/f'thermal-all-cases-{n}.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=list(a['thermal_cases'][0]));w.writeheader();w.writerows(a['thermal_cases'])
print(json.dumps(r,indent=2))
