#!/bin/sh
set -eu
sh tools/pcb-build.sh
cad_root=hardware/reference_pcie_adapter
pcb_file="$cad_root/kicad/pi5_m2_reference.kicad_pcb"
out_dir="$cad_root/outputs/DRAFT_NOT_FOR_MANUFACTURE"
mkdir -p "$out_dir"
printf '%s\n' 'DESIGN REVIEW DRAFT ONLY. NOT RELEASED FOR MANUFACTURE.' 'ERC/DRC connectivity checks do not qualify components, mechanics, SI, power or fabrication.' 'No fabrication/purchase/physical testing is authorized. See ../../README.md release gates.' > "$out_dir/README.txt"
kicad-cli pcb export gerbers --layers F.Cu,In1.Cu,In2.Cu,B.Cu,F.Mask,B.Mask,F.SilkS,B.SilkS,Edge.Cuts --subtract-soldermask -o "$out_dir/" "$pcb_file"
kicad-cli pcb export drill --format excellon --excellon-units mm --excellon-separate-th --generate-map --map-format svg --generate-report --report-path "$out_dir/drill-report.txt" -o "$out_dir/" "$pcb_file"
python3 - <<'PY'
from pathlib import Path
import hashlib,json
p=Path('hardware/reference_pcie_adapter/outputs/DRAFT_NOT_FOR_MANUFACTURE')
gerbers=list(p.glob('*.g*'));drills=list(p.glob('*.drl'))
assert len(gerbers)>=9 and len(drills)==2
for f in gerbers:
 if f.suffix!='.gbrjob':assert 'M02*' in f.read_text(),f
for f in drills:assert 'M48' in f.read_text() and 'M30' in f.read_text(),f
files={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(p.iterdir()) if f.is_file() and f.name!='export-manifest.json'}
(p/'export-manifest.json').write_text(json.dumps({'scope':'Native KiCad DRAFT export structural checks only; no CAM/DFM qualification','fabrication_released':False,'sha256':files},indent=2)+'\n')
print('DRAFT files exported and structural checks passed; manufacturing remains NOT RELEASED')
PY
