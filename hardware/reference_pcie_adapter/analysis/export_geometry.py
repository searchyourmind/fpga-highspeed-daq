"""Export real KiCad objects used by independent engineering checks."""
from pathlib import Path
import json,pcbnew as k
H=Path(__file__).resolve().parents[1];b=k.LoadBoard(str(H/'kicad/pi5_m2_reference.kicad_pcb'))
pt=lambda p:[p.x/1e6,p.y/1e6]
tracks=[];fps=[];pads=[]
for t in b.GetTracks():
 via=isinstance(t,k.PCB_VIA)
 tracks.append({'net':t.GetNetname(),'kind':'via' if via else 'track','a':pt(t.GetStart()),'b':pt(t.GetEnd()),'width':t.GetWidth(k.F_Cu)/1e6 if via else t.GetWidth()/1e6,'layer':'ALL' if via else t.GetLayerName(),'drill':t.GetDrill()/1e6 if via else 0})
for f in b.GetFootprints():
 box=f.GetBoundingBox(False,False)
 fps.append({'ref':f.GetReference(),'value':f.GetValue(),'xy':pt(f.GetPosition()),'bbox':[box.GetX()/1e6,box.GetY()/1e6,box.GetRight()/1e6,box.GetBottom()/1e6],'footprint':f.GetFPIDAsString()})
 for p in f.Pads():
  bb=p.GetBoundingBox()
  pads.append({'ref':f.GetReference(),'pin':p.GetNumber(),'net':p.GetNetname(),'xy':pt(p.GetPosition()),'size':pt(p.GetSize()),'bbox':[bb.GetX()/1e6,bb.GetY()/1e6,bb.GetRight()/1e6,bb.GetBottom()/1e6],'drill':pt(p.GetDrillSize()),'through':bool(p.IsOnLayer(k.B_Cu))})
# Export the actual filled polygons; holes subtracted by downstream geometry tool.
planes=[]
for z in b.Zones():
 poly=z.GetFilledPolysList(z.GetLayer());shapes=[]
 for i in range(poly.OutlineCount()):
  shape={'outer':[pt(poly.COutline(i).CPoint(j)) for j in range(poly.COutline(i).PointCount())],'holes':[]}
  for n in range(poly.HoleCount(i)):
   h=poly.CHole(i,n);shape['holes'].append([pt(h.CPoint(j)) for j in range(h.PointCount())])
  shapes.append(shape)
 planes.append({'layer':b.GetLayerName(z.GetLayer()),'net':z.GetNetname(),'polygons':shapes})
result={'units':'mm','tracks':tracks,'pads':pads,'footprints':fps,'planes':planes}
(H/'outputs/engineering').mkdir(exist_ok=True);(H/'outputs/engineering/cad-geometry.json').write_text(json.dumps(result,indent=2)+'\n')
print('Exported actual tracks/pads/filled GND polygons')
