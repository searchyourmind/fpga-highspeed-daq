"""Independent budget decomposition; preserve every existing error allowance."""
from pathlib import Path
import json
O=Path(__file__).resolve().parents[1]/'outputs/engineering';b=json.loads((O/'power-corners.json').read_text())['budget'];vnom=3.328;tol=.0035;rt=31600;rb=10000
rows=[]
for name,fb,s in [('full_load_low',.7856,-1),('light_load_PSM_high',.8224,1)]:
 reference=fb*(1+rt/rb);divider=fb*(1+rt*(1+s*tol)/(rb*(1-s*tol)));leak=s*100e-9*rt*(1+tol)
 terms=[('nominal',vnom),('reference_error',reference-vnom),('divider_ratio_error',divider-reference),('FB_leakage',leak)]
 if s<0:terms += [('output_copper',-b['copper_drop_V']),('ground_reserve',-.010),('contact_reserve',-.025),('dynamic_reserve',-.040),('line_load_reserve',-.005)]
 else:terms += [('dynamic_reserve',.040),('line_load_reserve',.005)]
 value=sum(x[1] for x in terms);limit=3.135 if s<0 else 3.465
 assert abs(value-b['loaded_min_V' if s<0 else 'idle_max_V'])<1e-12
 rows.append({'case':name,'terms_V':dict(terms),'result_V':value,'limit_V':limit,'margin_mV':(value-limit)*1000 if s<0 else (limit-value)*1000})
# Mode-specific separate evidence, not a substitute: PSM table requires22uF and cannot
# guarantee the16uF stressed external-component transient, nor loaded PWM behavior.
pwm_hi=.8144*(1+rt*(1+tol)/(rb*(1-tol)))+100e-9*rt*(1+tol)+.045
maxdrop=.7856*(1+rt*(1-tol)/(rb*(1+tol)))-100e-9*rt*(1+tol)-.080-3.135
r={'status':'FAIL_REQUIREMENTS','unchanged_bounds_V':[3.135,3.465],'cases':rows,'full_load_PWM_high_budget_V':pwm_hi,'full_load_PWM_high_margin_mV':1000*(3.465-pwm_hi),'permitted_output_drop_for_low_bound_V':maxdrop,'actual_output_drop_V':b['copper_drop_V'],'PSM_high_allowance_left_after_FB_divider_leakage_V':3.465-b['feedback_PSM_high_V'],'required_dynamic_plus_line_load_allowance_V':.045,'caveats':['PSM FB extrema specified at22uF; effective cap16uF stress is outside that table condition, so the existing upper budget is not a complete guarantee.','FB accuracy, line/load and ripple terms may overlap in a joint mode-specific characterization, but no overlap is subtracted without a qualified envelope.','5mV line/load,10mV ground,25mV contact and40mV dynamics are explicit design reserves, not vendor-guaranteed measurements.','Steady current/mode/load consistency is unresolved; conservative composite failure remains.','Worst lower output lacks4.553mV even with corrected copper. Upper bound cannot be repaired by lower copper drop.'],'decision':'No divider or capacitor substitution adopted without qualification. Retain FAIL; obtain joint envelope or redesign regulation.','source':'https://www.ti.com/lit/ds/symlink/tps62130.pdf section7.5'}
(O/'voltage-root-cause.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
