# PCB Rev 0.3.1 independent engineering review

Published numerical tables and CAD views: [curated evidence](../../evidence/pcb/). Paths beginning `outputs/` or `results/` below identify regenerated/local historical outputs; all compact numerical originals are included under `evidence/pcb/engineering/`. This review is frozen for portfolio publication.

**Disposition: design-only; voltage, thermal and impedance acceptance remain FAIL. No fabrication release.** This Pi 5 carrier is independent of the FPGA DAQ RTL. The review corrects analysis assumptions and verification tooling; no unsupported component swap, stackup change or decorative routing has been adopted. All values below are modeled, not measured.

This review supersedes the thermal/process interpretation in the earlier checkpoint PDF and slide deck. The original limits remain **3.135-3.465 V, Tj <=125 C and 81-99 ohm**. Original ambient/load/convection and broad assumed etch/dielectric bounds are retained. Numerical solver convergence and command exit 0 do not mean the board requirements pass.

## Voltage: exact failing cases

| Composite case | Calculated V | Limit V | Signed margin mV | Result |
|---|---:|---:|---:|---|
| full_load_low | 3.130447188 | 3.135 | -4.552812 | FAIL |
| light_load_PSM_high | 3.487610442 | 3.465 | -22.610442 | FAIL |

Signed contributions relative to the nominal divider output:

| Term (mV) | Full-load low | Light-load PSM high |
|---|---:|---:|
| nominal | +3328.000000 | +3328.000000 |
| reference_error | -59.904000 | +93.184000 |
| divider_ratio_error | -17.316863 | +18.255382 |
| FB_leakage | -3.171060 | +3.171060 |
| output_copper | -37.160889 | +0.000000 |
| ground_reserve | -10.000000 | +0.000000 |
| contact_reserve | -25.000000 | +0.000000 |
| dynamic_reserve | -40.000000 | +40.000000 |
| line_load_reserve | -5.000000 | +5.000000 |

Finished outer copper30um and via plating20um are assumed lower bounds, not a verified manufacturing commitment. Published average hole plating must not be substituted for a guaranteed minimum. The 2 A / 125 C output-copper drop is 37.160889 mV. The lower budget permits only 32.608077 mV (16.304039 mohm), compared with the extracted 18.580444 mohm. Ground 10 mV, contact 25 mV, dynamic 40 mV and line/load 5 mV remain explicit reserves. Widening copper can help the lower case; it cannot fix the light-load upper case, where that current-dependent drop is absent.

The PWM high budget is 3.454152860 V, with +10.847140 mV margin. The failing high case is specifically the larger PSM feedback envelope: it leaves 22.389558 mV for dynamics and line/load but the unchanged allocation is 45 mV. Divider-only feasibility remains empty: Rtop >=31,658.44 ohm and <=31,327.32 ohm simultaneously. Raising/lowering the setpoint shifts the conflict.

The TI PSM feedback accuracy row is specified at Cout=22 uF; the 16 uF effective-capacitance stress is outside that explicit table condition. Therefore the composite upper result is not a complete silicon/capacitance guarantee. Static accuracy, line/load and ripple terms may overlap under a qualified mode-specific envelope, but no overlap is subtracted without evidence. Reference and divider extremes are conservatively combined; simultaneous mode/process conditions still need qualification. No capacitor or regulator substitution is accepted solely from a nominal transient.

The retained nominal and externally stressed switching traces pass their modeled windows. They use nominal room-temperature internal semiconductor parameters and do not close these joint tolerance bounds. The clean rerun status is separately recorded in `results/release-audit/`; no unfinished transient is counted as passed.

Source: [TI TPS62130/A datasheet, electrical characteristics](https://www.ti.com/lit/ds/symlink/tps62130.pdf). Exact terms: `outputs/engineering/voltage-root-cause.json`.

## Thermal: five original failures and corrected copper corner

All cases below add 0.25 W inductor and 0.25 W copper loss. h is convection per exposed side in W/m2K. Original model uses 35 um outer copper; refinements retain its inputs and 125 C limit.

| ID | Ambient C / h | Regulator / SSD coupling W | 1.0 mm Tj C | 0.5 mm Tj C | 0.25 mm Tj C | Fine signed margin C |
|---|---|---|---:|---:|---:|---:|
| 11 | 40 / 5 | 1.0 / 1.65 | 139.381092 | 137.694627 | 137.388779 | -12.388779 |
| 17 | 60 / 5 | 0.6 / 1.65 | 134.757967 | 133.712536 | 133.530989 | -8.530989 |
| 18 | 60 / 5 | 1.0 / 0.00 | 137.240886 | 135.391245 | 135.058490 | -10.058490 |
| 19 | 60 / 5 | 1.0 / 1.65 | 159.381092 | 157.694627 | 157.388779 | -32.388779 |
| 23 | 60 / 10 | 1.0 / 1.65 | 131.231218 | 129.631578 | 129.318654 | -4.318654 |

The original 159.381 C case is not just a numerical artifact. At 60 C ambient, h=5 and 3.15 W total heat, the analytical average board rise is 50.480769 C, before the local regulator hotspot and package path. At the same full-load hotspot on the 0.5 mm / 35 um solve, heat contributions are:

| Source | Board rise C | Additional junction path C |
|---|---:|---:|
| regulator | 52.567258 | 7.458807 |
| inductor | 8.536352 | 0.000000 |
| SSD_coupling | 22.378781 | 0.000000 |
| copper | 6.753428 | 0.000000 |

Superposition maximum error is 9.95e-14 C. An independent uniform-source exact solution agrees within 1.14e-11 C. These support implementation correctness for the assumed linear sheet model, not its physical qualification.

**Correction:** the prior thermal model assumed 35 um nominal outer copper, while DC loss used 30 um minimum. Rerunning all 24 thermal cases at 30 um and 0.5 mm grid produces **6 failures**. No loss, ambient, convection or acceptance limit was lowered.

| ID | Ambient C / h | Regulator / SSD W | Tj C (0.5 mm) | Margin C | Result |
|---|---|---|---:|---:|---|
| 3 | 25 / 5 | 1.0 / 1.65 | 125.575206 | -0.575206 | FAIL |
| 11 | 40 / 5 | 1.0 / 1.65 | 140.575206 | -15.575206 | FAIL |
| 17 | 60 / 5 | 0.6 / 1.65 | 135.530751 | -10.530751 | FAIL |
| 18 | 60 / 5 | 1.0 / 0.00 | 138.622222 | -13.622222 | FAIL |
| 19 | 60 / 5 | 1.0 / 1.65 | 160.575206 | -35.575206 | FAIL |
| 23 | 60 / 10 | 1.0 / 1.65 | 132.259317 | -7.259317 | FAIL |

Worst-case fine-grid result: **160.302515 C**, margin **-35.302515 C**; last grid change 0.272692 C. Newly failing case 3 also remains above limit on the fine grid: **125.302515 C**. Its small margin is within broader model uncertainty, so it cannot support a PASS.

The estimated temperatures exceed recommended operation and, at the worst point, the 150 C absolute maximum and roughly 160 C typical shutdown region. The steady linear extrapolation is a rejection indicator, not a prediction that the IC can operate sustainably at that temperature. Loss and convection are assumed; temperature-dependent loss/shutdown is not dynamically modeled. ThetaJCbottom=4.5 K/W is a package/cold-plate metric, not a full-board thermal resistance. The sheet model assumes through-thickness equilibrium and simplified via/solder heat flow. SSD die temperature and enclosure airflow are unqualified. Earlier added-sink results are unimplemented sensitivities, not an approved solution; they also require recomputation at minimum copper before any acceptance.

Sources: [TI datasheet](https://www.ti.com/lit/ds/symlink/tps62130.pdf), [TI package thermal metrics](https://www.ti.com/lit/an/spra953d/spra953d.pdf). All 24 corrected rows and all refinements: `outputs/engineering/thermal-independent-review.json`.

## Impedance: material, spacing and process sensitivity

Current routed geometry remains w=0.14 / edge gap=0.152 mm, h=0.0994 mm, Er=4.1. The original fine nominal is 93.9369 ohm; original broad corners are 83.29-106.125704 ohm. High corner margin is **-7.125704 ohm**. Its narrower width, wider gap, thicker dielectric and lower Er increase impedance. The local 0.36 mm fanout gap yields 104.134617 ohm, margin **-5.134617 ohm**. These are local cross-sections, not complete-channel compliance.

The extended solver reproduces the retained 5 um-grid baseline exactly (94.300723 ohm); it is not silently compared with a different mesh's nominal value. New one-variable sensitivities:

| Cross-section case (5 um grid unless noted) | Zdiff ohm | Lower margin ohm | Upper margin ohm |
|---|---:|---:|---:|
| legacy_reproduction | 94.300723 | +13.300723 | +4.699277 |
| Cu30um | 95.728973 | +14.728973 | +3.271027 |
| Cu40p64um | 92.792377 | +11.792377 | +6.207623 |
| mask_manufacturer_rect | 89.866954 | +8.866954 | +9.133046 |
| etched_top | 96.218105 | +15.218105 | +2.781895 |
| coplanar_0p15 | 92.852263 | +11.852263 | +6.147737 |
| coplanar_0p30 | 94.136818 | +13.136818 | +4.863182 |
| manufacturer_reference_combined | 90.329094 | +9.329094 | +8.670906 |
| manufacturer_combined_fine | 90.208598 | +9.208598 | +8.791402 |

The manufacturer calculator guide uses 40.64 um external copper, 30.48 um mask on substrate/gap, 15.24 um over traces, mask Er=3.8 and trace top narrowing of 17.78 um. Its stack table separately lists 35 um outer copper. These are reference inputs, not a confirmed fabrication specification. The original 10 um/Er3.3 rectangular-mask assumption is insufficiently qualified. The new tapered/rectilinear models are sensitivities, not measured microsections.

Seven stack/geometry candidates retain the original etch +/-15 um, h +/-10% and Er +/-0.2 screening bounds. The h percentage is an assumption, not a promised prepreg tolerance. Generic manufacturer track-width +/-20% is also not an acceptance of our tighter assumed absolute etch bound.

| Stack | h mm / Er | Width / gap mm | Low / high ohm | Lower / upper margins ohm | Two original corners |
|---|---|---|---|---|---|
| 3313 | 0.0994 / 4.1 | 0.13 / 0.1 | 78.0783 / 101.1965 | -2.9217 / -2.1965 | FAIL |
| 3313 | 0.0994 / 4.1 | 0.15 / 0.2 | 84.4835 / 107.2435 | +3.4835 / -8.2435 | FAIL |
| 3313 | 0.0994 / 4.1 | 0.17 / 0.3 | 82.6955 / 105.0924 | +1.6955 / -6.0924 | FAIL |
| 7628 | 0.2104 / 4.4 | 0.3 / 0.2 | 81.8300 / 97.5746 | +0.8300 / +1.4254 | PASS SCREEN ONLY |
| 7628 | 0.2104 / 4.4 | 0.32 / 0.3 | 84.4101 / 100.7714 | +3.4101 / -1.7714 | FAIL |
| 7628 | 0.2104 / 4.4 | 0.34 / 0.4 | 84.3858 / 100.6602 | +3.3858 / -1.6602 | FAIL |
| 1080 | 0.0764 / 3.91 | 0.12 / 0.1 | 73.8774 / 98.2851 | -7.1226 / +0.7149 | FAIL |

Additional manufacturer-profile/copper sweeps challenge the apparently passing 7628 candidate:

| Case | Zdiff ohm | Lower / upper margins ohm |
|---|---:|---|
| current3313_low_manufacturer_Cu0.03 | 82.769294 | +1.769294 / +16.230706 |
| current3313_low_manufacturer_Cu0.04064 | 79.907175 | -1.092825 / +19.092825 |
| current3313_high_manufacturer_Cu0.03 | 105.074021 | +24.074021 / -6.074021 |
| current3313_high_manufacturer_Cu0.04064 | 101.199005 | +20.199005 / -2.199005 |
| candidate7628_low_manufacturer_Cu0.03 | 81.133533 | +0.133533 / +17.866467 |
| candidate7628_low_manufacturer_Cu0.04064 | 79.257411 | -1.742589 / +19.742589 |
| candidate7628_high_manufacturer_Cu0.03 | 96.337675 | +15.337675 / +2.662325 |
| candidate7628_high_manufacturer_Cu0.04064 | 94.231219 | +13.231219 / +4.768781 |

The 7628 candidate fails at 79.257411 ohm after adding the published mask/etch profile and 40.64 um copper at the low-Z corner: **-1.742589 ohm** lower margin. Thus it is not an accepted design fix. No stackup or route changes were committed merely to make the original two checks pass.

Same-layer ground fill is at least 8.605 mm from the inspected signal segment edges. The 0.15/0.30 mm coplanar-ground experiments are hypothetical sensitivity studies, not a claim that the current tracks have that nearby ground. Filled reference planes and return-via geometry remain checked separately. Full via/pad/connector/FFC discontinuities, insertion/return loss, roughness, dispersion, crosstalk, eye/TDR and protocol compliance are absent. A 2D nominal impedance pass cannot close these gates.

Sources: [JLC stack table](https://jlcpcb.com/impedance), [calculator input guide](https://jlcpcb.com/help/article/user-guide-to-the-jlcpcb-impedance-calculator), [manufacturing capabilities](https://jlcpcb.com/capabilities/pcb-capabilities/). Full inputs/results: `outputs/engineering/si-independent-review.json`.

## CAD and mechanical scope

Source-only native rebuild and draft export pass ERC/DRC/unconnected/parity with zero issues. The board remains 80 x 78 x 1.6 mm; 2242 SSD planar envelope and reference-plane geometry pass the documented 2D screens. This does not qualify actual connector seating, SSD underside components, support height, screw engagement, cable orientation, insertion envelope, via-in-pad process or assembly tolerances. Conditional component selection is not purchasing approval.

![Native KiCad rendering](../../evidence/pcb/board-3d.png)

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
