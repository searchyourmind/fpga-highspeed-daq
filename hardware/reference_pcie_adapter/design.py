"""Pin-accurate electrical source of truth; separate Pi 5 reference design."""
from dataclasses import dataclass
@dataclass
class Part:
    ref:str; value:str; footprint:str; pins:dict; xy:tuple; sch:tuple; role:str='passive'; note:str=''
P=[]
def add(ref,value,fp,pins,xy,sch,role='passive',note=''):
    P.append(Part(ref,value,fp,{str(k):v for k,v in pins.items()},xy,sch,role,note))
ffc={1:'PI_5V',2:'PI_5V',3:'GND',4:'CLK_P',5:'CLK_N',6:'GND',7:'RX_P',8:'RX_N',9:'GND',10:'TX_P',11:'TX_N',12:'GND',13:'PWR_EN',14:'DET_WAKE',15:'CLKREQ_PI',16:'RESET_PI','MP':'GND'}
add('J1','TE 1-1734839-6 (top contact)','Connector_FFC-FPC:TE_1-1734839-6_1x16-1MP_P0.5mm_Horizontal',ffc,(62,27,180),(45,68),'connector','Superseded part; replacement qualification required')
m2={i:None for i in range(1,76) if i not in range(59,67)}
for n in (1,3,9,15,21,27,33,39,45,51,57,69,71,73,75):m2[n]='GND'
for n in (2,4,12,14,16,18,70,72,74):m2[n]='SSD_3V3'
m2.update({41:'RX_N',43:'RX_P',47:'TX_N',49:'TX_P',53:'CLK_N',55:'CLK_P',50:'RESET_SSD',52:'CLKREQ_SSD',54:'PEWAKE',68:'SUSCLK',76:'GND',77:'GND'})
add('J2','TE 1-2199230-4 M-key','DAQ:TE_M2_M_1-2199230-4',m2,(65,50,0),(145,108),'connector','Custom footprint from TE G-2199230 B3 sheet 3; review before release')
add('J3','External regulated 5V / 3A','Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical',{1:'EXT_5V',2:'GND'},(23,57,0),(265,35),'source','No reverse-polarity or hot-plug protection: external current-limited source only')
add('U1','TPS62130ARGTR','Package_DFN_QFN:VQFN-16-1EP_3x3mm_P0.5mm_EP1.6x1.6mm',{1:'SW',2:'SW',3:'SW',4:'PG',5:'FB',6:'GND',7:'GND',8:'GND',9:'SS',10:'EXT_5V',11:'EXT_5V',12:'EXT_5V',13:'PWR_EN',14:'SSD_3V3',15:'GND',16:'GND',17:'GND'},(35,54,0),(275,85),'regulator','3.328V nominal; <=2A SSD; 8 thermal vias; assembly review pending')
add('U2','NC7SB3157P6X','Package_TO_SOT_SMD:SOT-363_SC-70-6',{1:'CLKREQ_PI',2:'GND',3:'GND',4:'CLKREQ_SSD',5:'EXT_5V',6:'PG'},(85,46,0),(275,145),'switch','S=0 grounds SSD CLKREQ; S=1 connects host')
for ref,nets,xy,sch in [('Q1',{1:'PG',2:'RESET_SSD',3:'RESET_R'},(84,53,0),(360,50)),('Q2',{1:'PEWAKE',2:'GND',3:'WAKE_INV'},(87,65,0),(360,90)),('Q3',{1:'WAKE_INV',2:'GND',3:'DET_WAKE'},(92,65,0),(360,125))]:
    add(ref,'DMG1012T-7','Package_TO_SOT_SMD:SOT-523',nets,xy,sch,'mosfet')
# Oscillator is deliberately a sourced interface, not an invented vendor footprint.
add('J4','Optional 32.768kHz input','Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical',{1:'SSD_3V3',2:'OSC_IN',3:'GND'},(90,76,0),(360,165),'connector','External oscillator footprint/part not selected; SSD-dependent requirement remains open')
add('H5','Wurth 9774025243R / M2 / H2.5mm','Mounting_Wuerth:Mounting_Wuerth_WA-SMSI-M2_H2.5mm_9774025243',{1:'GND'},(65,90.25,0),(465,165),'passive','SMT support; height and insertion datum require mating-card confirmation')
passives=[
('L1','2.2uH XAL4020-222MEC','Inductor_SMD:L_Coilcraft_XAL4020-XXX','SW','SSD_3V3',(29,53,90)),
('C1','10uF 25V X7R','Capacitor_SMD:C_1206_3216Metric','EXT_5V','GND',(41,53,90)),
('C2','10uF 25V X7R','Capacitor_SMD:C_1206_3216Metric','EXT_5V','GND',(44,53,90)),
('C3','22uF 10V X7R','Capacitor_SMD:C_1206_3216Metric','SSD_3V3','GND',(28,59,0)),
('C4','22uF 10V X7R','Capacitor_SMD:C_1206_3216Metric','SSD_3V3','GND',(28,62,0)),
('C5','100nF','Capacitor_SMD:C_0402_1005Metric','EXT_5V','GND',(40,50,0)),
('C6','3.3nF soft start','Capacitor_SMD:C_0402_1005Metric','SS','GND',(40,57,90)),
('C7','100nF','Capacitor_SMD:C_0402_1005Metric','EXT_5V','GND',(88,45,90)),
('C8','100nF','Capacitor_SMD:C_0402_1005Metric','SSD_3V3','GND',(90,72,0)),
('R1','31.6k 0.1% 25ppm','Resistor_SMD:R_0402_1005Metric','SSD_3V3','FB',(34,60,90)),
('R2','10k 0.1% 25ppm','Resistor_SMD:R_0402_1005Metric','FB','GND',(37,60,90)),
('R3','100k','Resistor_SMD:R_0402_1005Metric','PWR_EN','GND',(40,46,0)),
('R4','10k','Resistor_SMD:R_0402_1005Metric','EXT_5V','PG',(81,45,90)),
('R5','3.6k 1%','Resistor_SMD:R_0402_1005Metric','PI_5V','DET_WAKE',(73,29,90)),
('R6','6.8k 1%','Resistor_SMD:R_0402_1005Metric','DET_WAKE','GND',(76,29,90)),
('R7','33R','Resistor_SMD:R_0402_1005Metric','RESET_PI','RESET_R',(81,53,0)),
('R8','2.2k','Resistor_SMD:R_0402_1005Metric','RESET_SSD','GND',(87,53,90)),
('R9','10k','Resistor_SMD:R_0402_1005Metric','SSD_3V3','PEWAKE',(84,62,0)),
('R10','10k','Resistor_SMD:R_0402_1005Metric','SSD_3V3','WAKE_INV',(92,62,0)),
('R11','33R','Resistor_SMD:R_0402_1005Metric','OSC_IN','SUSCLK',(86,75,0)),
]
for i,(ref,val,fp,a,b,xy) in enumerate(passives):
    add(ref,val,fp,{1:a,2:b},xy,(45+(i%6)*85,245+(i//6)*32))
# Explicit simulation-independent port electrical types; passive pins for connectors,
# source power flag only where an external supply actually exists.
def ptype(part,pin):
    pin=str(pin)
    if part.role=='source':return 'power_out'
    if part.role=='regulator':
        if pin in ('6','10','11','12','15','16','17'):return 'power_in'
        if pin=='1':return 'power_out'
        if pin in ('2','3'):return 'passive'
        if pin=='4':return 'open_collector'
        return 'input'
    if part.role=='switch':return 'power_in' if pin in ('2','5') else ('input' if pin=='6' else 'passive')
    return 'passive'
