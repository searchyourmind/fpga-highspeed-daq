"""Cross-section assumptions, actual coplanar proximity and unrelaxed design search."""
from field_solver import pair,O
from pathlib import Path
import json,math
from shapely.geometry import Polygon,LineString
from shapely.ops import unary_union
results=[]
def run(name,**kw):
 row,_=pair(step=.005,**kw);row.update(case=name,lower_margin_ohm=row['Zdiff_ohm']-81,upper_margin_ohm=99-row['Zdiff_ohm']);results.append(row);print(name,row['Zdiff_ohm'],flush=True);return row
baseline=run('legacy_reproduction') # compare exactly against retained mesh row below
old=json.loads((O/'field-solver.json').read_text());oldmesh=next(x for x in old['cases'] if x['case']=='mesh' and x['step']==.005);assert abs(baseline['Zdiff_ohm']-oldmesh['Zdiff_ohm'])<1e-8
# One variable at a time identifies input sensitivity instead of silently replacing assumptions.
for label,kw in [('Cu30um',dict(t=.030)),('Cu40p64um',dict(t=.04064)),('mask_manufacturer_rect',dict(mask_base=.03048,mask_top=.01524,mask_er=3.8)),('etched_top',dict(top_narrowing=.01778)),('coplanar_0p15',dict(coplanar_gap=.15)),('coplanar_0p30',dict(coplanar_gap=.30))]:run(label,**kw)
combined=dict(t=.04064,mask_base=.03048,mask_top=.01524,mask_er=3.8,top_narrowing=.01778)
run('manufacturer_reference_combined',**combined)
# Confirm stair-step trapezoid sensitivity at higher resolution without calibrating results.
fine,_=pair(step=.0025,**combined);results.append(dict(case='manufacturer_combined_fine',**fine))
# Candidate geometry study retains ORIGINAL etch/h/Er extremes, including correlated gaps.
# Manufacturer reference parameters are a separate sensitivity, not accepted process guarantees.
candidates=[]
for stack,h,er,w,g in [('3313',.0994,4.1,.13,.10),('3313',.0994,4.1,.15,.20),('3313',.0994,4.1,.17,.30),('7628',.2104,4.4,.30,.20),('7628',.2104,4.4,.32,.30),('7628',.2104,4.4,.34,.40),('1080',.0764,3.91,.12,.10)]:
 bounds=[]
 for label,dw,dg,hscale,de in [('low',.015,-.015,.9,.2),('high',-.015,.015,1.1,-.2)]:
  row=run(f'{stack}_{w}_{g}_{label}',w=w+dw,g=g+dg,h=h*hscale,er=er+de);bounds.append(row['Zdiff_ohm'])
 candidates.append(dict(stack=stack,nominal_h_mm=h,nominal_er=er,w_mm=w,g_mm=g,Zlow=bounds[0],Zhigh=bounds[1],lower_margin=bounds[0]-81,upper_margin=99-bounds[1],pass_original_bounds=bounds[0]>=81 and bounds[1]<=99))
# Qualify the apparently passing7628 candidate against additional published copper/mask assumptions.
for stack,h,er,w,g in [('current3313',.0994,4.1,.14,.152),('candidate7628',.2104,4.4,.30,.20)]:
 for label,dw,dg,hs,de in [('low',.015,-.015,.9,.2),('high',-.015,.015,1.1,-.2)]:
  for copper in (.030,.04064):
   run(f'{stack}_{label}_manufacturer_Cu{copper}',w=w+dw,g=g+dg,h=h*hs,er=er+de,t=copper,mask_base=.03048,mask_top=.01524,mask_er=3.8,top_narrowing=.01778)
# Actual same-layer GND fill changes whether a non-coplanar cross-section is representative.
j=json.loads((O/'cad-geometry.json').read_text());planes={x['layer']:unary_union([Polygon(p['outer'],p['holes']).buffer(0) for p in x['polygons']]) for x in j['planes']};near=[]
for t in j['tracks']:
 if t['kind']=='track' and t['net'] in ['/CLK_P','/CLK_N','/RX_P','/RX_N','/TX_P','/TX_N']:
  line=LineString([t['a'],t['b']]);d=line.buffer(t['width']/2).distance(planes[t['layer']]);near.append(dict(net=t['net'],layer=t['layer'],length_mm=line.length,minimum_edge_to_same_layer_GND_mm=d))
result={'status':'FAIL_OR_UNQUALIFIED','legacy_unchanged':True,'sensitivity_cases':results,'geometry_candidates':candidates,'same_layer_GND_proximity':near,'scope':['Unchanged81..99ohm limits and original etch+/-15um/h+/-10%/Er+/-0.2 for geometry candidates. No narrowed tolerances.','Manufacturer calculator uses40.64um external Cu,30.48/15.24/30.48um mask withEr3.8 and trace-top narrowing17.78um. Published stack table instead lists35um externalCu. Treat discrepancy as an unqualified input range, not silently selected truth.','New tapered conductor is a grid staircase; mask is a simplified rectilinear enclosure, not a photographed microsection.','Actual outer GND is at least8.6mm away on inspected segments; nearby coplanar GND is a hypothetical sensitivity, not current routing. Full connector/via sections remain unmodeled.','Manufacturers generic track-width tolerance+/-20% is not the original+/-15um screening assumption and cannot establish a controlled process commitment.','No candidate routed or accepted. Full3D via/pad/connector/FFC losses and material frequency dispersion absent.'],'sources':['https://jlcpcb.com/impedance','https://jlcpcb.com/help/article/user-guide-to-the-jlcpcb-impedance-calculator','https://jlcpcb.com/capabilities/pcb-capabilities/'],'fabrication_released':False}
(O/'si-independent-review.json').write_text(json.dumps(result,indent=2)+'\n')
