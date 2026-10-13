"""Extract every-point extrema from the completed loaded corner, retaining scope limits."""
from pathlib import Path
import json,hashlib
import numpy as np
import matplotlib.pyplot as plt
H=Path(__file__).resolve().parent; R=H.parents[2]; O=H.parent/'outputs/engineering'
a=np.loadtxt(R/'build/review-r03/adapter-loaded-corner.txt',skiprows=1)
t,v,load,pg,current,en=a.T
assert np.isfinite(a).all() and t[-1]>=.00305 and len(a)>10000
trap=np.trapezoid
windows={}
for name,(start,end) in {'pre_step':(.00195,.00205),'load_step':(.00209,.0025),'post_step':(.0026,.00275),'disabled':(.00285,.00305)}.items():
 m=(t>=start)&(t<=end); tt=t[m]
 row={'start_s':start,'end_s':end,'points':int(m.sum())}
 for label,x in [('regulator',v),('load',load)]:
  row[label]={'min_V':float(x[m].min()),'max_V':float(x[m].max()),'mean_V':float(trap(x[m],tt)/(tt[-1]-tt[0]))}
 row.update(PG_min_V=float(pg[m].min()),PG_max_V=float(pg[m].max()),inductor_peak_A=float(current[m].max()))
 windows[name]=row
excursion=max(abs(windows['load_step']['regulator'][k]-windows['pre_step']['regulator']['mean_V']) for k in ('min_V','max_V'))
checks={'pre_step_load_within_5pct':3.135<=windows['pre_step']['load']['min_V']<=windows['pre_step']['load']['max_V']<=3.465,'load_event_within_5pct':3.135<=windows['load_step']['load']['min_V']<=windows['load_step']['load']['max_V']<=3.465,'steady_PG_high':windows['post_step']['PG_min_V']>4.,'disabled_PG_low':windows['disabled']['PG_max_V']<.4,'peak_current_below_room_limit':float(current.max())<3.6}
result={'status':'PASS_MODEL_CHECKS' if all(checks.values()) else 'FAIL_MODEL_CHECKS','raw_points':len(a),'end_s':float(t[-1]),'source_sha256':hashlib.sha256((H/'adapter_loaded_corner.cir').read_bytes()).hexdigest(),'model':'TI TPS62130A SLVM893A unmodified, room-temperature internal behavior','scope':'4.65V input; L=1.232uH, DCR=75mohm, Cout=16uF, ESR=10mohm; 18.5804443272mohm equivalent output board path extracted at125C. 0.5A resistive baseline plus1.5A current pulse. External parts are stressed; this is not a hot regulator model, process sweep, worst feedback error, ground/contact drop, loop stability or silicon qualification.','windows':windows,'checks':checks,'regulator_event_peak_excursion_V':excursion,'existing_40mV_reserve_margin_V':.040-excursion,'event_load_lower_margin_V':windows['load_step']['load']['min_V']-3.135,'event_load_upper_margin_V':3.465-windows['load_step']['load']['max_V'],'overall_inductor_peak_A':float(current.max())}
(O/'adapter-loaded-corner.json').write_text(json.dumps(result,indent=2)+'\n')
idx=np.unique(np.r_[np.arange(0,len(a),max(1,len(a)//20000)),len(a)-1]); np.savetxt(O/'adapter-loaded-corner-preview.csv',a[idx],delimiter=',',header='time_s,regulator_V,load_V,PG_V,inductor_A,EN_V',comments='')
fig,axs=plt.subplots(2,1,figsize=(8,5.5),layout='constrained')
axs[0].plot(t[idx]*1e3,v[idx],label='Regulator');axs[0].plot(t[idx]*1e3,load[idx],label='Load');axs[0].plot(t[idx]*1e3,en[idx],label='EN',alpha=.6);axs[0].set(ylabel='V',title='TPS62130A: loaded external-component corner');axs[0].legend(ncol=3)
ids=np.flatnonzero((t>=.00205)&(t<=.0025))[::40]
axs[1].plot(t[ids]*1e3,v[ids],label='Regulator');axs[1].plot(t[ids]*1e3,load[ids],label='Load');axs[1].axhline(3.135,color='r',ls='--');axs[1].axhline(3.465,color='r',ls='--');axs[1].set(xlabel='Time (ms)',ylabel='V',title='0.5 A to 2 A load event; contact/ground errors not included');axs[1].legend()
fig.savefig(O/'adapter-loaded-corner.png',dpi=180);plt.close(fig)
print(json.dumps(result,indent=2));assert all(checks.values()),checks
