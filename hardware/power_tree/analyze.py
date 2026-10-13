"""Calculation-backed hypothetical rail tree and actual TI-model SPICE runs."""
from pathlib import Path
import subprocess,json,math
import numpy as np
import matplotlib.pyplot as plt
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
OUT=ROOT/'results/power';OUT.mkdir(parents=True,exist_ok=True)
rails=[('VCCINT_VCCBRAM',1.0,2.0,24900),('VCCAUX',1.8,.4,124000),('VCCO_3V3',3.3,.8,312000)]
budget=[]
for name,v,current,rtop in rails:
    nominal=.8*(1+rtop/100000)
    ripple=v*(1-v/12)/(2.2e-6*2.5e6)
    budget.append(dict(rail=name,target_V=v,divider_nominal_V=nominal,assumed_load_A=current,
        margin_load_A=1.25*current,regulator_limit_A=3.,estimated_inductor_ripple_A=ripple,
        minimum_inductor_peak_A=1.25*current+ripple/2,Rtop_ohm=rtop,Rbottom_ohm=100000))
    assert abs(nominal/v-1)<.01 and 1.25*current<3
power=sum(v*i*1.25 for _,v,i,_ in rails)
results={'scope':'HYPOTHETICAL REFERENCE; currents and 85% efficiency are budgeting assumptions, not XPE or measurements',
    'input_V':12,'assumed_efficiency':.85,'budget_output_W':power,'budget_input_A':power/.85/12,
    'rails':budget,'spice':{}}
for mode,timeout in [('average',60),('transient',300)]:
    path=HERE/f'tps62130_{mode}.cir'
    try:
        r=subprocess.run(['ngspice','-b',str(path.name)],cwd=HERE,text=True,capture_output=True,timeout=timeout)
        (OUT/f'{mode}.log').write_text(r.stdout+'\n'+r.stderr)
        if r.returncode: raise RuntimeError(f'ngspice exit {r.returncode}')
        if mode=='average':
            dc=np.loadtxt(HERE/'average_dc.txt',skiprows=1,ndmin=2)
            vout=float(dc[0,1]); assert 3.15<vout<3.45, vout
            ac=np.loadtxt(HERE/'average_ac.txt',skiprows=1,ndmin=2)
            assert np.isfinite(ac).all()
            fig,ax=plt.subplots(figsize=(7,3.6),layout='constrained')
            ax.loglog(ac[:,0],ac[:,1]);ax.grid(True,which='both',alpha=.2)
            ax.set(xlabel='Frequency (Hz)',ylabel='Output impedance (ohm)',title='TI TPS62130 average model / ngspice / CCM only')
            fig.savefig(OUT/'output-impedance.png',dpi=160);plt.close(fig)
            results['spice'][mode]={'status':'PASS','dc_output_V':vout,'points':len(ac),
                'limitations':'Vendor average-model DC/AC only; no ripple, startup, thermal, or hardware validation'}
        else:
            tran=np.loadtxt(HERE/'transient.txt',skiprows=1,ndmin=2)
            assert np.isfinite(tran).all() and tran[-1,0]>=.00119
            steady=tran[(tran[:,0]>.00105),1]
            assert 3.1<float(steady.mean())<3.5, float(steady.mean())
            fig,ax=plt.subplots(figsize=(7,3.6),layout='constrained')
            ax.plot(tran[::20,0]*1000,tran[::20,1]);ax.grid(alpha=.2)
            ax.set(xlabel='Simulated time (ms)',ylabel='Output voltage (V)',title='TI TPS62130 transient model / ngspice / no hardware')
            fig.savefig(OUT/'startup-load-step.png',dpi=160);plt.close(fig)
            results['spice'][mode]={'status':'PASS','points':len(tran),'final_mean_V':float(steady.mean()),
                'modeled_steady_pp_V':float(np.ptp(steady)),'limitations':'Vendor PSpice model in ngspice compatibility mode; not measured or vendor-certified simulation'}
    except (subprocess.TimeoutExpired,RuntimeError,AssertionError,OSError,ValueError) as exc:
        if isinstance(exc,subprocess.TimeoutExpired):
            (OUT/f'{mode}.log').write_text('TIMEOUT after '+str(timeout)+' seconds\n'+str(exc.stdout or '')+'\n'+str(exc.stderr or ''))
        results['spice'][mode]={'status':'BLOCKED','reason':str(exc)}
(OUT/'power-results.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2))
assert all(r['status']=='PASS' for r in results['spice'].values()), 'All requested SPICE modes must pass; see power-results.json'
