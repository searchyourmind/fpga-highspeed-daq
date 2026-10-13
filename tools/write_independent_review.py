"""Render the current PCB review from recorded independent studies."""
from pathlib import Path
import json
R=Path(__file__).resolve().parents[1];H=R/'hardware/reference_pcie_adapter';O=H/'outputs/engineering';j=lambda n:json.loads((O/(n+'.json')).read_text())
v,t,s=j('voltage-root-cause'),j('thermal-independent-review'),j('si-independent-review')
text='''# PCB Rev 0.3.1 independent engineering review

**Disposition: design-only; voltage, thermal and impedance acceptance remain FAIL. No fabrication release.** This Pi 5 carrier is independent of the FPGA DAQ RTL. The review corrects analysis assumptions and verification tooling; no unsupported component swap, stackup change or decorative routing has been adopted. All values below are modeled, not measured.

This review supersedes the thermal/process interpretation in the earlier checkpoint PDF and slide deck. The original limits remain **3.135-3.465 V, Tj <=125 C and 81-99 ohm**. Original ambient/load/convection and broad assumed etch/dielectric bounds are retained. Numerical solver convergence and command exit 0 do not mean the board requirements pass.

## Voltage: exact failing cases

| Composite case | Calculated V | Limit V | Signed margin mV | Result |
|---|---:|---:|---:|---|
'''
for r in v['cases']:text+=f"| {r['case']} | {r['result_V']:.9f} | {r['limit_V']:.3f} | {r['margin_mV']:+.6f} | FAIL |\n"
text+='\nSigned contributions relative to the nominal divider output:\n\n| Term (mV) | Full-load low | Light-load PSM high |\n|---|---:|---:|\n'
a,b=[r['terms_V'] for r in v['cases']]
for name in dict.fromkeys([*a,*b]):text+=f"| {name} | {a.get(name,0)*1000:+.6f} | {b.get(name,0)*1000:+.6f} |\n"
text+='''
Finished outer copper30um and via plating20um are assumed lower bounds, not a verified manufacturing commitment. Published average hole plating must not be substituted for a guaranteed minimum. The 2 A / 125 C output-copper drop is 37.160889 mV. The lower budget permits only 32.608077 mV (16.304039 mohm), compared with the extracted 18.580444 mohm. Ground 10 mV, contact 25 mV, dynamic 40 mV and line/load 5 mV remain explicit reserves. Widening copper can help the lower case; it cannot fix the light-load upper case, where that current-dependent drop is absent.

The PWM high budget is 3.454152860 V, with +10.847140 mV margin. The failing high case is specifically the larger PSM feedback envelope: it leaves 22.389558 mV for dynamics and line/load but the unchanged allocation is 45 mV. Divider-only feasibility remains empty: Rtop >=31,658.44 ohm and <=31,327.32 ohm simultaneously. Raising/lowering the setpoint shifts the conflict.

The TI PSM feedback accuracy row is specified at Cout=22 uF; the 16 uF effective-capacitance stress is outside that explicit table condition. Therefore the composite upper result is not a complete silicon/capacitance guarantee. Static accuracy, line/load and ripple terms may overlap under a qualified mode-specific envelope, but no overlap is subtracted without evidence. Reference and divider extremes are conservatively combined; simultaneous mode/process conditions still need qualification. No capacitor or regulator substitution is accepted solely from a nominal transient.

The retained nominal and externally stressed switching traces pass their modeled windows. They use nominal room-temperature internal semiconductor parameters and do not close these joint tolerance bounds. The clean rerun status is separately recorded in `results/release-audit/`; no unfinished transient is counted as passed.

Source: [TI TPS62130/A datasheet, electrical characteristics](https://www.ti.com/lit/ds/symlink/tps62130.pdf). Exact terms: `outputs/engineering/voltage-root-cause.json`.

## Thermal: five original failures and corrected copper corner

All cases below add 0.25 W inductor and 0.25 W copper loss. h is convection per exposed side in W/m2K. Original model uses 35 um outer copper; refinements retain its inputs and 125 C limit.

| ID | Ambient C / h | Regulator / SSD coupling W | 1.0 mm Tj C | 0.5 mm Tj C | 0.25 mm Tj C | Fine signed margin C |
|---|---|---|---:|---:|---:|---:|
'''
for r in t['original_failing_case_refinement']:
 a,b,c=r['mesh_runs'];text+=f"| {r['original_case_id']} | {a['ambient_C']:.0f} / {a['h_each_side_W_m2K']:.0f} | {a['assumed_regulator_loss_W']:.1f} / {a['assumed_SSD_heat_into_carrier_W']:.2f} | {a['estimated_regulator_junction_C']:.6f} | {b['estimated_regulator_junction_C']:.6f} | {c['estimated_regulator_junction_C']:.6f} | {c['margin_C']:+.6f} |\n"
text+='''
The original 159.381 C case is not just a numerical artifact. At 60 C ambient, h=5 and 3.15 W total heat, the analytical average board rise is 50.480769 C, before the local regulator hotspot and package path. At the same full-load hotspot on the 0.5 mm / 35 um solve, heat contributions are:

| Source | Board rise C | Additional junction path C |
|---|---:|---:|
'''
for x in t['loss_attribution_worst35um_0p5mm']:text+=f"| {x['source']} | {x['board_rise_at_full_regulator_hotspot_C']:.6f} | {x['junction_path_rise_C']:.6f} |\n"
text+=f'''
Superposition maximum error is {t['superposition_max_error_C']:.3g} C. An independent uniform-source exact solution agrees within {t['uniform_source_exact_solution_error_C']:.3g} C. These support implementation correctness for the assumed linear sheet model, not its physical qualification.

**Correction:** the prior thermal model assumed 35 um nominal outer copper, while DC loss used 30 um minimum. Rerunning all 24 thermal cases at 30 um and 0.5 mm grid produces **{t['corrected_failing_count']} failures**. No loss, ambient, convection or acceptance limit was lowered.

| ID | Ambient C / h | Regulator / SSD W | Tj C (0.5 mm) | Margin C | Result |
|---|---|---|---:|---:|---|
'''
for x in t['corrected_minimum_outer_copper_cases']:
 if not x['within_125C']:text+=f"| {x['case_id']} | {x['ambient_C']:.0f} / {x['h_each_side_W_m2K']:.0f} | {x['assumed_regulator_loss_W']:.1f} / {x['assumed_SSD_heat_into_carrier_W']:.2f} | {x['estimated_regulator_junction_C']:.6f} | {x['margin_C']:+.6f} | FAIL |\n"
f=t['worst_corrected_fine'];c=t['case3_corrected_fine']
text+=f'''
Worst-case fine-grid result: **{f['estimated_regulator_junction_C']:.6f} C**, margin **{125-f['estimated_regulator_junction_C']:+.6f} C**; last grid change {t['worst_corrected_mesh_delta_C']:.6f} C. Newly failing case 3 also remains above limit on the fine grid: **{c['estimated_regulator_junction_C']:.6f} C**. Its small margin is within broader model uncertainty, so it cannot support a PASS.

The estimated temperatures exceed recommended operation and, at the worst point, the 150 C absolute maximum and roughly 160 C typical shutdown region. The steady linear extrapolation is a rejection indicator, not a prediction that the IC can operate sustainably at that temperature. Loss and convection are assumed; temperature-dependent loss/shutdown is not dynamically modeled. ThetaJCbottom=4.5 K/W is a package/cold-plate metric, not a full-board thermal resistance. The sheet model assumes through-thickness equilibrium and simplified via/solder heat flow. SSD die temperature and enclosure airflow are unqualified. Earlier added-sink results are unimplemented sensitivities, not an approved solution; they also require recomputation at minimum copper before any acceptance.

Sources: [TI datasheet](https://www.ti.com/lit/ds/symlink/tps62130.pdf), [TI package thermal metrics](https://www.ti.com/lit/an/spra953d/spra953d.pdf). All 24 corrected rows and all refinements: `outputs/engineering/thermal-independent-review.json`.

## Impedance: material, spacing and process sensitivity

Current routed geometry remains w=0.14 / edge gap=0.152 mm, h=0.0994 mm, Er=4.1. The original fine nominal is 93.9369 ohm; original broad corners are 83.29-106.125704 ohm. High corner margin is **-7.125704 ohm**. Its narrower width, wider gap, thicker dielectric and lower Er increase impedance. The local 0.36 mm fanout gap yields 104.134617 ohm, margin **-5.134617 ohm**. These are local cross-sections, not complete-channel compliance.

The extended solver reproduces the retained 5 um-grid baseline exactly (94.300723 ohm); it is not silently compared with a different mesh's nominal value. New one-variable sensitivities:

| Cross-section case (5 um grid unless noted) | Zdiff ohm | Lower margin ohm | Upper margin ohm |
|---|---:|---:|---:|
'''
for x in s['sensitivity_cases'][:9]:
 z=x['Zdiff_ohm'];text+=f"| {x['case']} | {z:.6f} | {z-81:+.6f} | {99-z:+.6f} |\n"
text+='''
The manufacturer calculator guide uses 40.64 um external copper, 30.48 um mask on substrate/gap, 15.24 um over traces, mask Er=3.8 and trace top narrowing of 17.78 um. Its stack table separately lists 35 um outer copper. These are reference inputs, not a confirmed fabrication specification. The original 10 um/Er3.3 rectangular-mask assumption is insufficiently qualified. The new tapered/rectilinear models are sensitivities, not measured microsections.

Seven stack/geometry candidates retain the original etch +/-15 um, h +/-10% and Er +/-0.2 screening bounds. The h percentage is an assumption, not a promised prepreg tolerance. Generic manufacturer track-width +/-20% is also not an acceptance of our tighter assumed absolute etch bound.

| Stack | h mm / Er | Width / gap mm | Low / high ohm | Lower / upper margins ohm | Two original corners |
|---|---|---|---|---|---|
'''
for x in s['geometry_candidates']:text+=f"| {x['stack']} | {x['nominal_h_mm']} / {x['nominal_er']} | {x['w_mm']} / {x['g_mm']} | {x['Zlow']:.4f} / {x['Zhigh']:.4f} | {x['lower_margin']:+.4f} / {x['upper_margin']:+.4f} | {'PASS SCREEN ONLY' if x['pass_original_bounds'] else 'FAIL'} |\n"
text+='\nAdditional manufacturer-profile/copper sweeps challenge the apparently passing 7628 candidate:\n\n| Case | Zdiff ohm | Lower / upper margins ohm |\n|---|---:|---|\n'
for x in s['sensitivity_cases']:
 if 'manufacturer_Cu' in x['case']:
  z=x['Zdiff_ohm'];text+=f"| {x['case']} | {z:.6f} | {z-81:+.6f} / {99-z:+.6f} |\n"
text+='''
The 7628 candidate fails at 79.257411 ohm after adding the published mask/etch profile and 40.64 um copper at the low-Z corner: **-1.742589 ohm** lower margin. Thus it is not an accepted design fix. No stackup or route changes were committed merely to make the original two checks pass.

Same-layer ground fill is at least 8.605 mm from the inspected signal segment edges. The 0.15/0.30 mm coplanar-ground experiments are hypothetical sensitivity studies, not a claim that the current tracks have that nearby ground. Filled reference planes and return-via geometry remain checked separately. Full via/pad/connector/FFC discontinuities, insertion/return loss, roughness, dispersion, crosstalk, eye/TDR and protocol compliance are absent. A 2D nominal impedance pass cannot close these gates.

Sources: [JLC stack table](https://jlcpcb.com/impedance), [calculator input guide](https://jlcpcb.com/help/article/user-guide-to-the-jlcpcb-impedance-calculator), [manufacturing capabilities](https://jlcpcb.com/capabilities/pcb-capabilities/). Full inputs/results: `outputs/engineering/si-independent-review.json`.

## CAD and mechanical scope

Source-only native rebuild and draft export pass ERC/DRC/unconnected/parity with zero issues. The board remains 80 x 78 x 1.6 mm; 2242 SSD planar envelope and reference-plane geometry pass the documented 2D screens. This does not qualify actual connector seating, SSD underside components, support height, screw engagement, cable orientation, insertion envelope, via-in-pad process or assembly tolerances. Conditional component selection is not purchasing approval.

![Native KiCad rendering](outputs/board-3d.png)

This is a CAD render, not fabricated hardware. Some component 3D bodies are unavailable. Native source is under `kicad/`, mechanical plots under `outputs/engineering/` and DRAFT exports under `outputs/DRAFT_NOT_FOR_MANUFACTURE/`.

## Reproduce and close the remaining gates

```sh
make pcb-rebuild
make pcb-engineering
./tools/run python hardware/reference_pcie_adapter/analysis/voltage_root_cause.py
./tools/run-analysis python3 hardware/reference_pcie_adapter/analysis/thermal_independent_review.py
./tools/run-analysis python3 hardware/reference_pcie_adapter/analysis/si_independent_review.py
python3 tools/write_independent_review.py
```

1. Obtain a defensible joint voltage envelope over load/mode, effective MLCC, temperature/process, input and connector drops, or redesign regulation without reducing requirements.
2. Establish a real thermal exit and SSD/enclosure limits; recompute minimum-copper and hot-loss conditions. Actual cooling/package validation remains deferred.
3. Qualify material/copper/mask/process bounds and route the selected stack; analyze discontinuities/full channel. No screened candidate is currently accepted.
4. Resolve connector/cable/SSD/assembly and fabrication checks before release. Fabrication, purchases and physical validation remain deferred.

The board is publishable only as an exploratory engineering case study that includes its failed gates. The verified RTL portfolio is a separate deliverable.
'''
(H/'INDEPENDENT_REVIEW.md').write_text(text)
p=H/'ENGINEERING_REVIEW.md';old=p.read_text();marker='> Current independent review:'
if marker not in old:p.write_text('> Current independent review: [Rev 0.3.1 independent audit](INDEPENDENT_REVIEW.md) supersedes the nominal-copper thermal interpretation below (six minimum-copper failures; 160.30 C fine-grid worst). The historical model and correction record below remain for traceability.\n\n'+old)
print('Wrote independent PCB review with signed margins and retained failures')
