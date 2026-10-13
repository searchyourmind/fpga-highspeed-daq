"""2-D finite-volume electrostatic odd-mode solver; SI screening, not signoff.
Solve div(epsilon grad V)=0 in half of a symmetric differential pair cross-section.
Copper is equipotential (+0.5 V); mirror plane and reference plane are 0 V.
The reflected negative conductor is -0.5 V: differential voltage is 1 V.
Cdiff=Qpositive/1V. Quasi-TEM Zdiff=1/(c sqrt(Cdiff Cdiff_vacuum)).
All dimensions are mm at input, SI in the solver. No fitted impedance formula.
"""
from pathlib import Path
import json, itertools
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve
import matplotlib.pyplot as plt
O=Path(__file__).resolve().parents[1]/'outputs/engineering';O.mkdir(exist_ok=True,parents=True)
EPS=8.8541878128e-12; C=299792458.
def grid(end,step,breaks):
    # Exact conductor/dielectric boundaries; avoid nearly coincident sliver cells.
    a=np.arange(0,end+step*.5,step)
    for p in breaks:
        if p<=0 or p>=end:continue
        a=a[np.abs(a-p)>step*.15];a=np.r_[a,p]
    return np.unique(np.r_[a,0,end])*1e-3

def solve(w=.14,g=.152,h=.0994,t=.035,er=4.1,mask=.01,mask_er=3.3,step=.005,extent=1.,top=.75,vacuum=False, planarized=False, top_narrowing=0., mask_base=None, mask_top=None, coplanar_gap=None):
    xf=grid(extent,step,[g/2,g/2+w]);yf=grid(top,step,[h,h+t,h+t+mask]);
    x=(xf[:-1]+xf[1:])/2;y=(yf[:-1]+yf[1:])/2;dx=np.diff(xf);dy=np.diff(yf)
    X,Y=np.meshgrid(x,y); ny,nx=X.shape
    cond=(X>g*.0005)&(X<(g/2+w)*.001)&(Y>h*.001)&(Y<(h+t)*.001)
    if top_narrowing:
        assert 0<=top_narrowing<w
        local_width=w-top_narrowing*np.clip((Y*1000-h)/t,0,1)
        cond=(abs(X*1000-(g/2+w/2))<local_width/2)&(Y>h*.001)&(Y<(h+t)*.001)
    ep=np.ones_like(X);ep[Y<h*.001]=er
    # Planarized mask to conductor top + mask thickness: conservative fabrication assumption.
    coating=(Y>=h*.001)&(Y<(h+mask)*.001)
    coating|=(X>(g/2-mask)*.001)&(X<(g/2+w+mask)*.001)&(Y>=h*.001)&(Y<(h+t+mask)*.001)
    if planarized:coating=(Y>=h*.001)&(Y<(h+t+mask)*.001)
    if mask_base is not None:
        assert mask_top is not None
        coating=(Y>=h*.001)&(Y<(h+mask_base)*.001)
        coating|=(X>(g/2-mask_top)*.001)&(X<(g/2+w+mask_top)*.001)&(Y>=h*.001)&(Y<(h+t+mask_top)*.001)
    ep[coating]=mask_er if (mask or mask_base) else 1.
    ground=np.zeros_like(cond) if coplanar_gap is None else ((X>(g/2+w+coplanar_gap)*.001)&(Y>h*.001)&(Y<(h+t)*.001))
    metal=cond|ground
    if vacuum:ep[:]=1
    ep*=EPS
    gx=dy[:,None]/(dx[:-1][None,:]/(2*ep[:,:-1])+dx[1:][None,:]/(2*ep[:,1:]))
    gy=dx[None,:]/(dy[:-1,None]/(2*ep[:-1,:])+dy[1:,None]/(2*ep[1:,:]))
    # Conductor potential is prescribed at its surface, not at a fictitious cell center.
    sel=metal[:,:-1]&~metal[:,1:];gx[sel]=(2*ep[:,1:]*dy[:,None]/dx[1:][None,:])[sel]
    sel=~metal[:,:-1]&metal[:,1:];gx[sel]=(2*ep[:,:-1]*dy[:,None]/dx[:-1][None,:])[sel]
    sel=metal[:-1,:]&~metal[1:,:];gy[sel]=(2*ep[1:,:]*dx[None,:]/dy[1:,None])[sel]
    sel=~metal[:-1,:]&metal[1:,:];gy[sel]=(2*ep[:-1,:]*dx[None,:]/dy[:-1,None])[sel]
    ids=np.arange(nx*ny).reshape(ny,nx); a=np.r_[ids[:,:-1].ravel(),ids[:-1,:].ravel()]; z=np.r_[ids[:,1:].ravel(),ids[1:,:].ravel()];G=np.r_[gx.ravel(),gy.ravel()]
    fixed=metal.ravel();charged=cond.ravel();pot=np.zeros(nx*ny);pot[charged]=.5;uid=np.full(nx*ny,-1);uid[~fixed]=np.arange((~fixed).sum());n=(~fixed).sum()
    diag=np.zeros(n);rhs=np.zeros(n);rows=[];cols=[];data=[]
    for aa,zz in ((a,z),(z,a)):
        sel=~fixed[aa];aa=aa[sel];zz=zz[sel];gg=G[sel]
        np.add.at(diag,uid[aa],gg)
        ff=fixed[zz];np.add.at(rhs,uid[aa[ff]],gg[ff]*pot[zz[ff]])
        rows.extend(uid[aa[~ff]]);cols.extend(uid[zz[~ff]]);data.extend(-gg[~ff])
    # Far boundaries grounded; quantify finite-domain error separately.
    edges=[(ids[:,0],ep[:,0]*dy/(dx[0]/2)),(ids[:,-1],ep[:,-1]*dy/(dx[-1]/2)),(ids[0,:],ep[0,:]*dx/(dy[0]/2)),(ids[-1,:],ep[-1,:]*dx/(dy[-1]/2))]
    for ii,gg in edges:
        sel=~fixed[ii];np.add.at(diag,uid[ii[sel]],gg[sel])
    rows.extend(np.arange(n));cols.extend(np.arange(n));data.extend(diag)
    A=coo_matrix((data,(rows,cols)),shape=(n,n)).tocsr();v=spsolve(A,rhs);pot[~fixed]=v
    residual=np.linalg.norm(A@v-rhs)/np.linalg.norm(rhs)
    charge=0.
    for aa,zz in ((a,z),(z,a)):
        sel=charged[aa]&~fixed[zz];charge+=np.sum(G[sel]*(pot[aa[sel]]-pot[zz[sel]]))
    energy=np.sum(G*(pot[a]-pot[z])**2)/2
    for ii,gg in edges:energy+=np.sum(gg*pot[ii]**2)/2
    # Half-domain energy = Qpositive * 0.5V / 2.
    energy_error=abs(energy/(charge*.25)-1)
    assert residual<1e-9 and energy_error<1e-8 and 0<v.min()+1e-10 and v.max()<.5+1e-10
    return charge,{'unknowns':int(n),'relative_residual':float(residual),'energy_charge_error':float(energy_error)},(x,y,pot.reshape(ny,nx))

def pair(**kw):
    cap,diagnostic,field=solve(**kw);vac,_,_=solve(**kw,vacuum=True)
    return dict(**kw,Zdiff_ohm=float(1/(C*np.sqrt(cap*vac))),Cdiff_pF_per_m=cap*1e12,C0diff_pF_per_m=vac*1e12,epsilon_effective=cap/vac,**diagnostic),field

def run():
    cases=[]
    for step in (.01,.005,.0025,.00125):
        r,f=pair(step=step);r['case']='mesh';cases.append(r);print(r,flush=True)
    nominal=cases[-1];convergence=abs(nominal['Zdiff_ohm']/cases[-2]['Zdiff_ohm']-1)
    r,_=pair(step=.005,extent=1.5,top=1.);r['case']='domain';cases.append(r)
    domain=abs(r['Zdiff_ohm']/cases[1]['Zdiff_ohm']-1)
    # Correlated fabrication screening extremes: width +/-15um, h +/-10%, er +/-0.2.
    # These are assumed bounds, not a fabricator tolerance commitment.
    for name,w,g,h,er,mask in [('low_Z',.155,.137,.08946,4.3,.01),('high_Z',.125,.167,.10934,3.9,.01),('no_mask',.14,.152,.0994,4.1,0),('wide_fanout',.14,.36,.0994,4.1,.01)]:
        r,_=pair(w=w,g=g,h=h,er=er,mask=mask,step=.005);r['case']=name;cases.append(r);print(r,flush=True)
    # Homogeneous dielectric identity provides an independent exact scaling check.
    uniform,_=pair(er=4.,mask_er=4.,h=.0994,mask=1.,step=.01,planarized=True)
    # This case is not fully homogeneous above top of copper, so test full fill via solve mask.
    assert abs(uniform['epsilon_effective']-4)<1e-9
    assert convergence<.035 and domain<.02,(convergence,domain)
    result={'status':'PASS_NUMERICS','claim':'Quasi-static 2-D screening only; no connector/cable/roughness/3-D discontinuity or PCIe compliance model',
      'mask_model':'10um conformal rectilinear coating on board and trace, er=3.3 assumed; mask omission case supplied',
      'nominal':nominal,'mesh_last_relative_change':convergence,'domain_relative_change':domain,
      'homogeneous_epsilon_check':uniform['epsilon_effective'],'target_ohm':[81,99],
      'nominal_in_target':81<=nominal['Zdiff_ohm']<=99,'all_screened_corners_in_target':all(81<=r['Zdiff_ohm']<=99 for r in cases if r['case'] in ('low_Z','high_Z')),'cases':cases}
    (O/'field-solver.json').write_text(json.dumps(result,indent=2)+'\n')
    x,y,V=f;fig,ax=plt.subplots(figsize=(7,3.6),layout='constrained');im=ax.pcolormesh(x*1e3,y*1e3,V,shading='auto',cmap='viridis');ax.set(xlim=(0,.55),ylim=(0,.4),xlabel='x from symmetry plane (mm)',ylabel='Height above GND plane (mm)',title='Odd-mode electrostatic field: +0.5 V trace / half-domain');fig.colorbar(im,ax=ax,label='Potential (V)');fig.savefig(O/'field-potential.png',dpi=170);plt.close(fig)
    return result
if __name__=='__main__':run()
