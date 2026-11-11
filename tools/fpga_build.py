"""Lattice ECP5 build of the ULX3S board top: Yosys -> nextpnr (several seeds) -> ecppack.

Runs in the fpga-daq-fpga image (make fpga-tools; make fpga). Writes ignored
results/fpga/; the summary is copied into evidence/fpga/ by hand when recorded.
"""
import argparse, json, re, statistics, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/fpga'
DEVICE=dict(family='ECP5',part='LFE5U-25F-6BG381C',board='ULX3S (25F)',args=['--25k','--package','CABGA381','--speed','6'])
CELLS=['LUT4','TRELLIS_FF','CCU2C','PFUMX','L6MUX21','TRELLIS_DPR16X4','DP16KD','MULT18X18D']

def sh(cmd,log):
    with open(log,'w') as f: subprocess.run(cmd,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True)

def sources():
    return ' '.join(str(p.relative_to(ROOT)) for p in sorted((ROOT/'rtl').glob('*.sv'))+sorted((ROOT/'fpga/rtl').glob('*.sv')))

def synthesize():
    read=f'read_verilog -sv -DSYNTHESIS {sources()}'
    sh(['yosys','-p',f'{read}; synth_ecp5 -top fpga_top -json {OUT}/fpga_top.json; check -assert; tee -q -o {OUT}/stat.json stat -json'],OUT/'yosys.log')
    # Separate unflattened run, only for the per-module breakdown.
    sh(['yosys','-p',f'{read}; synth_ecp5 -top fpga_top -noflatten; tee -q -o {OUT}/stat_hier.json stat -json'],OUT/'yosys_hier.log')
    total=json.loads((OUT/'stat.json').read_text())['design']['num_cells_by_type']
    modules={}
    for name,mod in json.loads((OUT/'stat_hier.json').read_text())['modules'].items():
        # Parameterized copies are named $paramod\<module>\<params>.
        base=name.split('\\')[1] if name.startswith('$paramod') else name.lstrip('\\')
        counts={c:mod['num_cells_by_type'].get(c,0) for c in CELLS}
        assert base not in modules,f'two synthesized copies of {base}'
        if any(counts.values()): modules[base]=counts
    return {c:total.get(c,0) for c in CELLS},modules

def place_and_route(seed,freq):
    report=OUT/f'report_seed{seed}.json'
    sh(['nextpnr-ecp5',*DEVICE['args'],'--json',str(OUT/'fpga_top.json'),'--lpf','fpga/ulx3s.lpf',
        '--freq',str(freq),'--seed',str(seed),'--timing-allow-fail','--report',str(report),
        '--textcfg',str(OUT/f'fpga_top_seed{seed}.config')],OUT/f'pnr_seed{seed}.log')
    r=json.loads(report.read_text())
    fmax=next(iter(r['fmax'].values()))['achieved']
    path=r['critical_paths'][0]['path']
    # nextpnr lists the launching register as the 'to' end of the clk-to-q step.
    logic_cells=[step['to']['cell'] for step in path if step['type']=='logic']
    logic=sum(s['delay'] for s in path if s['type']!='routing')
    routing=sum(s['delay'] for s in path if s['type']=='routing')
    return dict(seed=seed,fmax_mhz=round(fmax,2),utilization={k:v for k,v in r['utilization'].items() if v['used']},
                critical_path=dict(start=path[0]['to']['cell'],end=path[-1]['to']['cell'],logic_ns=round(logic,2),routing_ns=round(routing,2),
                                   multipliers_in_series=len({c for c in logic_cells if 'MULT18X18D' in c})))

def versions():
    out=lambda cmd: subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True).stdout.strip().splitlines()[0]
    return dict(yosys=out(['yosys','-V']),nextpnr=out(['nextpnr-ecp5','--version']).replace('"',''))

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--seeds',type=int,default=5); p.add_argument('--freq',type=float,default=100)
    a=p.parse_args(); OUT.mkdir(parents=True,exist_ok=True)
    cells,modules=synthesize()
    runs=[place_and_route(seed,a.freq) for seed in range(1,a.seeds+1)]
    fmax=[r['fmax_mhz'] for r in runs]
    median=sorted(runs,key=lambda r:r['fmax_mhz'])[len(runs)//2]
    sh(['ecppack','--compress',str(OUT/f"fpga_top_seed{median['seed']}.config"),str(OUT/'fpga_top.bit')],OUT/'ecppack.log')
    summary=dict(scope='Place-and-route timing of the ULX3S board top on ECP5; not measured on hardware',
        device={k:v for k,v in DEVICE.items() if k!='args'},tools=versions(),target_mhz=a.freq,
        board_clock_mhz=25,fmax_mhz=dict(min=min(fmax),median=statistics.median(fmax),max=max(fmax),per_seed=fmax),
        meets_board_clock=min(fmax)>=25,synthesis_cells=cells,cells_by_module=modules,
        median_run=median,bitstream=dict(path='results/fpga/fpga_top.bit',seed=median['seed'],bytes=(OUT/'fpga_top.bit').stat().st_size))
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    u=median['utilization']
    print(f"FPGA_BUILD_PASS {DEVICE['part']}: Fmax min/median/max {min(fmax):.1f}/{statistics.median(fmax):.1f}/{max(fmax):.1f} MHz "
          f"over {len(runs)} seeds (target {a.freq:g}); LUT4 {cells['LUT4']} FF {cells['TRELLIS_FF']} "
          f"DP16KD {u.get('DP16KD',{}).get('used',0)} MULT18X18D {u.get('MULT18X18D',{}).get('used',0)}")
