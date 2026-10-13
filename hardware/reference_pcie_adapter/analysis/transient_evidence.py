"""Time-weighted metrics from the completed official A-variant switching model."""
from pathlib import Path
import json,hashlib
import numpy as np
import matplotlib.pyplot as plt
H=Path(__file__).resolve().parent; R=H.parents[2]; O=H.parent/'outputs/engineering'
p=R/'build/review-r03/adapter-transient.txt'; a=np.loadtxt(p,skiprows=1)
t,v,pg,i,en=a.T
assert np.isfinite(a).all() and t[-1]>=.00305 and len(a)>10000
trap=getattr(np,'trapezoid',np.trapz) if hasattr(np,'trapz') else np.trapezoid
def window(start,end):
 m=(t>=start)&(t<=end); tt=t[m]
 return {'start_s':start,'end_s':end,'points':int(m.sum()),'min_V':float(v[m].min()),'max_V':float(v[m].max()),'time_weighted_mean_V':float(trap(v[m],tt)/(tt[-1]-tt[0])),'PG_min_V':float(pg[m].min()),'PG_max_V':float(pg[m].max()),'inductor_peak_A':float(i[m].max())}
windows={name:window(*se) for name,se in {'pre_step':(.00195,.00205),'load_step':(.00209,.0025),'post_step':(.0026,.00275),'disabled':(.00285,.00305)}.items()}
checks={'duration':True,'pre_step_in_5pct':3.135<=windows['pre_step']['min_V']<=windows['pre_step']['max_V']<=3.465,'step_in_5pct_at_regulator':3.135<=windows['load_step']['min_V']<=windows['load_step']['max_V']<=3.465,'steady_PG_high':windows['post_step']['PG_min_V']>4.,'disabled_PG_low':windows['disabled']['PG_max_V']<.4,'peak_current_below_room_min_limit':float(i.max())<3.6}
result={'status':'PASS_MODEL_CHECKS' if all(checks.values()) else 'FAIL_MODEL_CHECKS','model':'TI TPS62130A SLVM893A unmodified','scope':'5V input, nominal component values, 0.5A resistive base plus1.5A pulse. Output at regulator before PCB/contact drops. Nominal25C model only. No efficiency or hardware compliance claim.','raw_points':len(a),'end_s':float(t[-1]),'source_sha256':hashlib.sha256((H/'adapter_transient.cir').read_bytes()).hexdigest(),'checks':checks,'windows':windows,'overall_inductor_peak_A':float(i.max()),'first_3V135_s':float(t[np.flatnonzero(v>=3.135)[0]])}
(O/'adapter-transient.json').write_text(json.dumps(result,indent=2)+'\n')
# Keep original solver samples selected across the full trace, not invented waveform data.
idx=np.unique(np.r_[np.arange(0,len(a),max(1,len(a)//20000)),len(a)-1]);np.savetxt(O/'adapter-transient-preview.csv',a[idx],delimiter=',',header='time_s,output_V,PG_V,inductor_A,EN_V',comments='')
fig,axs=plt.subplots(2,1,figsize=(8,5.5),layout='constrained')
axs[0].plot(t[idx]*1e3,v[idx],label='Vout');axs[0].plot(t[idx]*1e3,pg[idx],label='PG (5V pullup)',alpha=.6);axs[0].plot(t[idx]*1e3,en[idx],label='EN',alpha=.6);axs[0].set(ylabel='V',title='TPS62130A nominal switching transient');axs[0].legend(ncol=3)
mm=(t>=.00205)&(t<=.0025);ids=np.flatnonzero(mm)[::max(1,int(mm.sum())//10000)];axs[1].plot(t[ids]*1e3,v[ids]);axs[1].axhline(3.135,color='r',ls='--');axs[1].axhline(3.465,color='r',ls='--');axs[1].set(xlabel='Time (ms)',ylabel='Vout (V)',title='0.5A to 2A to 0.5A load event, before board drop')
fig.savefig(O/'adapter-transient.png',dpi=180);plt.close(fig)
print(json.dumps(result,indent=2));assert all(checks.values()),checks
