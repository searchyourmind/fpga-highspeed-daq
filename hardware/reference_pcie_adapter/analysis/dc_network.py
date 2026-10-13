"""DC resistor graph extracted from actual two-layer track/pad/via geometry.
Pads treated as equipotential; adjacent inner planes are GND (no power plane).
Checks every 4-of-9 fully loaded M.2 pin combination at 0.5A/pin (2A total).
Copper resistivity/tolerance assumptions are explicit. Connector contact resistance
and GND plane drop are reserved separately, not invented as CAD measurements.
"""
from pathlib import Path
import json,math,itertools
import numpy as np
from shapely.geometry import LineString,Point,box
H=Path(__file__).resolve().parents[1];O=H/'outputs/engineering'
j=json.loads((O/'cad-geometry.json').read_text())

def analyze(net,source_ref,source_pin,loads,temp=75):
    ts=[t for t in j['tracks'] if t['net']==net and t['kind']=='track'];vs=[t for t in j['tracks'] if t['net']==net and t['kind']=='via'];ps=[p for p in j['pads'] if p['net']==net and p['pin']]
    lines=[LineString([t['a'],t['b']]) for t in ts];cuts=[[0.,l.length] for l in lines]
    bridges=[]
    for i,l in enumerate(lines):
      for n,m in enumerate(lines[:i]):
        if ts[i]['layer']!=ts[n]['layer']:continue
        q=l.intersection(m)
        if not q.is_empty:
          points=[q] if q.geom_type=='Point' else [Point(c) for c in (list(q.coords) if q.geom_type=='LineString' else [])]
          for p in points:cuts[i].append(l.project(p));cuts[n].append(m.project(p))
        # Copper contact at trace endpoints can exist away from a centerline intersection.
        for aa,bb,ia,ib in ((l,m,i,n),(m,l,n,i)):
          for c in aa.coords:
            pp=Point(c);dist=bb.distance(pp)
            if dist<=(ts[ia]['width']+ts[ib]['width'])/2+1e-8:
              pa=aa.project(pp);pb=bb.project(pp);cuts[ia].append(pa);cuts[ib].append(pb);bridges.append((ia,pa,ib,pb))
      for p in ps:
        if ts[i]['layer']=='F.Cu' or p['through']:
          q=l.intersection(box(*p['bbox']))
          if not q.is_empty:
            for c in (list(q.coords) if q.geom_type in ('LineString','Point') else []):cuts[i].append(l.project(Point(c)))
      for v in vs:
        p=Point(v['a'])
        if l.distance(p)<=v['width']/2+ts[i]['width']/2:cuts[i].append(l.project(p))
    parent={}
    def node(layer,xy):
      key=(layer,round(xy[0],6),round(xy[1],6));parent.setdefault(key,key);return key
    def root(a):
      if parent[a]!=a:parent[a]=root(parent[a])
      return parent[a]
    def union(a,b):parent[root(a)]=root(b)
    nodes=[];edges=[]
    rho=1.724e-8*(1+.00393*(temp-20));thick=.030e-3 # finished outer Cu minimum assumption
    for i,l in enumerate(lines):
      ds=sorted(set(round(min(l.length,max(0,d)),9) for d in cuts[i]));ns=[node(ts[i]['layer'],l.interpolate(d).coords[0]) for d in ds];nodes.append((ds,ns))
      for a,b,d0,d1 in zip(ns,ns[1:],ds,ds[1:]):
        if d1-d0>1e-8:edges.append((a,b,rho*((d1-d0)*1e-3)/(ts[i]['width']*1e-3*thick),i,(d1-d0)))
    def on(i,d):return nodes[i][1][min(range(len(nodes[i][0])),key=lambda n:abs(nodes[i][0][n]-d))]
    for i,d,n,e in bridges:union(on(i,d),on(n,e))
    padnodes={}
    for p in ps:
      pn=node('F.Cu',p['xy']);padnodes[p['ref'],p['pin']]=pn
      for n in list(parent):
        if n[0]=='F.Cu' or p['through']:
          if box(*p['bbox']).buffer(1e-7).covers(Point(n[1:])):union(pn,n)
    for v in vs:
      ends=[]
      for layer in ('F.Cu','B.Cu'):
        q=node(layer,v['a']);ends.append(q)
        for i,l in enumerate(lines):
          if ts[i]['layer']==layer and l.distance(Point(v['a']))<=v['width']/2+ts[i]['width']/2:union(q,on(i,l.project(Point(v['a']))))
      # 20um plating is a manufacturing requirement assumption, not verified.
      edges.append((ends[0],ends[1],rho*.0016/(math.pi*v['drill']*.001*20e-6),-1,.0016))
    source=root(padnodes[source_ref,source_pin]);roots=sorted(set(root(n) for n in parent));ids={n:i for i,n in enumerate(roots) if n!=source};ids={n:i for i,n in enumerate(ids)}
    G=np.zeros((len(ids),len(ids)));active=[]
    for a,b,r,i,l in edges:
      a=root(a);b=root(b)
      if a==b:continue
      active.append((a,b,r,i,l))
      for x,y in ((a,b),(b,a)):
        if x!=source:
          G[ids[x],ids[x]]+=1/r
          if y!=source:G[ids[x],ids[y]]-=1/r
    targets=[root(padnodes[r,p]) for r,p in loads];B=np.zeros((len(ids),len(targets)))
    for n,t in enumerate(targets):
      if t!=source:B[ids[t],n]=-1
    try:V=np.linalg.solve(G,B)
    except np.linalg.LinAlgError as exc:raise AssertionError('Disconnected copper graph '+net) from exc
    maxres=float(np.max(np.abs(G@V-B)))
    def evaluate(currents):
      vv=V@np.array(currents);value=lambda n:0 if n==source else vv[ids[n]]
      vals=[value(t) for t in targets];rises=[];watts=0;branches=[]
      for a,b,r,i,l in active:
        ii=abs((value(a)-value(b))/r);watts+=ii*ii*r
        if i>=0:
          area=(ts[i]['width']/0.0254)*(thick/0.0000254)
          dt=(ii/(.048*area**.725))**(1/.44) if ii else 0
          rises.append(dt);branches.append({'track_index':i,'current_A':ii,'drop_V':ii*r,'loss_W':ii*ii*r,'legacy_deltaT_C':dt,'width_mm':ts[i]['width'],'length_mm':l})
      return {'max_drop_V':float(-min(vals)),'loss_W':float(watts),'legacy_max_deltaT_C':float(max(rises,default=0)),'worst_branches':sorted(branches,key=lambda x:x['loss_W'],reverse=True)[:8]}
    equal=evaluate([2/len(targets)]*len(targets));corner=[]
    if len(targets)==9:
      for combo in itertools.combinations(range(9),4):
        c=[.5 if n in combo else 0 for n in range(9)];r=evaluate(c);corner.append((r['max_drop_V'],combo,r))
      worst=max(corner,key=lambda x:x[0]);details=worst[2];details['loaded_pins']=[loads[n][1] for n in worst[1]]
    else:details=equal
    return {'net':net,'nodes':len(ids)+1,'branches':len(active),'temperature_C':temp,'rho_ohm_m':rho,'outer_copper_min_um':30,'via_plating_min_um':20,'max_kcl_residual_A':maxres,'equal_load_2A':equal,'load_distribution_corners':len(corner),'worst_distribution_2A':details}

if __name__=='__main__':
    output=analyze('/SSD_3V3','L1','2',[('J2',str(n)) for n in (2,4,12,14,16,18,70,72,74)],temp=125)
    inp=analyze('/EXT_5V','J3','1',[('U1','11'),('U1','12')],temp=125)
    result={'status':'ANALYZED','scope':'Track/via resistor network; pads ideal; GND/contact/cable drop excluded. Fixed 2A stress per net; trace temperature formula is legacy IPC-2221 screening, not IPC-2152/thermal qualification.','output':output,'input':inp,'output_75C_comparison':analyze('/SSD_3V3','L1','2',[('J2',str(n)) for n in (2,4,12,14,16,18,70,72,74)],temp=75)}
    (O/'dc-network.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
