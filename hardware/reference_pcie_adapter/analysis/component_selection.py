"""Engineering BOM selections, with explicit lifecycle/qualification limits."""
from pathlib import Path
import csv,json,sys
H=Path(__file__).resolve().parents[1];sys.path.insert(0,str(H));from design import P
TI='https://www.ti.com/lit/ds/symlink/tps62130.pdf'
parts={}
def add(refs,mfr,mpn,url,status,note):
 for ref in refs.split():parts[ref]={'manufacturer':mfr,'mpn':mpn,'source':url,'selection_status':status,'qualification_note':note}
add('U1','Texas Instruments','TPS62130ARGTR',TI,'SELECTED','A variant required; 3A regulator, 125C recommended junction max. Actual TI A transient model included via fetch script.')
add('L1','Coilcraft','XAL4020-222MEC','https://www.coilcraft.com/getmedia/6adcb47d-8b55-416c-976e-1e22e0d2848c/xal4000.pdf','SELECTED_CONDITIONAL','2.2uH +/-20%; DCR max38.7mOhm at25C; Isat typ5.6A at30% drop; Irms4A for20C rise. Fault/hot-bias qualification remains required; values are not guaranteed hot saturation limits.')
add('C1 C2','TDK','C3216X7R1E106K160AB','https://product.tdk.com/en/search/capacitor/ceramic/mlcc/info?part_no=C3216X7R1E106K160AB','SELECTED_CONDITIONAL','10uF +/-10%,25V,X7R,1206. Analysis requires >=6uF each under bias/temp/aging; 12uF total used in SPICE. Vendor DC-bias curve export unavailable; this is an acceptance requirement, not measured data.')
add('C3 C4','Murata','GRM31CR71A226KE15L','https://search.murata.co.jp/Ceramy/image/img/A01X/G101/ENG/GRM31CR71A226KE15-01CA.pdf','SELECTED_CONDITIONAL','22uF +/-10%,10V,X7R,1206. 16..52.8uF total effective screening; vendor DC-bias acceptance remains open. TI LC table considers +20/-50% around nominal; no claim that nominal equals effective.')
add('C5 C7 C8','Murata','GRM155R71C104KA88D','https://www.murata.com/en-global/api/pdfdownloadapi?cate=luCeramicCapacitorsSMD&partno=GRM155R71C104KA88%23','SELECTED','100nF,+/-10%,16V,X7R,0402; local bypass.')
add('C6','Murata','GRM155R71H332KA01D','https://www.ti.com/lit/ug/snvu180a/snvu180a.pdf','SELECTED_CONDITIONAL','3.3nF,+/-10%,50V,X7R,0402; MPN confirmed in TI evaluation-board BOM. Allow tolerance/temp/aging in soft-start estimate; lifecycle confirmation remains required.')
for ref,code in [('R1','31K6'),('R2','10K0')]:add(ref,'Vishay',f'TNPW0402{code}BEED','https://www.vishay.com/docs/28758/tnpw.pdf','SELECTED','0.1%,25ppm/K,0402. Feedback ratio3.16 compensates trace drop; divider impedance reduced approximately10x to reduce worst-case FB leakage error.')
for ref,code in [('R3','100K'),('R4','10K'),('R5','3K6'),('R6','6K8'),('R7','33R'),('R8','2K2'),('R9','10K'),('R10','10K'),('R11','33R')]:
 add(ref,'Yageo',f'RC0402FR-07{code}L','https://www.yageo.com/upload/media/product/productsearch/datasheet/rchip/PYu-RC_Group_51_RoHS_L_12.pdf','SELECTED','1%,0402,1/16W minimum. Check full resistance code and current manufacturer approval sheet before purchase; no ordering performed.')
add('U2','onsemi','NC7SB3157P6X','https://www.onsemi.com/pdf/datasheet/nc7sb3157-d.pdf','SELECTED','5V-powered analog switch; missing external supply requires complete sequence/IO review.')
add('Q1 Q2 Q3','Diodes Inc.','DMG1012T-7','https://www.diodes.com/datasheet/download/DMG1012T.pdf','SELECTED','20V N-MOSFET,SOT523; same topology as official Pi reference. Not a complete missing-supply qualification.')
add('J1','TE Connectivity','1-1734839-6','https://www.te.com/en/product-1-1734839-6.html','LEGACY_HOLD','Existing exact top-contact16pin0.5mm footprint retained. Manufacturer marks superseded. Molex5034801600 is an alternate candidate only, NOT drop-in; cable orientation and pad mapping require redesign/review.')
add('J2','TE Connectivity','1-2199230-4','https://www.te.com/en/product-1-2199230-4.html','SELECTED_CONDITIONAL','M-key,4.2mm body height. Available TE RevB3 drawing inspected; slot lower datum2.48mm REF. Current part-specific approval and mating card remain gates.')
add('J3','Samtec','TSW-102-07-G-S','https://www.samtec.com/products/tsw-102-07-g-s','SELECTED_CONDITIONAL','2.54mm2pin0.635mm square post; actual cable/receptacle must be >=3A rated. Unkeyed, current-limited regulated5V only; not hot-plug/reverse protected.')
add('J4','Samtec','TSW-103-07-G-S','https://www.samtec.com/products/tsw-103-07-g-s','DNP_DEFAULT','Optional external3.3V CMOS32.768kHz input. Baseline restricts SSD to one not requiring host SUSCLK; no oscillator is fitted or claimed.')
add('H5','Wurth Elektronik','9774025243R','https://www.we-online.com/components/products/datasheet/9774025243R.pdf','SELECTED_CONDITIONAL','M2 internal-thread SMT spacer,2.5mm height; actual KiCad library footprint. TE lower slot datum2.48mm REF implies nominal+0.02mm. Final height tolerance/SSD approval still required.')
assert set(parts)=={p.ref for p in P}
rows=[dict(reference=p.ref,value=p.value,footprint=p.footprint,**parts[p.ref]) for p in P]
with (H/'BOM_selected.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
(H/'outputs/engineering/component-selection.json').write_text(json.dumps({'revision':'0.3','purchasing_authorized':False,'components':rows,'gate':'CONDITIONAL_ENGINEERING_BOM_NOT_PURCHASE_RELEASE'},indent=2)+'\n')
print(f'{len(rows)} electrical references mapped to candidate/selected manufacturer parts; no purchase release')
