"""Independently compare actual CAD differential routes with the preserved baseline."""
from pathlib import Path
import json,math,pcbnew as k
H=Path(__file__).resolve().parent;b=k.LoadBoard(str(H/'kicad/pi5_m2_reference.kicad_pcb'));old=json.loads((H/'routing/pair-baseline.json').read_text())
names=sorted({x['net'] for x in old});results={}
# Fill/connectivity must not silently reassign an intended via to a touching wrong net.
expected=json.loads((H/'routing/tracks.json').read_text())['items']
for r in expected:
 if r['kind']=='via':
  match=[t for t in b.GetTracks() if isinstance(t,k.PCB_VIA) and [t.GetPosition().x,t.GetPosition().y]==r['a']]
  assert len(match)==1 and match[0].GetNetname()==r['net'],('via net mismatch',r,[(t.GetNetname()) for t in match])

def point(p):return (p.x/1e6,p.y/1e6)
def dist(p,a,z):
 v=(z[0]-a[0],z[1]-a[1]);l=v[0]**2+v[1]**2
 u=max(0,min(1,((p[0]-a[0])*v[0]+(p[1]-a[1])*v[1])/l)) if l else 0
 return math.dist(p,(a[0]+u*v[0],a[1]+u*v[1]))
for n in names:
 ref=[r for r in old if r['net']==n];now=[t for t in b.GetTracks() if t.GetNetname()==n]
 ov=[r for r in ref if r['kind']=='via'];nv=[t for t in now if isinstance(t,k.PCB_VIA)];assert len(ov)==len(nv)
 for r in ov:assert min(math.dist(tuple(v/1e6 for v in r['a']),point(t.GetPosition())) for t in nv)<.001
 ot=[(tuple(v/1e6 for v in r['a']),tuple(v/1e6 for v in r['b']),r['layer']) for r in ref if r['kind']=='track']
 nt=[(point(t.GetStart()),point(t.GetEnd()),t.GetLayerName()) for t in now if not isinstance(t,k.PCB_VIA)]
 deviations=[]
 for source,target in ((ot,nt),(nt,ot)):
  for a,z,layer in source:
   for i in range(11):
    p=tuple(a[j]+(z[j]-a[j])*i/10 for j in range(2));deviations.append(min(dist(p,x,y) for x,y,l in target if l==layer))
 delta=max(deviations);assert delta<.001,(n,delta)
 assert all(t.GetWidth()==140000 for t in now if not isinstance(t,k.PCB_VIA))
 results[n]={'length_mm':sum(math.dist(a,z) for a,z,l in nt),'max_baseline_deviation_mm':delta,'vias':len(nv)}
assert all(isinstance(t,k.PCB_VIA) or t.GetLayer() in (k.F_Cu,k.B_Cu) for t in b.GetTracks())
assert len(list(b.Zones()))==4 and all(z.GetNetname()=='/GND' for z in b.Zones())
assert sorted(b.GetLayerName(z.GetLayer()) for z in b.Zones())==['B.Cu','F.Cu','In1.Cu','In2.Cu']
summary={'status':'PASS','scope':'Geometric preservation within 1 um; no electrical-delay/SI claim','pairs':results,'inner_signal_tracks':0,'ground_planes':2,'local_outer_ground_spreaders':2,'track_via_items':len(list(b.GetTracks())),'pad_count':sum(len(list(f.Pads())) for f in b.GetFootprints())}
(H/'outputs/routing-preservation.json').write_text(json.dumps(summary,indent=2)+'\n')
(H/'outputs/trace-lengths.json').write_text(json.dumps({'scope':'Actual CAD centerline lengths, excluding via/connector delay','length_mm':{n[1:]:v['length_mm'] for n,v in results.items()},'skew_mm':{p:abs(results['/'+p+'_P']['length_mm']-results['/'+p+'_N']['length_mm']) for p in ('CLK','RX','TX')}},indent=2)+'\n');print(json.dumps(summary,indent=2))
