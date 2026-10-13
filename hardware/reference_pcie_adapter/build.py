"""Generate native, electrically connected KiCad reference files and honest checks.
Does not manufacture. Layout is an unfinished routed high-speed reference.
"""
from pathlib import Path
import os,json,uuid,csv,subprocess,math,re
import faulthandler
faulthandler.enable()
faulthandler.dump_traceback_later(25,repeat=False)
import wx
app=wx.App(False)
import pcbnew as k
from design import P,ptype
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[1]
K=HERE/'kicad';OUT=HERE/'outputs';K.mkdir(exist_ok=True);OUT.mkdir(exist_ok=True)
uid=lambda s:str(uuid.uuid5(uuid.NAMESPACE_URL,'daq-reference/'+s))
rootid=uid('sheet')
(K/'pi5_m2_reference.kicad_pro').write_text(json.dumps({'meta':{'filename':'pi5_m2_reference.kicad_pro','version':1},'net_settings':{'classes':[{'name':'Default','clearance':0.1,'track_width':0.2,'via_diameter':0.4,'via_drill':0.2,'diff_pair_width':0.14,'diff_pair_gap':0.15}],'meta':{'version':3}}},indent=2))
def prop(name,value,x,y,hide=False):
 return f'(property "{name}" "{value}" (at {x} {y} 0) (effects (font (size 1 1))'+(' hide' if hide else '')+'))'
libs=[];instances=[];extras=[]
for part in P:
    ref=part.ref; pins=list(part.pins); n=(len(pins)+1)//2
    h=max(5,n*2.54/2+2.54);w=12.7 if len(pins)>6 else 8.89
    lib=[f'(symbol "DAQ:{ref}" (pin_names (offset 0.5)) (in_bom yes) (on_board yes)',prop('Reference',ref,0,h+3),prop('Value',part.value,0,h+1),prop('Footprint',part.footprint,0,0,True),f'(symbol "{ref}_0_1" (rectangle (start {-w} {h}) (end {w} {-h}) (stroke (width 0.254) (type default)) (fill (type background))))']
    # Library rectangle closing: retain outer symbol, insert pin unit before final close.
    lib.append(f'(symbol "{ref}_1_1"')
    sx,sy=(round(v/1.27)*1.27 for v in part.sch)
    for i,pin in enumerate(pins):
        left=i<n; row=i if left else i-n
        px=-(w+5.08) if left else w+5.08; py=(n-1)*1.27-row*2.54;angle=0 if left else 180
        net=part.pins[pin]; name=net or 'NC'
        lib.append(f'(pin {ptype(part,pin)} line (at {px} {py} {angle}) (length 5.08) (name "{name}" (effects (font (size 0.9 0.9)))) (number "{pin}" (effects (font (size 0.9 0.9)))))')
        x,y=sx+px,sy-py
        if net:
            end=x+(-5.08 if left else 5.08)
            extras.append(f'(wire (pts (xy {x} {y}) (xy {end} {y})) (stroke (width 0) (type default)) (uuid {uid(ref+pin+"wire")}))')
            extras.append(f'(label "{net}" (at {end} {y} 0) (effects (font (size 0.9 0.9)) (justify {"right" if left else "left"} bottom)) (uuid {uid(ref+pin+"label")}))')
        else: extras.append(f'(no_connect (at {x} {y}) (uuid {uid(ref+pin+"nc")}))')
    lib.append('))');libs.append('\n'.join(lib))
    instances.append(f'''(symbol (lib_id "DAQ:{ref}") (at {sx} {sy} 0) (unit 1) (in_bom yes) (on_board yes) (dnp no) (uuid {uid(ref)})
{prop('Reference',ref,sx,sy-h-4)}
{prop('Value',part.value,sx,sy-h-1.5)}
{prop('Footprint',part.footprint,sx,sy,True)}
(instances (project "pi5_m2_reference" (path "/{rootid}" (reference "{ref}") (unit 1)))))''')
notes=[('PI 5 FFC / M.2 M-KEY - DESIGN REVIEW DRAFT',25,15),('Separate reference board. Gen2 x1 target. Not fabricated or electrically validated.',25,20),('External 5V feeds SSD only. FFC 5V is detection-only; DO NOT connect supplies.',25,25),('HIGH-SPEED SIGNALS / HOST-SIDE PIN MAP',25,35),('POWER / POWER-DOWN SIDEBAND ISOLATION',240,25),('PASSIVES - NET LABELS ARE ELECTRICAL CONNECTIONS',25,215),('Optional SUSCLK input: oscillator selection and SSD requirements remain open.',25,385),('Routing is supplied separately. Component/mechanical review pending. DRAFT ONLY.',25,390)]
for i,(txt,x,y) in enumerate(notes):extras.append(f'(text "{txt}" (at {x} {y} 0) (effects (font (size 1.3 1.3)) (justify left bottom)) (uuid {uid("note"+str(i))}))')
sch=f'''(kicad_sch (version 20230121) (generator "eeschema") (uuid {rootid}) (paper "A2")
(title_block (title "Pi 5 to M.2 M-key / DESIGN REVIEW DRAFT") (date "2026-10-12") (rev "0.3.1") (company "Qizheng Sui - simulation-independent reference"))
(lib_symbols {''.join(libs)})
{''.join(extras)} {''.join(instances)} (sheet_instances (path "/" (page "1"))))'''
(K/'pi5_m2_reference.kicad_sch').write_text(sch)
# Same exact source pin map goes into netlist, BOM and board.
(K/'DAQ.kicad_sym').write_text('(kicad_symbol_lib (version 20220914) (generator kicad_symbol_editor)\n'+''.join(s.replace('"DAQ:','"',1) for s in libs)+')')
(K/'sym-lib-table').write_text('(sym_lib_table (lib (name "DAQ") (type "KiCad") (uri "${KIPRJMOD}/DAQ.kicad_sym") (options "") (descr "Audited pin-map symbols")))')
with (HERE/'BOM.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['Reference','Value','Footprint','Note']);w.writerows((p.ref,p.value,p.footprint,p.note) for p in P)
(HERE/'pin-map.json').write_text(json.dumps({p.ref:p.pins for p in P},indent=2)+'\n')
b=k.BOARD();b.SetCopperLayerCount(4)
nets={}
for name in sorted({net for p in P for net in p.pins.values() if net}):
 n=k.NETINFO_ITEM(b,'/'+name);b.Add(n);nets[name]=n
mm=k.FromMM
vec=lambda x,y:k.VECTOR2I(mm(x),mm(y))
def line(a,z,layer,width=.1):
 s=k.PCB_SHAPE();s.SetShape(k.SHAPE_T_SEGMENT);s.SetStart(vec(*a));s.SetEnd(vec(*z));s.SetLayer(layer);s.SetWidth(mm(width));b.Add(s)
for a,z in [((20,20),(100,20)),((100,20),(100,98)),((100,98),(20,98)),((20,98),(20,20))]:line(a,z,k.Edge_Cuts,.05)
def custom_m2():
 fp=k.FOOTPRINT(b);fp.SetFPID(k.LIB_ID('DAQ','TE_M2_M_1-2199230-4'))
 for num in [i for i in range(1,76) if i not in range(59,67)]+[76,77]:
  pad=k.PAD(fp);pad.SetNumber(str(num));pad.SetAttribute(k.PAD_ATTRIB_SMD);pad.SetShape(k.PAD_SHAPE_RECT);layers=k.LSET();layers.AddLayer(k.F_Cu);layers.AddLayer(k.F_Paste);layers.AddLayer(k.F_Mask);pad.SetLayerSet(layers)
  if num<=75:
   odd=num%2; x=-9.25+(num-1)/4 if odd else -9+(num-2)/4;y=-5.275 if odd else 2.275
   pad.SetSize(vec(.3,1.55))
  else:x=-10.35 if num==76 else 10.35;y=-4.5;pad.SetSize(vec(1.2,2.75))
  pad.SetPosition(vec(x,y));fp.Add(pad)
 for x,d in [(-10,1.1),(10,1.6)]:
  pad=k.PAD(fp);pad.SetAttribute(k.PAD_ATTRIB_NPTH);pad.SetShape(k.PAD_SHAPE_CIRCLE);pad.SetSize(vec(d,d));pad.SetDrillSize(vec(d,d));pad.SetPosition(vec(x,0));pad.SetLayerSet(k.LSET.AllCuMask());fp.Add(pad)
 # Accurate land pattern; simplified mechanical body outline, pending independent review.
 for layer in (k.F_Fab,k.F_CrtYd):
  for a,z in [((-11.2,-6.5),(11.2,-6.5)),((11.2,-6.5),(11.2,3.5)),((11.2,3.5),(-11.2,3.5)),((-11.2,3.5),(-11.2,-6.5))]:
   sh=k.PCB_SHAPE();sh.SetShape(k.SHAPE_T_SEGMENT);sh.SetStart(vec(*a));sh.SetEnd(vec(*z));sh.SetLayer(layer);sh.SetWidth(mm(.05));fp.Add(sh)
 return fp
fps={}
for p in P:
 if p.ref=='J2':fp=custom_m2()
 else:
  lib,name=p.footprint.split(':');fp=k.FootprintLoad('/usr/share/kicad/footprints/'+lib+'.pretty',name)
  if not fp:raise RuntimeError('Missing footprint '+p.footprint)
  fp.SetFPID(k.LIB_ID(lib,name))
 fp.SetReference(p.ref);fp.SetValue(p.value);fp.SetPosition(vec(*p.xy[:2]));fp.SetOrientationDegrees(p.xy[2]);b.Add(fp)
 path=k.KIID_PATH();path.push_back(k.KIID(rootid));path.push_back(k.KIID(uid(p.ref)));fp.SetPath(path)
 for pad in fp.Pads():
  net=p.pins.get(pad.GetNumber())
  if net:pad.SetNet(nets[net])
  elif pad.GetNumber() in p.pins:
   n=k.NETINFO_ITEM(b,f'unconnected-({p.ref}-NC-Pad{pad.GetNumber()})');b.Add(n);pad.SetNet(n)
 fp.Reference().SetTextSize(vec(.8,.8));fp.Reference().SetPosition(vec(p.xy[0],p.xy[1]+3.5));fp.Reference().SetVisible(True);fp.Reference().SetLayer(k.F_Fab);fp.Value().SetVisible(False)
 fps[p.ref]=fp
# Persist custom footprint for native editing; it is not a fabricated 3D component.
local=K/'DAQ.pretty';local.mkdir(exist_ok=True);mf=custom_m2();mf.SetValue('TE_M2_M_1-2199230-4');plugin=k.PCB_IO_KICAD_SEXPR();plugin.FootprintSave(str(local),mf)
(K/'fp-lib-table').write_text('(fp_lib_table\n'+''.join(f'(lib (name "{l}") (type "KiCad") (uri "${{KICAD9_FOOTPRINT_DIR}}/{l}.pretty") (options "") (descr "KiCad official library"))' for l in sorted({p.footprint.split(':')[0] for p in P if not p.footprint.startswith('DAQ:')}))+'(lib (name "DAQ") (type "KiCad") (uri "${KIPRJMOD}/DAQ.pretty") (options "") (descr "Review-draft M-key land pattern")))')
def padxy(ref,pin):
 p=next(p for p in fps[ref].Pads() if p.GetNumber()==str(pin));return k.ToMM(p.GetPosition().x),k.ToMM(p.GetPosition().y)
def track(net,points,layer=k.F_Cu,width=.14):
 for a,z in zip(points,points[1:]):
  if a==z:continue
  t=k.PCB_TRACK(b);t.SetStart(vec(*a));t.SetEnd(vec(*z));t.SetWidth(mm(width));t.SetLayer(layer);t.SetNet(nets[net]);b.Add(t)
def via(net,xy):
 v=k.PCB_VIA(b);v.SetPosition(vec(*xy));v.SetWidth(mm(.4));v.SetDrill(mm(.2));v.SetViaType(k.VIATYPE_THROUGH);v.SetLayerPair(k.F_Cu,k.B_Cu);v.SetNet(nets[net]);b.Add(v)
# Three coupled pair trunks: keep TX on bottom to avoid crossing RX/clock.
lengths={}
for prefix,pins1,pins2,layer,ybend in [('CLK',(4,5),(55,53),k.F_Cu,34),('RX',(7,8),(43,41),k.F_Cu,38),('TX',(10,11),(49,47),k.B_Cu,34.0)]:
 for suffix,p1,p2,sgn in zip(('P','N'),pins1,pins2,(1,-1)):
  net=prefix+'_'+suffix;a=padxy('J1',p1);z=padxy('J2',p2)
  if layer==k.B_Cu:
   va=(a[0]+sgn*.075,a[1]+2.7);vz=(z[0]+sgn*.075,z[1]-2.7);track(net,[a,va]);track(net,[vz,z]);via(net,va);via(net,vz);a,z=va,vz
  # 0.29mm center spacing in the main parallel segment; connector breakouts 0.5mm.
  center_a=sum(padxy('J1',i)[0] for i in pins1)/2;center_z=sum(padxy('J2',i)[0] for i in pins2)/2
  xa=center_a+sgn*.146;xz=center_z+sgn*.146
  bend=ybend-sgn*.146*(math.sqrt(2)-1)
  points=[a,(xa,a[1]+.8),(xa,bend),(xz,bend+abs(xz-xa)),(xz,z[1]-.8),z]
  track(net,points,layer);lengths[net]=sum(math.dist(x,y) for x,y in zip(points,points[1:]))+(2*math.hypot(.075,2.7) if layer==k.B_Cu else 0)
# Power-stage local loops: direct pad-to-pad only where geometrically short.
for net,ends,width in [('SW',[('U1',1),('U1',2),('U1',3)],.3),('SW',[('U1',2),('L1',1)],.5),('SSD_3V3',[('C3',1),('C4',1)],.6)]:
 track(net,[padxy(*e) for e in ends],width=width)
track('SSD_3V3',[padxy('L1',2),(26.5,51.525),(26.5,59),padxy('C3',1)],width=.6)
# Solid reference planes. No power split below the high-speed pair trunks.
for layer in (k.In1_Cu,k.In2_Cu):
 zone=k.ZONE(b);zone.SetLayer(layer);zone.SetNet(nets['GND']);zone.SetLocalClearance(mm(.15));zone.SetThermalReliefGap(mm(.2));zone.SetThermalReliefSpokeWidth(mm(.25));zone.SetPadConnection(k.ZONE_CONNECTION_FULL)
 o=zone.Outline();o.NewOutline()
 for x,y in [(20.3,20.3),(99.7,20.3),(99.7,97.7),(20.3,97.7)]:o.Append(mm(x),mm(y))
 b.Add(zone)
# Local solid outer-layer GND spreaders; keep high-speed pair area unchanged.
for layer in (k.F_Cu,k.B_Cu):
 zone=k.ZONE(b);zone.SetLayer(layer);zone.SetNet(nets['GND']);zone.SetLocalClearance(mm(.2));zone.SetPadConnection(k.ZONE_CONNECTION_FULL);o=zone.Outline();o.NewOutline()
 for x,y in [(20.3,20.3),(52,20.3),(52,57.5),(99.7,57.5),(99.7,97.7),(20.3,97.7)]:o.Append(mm(x),mm(y))
 b.Add(zone)
# Ground-return vias at each connector ground; power EP via is included.
for ref in ('J1','J2','U1'):
 for pad in fps[ref].Pads():
  if pad.GetNetname()=='/GND' and pad.GetNumber():
   xy=(k.ToMM(pad.GetPosition().x),k.ToMM(pad.GetPosition().y));vxy=(xy[0],xy[1]+(1.7 if ref=='J1' else (1.5 if ref=='J2' and xy[1]>50 else -1.5)))
   # Plane connection near pad; final fanout DRC is a release gate.
   if ref=='U1':continue
   track('GND',[xy,vxy],width=.16);via('GND',vxy)
text=k.PCB_TEXT(b);text.SetText('PI5 / M.2 REFERENCE 0.1\nDESIGN REVIEW ONLY - UNROUTED');text.SetPosition(vec(48,93));text.SetTextSize(vec(1,1));text.SetTextThickness(mm(.15));text.SetLayer(k.F_SilkS);b.Add(text)
# 2242 card envelope based on TE insertion datum and a 42mm module.
# Standoff datum is provisional until mating SSD drawing is approved; review-only NPTH.
for a,z in [((54,48.25),(54,90.25)),((54,90.25),(76,90.25)),((76,90.25),(76,48.25)),((76,48.25),(54,48.25))]:line(a,z,k.Dwgs_User,.15)
# Standalone adapter mounting: not a Pi HAT+ hole pattern.
for ref,xy,d in [('H1',(24,24),2.7),('H2',(96,24),2.7),('H3',(24,94),2.7),('H4',(96,94),2.7)]:
 fp=k.FootprintLoad('/usr/share/kicad/footprints/MountingHole.pretty','MountingHole_2.7mm_M2.5' if d==2.7 else 'MountingHole_2.2mm_M2')
 fp.SetReference(ref);fp.SetValue('M2.5 board mount' if d==2.7 else 'SSD standoff / DATUM REVIEW');fp.SetPosition(vec(*xy));fp.SetAttributes(k.FP_EXCLUDE_FROM_BOM|k.FP_EXCLUDE_FROM_POS_FILES|k.FP_BOARD_ONLY)
 fp.Reference().SetVisible(False);fp.Value().SetVisible(False);b.Add(fp)
board=K/'pi5_m2_reference.kicad_pcb';k.SaveBoard(str(board),b)
# Replace default stack with documented four-layer reference stack. Impedance is preliminary.
s=board.read_text();
if '(stackup' not in s: s=s.replace('(setup','(setup (stackup)',1)
start=s.index('(stackup');depth=0;end=None
for i in range(start,len(s)):
 if s[i]=='(':depth+=1
 elif s[i]==')':
  depth-=1
  if depth==0:end=i+1;break
stack='''(stackup
(layer "F.SilkS" (type "Top Silk Screen"))
(layer "F.Paste" (type "Top Solder Paste"))
(layer "F.Mask" (type "Top Solder Mask") (thickness 0.01))
(layer "F.Cu" (type "copper") (thickness 0.035))
(layer "dielectric 1" (type "prepreg") (thickness 0.0994) (material "3313") (epsilon_r 4.1) (loss_tangent 0.02))
(layer "In1.Cu" (type "copper") (thickness 0.0152))
(layer "dielectric 2" (type "core") (thickness 1.265) (material "FR4") (epsilon_r 4.6) (loss_tangent 0.02))
(layer "In2.Cu" (type "copper") (thickness 0.0152))
(layer "dielectric 3" (type "prepreg") (thickness 0.0994) (material "3313") (epsilon_r 4.1) (loss_tangent 0.02))
(layer "B.Cu" (type "copper") (thickness 0.035))
(layer "B.Mask" (type "Bottom Solder Mask") (thickness 0.01))
(layer "B.Paste" (type "Bottom Solder Paste"))
(layer "B.SilkS" (type "Bottom Silk Screen")) (copper_finish "ENIG") (dielectric_constraints no))'''
s=s[:start]+stack+s[end:];board.write_text(s)
(K/'pi5_m2_reference.kicad_dru').write_text('''(version 1)
(rule "Minimum via" (constraint via_diameter (min 0.4mm)))
(rule "Minimum drill" (constraint hole_size (min 0.2mm)))
(rule "Minimum trace" (constraint track_width (min 0.127mm)))
(rule "Copper clearance" (constraint clearance (min 0.1mm)))
(rule "PCIe pair gap" (condition "A.NetName == '/CLK_P' || A.NetName == '/CLK_N' || A.NetName == '/RX_P' || A.NetName == '/RX_N' || A.NetName == '/TX_P' || A.NetName == '/TX_N'") (constraint diff_pair_gap (min 0.15mm) (opt 0.15mm) (max 0.36mm)))
''')
(OUT/'trace-lengths.json').write_text(json.dumps({'scope':'CAD centerline lengths, not electrical delay; no connector/via delay model','length_mm':lengths,'skew_mm':{x:abs(lengths[x+'_P']-lengths[x+'_N']) for x in ('CLK','RX','TX')}},indent=2)+'\n')
print('NATIVE_REFERENCE_WRITTEN: electrically connected schematic; four-layer partial layout; checks follow')
