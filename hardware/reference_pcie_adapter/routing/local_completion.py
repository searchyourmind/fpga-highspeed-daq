import pcbnew as k
p='hardware/reference_pcie_adapter/kicad/pi5_m2_reference.kicad_pcb';b=k.LoadBoard(p)
mm=k.FromMM
vec=lambda x,y:k.VECTOR2I(mm(x),mm(y))
def via(net,xy,w=.4,d=.2):
 v=k.PCB_VIA(b);v.SetPosition(vec(*xy));v.SetWidth(mm(w));v.SetDrill(mm(d));v.SetViaType(k.VIATYPE_THROUGH);v.SetLayerPair(k.F_Cu,k.B_Cu);v.SetNet(b.FindNet('/'+net));b.Add(v)
def track(net,points,layer=k.F_Cu,width=.2):
 for a,z in zip(points,points[1:]):
  t=k.PCB_TRACK(b);t.SetStart(vec(*a));t.SetEnd(vec(*z));t.SetWidth(mm(width));t.SetLayer(layer);t.SetNet(b.FindNet('/'+net));b.Add(t)
for t in list(b.GetTracks()):
 if isinstance(t,k.PCB_VIA) and t.GetNetname()=='/RESET_PI' and abs(k.ToMM(t.GetPosition().x)-79.985)<.001:b.Remove(t)
for a,z in [((28.95,59),(29.8,59)),((28.95,62),(29.8,62)),((76,28.49),(76,27.7)),((84.1125,46),(83.2,47.5))]:
 track('GND',[a,z]);via('GND',z)
for xy in [(83.2604,44.1461),(90.48,66.2),(34.6,53.6),(35.4,53.6),(34.6,54.4),(35.4,54.4)]:via('GND',xy)
for x in (41,44):
 track('GND',[(x,52.05),(x,51.2)],width=.4);via('GND',(x,51.2));via('GND',(x+.6,51.2));track('GND',[(x,51.2),(x+.6,51.2)],width=.4)
track('EXT_5V',[(24,57),(28,57),(31,54),(31,51),(34,51),(35.5,52.5),(37,54),(43,54)],k.B_Cu,.8)
for x in (42,43):
 via('EXT_5V',(x,54),.6,.3);track('EXT_5V',[(x,54),(x,53.95)],width=.6)
via('EXT_5V',(86.25,46))
k.SaveBoard(p,b)
print('Ground plane stitching, EP thermal vias, input feed and local supply connection added')
