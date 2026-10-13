"""Current portable four-page release review; all quantities read from evidence."""
from pathlib import Path
import json,xml.etree.ElementTree as ET
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.platypus import Paragraph,Table,TableStyle
from reportlab.lib.styles import ParagraphStyle
R=Path(__file__).resolve().parents[1];O=R/'output/pdf';O.mkdir(parents=True,exist_ok=True)
H=R/'hardware/reference_pcie_adapter';E=H/'outputs/engineering';j=lambda n:json.loads((E/(n+'.json')).read_text());v,t,s=j('voltage-root-cause'),j('thermal-independent-review'),j('si-independent-review')
assert sum(len(list(ET.parse(p).iter('testcase'))) for p in (R/'results').glob('*.xml'))==63
c=canvas.Canvas(str(O/'Independent_Release_Review.pdf'),pagesize=(612,792));c.setTitle('FPGA DAQ - Independent Release Review');c.setAuthor('Qizheng Sui')
body=ParagraphStyle('body',fontName='Helvetica',fontSize=10.2,leading=14,textColor=HexColor('#203449'));small=ParagraphStyle('small',parent=body,fontSize=8.6,leading=11.5)
def para(text,y,style=body):
 p=Paragraph(text,style);_,h=p.wrap(540,720);assert y-h>38,(text,y,h);p.drawOn(c,36,y-h);return y-h-10

def title(n,name,sub):
 c.setFillColor(HexColor('#17334b'));c.rect(0,697,612,95,fill=1,stroke=0);c.setFillColor(HexColor('#ffffff'));c.setFont('Helvetica-Bold',22);c.drawString(36,752,name);c.setFont('Helvetica',10);c.drawString(36,725,sub)
 c.setFillColor(HexColor('#526172'));c.setFont('Helvetica',8);c.drawString(36,24,'Qizheng Sui | Independent review | 12 October 2026 | Simulated, not measured');c.drawRightString(576,24,f'{n} / 4')
def table(rows,y,widths):
 cells=[[Paragraph(str(a),small) for a in row] for row in rows];obj=Table(cells,colWidths=widths);obj.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),HexColor('#e0e9ef')),('LINEBELOW',(0,0),(-1,-1),.3,HexColor('#c4d1d8')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]));_,h=obj.wrap(540,700);assert y-h>38;obj.drawOn(c,36,y-h);return y-h-12

def pic(p,x,y,w,h):c.drawImage(str(p),x,y,width=w,height=h,preserveAspectRatio=True,anchor='c',mask='auto')
title(1,'Verified RTL simulation','Publication recommendation: ready as a scoped simulation portfolio')
y=para('<b>63 tests PASS; all 33 E2E scenarios MATCH.</b> A fresh no-cache Docker tool build and source-only workspace reproduce lint, the complete test suite and generic synthesis. No new production RTL or model features were added during this review.',674)
pic(R/'portfolio/assets/architecture.png',36,360,540,235)
y=table([['Verification','Executed result'],['Production tests','39 pytest + 24 cocotb; 0 failures/skips. 33 matrix rows are inside these tests.'],['Independent challenges','Independent integer/CRC fixtures; six isolated mutations detected. An assertion-aborted mutant uses a bounded watchdog.'],['Toolchain','Verilator 5.040; cocotb 2.0.0; pytest 8.4.2; Yosys 0.33. Actual versions/return codes retained.'],['Generic synthesis','No latches/combination loops; 1,447 generic flip-flops; 42-cell longest topological combinational path.']],350,[119,421])
y=para('<b>Device timing closure remains BLOCKED.</b> There is no selected FPGA/speed grade, placed-and-routed design, vendor timing model or setup/hold slack. The illustrative 100 MHz constraint is not a result. DDR is behavioral; the link uses a custom envelope/CRC, not a real PCIe endpoint.',y)
para('Source and command evidence: docs/VERIFICATION_REVIEW.md; docs/SYSTEM_AUDIT.md; results/release-audit/; synthesis/reports/. No GitHub push or remote CI run occurred.',y,small);c.showPage()
title(2,'Debugging and real traces','Reproduction defects fixed; functional requirements unchanged')
y=para('Prior verified fixes: 4 KiB packet crossing at 0x1ff8; rejection of the final legal 8-byte record; host-context loss when completion preceded delayed delivery; and a runner that returned success despite failed cocotb XML.',674)
y=para('<b>Independent-review defect:</b> clean builds lacked results/system-audit/, causing extended tests to fail. The runner and writer now initialize it. A second clean source copy with a new tool image passes. Fault injection does not modify production sources.',y)
pic(R/'portfolio/assets/waveform.png',36,294,540,287)
pic(R/'portfolio/assets/benchmarks.png',36,103,540,181)
para('Plots are generated from actual VCD transitions and recorded benchmark JSON. Axes represent simulated time/cycles, not physical timing or bandwidth. Full VCD and SVG/PNG provenance: results/waveforms/ and portfolio/assets/.',91,small);c.showPage()
title(3,'Separate PCB: remaining FAILs','Rev 0.3.1 Pi carrier is not the FPGA DAQ board')
y=table([['Requirement','Result / unchanged acceptance'],['Voltage budget','3.130447-3.487610 V versus 3.135-3.465 V; margins -4.553 / -22.610 mV. FAIL.'],['Thermal minimum copper',f"6/24 cases fail at 30 um outer copper. Fine worst {t['worst_corrected_fine']['estimated_regulator_junction_C']:.3f} C versus 125 C; margin {125-t['worst_corrected_fine']['estimated_regulator_junction_C']:+.3f} C."],['Current impedance','Original broad high corner 106.126 ohm versus 99 ohm; local wide-gap fanout 104.135 ohm. FAIL.'],['Native CAD','Clean rebuild: ERC/DRC/unconnected/parity all zero. Geometric success does not qualify electrical or manufacturing gates.']],674,[122,418])
y=para('<b>Voltage roots:</b> low feedback/divider/leakage plus copper, ground/contact and dynamic reserves; high PSM feedback plus positive dynamic allowance. A divider-only solution cannot satisfy both bounds. PWM high margin is +10.847 mV; PSM is the failing upper case. The 16 uF stress is outside the datasheet PSM row\'s explicit 22 uF condition.',y)
y=para('<b>Thermal correction:</b> 35 um nominal copper was inconsistent with the 30 um minimum used for DC. All 24 cases were rerun without lowering losses or ambient. Original 159.381 C becomes 157.389 C with finer grid at 35 um, but 160.303 C at 30 um. The sixth failure remains 125.303 C on the fine grid.',y)
y=para('At the worst original hotspot, regulator board rise is 52.567 C; SSD coupling 22.379 C; inductor 8.536 C; copper 6.753 C; simplified package path 7.459 C. Weak convection and local heat dominate. Exact uniform-source and superposition checks pass. Above absolute maximum / near shutdown, the linear extrapolation is a rejection indicator, not sustainable operation.',y)
para('Thermal model is a 2D sheet with assumed heat/convection and simplified package/via path. No measured Tj, SSD die temperature, enclosure airflow or full 3D validation. Current detailed signed tables: hardware/reference_pcie_adapter/INDEPENDENT_REVIEW.md.',y,small);c.showPage()
title(4,'Process review and release limits','Publish truthful engineering evidence; retain hardware holds')
y=para('Stack, width/gap, copper, dielectric and solder-mask sensitivity were rerun. The manufacturer reference uses 40.64 um copper, 30.48/15.24 um mask with Er3.8 and 17.78 um top narrowing; its stack table separately lists 35 um copper. Inputs are not a manufacturing commitment.',674)
y=para('A 7628 candidate with h0.2104 mm, Er4.4, width0.30/gap0.20 mm passes the original two corners at 81.830-97.575 ohm. Adding published copper/mask/etch geometry produces a 79.257 ohm low corner: -1.743 ohm margin. It was not adopted. No requirement or tolerance was relaxed.',y)
pic(H/'outputs/board-3d.png',36,255,540,290)
y=para('<b>Open hardware gates:</b> joint voltage envelope, effective capacitors, thermal exit/SSD limits, qualified stack/process, connector/cable/assembly, full 3D channel and fabrication review.',228)
y=para('<b>Ready:</b> documented RTL/model source, 63-test regression, 33 E2E scenarios, generic synthesis, debug evidence and portable plots.<br/><b>Not tested:</b> FPGA timing/implementation, physical DDR/PCIe, measured throughput/power, hardware bring-up or fabrication. Historical v4 slides/PDFs are excluded from the current release scope.',y)
para('Official references: TI tps62130.pdf and spra953d.pdf; JLC stack table and impedance-calculator guide. Exact links, assumptions and evidence are in the independent PCB review. Reproduce: docs/REPRODUCING.md. Final disposition: docs/REQUIREMENTS_MATRIX.md. No purchases, fabrication or GitHub push.',y,small)
c.save();print(O/'Independent_Release_Review.pdf')
