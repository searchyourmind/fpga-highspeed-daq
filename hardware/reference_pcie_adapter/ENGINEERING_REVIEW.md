> Current independent review: [Rev 0.3.1 independent audit](INDEPENDENT_REVIEW.md) supersedes the nominal-copper thermal interpretation below (six minimum-copper failures; 160.30 C fine-grid worst). The historical model and correction record below remain for traceability.

# Rev 0.3 corrective review - Rev 0.3.1, 2026-10-12

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
| full-load lower composite | 3.108211 | -26.789 | 3.130447 | -4.553 | FAIL |
| PSM upper plus dynamic composite | 3.487610 | -22.610 | 3.487610 | -22.610 | FAIL |

Lower root cause: minimum FB reference and divider/leakage error plus output copper, ground, connector and dynamic drops. Upper root cause: PSM high FB reference plus divider/leakage and positive dynamic allowance. These are conservative independent extrema, not a simulated claim that all occur simultaneously.

Same budgets: PWM FB minimum0.7856V, PSM maximum0.8224V;100nA FB leakage;0.1% resistors plus25ppm/K over100K;10mV GND,25mV contact,40mV transient/ripple,5mV line/load. The40mV reserve was retained despite the new trace being smaller; two traces do not justify shrinking the full process/temperature budget.

Actual resistor-network extraction covers equal sharing and all126 combinations of four0.5A loads among nine power pads at125C,30um outer copper and20um via plating. Worst2A output drop improved59.397->37.161mV. Pads are ideal; ground/contact/cable drops are separate. KCL and independent analytic resistor fixtures pass. Thermal copper allowance stays0.25W and still covers the independently stressed input+output network. This is not IPC-2152 ampacity qualification.

Divider feasibility was solved algebraically with the same errors/reserves and10kohm bottom resistor: Rtop must be >=**31658.44ohm** for the lower bound and <=**31327.32ohm** for the upper bound. The feasible intervals do not overlap (-331.12ohm gap). Divider-only retargeting is rejected, not presented as a fix.

### Executed power simulations

108 original CCM DC/AC cases rerun: Vin4.65/5/5.25V, load0.5/1/2A, Cout16/22/52.8uF, L1.232/2.64uH, ESR5/30mohm. All DC outputs within target and121 finite AC samples per case. This shared-core non-A average model cannot validate A PG, PFM, fault current or phase margin.

The retained official TPS62130A nominal trace has6,605,420 points over3.05ms and output3.292944-3.362127V at the regulator. A **new actual loaded external-component corner** also completed:4.65V input,1.232uH,75mohmDCR,16uF,10mohmESR,3.3nF soft start and18.580444mohm extracted output route.0.5A resistive base plus1.5A pulse, EN shutdown at2.8ms.

- 6,455,898 solver points; load-event load voltage **3.266353-3.342949V**; target margins **+131.353/+122.051mV**.
- Regulator excursion25.013mV leaves14.987mV inside the existing40mV reserve. Compare regulator excursion here, avoiding double-counting the separately modeled DC board drop.
- PeakIL2.219306A; PG steady4.6485V and shutdown0.0687V. All trace checksPASS.

This is a room-temperature internal semiconductor model with stressed external components and an equivalent hot trace resistor. It is not a full semiconductor process/temperature sweep, measured efficiency, joint FB-error transient, input cable model, hot fault test or stability phase-margin result. Effective MLCC curves and actual SSD load remain unqualified. Existing inductor normal-peak screening2.251A and soft-start1.110-2.269ms are assumptions, not new measurements.

## Every original failing thermal case

Each row also includes fixed0.25W inductor and0.25W copper heat. Tj limit remains125C; margin=125-Tj. Case IDs index the24-row Cartesian product in `thermal.json`.

| ID | Ambient C | h each side W/m2K | Regulator W | SSD-to-board W | Before Tj C | Corrected Tj C | Corrected margin C | Disposition |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| 3 | 25 | 5 | 1.0 | 1.65 | 125.778 | 124.381 | +0.619 | PASS_SCREEN |
| 11 | 40 | 5 | 1.0 | 1.65 | 140.778 | 139.381 | -14.381 | FAIL |
| 17 | 60 | 5 | 0.6 | 1.65 | 135.629 | 134.758 | -9.758 | FAIL |
| 18 | 60 | 5 | 1.0 | 0.00 | 139.299 | 137.241 | -12.241 | FAIL |
| 19 | 60 | 5 | 1.0 | 1.65 | 160.778 | 159.381 | -34.381 | FAIL |
| 23 | 60 | 10 | 1.0 | 1.65 | 131.674 | 131.231 | -6.231 | FAIL |

**5/24 still fail.** Case3's nominal+0.619C is too small to qualify hardware given model/process uncertainty; it is only a numerical screen pass. Current mesh0.5-to0.25mm change is0.274C in the convergence case; energy residuals pass.

Root cause: local regulator dissipation plus SSD coupling and insufficient heat exit at hot ambient/weak convection. Expanded ground spreading lowers worst Tj by only1.397C, so more copper alone is insufficient. The2D model samples actual outer GND copper with50% conductance derating, two derated15.2um inner planes, FR4 k0.3W/mK and copper385W/mK; adds modeled solder/via path and4.5K/W bottom junction resistance. It does not substitute datasheet JEDEC thetaJA for the actual board. Predicted overheating is rejection evidence, not precision characterization outside valid material temperatures. No2A continuous rating is released.

### Quantified additional heat-path requirement

Four actual2D solves add a candidate10x10mm regulator-region contact while removing covered-side free convection; ambient60C, h5 and all losses/limits remain unchanged. R includes the total PCB/contact/interface/sink-to-ambient path, not just a catalog sink rating.

| Total candidate path K/W | Estimated Tj C | Margin C |
|---:|---:|---:|
| 60 | 127.490 | -2.490 |
| 40 | 119.164 | +5.836 |
| 25 | 109.325 | +15.675 |
| 15 | 99.493 | +25.507 |

Coarse1mm-mesh bisection suggests R<=49.79K/W just to meet125C. This is an **unimplemented candidate requirement**, not an accepted assembly or design pass. Even the15K/W case leaves modeled SSD-region board temperature103.49C, so IC cooling alone does not qualify the SSD. Actual SSD rating,3D interface, enclosure and coupling remain open.

## Exact impedance failures and attempted correction

Nominal93.9369ohm uses width0.14mm, gap0.152mm, dielectric0.0994mm, Er4.1,35um copper and assumed10um/Er3.3 conformal mask. Existing mesh/domain/energy/residual/uniform-dielectric checks pass; finest mesh480329 unknowns. Signal geometry and inner dielectric stack are unchanged by this correction.

| Case | Width/gap/h mm | Er | Zdiff ohm | Lower margin ohm | Upper margin ohm | Result |
|---|---|---:|---:|---:|---:|---|
| low_Z | 0.15500/0.13700/0.08946 | 4.3 | 83.29022 | +2.29022 | +15.70978 | PASS_SCREEN |
| high_Z | 0.12500/0.16700/0.10934 | 3.9 | 106.12570 | +25.12570 | -7.12570 | FAIL_LOCAL_CROSS_SECTION |
| no_mask | 0.14000/0.15200/0.09940 | 4.1 | 98.49027 | +17.49027 | +0.50973 | PASS_SCREEN |
| wide_fanout | 0.14000/0.36000/0.09940 | 4.1 | 104.13462 | +23.13462 | -5.13462 | FAIL_LOCAL_CROSS_SECTION |

Root cause: narrow etched traces, larger plane spacing, lower permittivity and increased local fanout spacing raise impedance. These are local quasi-static cross-sections, not a full channel pass/fail or reflected-wave/eye result.

Eight new2D field solves tested four width choices against the **same** etch+/-15um, h+/-10%, Er+/-0.2 and fixed-mask broad corners. Gap and limits unchanged:

| Candidate width mm | Low Z | High Z | Lower margin | Upper margin | Both pass |
|---:|---:|---:|---:|---:|---|
| 0.14 | 83.290 | 106.126 | +2.290 | -7.126 | NO |
| 0.15 | 80.825 | 102.838 | -0.175 | -3.838 | NO |
| 0.16 | 78.514 | 99.776 | -2.486 | -0.776 | NO |
| 0.17 | 76.342 | 96.914 | -4.658 | +2.086 | NO |

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

## Primary references
- [TI TPS62130/A datasheet SLVSAG7F](https://www.ti.com/lit/ds/symlink/tps62130.pdf)
- [TI TPS62130A original transient model SLVM893A](https://www.ti.com/lit/zip/slvm893), ZIP SHA256 `0e66ec33e5d44c0358abef9c1e6d74289679799d6338f35da16457418457bf09`; downloaded model not redistributed.
- [Coilcraft XAL4020](https://www.coilcraft.com/getmedia/6adcb47d-8b55-416c-976e-1e22e0d2848c/xal4000.pdf)
- [TDK C3216X7R1E106K160AB](https://product.tdk.com/en/search/capacitor/ceramic/mlcc/info?part_no=C3216X7R1E106K160AB)
- [Murata GRM31CR71A226KE15 specification](https://search.murata.co.jp/Ceramy/image/img/A01X/G101/ENG/GRM31CR71A226KE15-01CA.pdf)
- [TE G-2199230 RevB3 manufacturer drawing](https://cdn.sparkfun.com/assets/9/c/e/b/6/MicroMod_M.2_Connector_Datasheet_TE_2199230-4.pdf)
- [Cervoz2242 manufacturer drawing, distributor hosted](https://globalamericaninc.com/wp-content/uploads/2023/04/2242-NVMe-with-DRAM-MLC-1.pdf)
- [Wurth9774025243R](https://www.we-online.com/components/products/datasheet/9774025243R.pdf)
- [Raspberry Pi PCIe connector standard](https://datasheets.raspberrypi.com/pcie/pcie-connector-standard.pdf)
- [TI thermal metric guidance](https://www.ti.com/design-development/design-simulation-tools/pcb-thermal-calculator.html)
Full per-part provenance and uncertainty are in `BOM_selected.csv`. Referenced drawings were read as evidence, never as task instructions.

