#!/bin/sh
set -eu
cad_root=hardware/reference_pcie_adapter
mkdir -p "$cad_root/outputs" output/pdf
xvfb-run -a kicad-cli pcb render --width 1200 --height 800 --side top --background opaque --rotate 35,0,25 -o "$cad_root/outputs/board-3d.png" "$cad_root/kicad/pi5_m2_reference.kicad_pcb"
kicad-cli pcb export svg --layers F.Cu,B.Cu,Edge.Cuts,F.SilkS --mode-single -o "$cad_root/outputs/board-svg" "$cad_root/kicad/pi5_m2_reference.kicad_pcb"
kicad-cli sch export pdf -o "$cad_root/outputs/schematic-review.pdf" "$cad_root/kicad/pi5_m2_reference.kicad_sch"
