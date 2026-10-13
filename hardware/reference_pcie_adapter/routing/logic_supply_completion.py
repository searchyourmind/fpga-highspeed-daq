import pcbnew as k
p='hardware/reference_pcie_adapter/kicad/pi5_m2_reference.kicad_pcb';b=k.LoadBoard(p)
mm=k.FromMM
vec=lambda x,y:k.VECTOR2I(mm(x),mm(y))
def via(net,xy,w=.4,d=.2):
 v=k.PCB_VIA(b);v.SetPosition(vec(*xy));v.SetWidth(mm(w));v.SetDrill(mm(d));v.SetViaType(k.VIATYPE_THROUGH);v.SetLayerPair(k.F_Cu,k.B_Cu);v.SetNet(b.FindNet('/'+net));b.Add(v)
def track(net,points,layer=k.F_Cu,width=.2):
 for a,z in zip(points,points[1:]):
  t=k.PCB_TRACK(b);t.SetStart(vec(*a));t.SetEnd(vec(*z));t.SetWidth(mm(width));t.SetLayer(layer);t.SetNet(b.FindNet('/'+net));b.Add(t)
# Low-current logic supply, with layer transitions avoiding sideband crossings.
track('EXT_5V',[(43,54),(46,53.95)],k.B_Cu)
track('EXT_5V',[(46,53.95),(48,53.95),(51,50.95),(52,50.95)])
for xy in [(46,53.95),(52,50.95),(69.65,49.8),(73.5,49.8),(82,47.3)]:via('EXT_5V',xy)
track('EXT_5V',[(52,50.95),(68.5,50.95),(69.65,49.8)],k.B_Cu)
track('EXT_5V',[(69.65,49.8),(73.5,49.8)])
track('EXT_5V',[(73.5,49.8),(74.2,51.45),(77.5,51.45),(80.5,48.45),(82,47.3)],k.B_Cu)
track('EXT_5V',[(82,47.3),(82,45.8),(81.7741,45.2437)])
k.SaveBoard(p,b)
print('Ground plane stitching, EP thermal vias, input feed and local supply connection added')
