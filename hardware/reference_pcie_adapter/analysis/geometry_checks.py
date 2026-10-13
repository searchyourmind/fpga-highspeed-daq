"""Actual filled-plane SI return-path audit and dimensional envelope checks."""
from pathlib import Path
import json,math
from shapely.geometry import Polygon,LineString,Point,box
from shapely.ops import unary_union
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,Circle
H=Path(__file__).resolve().parents[1];O=H/'outputs/engineering';j=json.loads((O/'cad-geometry.json').read_text())
planes={p['layer']:unary_union([Polygon(x['outer'],x['holes']).buffer(0) for x in p['polygons']]) for p in j['planes']}
pairs=['/'+p+'_'+n for p in ('CLK','RX','TX') for n in ('P','N')]
returns=[];voids=[]
for t in j['tracks']:
 if t['net'] not in pairs:continue
 if t['kind']=='track':
  p=planes['In1.Cu' if t['layer']=='F.Cu' else 'In2.Cu'];line=LineString([t['a'],t['b']]);uncovered=line.difference(p).length
  # Ignore each own via's antipad: unavoidable launch, audited separately below.
  launch=unary_union([Point(v['a']).buffer(v['width']/2+.16) for v in j['tracks'] if v['kind']=='via' and v['net']==t['net']])
  beyond=line.difference(p).difference(launch).length
  if beyond>1e-5:voids.append({'net':t['net'],'layer':t['layer'],'unreferenced_mm':beyond,'a':t['a'],'b':t['b']})
 else:
  nearest=min(math.dist(t['a'],v['a']) for v in j['tracks'] if v['kind']=='via' and v['net']=='/GND')
  returns.append({'net':t['net'],'xy':t['a'],'nearest_GND_via_center_mm':nearest,'within_1mm':nearest<=1.0})
# Coordinates are CAD datums, not a fabricated enclosure. TE peg datum=(65,50).
card=box(54,48.25,76,90.25);tolerance=card.buffer(.35,join_style='mitre');board=box(20,20,100,98)
collisions=[]
for f in j['footprints']:
 if f['ref'] in ['J2','H5']:continue
 if box(*f['bbox']).intersects(tolerance):collisions.append(f['ref'])
holes={f['ref']:f['xy'] for f in j['footprints'] if f['ref'].startswith('H')}
source={'TE_drawing':'https://cdn.sparkfun.com/assets/9/c/e/b/6/MicroMod_M.2_Connector_Datasheet_TE_2199230-4.pdf','module_envelope':'https://globalamericaninc.com/wp-content/uploads/2023/04/2242-NVMe-with-DRAM-MLC-1.pdf'}
mech={'status':'PASS_2D' if not collisions and board.covers(tolerance) else 'FAIL','board_mm':[80,78,1.6],'outline_mm':[20,20,100,98],'card_nominal_mm':[22,42],'card_bbox_mm':list(card.bounds),'tolerance_expansion_mm':.35,'minimum_card_to_board_edge_mm':board.boundary.distance(tolerance),'other_footprints_in_card_envelope':collisions,'mounting_centers_mm':holes,'standoff':'2.48mm lower card plane REF from TE; 2.5mm support candidate. Final mating-height tolerance and actual SSD drawing still open. H5 is Wurth9774025243R SMT support at a candidate mating datum; library footprint includes a 3mm NPTH center clearance.', 'card_tip_from_TE_peg_mm':-1.75,'card_end_and_notch_center_Y_mm':90.25,'height_envelope_above_carrier_mm':6.5,'height_scope':'Reserved envelope >=2.48mm card underside + up to3.65mm example double-sided module + tolerance. Includes no enclosure. Connector4.2mm max, header~8.4mm separately.','sources':source,'pi_HAT_compatible_claim':False}
si={'status':'PASS_GEOMETRY' if not voids and all(x['within_1mm'] for x in returns) else 'ACTION_REQUIRED','scope':'Actual filled inner-plane projection and return-via distance. Via antipads exempted within0.36mm of own launch; no3D EM result.','reference_plane_void_segments':voids,'TX_transitions':returns,'reference_plane_areas_mm2':{k:v.area for k,v in planes.items()},'return_via_design_target_mm':1.0}
(O/'mechanical.json').write_text(json.dumps(mech,indent=2)+'\n');(O/'si-return-paths.json').write_text(json.dumps(si,indent=2)+'\n')
fig,ax=plt.subplots(figsize=(7,6.7),layout='constrained');ax.add_patch(Rectangle((20,20),80,78,fill=False,lw=2));ax.add_patch(Rectangle((54,48.25),22,42,fc='#dcecf7',ec='#28628c',alpha=.8));
for f in j['footprints']:
 x,y,xx,yy=f['bbox'];ax.add_patch(Rectangle((x,y),xx-x,yy-y,fill=False,lw=.5));ax.text(*f['xy'],f['ref'],fontsize=7)
for ref,xy in holes.items():ax.add_patch(Circle(xy,1.5 if ref=='H5' else 1.35,fill=False,color='red'))
ax.annotate('2242 SSD: 22 x 42 mm\nTE insertion datum y=48.25\nSupport datum y=90.25',(65,75),ha='center',fontsize=8)
ax.set(xlim=(15,105),ylim=(103,15),aspect='equal',xlabel='x (mm)',ylabel='y (mm)',title='Rev0.3.1 mechanical envelope / standalone adapter');ax.grid(alpha=.15);fig.savefig(O/'mechanical-plan.png',dpi=180);plt.close(fig)
print(json.dumps({'mechanical':mech,'si':si},indent=2))
