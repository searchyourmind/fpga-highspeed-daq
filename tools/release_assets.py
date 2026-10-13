"""Create portable diagrams, actual-waveform excerpts and benchmark figures."""
from pathlib import Path
import json,gzip,hashlib,shutil,xml.etree.ElementTree as ET
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
R=Path(__file__).resolve().parents[1];O=R/'portfolio/assets';O.mkdir(parents=True,exist_ok=True)
plt.rcParams.update({'font.size':10,'svg.fonttype':'none'})
def save(fig,name):
 for suffix in ('svg','png'):fig.savefig(O/f'{name}.{suffix}',dpi=165,bbox_inches='tight')
 plt.close(fig)
fig,ax=plt.subplots(figsize=(12,5.5));ax.set(xlim=(0,12),ylim=(0,5.7));ax.axis('off')
nodes=[('Synthetic source\nsensor_source',.2,4),('Gain + saturation\nstream_processor',3.1,4),('Ready/valid FIFO\nstream_fifo',6,4),('Capture writer\nstream_to_mem\n+ dma_writer',8.9,4),('Host scoreboard\nPython + golden data',.2,1.3),('PCIe transaction model\nCustom delay / CRC',3.1,1.3),('DMA reader\n+ tlp_packetizer',6,1.3),('DDR3 behavioral model\nPython transactions',8.9,1.3)]
for label,x,y in nodes:
 py=label.startswith(('Host','PCIe','DDR3'))
 ax.add_patch(FancyBboxPatch((x,y),2.55,1.05,boxstyle='round,pad=0.04',facecolor='#e1f1ed' if py else '#e3eaf4',edgecolor='#28425a'))
 ax.text(x+1.275,y+.525,label,ha='center',va='center',fontsize=10)
for a,b in [(0,1),(1,2),(2,3),(7,6),(6,5),(5,4)]:
 _,x,y=nodes[a];_,xx,yy=nodes[b];d=1 if xx>x else -1
 ax.annotate('',xy=(xx if d>0 else xx+2.55,yy+.525),xytext=(x+2.55 if d>0 else x,y+.525),arrowprops={'arrowstyle':'->','lw':1.8})
ax.annotate('',xy=(10.175,2.35),xytext=(10.175,4),arrowprops={'arrowstyle':'->','lw':1.8})
ax.text(10.3,3.2,'write first,\nthen read',fontsize=9,va='center')
ax.text(.2,3.12,'Descriptor control: dma_descriptor / daq_top | one active job | synchronous active-low reset',fontsize=11)
ax.text(.2,.43,'Blue: synthesizable SystemVerilog. Green: simulation-only Python.\nNo DDR PHY, real PCIe endpoint, device timing or concurrent continuous capture.',fontsize=10)
ax.set_title('Verified DAQ simulation architecture',loc='left',fontsize=17,fontweight='bold');save(fig,'architecture')
rows=json.loads((R/'results/benchmark_csv/e2e.json').read_text());ext=[x for p in sorted((R/'results/system-audit').glob('extended-ring-*.json')) for x in json.loads(p.read_text())]
assert len(rows)==15 and len(ext)==18 and all(x['status']=='MATCH' for x in rows+ext)
fig,axs=plt.subplots(1,2,figsize=(12,4.4),layout='constrained')
for seed in sorted({x['seed'] for x in rows}):
 data=[x for x in rows if x['seed']==seed];axs[0].plot(range(1,len(data)+1),[x['records_per_cycle'] for x in data],'o-',label=f'Seed {seed}')
axs[0].set(xlabel='Scenario configuration (size, latency and stalls vary)',ylabel='Records / simulated cycle',title='15 baseline scenarios');axs[0].legend(fontsize=9);axs[0].grid(alpha=.2)
for ring in (32,257):
 data=[x for x in ext if x['ring_words']==ring];axs[1].scatter(range(1,len(data)+1),[x['cycles'] for x in data],label=f'Ring {ring}')
axs[1].set(xlabel='Extended matrix entry',ylabel='Job completion cycles',title='18 extended scenarios');axs[1].legend();axs[1].grid(alpha=.2)
fig.suptitle('Executed RTL + behavioral models — no physical throughput claim');save(fig,'benchmarks')
# Parse only top-level scalar VCD changes; never synthesize a waveform from expectations.
vcd=R/'tb/dump.vcd';assert vcd.exists(),'Run WAVES=1 make e2e first'
names=['desc_valid','desc_ready','mem_cmd_valid','mem_cmd_write','mem_cmd_ready','mem_rsp_valid','link_valid','link_ready','link_sop','link_eop','comp_valid']
codes={};events={s:[] for s in names};scopes=[];time=0;header=True
for ln in vcd.open():
 t=ln.split()
 if not t:continue
 if header:
  if t[0]=='$scope':scopes.append(t[2])
  elif t[0]=='$upscope':scopes.pop()
  elif t[0]=='$var' and scopes==['$rootio'] and t[4] in names:codes[t[3]]=t[4]
  elif t[0]=='$enddefinitions':header=False
  continue
 if ln.startswith('#'):time=int(ln[1:])
 elif ln[0] in '01xz' and ln[1:].strip() in codes:
  name=codes[ln[1:].strip()];events[name].append((time/1000,0 if ln[0] in '0xz' else 1))
assert len(codes)==len(names)
# A later baseline transaction contains write/read/stall activity; use actual 1600ns window.
start=360.;end=1960.
fig,axs=plt.subplots(len(names),1,figsize=(12,7),sharex=True,layout='constrained')
for ax,name in zip(axs,names):
 ev=events[name];prior=[v for t,v in ev if t<=start];points=[(start,prior[-1] if prior else 0)]+[(t,v) for t,v in ev if start<t<end];points.append((end,points[-1][1]));ax.step([p[0] for p in points],[p[1] for p in points],where='post',color='#146a79');ax.set(ylim=(-.2,1.2),yticks=[0,1]);ax.set_ylabel(name,rotation=0,ha='right',va='center',fontsize=9);ax.grid(axis='x',alpha=.15)
axs[-1].set(xlabel='Simulation time (ns); testbench clock units, not timing closure',xlim=(start,end));fig.suptitle('Verilator waveform excerpt from the six-test E2E rerun');save(fig,'waveform')
W=R/'results/waveforms';W.mkdir(parents=True,exist_ok=True)
with gzip.GzipFile(filename=str(W/'daq_top.vcd.gz'),mode='wb',mtime=0) as z:z.write(vcd.read_bytes())
meta={'waveform_source':'tb/dump.vcd','raw_sha256':hashlib.sha256(vcd.read_bytes()).hexdigest(),'test_command':'WAVES=1 ./tools/run python tools/rtl_tests.py e2e','timescale':'1ps','excerpt_ns':[start,end],'samples':'Actual VCD transitions; no interpolated measurement or hardware claim','benchmark_sources':['results/benchmark_csv/e2e.json','results/system-audit/extended-ring-32.json','results/system-audit/extended-ring-257.json'],'source_sha256':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((R/'rtl').glob('*.sv'))}}
(O/'evidence.json').write_text(json.dumps(meta,indent=2)+'\n');print('Architecture, 33-scenario benchmark and real VCD excerpt generated')
