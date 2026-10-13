"""Actual TI CCM average-model screening plus independent worst-case budgets.
The A-specific transient model is separate. Average model shares power core only;
it cannot validate A PG shutdown, PFM, current limit or stability phase margin.
"""
from pathlib import Path
import subprocess,json,itertools,re,math
import numpy as np
H=Path(__file__).resolve().parent;O=H.parent/'outputs/engineering';B=H.parents[2]/'build/review-r03';rows=[]
# 3 Vin x3 currents x3 effective capacitor values x2 L x2 ESR=108 actual DC/AC cases.
for n,(vin,current,cap,L,esr) in enumerate(itertools.product((4.65,5.,5.25),(.5,1.,2.),(16.,22.,52.8),(1.232,2.64),(.005,.03))):
 source=f'''Adapter power-core CCM corner{n}
.include ../../../hardware/power_tree/vendor/tps62130_avg.lib
Vinput vin 0 {vin}
Xreg vin fb out sw TPS62130_AVG
L1 sw lx {L}u
Rdcr lx out .050
Cout out cesr {cap}u
Resr cesr 0 {esr}
Rtop out fb 31.6k
Rbottom fb 0 10k
Rload out 0 {3.328/current}
Itest out 0 DC 0 AC 1
.nodeset v(out)=3.328 v(fb)=.8
.control
set wr_singlescale
set wr_vecnames
op
print v(out)
ac dec 30 100 1Meg
let zout_mag=mag(v(out))
wrdata ac-corner.txt zout_mag
quit
.endc
.end
'''
 # cwd remains analysis so compatibility file and relative model path are reproducible.
 source=source.replace('../../../hardware/power_tree/vendor/','../../power_tree/vendor/')
 p=H/'working-corner.cir';p.write_text(source)
 r=subprocess.run(['ngspice','-b',p.name],cwd=H,capture_output=True,text=True,timeout=30)
 assert r.returncode==0,r.stdout+r.stderr
 m=re.search(r'v\(out\)\s*=\s*(\S+)',r.stdout);assert m,r.stdout
 v=float(m.group(1));ac=np.loadtxt(H/'ac-corner.txt',skiprows=1,ndmin=2)
 assert np.isfinite(ac).all() and 3.135<v<3.465
 rows.append({'vin_V':vin,'load_A':current,'Ceff_uF':cap,'Leff_uH':L,'ESR_ohm':esr,'dc_output_V':v,'ac_points':len(ac),'peak_output_impedance_ohm':float(ac[:,1].max()),'status':'PASS_DC_AND_FINITE_AC'})
 (B/f'power-corner-{n:03}.log').write_text(r.stdout+r.stderr)
p.unlink();(H/'ac-corner.txt').unlink()
# Datasheet min/max feedback include temp; resistors include0.1%+25ppm/K*100K.
rt=31600.;rb=10000.;tol=.001+25e-6*100
vlow=.7856*(1+rt*(1-tol)/(rb*(1+tol)))-100e-9*rt*(1+tol)
vhigh=.8224*(1+rt*(1+tol)/(rb*(1-tol)))+100e-9*rt*(1+tol)
net=json.loads((O/'dc-network.json').read_text());drop=net['output']['worst_distribution_2A']['max_drop_V']
reserve={'ground_drop_V':.010,'contact_drop_V':.025,'ripple_transient_peak_V':.040,'line_load_regulation_V':.005}
loaded_min=vlow-drop-sum(reserve.values());idle_max=vhigh+reserve['ripple_transient_peak_V']+reserve['line_load_regulation_V']
Lmin=2.2e-6*.8*.7 # -20% production and30% inductance reduction screening.
fmin=2e6 # assumed floor for2.5MHz setting; not datasheet guaranteed min.
ripple=max(v*(1-v/vi)/(Lmin*fmin) for v in (vlow,vhigh) for vi in (4.65,5.25))
peak=2+ripple/2
result={'status':'PASS_SIMULATIONS','average_scope':'108 CCM power-core DC/AC cases; A transient separate; no PFM/current-limit/phase-margin claim','cases':rows,
 'budget':{'nominal_V':.8*(1+rt/rb),'feedback_low_V':vlow,'feedback_PSM_high_V':vhigh,'temp_tolerance_resistors':tol,'FB_leakage_max_A':100e-9,'copper_drop_V':drop,'reserve_note':'40mV transient reserve exceeds nominal35mV and executed loaded external-component corner25.1mV regulator excursions; no joint silicon/temperature/process qualification. Ground/contact reserves unverified.','explicit_unverified_reserves':reserve,'loaded_min_V':loaded_min,'idle_max_V':idle_max,'allowed_V':[3.135,3.465],'tolerance_budget_pass':loaded_min>=3.135 and idle_max<=3.465,'assumed_switching_floor_Hz':fmin,'screened_Lmin_H':Lmin,'estimated_worst_ripple_A':ripple,'estimated_inductor_peak_A':peak,'current_limit_min_room_A':3.6,'current_limit_max_room_A':4.9,'Isat_typ_25C_A':5.6,'normal_peak_below_min_limit':peak<3.6,'current_limit_caveat':'TI current-limit table condition12V25C; delay overshoot and hot Isat not covered; no short-circuit qualification','Cin_effective_requirement_uF':12,'Cout_screened_effective_uF':[16,52.8],'efficiency_assumption':.85,'input_budget_A':3.328*2/.85/4.65,'SS_nominal_s':3.3e-9*1.25/2.5e-6,'SS_extreme_s':[3.3e-9*.9*.85*.95*1.25/2.7e-6,3.3e-9*1.1*1.15*1.25/2.3e-6]}}
(O/'power-corners.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'cases':len(rows),'budget':result['budget']},indent=2))
