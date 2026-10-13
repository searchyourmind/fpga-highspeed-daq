import faulthandler
faulthandler.enable()
import wx
app=wx.App(False)
import pcbnew as k
p='hardware/reference_pcie_adapter/kicad/pi5_m2_reference.kicad_pcb'
b=k.LoadBoard(p)
b.BuildConnectivity()
f=k.ZONE_FILLER(b)
f.Fill(b.Zones())
k.SaveBoard(p,b)
print('Planes filled and board saved')
