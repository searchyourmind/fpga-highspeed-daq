"""Create a five-page engineering review from executed evidence, not claimed signoff."""
from pathlib import Path
import json
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph,Table,TableStyle
from reportlab.lib.styles import ParagraphStyle
R=Path(__file__).resolve().parents[3];H=R/'hardware/reference_pcie_adapter';O=H/'outputs/engineering'
j=lambda n:json.loads((O/(n+'.json')).read_text())
power=j('power-corners');tr=j('adapter-transient');therm=j('thermal');field=j('field-solver');proc=j('process-window');dc=j('dc-network');mech=j('mechanical');si=j('si-return-paths')
(R/'output/pdf').mkdir(parents=True,exist_ok=True)
c=canvas.Canvas(str(R/'output/pdf/PCB_Engineering_Review.pdf'),pagesize=(612,792));c.setTitle('PCB Reference Engineering Review - Revision 0.3.1');c.setAuthor('Qizheng Sui')
style=ParagraphStyle('body',fontName='Helvetica',fontSize=10.3,leading=14,textColor=HexColor('#203449'))
small=ParagraphStyle('small',parent=style,fontSize=8.5,leading=11)
def para(s,y,x=36,w=540,st=style):
 p=Paragraph(s,st);_,h=p.wrap(w,700);p.drawOn(c,x,y-h);
 assert y-h>38, (s,y,h)
 return y-h-10
def title(n,s,sub):
 c.setFillColor(HexColor('#17334b'));c.rect(0,694,612,98,fill=1,stroke=0);c.setFillColor(HexColor('#ffffff'));c.setFont('Helvetica-Bold',22);c.drawString(36,747,s);c.setFont('Helvetica',10);c.drawString(36,720,sub)
 c.setFillColor(HexColor('#667480'));c.setFont('Helvetica',8);c.drawString(36,24,'Qizheng Sui / 12 October 2026 / Rev 0.3.1 / DESIGN REVIEW DRAFT');c.drawRightString(576,24,f'{n} / 5')
def table(rows,y,widths):
 cells=[[Paragraph(str(a),small) for a in r] for r in rows];t=Table(cells,colWidths=widths);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),HexColor('#dfe9ef')),('LINEBELOW',(0,0),(-1,0),.6,HexColor('#537083')),('LINEBELOW',(0,1),(-1,-1),.3,HexColor('#d5dee4')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]));_,h=t.wrap(540,700);t.drawOn(c,36,y-h);
 assert y-h>38, (y,h)
 return y-h-12
def img(name,x,y,w,h):c.drawImage(ImageReader(str(name)),x,y,width=w,height=h,preserveAspectRatio=True,anchor='c',mask='auto')

margin=j('failure-margins');before=margin['baseline_rev03'];after=margin['corrected_copper_rev03_1'];loaded=j('adapter-loaded-corner');vf=j('voltage-feasibility');sink=j('thermal-exit-requirement');width=j('si-width-feasibility')
title(1,'PCB corrective engineering review','Rev 0.3 reviewed; corrected CAD Rev 0.3.1 / separate from the FPGA DAQ system')
y=para('<b>Software checks completed. Voltage, thermal and SI acceptance remain open.</b> The requirements were retained: 3.135-3.465 V supply, 125 C regulator junction, 81-99 ohm differential impedance, original ambient/cooling and broad process corners.',674)
y=table([['Executed work','Result'],['Native CAD','ERC 0 / DRC 0 / unconnected 0 / parity 0; original pairs preserved'],['Actual correction','Five long supply tracks 1.2 to 3.0 mm; feeder 1.0 to 1.3 mm; expanded outer GND spreaders'],['Power / thermal','108 DC/AC cases; new 6,455,898-point loaded switching trace; 126 copper distributions; 24 thermal cases'],['SI correction study','Eight new field solves, four widths under original process bounds; no passing width-only candidate'],['Remaining margins','Voltage -4.55 / -22.61 mV; worst Tj margin -34.38 C; broad high-Z margin -7.13 ohm']],y,[128,412])
img(H/'outputs/board-3d.png',36,106,540,250)
para('Actual KiCad render; some component bodies absent. No purchases, manufacture, hardware testing or GitHub push. Draft Gerber/drill exports are review evidence only. Full case tables and primary references: ENGINEERING_REVIEW.md.',89,st=small)
c.showPage()
title(2,'Voltage failures and simulation','Corrected copper improves low-voltage margin; composite tolerance gate remains FAIL')
rows=[['Composite case','Before V / margin mV','Corrected V / margin mV']]
for a,z in zip(before['voltage'],after['voltage']):rows.append([z['case'],f"{a['actual_V']:.6f} / {a['margin_mV']:+.3f}",f"{z['actual_V']:.6f} / {z['margin_mV']:+.3f}"])
y=table(rows,674,[174,183,183])
y=para('Roots: minimum feedback/divider/leakage plus distribution loss; PSM high feedback plus positive dynamic allowance. Copper drop at 2 A/125 C improved 59.397 to 37.161 mV. All other allowances retained: ground 10, contact 25, dynamic 40 and line/load 5 mV.',y)
y=para(f"Divider-only solution is infeasible under these bounds: Rtop must be at least {vf['lower_bound_required_Rtop_ohm']:.1f} ohm and at most {vf['upper_bound_allowed_Rtop_ohm']:.1f} ohm, with Rbottom 10 kohm. Raising one bound cannot close both.",y)
img(O/'adapter-loaded-corner.png',36,161,540,290)
y=para(f"New actual loaded corner: Vin 4.65 V; L 1.232 uH, DCR 75 mohm, Cout 16 uF, board R 18.580 mohm. Load event 3.266353-3.342949 V gives +131.353/+122.051 mV target margins. Peak IL 2.219306 A; steady/shutdown PG checks pass.",151)
para('TI A internal model remains room-temperature nominal. External-component stress is not a joint silicon/process/temperature sweep. The 40 mV allowance exceeds observed regulator excursions (nominal 35 mV; loaded corner 25.013 mV), but full qualification remains open. AC finiteness is not loop phase margin.',y,st=small)
c.showPage()
title(3,'Thermal failures and heat path','All original failing cases retained / no change to the 125 C acceptance limit')
rows=[['ID','Ambient / h','Reg / SSD W','Before Tj C','After Tj C','Margin C']]
for a,z in zip(before['thermal_cases'],after['thermal_cases']):
 if a['result']=='FAIL':rows.append([z['case_id'],f"{z['ambient_C']:.0f} / {z['h_each_side_W_m2K']:.0f}",f"{z['assumed_regulator_loss_W']:.1f} / {z['assumed_SSD_heat_into_carrier_W']:.2f}",f"{a['estimated_regulator_junction_C']:.3f}",f"{z['estimated_regulator_junction_C']:.3f}",f"{z['margin_C']:+.3f}"])
y=table(rows,674,[32,95,98,105,105,105])
y=para('<b>Five of 24 cases still fail.</b> Every case adds inductor 0.25 W and copper 0.25 W; h is W/m2K per exposed side. Case 3 now has only +0.619 C nominal margin, insufficient for hardware qualification given model uncertainty.',y)
y=para('Root cause: local regulator heat plus SSD coupling and insufficient heat exit at hot ambient/weak convection. Expanded copper lowers worst Tj by 1.397 C. Actual filled copper is sampled with 50% conductance derating; this is 2D steady screening, not CFD or an SSD die model.',y)
y=table([['Candidate total heat path K/W','Tj C at 60 C ambient / h5','Margin C']]+[[f"{x['candidate_sink_total_K_W']:.0f}",f"{x['estimated_regulator_junction_C']:.3f}",f"{x['margin_C']:+.3f}"] for x in sink['cases']],y,[180,215,145])
y=para('Candidate 10 x 10 mm contact: total resistance includes PCB/contact/interface/sink-to-ambient; covered convection removed. Coarse bisection gives about 49.79 K/W maximum for 125 C. This is an unimplemented requirement; no sink or assembly is approved. Even 15 K/W leaves SSD-region board temperature 103.49 C.',y)
para(f"Mesh 0.5-to-0.25 mm change: {therm['mesh_last_delta_T_C']:.3f} C in convergence case; energy balances pass. No 2 A continuous rating. Full 24-row signed margins: thermal-all-cases-before.csv and thermal-all-cases-after.csv.",y,st=small)
c.showPage()
title(4,'Components and mechanical review','30 conditional electrical references / no ordering or assembly release')
y=table([['Selection','Disposition'],['TPS62130ARGTR; XAL4020-222MEC','A regulator and 2.2 uH inductor retained. Hot fault behavior and joint voltage/thermal limits open.'],['1206 X7R input/output caps','TDK 10 uF/25 V; Murata 22 uF/10 V. Effective bias/temperature/aging curves not approved.'],['FFC / cable / M-key','Legacy TE FFC on hold; Molex candidate not drop-in. TE 1-2199230-4 M-key needs part-specific mating approval.'],['Support and assembly','Wurth 9774025243R 2.5 mm SMT support; slot datum 2.48 mm REF. Via-in-pad, screw and tolerances open.']],674,[154,386])
img(O/'mechanical-plan.png',74,197,464,257)
y=para('80 x 78 x 1.6 mm carrier. 2242 SSD envelope 22 x 42 mm; x54..76/y48.25..90.25. Expanded 0.35 mm planar envelope passes with 7.4 mm edge margin. Four 2.7 mm board mounts: (24,24), (96,24), (24,94), (96,94) mm. Not a Pi HAT+ pattern.',183)
y=para('Card support datum (65,90.25) mm. Reserved card height 6.5 mm; header separately about 8.4 mm. Actual SSD bottom components, insertion seating, mating-height stack, screw engagement and enclosure remain open. 92 plated / 7 unplated drill holes.',y)
para('Additional gates: SUSCLK DNP compatibility, missing-supply/IO sequencing, hot-plug/reverse protection, cable current/orientation, hot inductor/current-limit behavior, solder process and independent electrical/CAM/DFM review.',y,st=small)
c.showPage()
title(5,'Impedance and remaining gates','Original broad process bounds retained / no claim of full-channel compliance')
y=para('Nominal Zdiff 93.9369 ohm: width 0.14 mm, gap 0.152 mm, h0.0994 mm, Er4.1, copper35 um and assumed10 um mask. Fine mesh/domain/energy/scaling checks pass. High-speed geometry and stack are unchanged.',674)
y=table([['Case','Zdiff ohm','Lower margin','Upper margin']]+[[z['case'],f"{z['Zdiff_ohm']:.4f}",f"{z['lower_margin_ohm']:+.4f}",f"{z['upper_margin_ohm']:+.4f}"] for z in after['impedance']],y,[174,122,122,122])
y=para('High-Z corner: width0.125/gap0.167/h0.10934 mm, Er3.9. Narrow traces, larger plane distance and lower Er raise Z. Wide fanout gap0.36 mm also exceeds99 ohm locally. Local cross-sections are not complete channel eye or reflection results.',y)
y=table([['Candidate width mm','Low Z ohm','High Z ohm','Both pass']]+[[f"{x['nominal_width_mm']:.2f}",f"{x['process_low_Z_ohm']:.3f}",f"{x['process_high_Z_ohm']:.3f}",'NO'] for x in width['candidates']],y,[174,122,122,122])
y=para('Eight new solves retained etch +/-15 um, h +/-10%, Er +/-0.2 and fixed mask. No accepted width-only fix; finite search is not proof over all possible geometries. Earlier tighter-process sensitivity is not used to change this result.',y)
y=para('Actual filled-plane projection passes: no unintended voids beyond own-via exemptions; TX return vias within0.891 mm vs1 mm geometric target. Original planar lengths/skew preserved. Cable, connectors,3D vias, loss, crosstalk, eye/TDR and compliance remain unmodeled.',y)
para('Release requires valid voltage/thermal budgets, stack/channel redesign or justified original-corner closure, qualified parts/cable/SSD mechanics and assembly review. Full sources, commands and signed margins: ENGINEERING_REVIEW.md and outputs/engineering/*.json. Whole-system status: docs/SYSTEM_AUDIT.md.',y,st=small)
c.save();print('Wrote output/pdf/PCB_Engineering_Review.pdf (5 pages)')
