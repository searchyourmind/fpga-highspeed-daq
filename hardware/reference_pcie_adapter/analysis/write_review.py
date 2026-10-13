"""Compose the corrective review directly from executed corner evidence."""
from pathlib import Path
import json
H=Path(__file__).resolve().parents[1];O=H/'outputs/engineering';read=lambda s:json.loads((O/(s+'.json')).read_text())
p=H/'ENGINEERING_REVIEW.md';references=(H/'analysis/PRIMARY_REFERENCES.md').read_text()
f=read('failure-margins');before=f['baseline_rev03'];after=f['corrected_copper_rev03_1'];b=read('power-corners')['budget'];tr=read('adapter-loaded-corner');therm=read('thermal');vf=read('voltage-feasibility');sw=read('si-width-feasibility');sink=read('thermal-exit-requirement')
s='''# Rev 0.3 corrective review - Rev 0.3.1, 2026-10-12

**DESIGN REVIEW DRAFT. NOT RELEASED FOR PURCHASE OR MANUFACTURE.**
The review and software checks are complete for this checkpoint; voltage, thermal and SI acceptance remain OPEN/FAIL. The Pi5 carrier is separate from the FPGA DAQ simulation. No hardware was purchased, fabricated, powered or tested.

## Requirements and disposition

Requirements were not relaxed: SSD supply3.135-3.465V, regulator Tj<=125C, differential cross-section81-99ohm, original ambient25/40/60C and h5/10W/m2K per side, original broad SI process corners. Failed or borderline cases remain visible. `results/review-r03-baseline/` preserves the original evidence; `outputs/engineering/failure-margins.json` and both `thermal-all-cases-*.csv` enumerate every before/after case with signed margins.

## Implemented corrections

- Five long SSD_3V3 sections widened from1.2 to3.0mm. The short J2 feed retains1.2mm to avoid PEWAKE. The main supply feeder atx26.5 widens from1.0 to1.3mm. No divider, target voltage, cap value or semiconductor model was changed.
- Expanded the actual outer GND polygons into the power/SSD region while preserving both inner reference planes and the original high-speed pair centerlines. This improves spreading, but does not create an unmodeled heatsink.
- Wider trial tracks that shorted PEWAKE/SW were rejected by actual DRC and corrected. Logs `pcb-r04-first.log` and `pcb-r04-feeder.log` are failure history, not accepted layouts.
- Native revision0.3.1 rebuild and final draft export pass: ERC0, DRC0, unconnected0, schematic parity0, pin contracts and pair preservationPASS.424 tracks/vias,183 pads,4 filled GND zones,92PTH/7NPTH. See `results/simulation_logs/pcb-r031-*.log`.

## Exact voltage failures and root causes

Margins are actual-minus-minimum for lower bounds, maximum-minus-actual for upper bounds.

| Composite case | Before (V) | Before margin (mV) | Corrected (V) | Corrected margin (mV) | Result |
|---|---:|---:|---:|---:|---|
'''
for a,z in zip(before['voltage'],after['voltage']):s+=f"| {z['case']} | {a['actual_V']:.6f} | {a['margin_mV']:+.3f} | {z['actual_V']:.6f} | {z['margin_mV']:+.3f} | FAIL |\n"
s+='''
Lower root cause: minimum FB reference and divider/leakage error plus output copper, ground, connector and dynamic drops. Upper root cause: PSM high FB reference plus divider/leakage and positive dynamic allowance. These are conservative independent extrema, not a simulated claim that all occur simultaneously.

Same budgets: PWM FB minimum0.7856V, PSM maximum0.8224V;100nA FB leakage;0.1% resistors plus25ppm/K over100K;10mV GND,25mV contact,40mV transient/ripple,5mV line/load. The40mV reserve was retained despite the new trace being smaller; two traces do not justify shrinking the full process/temperature budget.

Actual resistor-network extraction covers equal sharing and all126 combinations of four0.5A loads among nine power pads at125C,30um outer copper and20um via plating. Worst2A output drop improved59.397->37.161mV. Pads are ideal; ground/contact/cable drops are separate. KCL and independent analytic resistor fixtures pass. Thermal copper allowance stays0.25W and still covers the independently stressed input+output network. This is not IPC-2152 ampacity qualification.

'''
s+=f"Divider feasibility was solved algebraically with the same errors/reserves and10kohm bottom resistor: Rtop must be >=**{vf['lower_bound_required_Rtop_ohm']:.2f}ohm** for the lower bound and <=**{vf['upper_bound_allowed_Rtop_ohm']:.2f}ohm** for the upper bound. The feasible intervals do not overlap ({vf['overlap_ohm']:.2f}ohm gap). Divider-only retargeting is rejected, not presented as a fix.\n"
s+='''
### Executed power simulations

108 original CCM DC/AC cases rerun: Vin4.65/5/5.25V, load0.5/1/2A, Cout16/22/52.8uF, L1.232/2.64uH, ESR5/30mohm. All DC outputs within target and121 finite AC samples per case. This shared-core non-A average model cannot validate A PG, PFM, fault current or phase margin.

The retained official TPS62130A nominal trace has6,605,420 points over3.05ms and output3.292944-3.362127V at the regulator. A **new actual loaded external-component corner** also completed:4.65V input,1.232uH,75mohmDCR,16uF,10mohmESR,3.3nF soft start and18.580444mohm extracted output route.0.5A resistive base plus1.5A pulse, EN shutdown at2.8ms.

'''
s+=f"- {tr['raw_points']:,} solver points; load-event load voltage **{tr['windows']['load_step']['load']['min_V']:.6f}-{tr['windows']['load_step']['load']['max_V']:.6f}V**; target margins **+{tr['event_load_lower_margin_V']*1000:.3f}/+{tr['event_load_upper_margin_V']*1000:.3f}mV**.\n- Regulator excursion{tr['regulator_event_peak_excursion_V']*1000:.3f}mV leaves{tr['existing_40mV_reserve_margin_V']*1000:.3f}mV inside the existing40mV reserve. Compare regulator excursion here, avoiding double-counting the separately modeled DC board drop.\n- PeakIL{tr['overall_inductor_peak_A']:.6f}A; PG steady{tr['windows']['post_step']['PG_min_V']:.4f}V and shutdown{tr['windows']['disabled']['PG_max_V']:.4f}V. All trace checksPASS.\n"
s+='''
This is a room-temperature internal semiconductor model with stressed external components and an equivalent hot trace resistor. It is not a full semiconductor process/temperature sweep, measured efficiency, joint FB-error transient, input cable model, hot fault test or stability phase-margin result. Effective MLCC curves and actual SSD load remain unqualified. Existing inductor normal-peak screening2.251A and soft-start1.110-2.269ms are assumptions, not new measurements.

## Every original failing thermal case

Each row also includes fixed0.25W inductor and0.25W copper heat. Tj limit remains125C; margin=125-Tj. Case IDs index the24-row Cartesian product in `thermal.json`.

| ID | Ambient C | h each side W/m2K | Regulator W | SSD-to-board W | Before Tj C | Corrected Tj C | Corrected margin C | Disposition |
|---|---:|---:|---:|---:|---:|---:|---:|---|
'''
for a,z in zip(before['thermal_cases'],after['thermal_cases']):
 if a['result']=='FAIL' or z['result']=='FAIL':s+=f"| {z['case_id']} | {z['ambient_C']:.0f} | {z['h_each_side_W_m2K']:.0f} | {z['assumed_regulator_loss_W']:.1f} | {z['assumed_SSD_heat_into_carrier_W']:.2f} | {a['estimated_regulator_junction_C']:.3f} | {z['estimated_regulator_junction_C']:.3f} | {z['margin_C']:+.3f} | {z['result']} |\n"
s+=f"\n**5/24 still fail.** Case3's nominal+0.619C is too small to qualify hardware given model/process uncertainty; it is only a numerical screen pass. Current mesh0.5-to0.25mm change is{therm['mesh_last_delta_T_C']:.3f}C in the convergence case; energy residuals pass.\n"
s+='''
Root cause: local regulator dissipation plus SSD coupling and insufficient heat exit at hot ambient/weak convection. Expanded ground spreading lowers worst Tj by only1.397C, so more copper alone is insufficient. The2D model samples actual outer GND copper with50% conductance derating, two derated15.2um inner planes, FR4 k0.3W/mK and copper385W/mK; adds modeled solder/via path and4.5K/W bottom junction resistance. It does not substitute datasheet JEDEC thetaJA for the actual board. Predicted overheating is rejection evidence, not precision characterization outside valid material temperatures. No2A continuous rating is released.

### Quantified additional heat-path requirement

Four actual2D solves add a candidate10x10mm regulator-region contact while removing covered-side free convection; ambient60C, h5 and all losses/limits remain unchanged. R includes the total PCB/contact/interface/sink-to-ambient path, not just a catalog sink rating.

| Total candidate path K/W | Estimated Tj C | Margin C |
|---:|---:|---:|
'''
for x in sink['cases']:s+=f"| {x['candidate_sink_total_K_W']:.0f} | {x['estimated_regulator_junction_C']:.3f} | {x['margin_C']:+.3f} |\n"
s+=f"\nCoarse1mm-mesh bisection suggests R<={sink['coarse_required_total_Rth_at_most_K_W']:.2f}K/W just to meet125C. This is an **unimplemented candidate requirement**, not an accepted assembly or design pass. Even the15K/W case leaves modeled SSD-region board temperature103.49C, so IC cooling alone does not qualify the SSD. Actual SSD rating,3D interface, enclosure and coupling remain open.\n"
s+='''
## Exact impedance failures and attempted correction

Nominal93.9369ohm uses width0.14mm, gap0.152mm, dielectric0.0994mm, Er4.1,35um copper and assumed10um/Er3.3 conformal mask. Existing mesh/domain/energy/residual/uniform-dielectric checks pass; finest mesh480329 unknowns. Signal geometry and inner dielectric stack are unchanged by this correction.

| Case | Width/gap/h mm | Er | Zdiff ohm | Lower margin ohm | Upper margin ohm | Result |
|---|---|---:|---:|---:|---:|---|
'''
for z in after['impedance']:s+=f"| {z['case']} | {z['width_mm']:.5f}/{z['gap_mm']:.5f}/{z['dielectric_mm']:.5f} | {z['er']:.1f} | {z['Zdiff_ohm']:.5f} | {z['lower_margin_ohm']:+.5f} | {z['upper_margin_ohm']:+.5f} | {z['result']} |\n"
s+='''
Root cause: narrow etched traces, larger plane spacing, lower permittivity and increased local fanout spacing raise impedance. These are local quasi-static cross-sections, not a full channel pass/fail or reflected-wave/eye result.

Eight new2D field solves tested four width choices against the **same** etch+/-15um, h+/-10%, Er+/-0.2 and fixed-mask broad corners. Gap and limits unchanged:

| Candidate width mm | Low Z | High Z | Lower margin | Upper margin | Both pass |
|---:|---:|---:|---:|---:|---|
'''
for x in sw['candidates']:s+=f"| {x['nominal_width_mm']:.2f} | {x['process_low_Z_ohm']:.3f} | {x['process_high_Z_ohm']:.3f} | {x['lower_margin_ohm']:+.3f} | {x['upper_margin_ohm']:+.3f} | NO |\n"
s+='''
Simple width retuning failed this finite candidate set; not proof that every possible stack/geometry is infeasible. No high-speed route change is accepted. The earlier tighter-process result90.01-98.11ohm is retained only as historical sensitivity, **not used to close the original requirement**. A stack/geometry/channel revision and actual fabricator material data are needed.

Final filled-plane geometry check was rerun: no unintended HS reference voids outside0.36mm own-via launch exemptions; four TX transitions have GND vias within0.891mm vs1mm target. Original CLK/RX/TX conductor lengths18.459531/17.838211/19.109033mm and zero planar P/N skew are preserved. No3D connector/via/cable, losses, crosstalk, S-parameter, TDR or PCIe compliance analysis is claimed.

## Component and mechanical disposition

`BOM_selected.csv` maps all30 electrical references. TI TPS62130ARGTR, Coilcraft XAL4020-222MEC, TDK10uF25V and Murata22uF10V X7R1206,31.6k/10k0.1%25ppm divider remain conditional engineering selections. No purchasing release.

80x78x1.6mm carrier, four2.7mm mounts at(24,24),(96,24),(24,94),(96,94)mm.2242 card22x42mm atx54..76/y48.25..90.25; expanded0.35mm planar envelope passes with7.4mm edge margin. TE peg datum(65,50), slot lower datum2.48mm REF, Wurth9774025243R2.5mm support at(65,90.25). Nominal0.02mm height difference is not tolerance approval.6.5mm card envelope and about8.4mm header require enclosure review. Not a Pi HAT+ mounting pattern.

Remaining release gates:
1. Failed voltage, thermal and original SI corners above; joint load/process/temperature bounds and effective MLCC data.
2. Legacy J1 TE FFC is superseded/on hold. Molex5034801600 is a candidate, not drop-in. Qualify drawing, footprint and selected cable contact orientation/current rating.
3. Current TE M-key approval, actual SSD temperature/rating/drawing, bottom components, mating-height tolerances and screw engagement/support process.
4. J4 SUSCLK DNP assumes SSD does not need it. Missing-supply/sideband sequence, hot plug, reverse polarity, hot fault current and protection are not qualified.
5. QFN/H5/U2 via-in-pad process, solder wicking, stencil, filling/capping/tenting; independent electrical review and CAM/DFM.
6. FPGA device timing/physical DDR/PCIe are separate system tasks; this carrier cannot establish them. See `docs/SYSTEM_AUDIT.md` for all10 project areas.

## Actual commands and logs

From project root, completed commands include:

```sh
make pcb-rebuild
make pcb-draft
./tools/run-analysis python3 hardware/reference_pcie_adapter/analysis/export_geometry.py
./tools/run-analysis python3 hardware/reference_pcie_adapter/analysis/geometry_checks.py
./tools/run-analysis python3 hardware/reference_pcie_adapter/analysis/dc_network.py
./tools/run python hardware/reference_pcie_adapter/analysis/power_corners.py
./tools/run bash -c 'cd hardware/reference_pcie_adapter/analysis; ngspice -b adapter_loaded_corner.cir'
./tools/run python hardware/reference_pcie_adapter/analysis/loaded_transient_evidence.py
./tools/run-analysis python3 hardware/reference_pcie_adapter/analysis/thermal.py
./tools/run-analysis python3 hardware/reference_pcie_adapter/analysis/thermal_exit_requirement.py
./tools/run-analysis python3 hardware/reference_pcie_adapter/analysis/si_feasibility.py
./tools/run python hardware/reference_pcie_adapter/analysis/voltage_feasibility.py
./tools/run-analysis python3 hardware/reference_pcie_adapter/analysis/review_margins.py
make pcb-engineering-check
```

Exact retained logs: `results/simulation_logs/pcb-r031-*.log`, `r031-*.log`, `r04-dc.log`, `r04-loaded-transient-final.log`, `r04-loaded-transient-metrics.log`, `r04-thermal-mitigation.log`, `r04-si-feasibility.log`. Early stopped/failed attempts are explicitly historical. Software evidence checks are separate from failed hardware gates.

`make pcb-engineering` reproduces the full chain including both switching traces and current analyses; it was updated, not rerun as an aggregate in this continuation. Its stages above were individually executed. Full raw multi-million-point data stays in local build; compact true-sample CSV, metrics and plots are portable. Model-fetch scripts reproduce copyrighted vendor inputs, which are not redistributed. `python3 tools/package.py` validates the final ZIP hashes.

'''
s+=references
if (H/'INDEPENDENT_REVIEW.md').exists():s='> Current independent review: [independent audit](INDEPENDENT_REVIEW.md) supersedes nominal-copper thermal interpretation below. Minimum-copper review has six failures and160.30C fine worst. Historical results below remain for traceability.\n\n'+s
p.write_text(s);print('Wrote Rev0.3.1 evidence-based review')
