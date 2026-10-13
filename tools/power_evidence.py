"""Compact observed transient trace and quantitative load-step evidence."""
from pathlib import Path
import numpy as np,json
import matplotlib.pyplot as plt
r=Path(__file__).resolve().parents[1];o=r/'results/power';x=np.loadtxt(r/'hardware/power_tree/transient.txt',skiprows=1)
assert x[-1,0]>=.00119
stable=x[x[:,0]>.00065];final=x[x[:,0]>.00105]
assert 3.15<stable[:,1].min() and stable[:,1].max()<3.45
assert final[:,2].mean()>3.0
sample=x[::max(1,len(x)//5000)];np.savetxt(o/'transient-preview.csv',sample,delimiter=',',header='time_s,vout_V,power_good_V,inductor_current_A',comments='')
d={'original_points':len(x),'preview_points':len(sample),'soft_start_cap_F':1e-9,'load_step_time_s':.00075,'added_load_A':.5,'pulse_width_s':.0002,'steady_window_start_s':.00105,'steady_mean_V':float(final[:,1].mean()),'steady_pk_pk_V':float(np.ptp(final[:,1])),'post_startup_min_V':float(stable[:,1].min()),'post_startup_max_V':float(stable[:,1].max()),'final_PG_mean_V':float(final[:,2].mean()),'scope':'Original TI switching model in ngspice; simulated only, no hardware'}
(o/'transient-metrics.json').write_text(json.dumps(d,indent=2)+'\n')
y=x[(x[:,0]>.0007)&(x[:,0]<.00105)][::10]
f,a=plt.subplots(figsize=(7,3.5),layout='constrained');a.plot(y[:,0]*1000,y[:,1]);a.axvline(.75,color='gray',ls='--');a.axvline(.96,color='gray',ls='--');a.set(xlabel='Simulated time (ms)',ylabel='Output voltage (V)',title='TI switching model: additional 0.5 A pulse at 0.75 ms');a.grid(alpha=.2);f.savefig(o/'load-step-detail.png',dpi=160);print(json.dumps(d,indent=2))
