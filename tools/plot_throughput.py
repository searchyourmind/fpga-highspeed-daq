"""Plot the DMA throughput baseline from results/benchmark_csv/dma_throughput.json."""
from pathlib import Path
import json
import matplotlib.pyplot as plt
root=Path(__file__).resolve().parents[1]
rows=json.loads((root/'results/benchmark_csv/dma_throughput.json').read_text())
out=root/'results/charts'; out.mkdir(parents=True,exist_ok=True)

SURFACE,INK,INK2,MUTED,GRID,AXIS='#fcfcfb','#0b0b0b','#52514e','#898781','#e1e0d9','#c3c2b7'
WRITE,READ='#2a78d6','#eb6834'  # categorical slots 1 and 2, validated for CVD separation

lat=[r['memory_latency'] for r in rows]
series=[('DMA write',WRITE,[r['write_words_per_cycle'] for r in rows]),
        ('DMA read',READ,[r['read_words_per_cycle'] for r in rows])]

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10})
fig,ax=plt.subplots(figsize=(8,4.5),dpi=180,facecolor=SURFACE)
ax.set_facecolor(SURFACE)
ax.axhline(1.0,color=MUTED,lw=1.2,ls=(0,(4,3)),zorder=1)
ax.text(lat[0],1.03,'Pipelined target: 1 word per cycle',color=INK2,fontsize=9,va='bottom')
# Direct labels sit at latency 2, where the lines are still apart; they meet near 0.03.
for (label,color,values),dy,va in zip(series,(10,-12),('bottom','top')):
    ax.plot(lat,values,color=color,lw=2,marker='o',ms=6,mec=SURFACE,mew=2,label=label,zorder=3)
    ax.annotate(label,(lat[1],values[1]),xytext=(4,dy),textcoords='offset points',
                ha='left',va=va,color=INK,fontsize=9)
write_first,write_last=series[0][2][0],series[0][2][-1]
ax.annotate(f'{write_first:.2f}',(lat[0],write_first),xytext=(0,9),textcoords='offset points',
            ha='center',color=INK2,fontsize=9)
ax.annotate(f'{write_last:.2f}',(lat[-1],write_last),xytext=(0,9),textcoords='offset points',
            ha='center',color=INK2,fontsize=9)
ax.set_xscale('log',base=2); ax.set_xticks(lat,[str(x) for x in lat])
ax.set_xlim(lat[0]/1.25,lat[-1]*1.25); ax.set_ylim(0,1.15)
ax.set_xlabel('Memory latency (clock cycles)',color=INK2)
ax.set_ylabel('Words per cycle',color=INK2)
ax.grid(axis='y',color=GRID,lw=0.8); ax.set_axisbelow(True)
for side in ('top','right','left'): ax.spines[side].set_visible(False)
ax.spines['bottom'].set_color(AXIS)
ax.tick_params(colors=MUTED,length=0,pad=6)
ax.legend(loc='upper right',bbox_to_anchor=(1,0.9),frameon=False,labelcolor=INK2,fontsize=9)
ax.text(0,1.17,'Baseline DMA keeps one memory command in flight',transform=ax.transAxes,
        color=INK,fontsize=13,fontweight='bold')
ax.text(0,1.10,'Simulated RTL; the memory model accepts up to 64 commands and the link never stalls',
        transform=ax.transAxes,color=INK2,fontsize=9)
fig.tight_layout(); fig.subplots_adjust(top=0.82)
fig.savefig(out/'dma-throughput-baseline.png',facecolor=SURFACE)
print('Plotted',len(rows),'latencies')
