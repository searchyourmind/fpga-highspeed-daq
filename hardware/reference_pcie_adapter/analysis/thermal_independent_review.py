"""Audit the five thermal failures, convergence and loss attribution independently."""
from thermal import plate,O
import numpy as np,json,math
old=json.loads((O/'thermal.json').read_text());fail=[(i,r) for i,r in enumerate(old['cases']) if not r['within_125C']]
rows=[]
for i,c in fail:
 runs=[]
 for mesh in (.001,.0005,.00025):
  r,_=plate(step=mesh,ambient=c['ambient_C'],h_air=c['h_each_side_W_m2K'],reg_loss=c['assumed_regulator_loss_W'],ssd_coupled=c['assumed_SSD_heat_into_carrier_W']);r['margin_C']=125-r['estimated_regulator_junction_C'];runs.append(r)
 rows.append({'original_case_id':i,'mesh_runs':runs,'last_mesh_delta_C':abs(runs[-1]['estimated_regulator_junction_C']-runs[-2]['estimated_regulator_junction_C'])})
# Source attribution via linear superposition at the SAME original worst-case hotspot.
full,(_,_,T)=plate(ambient=60,h_air=5,reg_loss=1,ssd_coupled=1.65,step=.0005)
parts=[];total_map=np.zeros_like(T)
for name,args in [('regulator',dict(reg_loss=1,ind_loss=0,ssd_coupled=0,copper_loss=0)),('inductor',dict(reg_loss=0,ind_loss=.25,ssd_coupled=0,copper_loss=0)),('SSD_coupling',dict(reg_loss=0,ind_loss=0,ssd_coupled=1.65,copper_loss=0)),('copper',dict(reg_loss=0,ind_loss=0,ssd_coupled=0,copper_loss=.25))]:
 r,(x,y,part)=plate(ambient=0,h_air=5,step=.0005,**args);total_map+=part
 mask=(abs(x[None,:]-.015)<=.0015)&(abs(y[:,None]-.034)<=.0015)
 # Location chosen from the complete solve, not each component's unrelated maximum.
 idx=np.unravel_index(np.argmax(np.where(mask,T,-np.inf)),T.shape)
 parts.append({'source':name,'board_rise_at_full_regulator_hotspot_C':float(part[idx]),'junction_path_rise_C':r['estimated_regulator_junction_C']-float(part[mask].max())})
error=float(np.max(abs(total_map-(T-60))));assert error<1e-8
# Manufactured uniform-source solution is spatially constant, even for nonuniform K.
r,(_,_,u)=plate(ambient=40,h_air=5,uniform_heat_W=1,step=.001)
expected=40+1/(2*5*.080*.078);uniform_error=float(np.max(abs(u-expected)));assert uniform_error<1e-8
# Correct the corner assumption mismatch: DC extraction uses30um minimum outer Cu,
# while the older thermal screen used35um nominal. Retain both, never lower losses/ambient.
min_copper=[]
for i,c in enumerate(old['cases']):
 r,_=plate(step=.0005,outer_cu_um=30,ambient=c['ambient_C'],h_air=c['h_each_side_W_m2K'],reg_loss=c['assumed_regulator_loss_W'],ssd_coupled=c['assumed_SSD_heat_into_carrier_W']);r.update(case_id=i,margin_C=125-r['estimated_regulator_junction_C']);min_copper.append(r)
worst=max(min_copper,key=lambda x:x['estimated_regulator_junction_C'])
# Rerun fine-grid worst with30um; not just convergence at the benign default point.
fine,_=plate(step=.00025,outer_cu_um=30,ambient=60,h_air=5,reg_loss=1,ssd_coupled=1.65)
case3,_=plate(step=.00025,outer_cu_um=30,ambient=25,h_air=5,reg_loss=1,ssd_coupled=1.65)
assert abs(case3['estimated_regulator_junction_C']-(fine['estimated_regulator_junction_C']-35))<1e-6
r={'case3_corrected_fine':case3,'status':'FAIL_REQUIREMENTS','original_failing_case_refinement':rows,'loss_attribution_worst35um_0p5mm':parts,'superposition_max_error_C':error,'uniform_source_exact_solution_error_C':uniform_error,'uniform_expected_C':expected,'original_total_heat_W':3.15,'worst_average_board_rise_analytic_C':3.15/(2*5*.080*.078),'corrected_minimum_outer_copper_cases':min_copper,'corrected_failing_count':sum(not x['within_125C'] for x in min_copper),'worst_corrected':worst,'worst_corrected_fine':fine,'worst_corrected_mesh_delta_C':abs(worst['estimated_regulator_junction_C']-fine['estimated_regulator_junction_C']),'model_limits':['Losses, convection, material conductivities and heat coupling assumed. This is an isothermal-thickness2D sheet, not validated3D thermal analysis.','35um nominal was inconsistent with the30um copper minimum used for DC screening. New independent corner corrects this assumption; CAD unchanged.','Original159.38C is extrapolated beyond125C recommended and150C absolute maximum, near160C typical shutdown. It indicates failure, not sustainable operation or a prediction of measured die temperature.','4.5K/W thetaJCbottom plus simplified via/solder path assumes heat leaves through bottom. The lumped model and other heat paths need3D/package validation.','No relaxation of125C, original loss/ambient/h assumptions or SSD limits.'],'sources':['https://www.ti.com/lit/ds/symlink/tps62130.pdf','https://www.ti.com/lit/an/spra953d/spra953d.pdf']}
(O/'thermal-independent-review.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:r[k] for k in ('status','corrected_failing_count','worst_corrected','worst_corrected_mesh_delta_C','loss_attribution_worst35um_0p5mm','superposition_max_error_C','uniform_source_exact_solution_error_C')},indent=2))
