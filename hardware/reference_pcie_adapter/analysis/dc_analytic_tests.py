"""Independent analytic fixtures for the CAD-extracted resistor graph solver."""
import json,math
import dc_network as d

def fixture(parallel=False,disconnected=False):
 pads=[{'ref':r,'pin':'1','net':'test','xy':[x,0],'bbox':[x-.1,-2,x+.1,2],'through':False} for r,x in [('S',0),('D',10)]]
 tracks=[] if disconnected else [{'net':'test','kind':'track','a':[0,y],'b':[10,y],'width':1.,'layer':'F.Cu','drill':0} for y in ([-1,1] if parallel else [0])]
 return {'pads':pads,'tracks':tracks}
checks={}
for parallel in (False,True):
 d.j=fixture(parallel=parallel);r=d.analyze('test','S','1',[('D','1')],temp=20)
 # Ideal source/load pads each cover0.1mm; remaining copper length9.8mm.
 resistance=1.724e-8*.0098/(.001*30e-6)/(2 if parallel else 1)
 checks['parallel_tracks' if parallel else 'single_track']=math.isclose(r['equal_load_2A']['max_drop_V'],2*resistance,rel_tol=1e-8) and math.isclose(r['equal_load_2A']['loss_W'],4*resistance,rel_tol=1e-8)
d.j=fixture(disconnected=True)
try:d.analyze('test','S','1',[('D','1')],temp=20);checks['disconnected_graph_rejected']=False
except AssertionError:checks['disconnected_graph_rejected']=True
(d.O/'dc-analytic-tests.json').write_text(json.dumps({'checks':checks,'status':'PASS' if all(checks.values()) else 'FAIL'},indent=2)+'\n');print(checks);assert all(checks.values())
