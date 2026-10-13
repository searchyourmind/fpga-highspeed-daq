from pathlib import Path
import json
import matplotlib.pyplot as plt
root=Path(__file__).resolve().parents[1]
(root/'results/charts').mkdir(parents=True,exist_ok=True)
rows=json.loads((root/'results/benchmark_csv/e2e.json').read_text())
assert rows and all(r['status']=='MATCH' for r in rows)
fig,axs=plt.subplots(1,2,figsize=(11,4),layout='constrained')
for seed in sorted({r['seed'] for r in rows}):
    data=[r for r in rows if r['seed']==seed]
    labels=[f"{r['records']} rec / L{r['memory_latency']}" for r in data]
    axs[0].plot(labels,[r['records_per_cycle'] for r in data],'o-',label=f'Seed {seed}')
    axs[1].plot(labels,[r['final_host_cycles'] for r in data],'o-',label=f'Seed {seed}')
axs[0].set_ylabel('Records per simulated cycle'); axs[1].set_ylabel('Final host delivery (cycles)')
for ax in axs: ax.grid(alpha=.2); ax.tick_params(axis='x',rotation=25)
axs[0].legend();fig.suptitle('Actual RTL simulation with modeled memory/link stalls — not physical bandwidth')
fig.savefig(root/'results/charts/simulation-performance.png',dpi=180)
print('Plotted',len(rows),'executed simulation configurations')
