"""Find a required extra heat path without changing ambient/loss/125C criteria."""
from thermal import plate,O
import json
rows=[]
for rth in (60.,40.,25.,15.):
 r,_=plate(ambient=60,h_air=5,reg_loss=1.,ssd_coupled=1.65,sink_K_W=rth,step=.0005);r['margin_C']=125-r['estimated_regulator_junction_C'];rows.append(r)
lo,hi=1.,100.
for _ in range(14):
 mid=(lo+hi)/2;r,_=plate(ambient=60,h_air=5,reg_loss=1.,ssd_coupled=1.65,sink_K_W=mid,step=.001)
 if r['within_125C']:lo=mid
 else:hi=mid
result={'status':'CANDIDATE_REQUIREMENT_NOT_IMPLEMENTED','scope':'Additional10x10mm contact under regulator region. R includes all PCB-to-contact/interface/sink-to-ambient paths; no assumed commercial sink rating. Covered-side convection removed. Original60C ambient,h5,losses and125C limit unchanged. Extra mounting/thermal assembly absent from CAD and requires3D/mechanical validation.','cases':rows,'coarse_required_total_Rth_at_most_K_W':lo,'manufacturing_released':False}
(O/'thermal-exit-requirement.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
