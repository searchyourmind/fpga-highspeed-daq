"""Replay checked, project-owned routing after an explicit PCB regeneration."""
from pathlib import Path
import json,pcbnew as k
H=Path(__file__).resolve().parent;p=H/'kicad/pi5_m2_reference.kicad_pcb';b=k.LoadBoard(str(p))
for t in list(b.GetTracks()):b.Remove(t)
for r in json.loads((H/'routing/tracks.json').read_text())['items']:
 t=k.PCB_VIA(b) if r['kind']=='via' else k.PCB_TRACK(b)
 t.SetStart(k.VECTOR2I(*r['a']));t.SetEnd(k.VECTOR2I(*r['b']));t.SetWidth(r['width_nm']);t.SetNet(b.FindNet(r['net']))
 if r['kind']=='via':
  t.SetDrill(r['drill_nm']);t.SetViaType(k.VIATYPE_THROUGH);t.SetLayerPair(k.F_Cu,k.B_Cu)
 else:t.SetLayer(b.GetLayerID(r['layer']))
 t.SetLocked(r['net'] in {'/'+a+'_'+z for a in ('CLK','RX','TX') for z in ('P','N')});b.Add(t)
k.SaveBoard(str(p),b)
p.write_text(p.read_text().replace('PI5 / M.2 REFERENCE 0.1', 'PI5 / M.2 REFERENCE 0.3.1').replace('DESIGN REVIEW ONLY - UNROUTED', 'DESIGN REVIEW ONLY - DRAFT'))
print('Replayed routing snapshot; differential nets locked')
