"""Steady 2-D PCB heat-spreading sensitivity, energy and mesh checked.
Two inner35? NO: two15.2um planes; conservative50% effective coverage.
No airflow/enclosure/SSD geometry claimed. Sources are assumed loss envelopes.
"""
from pathlib import Path
import json,itertools,math
import numpy as np
from scipy.sparse import diags
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union
import shapely
from scipy.sparse.linalg import spsolve
import matplotlib.pyplot as plt
O=Path(__file__).resolve().parents[1]/'outputs/engineering'

def plate(step=.001,h_air=8.,ambient=40.,reg_loss=.8,ind_loss=.25,ssd_coupled=0.,coverage=.5, spreaders=True, copper_loss=.25, sink_K_W=None, outer_cu_um=35., uniform_heat_W=None):
    W,H=.080,.078;nx=round(W/step);ny=round(H/step);dx=W/nx;dy=H/ny
    # Sheet conductance W/K; FR4 in-plane0.3W/mK and copper385W/mK assumptions.
    x=(np.arange(nx)+.5)*dx;y=(np.arange(ny)+.5)*dy;X,Y=np.meshgrid(x,y)
    K=np.ones((ny,nx))*(.3*.0016+385*(2*15.2e-6)*coverage)
    if spreaders:
      geometry=json.loads((O/'cad-geometry.json').read_text())
      for layer in ('F.Cu','B.Cu'):
        pp=next(p for p in geometry['planes'] if p['layer']==layer)
        polygons=unary_union([Polygon(p['outer'],p['holes']).buffer(0) for p in pp['polygons']])
        # Actual filled copper samples, derated50% for unresolved sub-grid apertures.
        present=shapely.contains_xy(polygons,20+X*1000,20+Y*1000)
        K+=385*outer_cu_um*1e-6*.5*present
    gx=2*K[:,:-1]*K[:,1:]/(K[:,:-1]+K[:,1:])*dy/dx
    gy=2*K[:-1,:]*K[1:,:]/(K[:-1,:]+K[1:,:])*dx/dy
    N=nx*ny;right=np.zeros((ny,nx));right[:,:-1]=-gx;right=right.ravel()[:-1]
    up=-gy.ravel();diag=np.ones((ny,nx))*(2*h_air*dx*dy)
    diag[:,:-1]+=gx;diag[:,1:]+=gx;diag[:-1,:]+=gy;diag[1:,:]+=gy
    sink_mask=(abs(X-.015)<=.005)&(abs(Y-.034)<=.005)
    sink_G=np.zeros_like(K)
    if sink_K_W is not None:
      # Total interface+via+sink-to-ambient resistance is a candidate requirement.
      # One side is covered by the10x10mm contact, so remove its free convection.
      diag[sink_mask]-=h_air*dx*dy
      sink_G[sink_mask]=1/sink_K_W/sink_mask.sum();diag+=sink_G
    A=diags([right,up,diag.ravel(),up,right],[-1,-nx,0,nx,1],format='csr');q=np.zeros((ny,nx))
    masks=[]
    for xx,yy,w,hh,p in [(.015,.034,.003,.003,reg_loss),(.009,.033,.0043,.0043,ind_loss),(.045,.050,.022,.028,ssd_coupled),(.018,.040,.028,.028,copper_loss)]:
      mask=(abs(X-xx)<=w/2)&(abs(Y-yy)<=hh/2);assert mask.any();q[mask]+=p/mask.sum();masks.append(mask)
    if uniform_heat_W is not None:q[:]=uniform_heat_W/q.size
    dt=spsolve(A,q.ravel()).reshape(ny,nx);heat_out=2*h_air*dx*dy*dt.sum()+np.sum(sink_G*dt)
    if sink_K_W is not None:heat_out-=h_air*dx*dy*dt[sink_mask].sum()
    energy=abs(heat_out/q.sum()-1)
    assert energy<1e-8
    # EP solder0.05mm, k50; vias conduct from top to nearest GND plane0.0994mm.
    solder=.00005/(50*(.0016**2));via_r=.0000994/(385*8*math.pi*.0002*.000020)
    tj=float(ambient+dt[masks[0]].max()+reg_loss*(4.5+solder+via_r))
    return {'outer_copper_um':outer_cu_um,'average_board_C':float(ambient+dt.mean()),'candidate_sink_total_K_W':sink_K_W,'mesh_mm':step*1000,'ambient_C':ambient,'h_each_side_W_m2K':h_air,'inner_plane_coverage_factor':coverage,'assumed_regulator_loss_W':reg_loss,'assumed_inductor_loss_W':ind_loss,'assumed_SSD_heat_into_carrier_W':ssd_coupled,'assumed_copper_loss_W':copper_loss,'SSD_region_board_max_C':float(ambient+dt[masks[2]].max()),'feedback_region_board_max_C':float(ambient+dt[(abs(X-.026)<.005)&(abs(Y-.039)<.005)].max()),'pcb_hotspot_C':float(ambient+dt.max()),'estimated_regulator_junction_C':tj,'regulator_limit_C':125,'within_125C':tj<=125,'energy_balance_relative_error':energy,'via_to_nearest_plane_K_W':via_r},(x,y,dt+ambient)

def run():
    mesh=[]
    for step in (.001,.0005,.00025):r,f=plate(step=step);mesh.append(r)
    delta=abs(mesh[-1]['estimated_regulator_junction_C']-mesh[-2]['estimated_regulator_junction_C']);assert delta<2
    cases=[]
    for ambient,h,loss,coupled in itertools.product((25.,40.,60.),(5.,10.),(.6,1.),(0.,1.65)):
      r,_=plate(ambient=ambient,h_air=h,reg_loss=loss,ssd_coupled=coupled);cases.append(r)
    # Uniform volumetric distribution has exact average dT=P/(2*h*A).
    result={'status':'PASS_NUMERICS','scope':'Assumption-based steady2D screening. Not CFD, measured thermal performance or an enclosure/SSD qualification. IC loss0.6..1.0W, inductor0.25W, SSD coupling0..25% of6.6W, copper loss0.25W (conservative vs extracted125C input+output network; checked independently), h5..10 each side. SSD die and enclosure excluded.','outer_spreader_model':'Actual filled F/B GND polygons sampled at cell centers; 50% conductance derating', 'mesh':mesh,'mesh_last_delta_T_C':delta,'cases':cases,'worst':max(cases,key=lambda r:r['estimated_regulator_junction_C']),'conditional_40C_h10_cases_pass':all(r['within_125C'] for r in cases if r['ambient_C']<=40 and r['h_each_side_W_m2K']==10),'conditional_40C_ambient_cases_pass':all(r['within_125C'] for r in cases if r['ambient_C']<=40),'datasheet_thetaJA_K_W':45,'thetaJA_note':'JEDEC reference45K/W is not substituted for actual layout thermal resistance.'}
    (O/'thermal.json').write_text(json.dumps(result,indent=2)+'\n')
    r,(x,y,T)=plate(ambient=40,h_air=5,reg_loss=1.,ssd_coupled=1.65,step=.0005)
    fig,ax=plt.subplots(figsize=(6,5),layout='constrained');im=ax.pcolormesh(20+x*1000,20+y*1000,T,shading='auto',cmap='inferno');ax.set(aspect='equal',xlabel='Board x (mm)',ylabel='Board y (mm)',title='Assumed loss / convection thermal screening');ax.invert_yaxis();fig.colorbar(im,ax=ax,label='Estimated board temperature (C)');fig.savefig(O/'thermal-map.png',dpi=180);plt.close(fig)
    print(json.dumps({k:result[k] for k in ('status','mesh_last_delta_T_C','worst','conditional_40C_ambient_cases_pass')},indent=2))
if __name__=='__main__':run()
