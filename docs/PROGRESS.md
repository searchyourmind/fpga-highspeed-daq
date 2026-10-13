# Engineering progress

## Session 2026-10-12 (America/New_York)

Status: core simulation, generic synthesis, power simulation and portfolio implemented; PCB routing and native CAD checks now complete. Manufacturing qualification remains open. No hardware work or publication performed.

### Input audit / Phase 0
- Fully read the archive's `Codex_Master_Prompt.md`, `START_HERE.md`, and roadmap.
- Requested `Codex_Execute_First.md` is absent from the supplied archive and Downloads search. The supplied master specification is used; the user's implementation-first instruction overrides its teaching/exercise requests.
- Original package SHA-256: `48cb0e1d99f14d43f3a1d18674ff02033ec6faac14f3040570b64fe8a29c9f4e`.
- Extracted immutable working reference to `../fpga-highspeed-daq-package/starter-original/fpga-ddr-pcie-week1` and copied it here. Counter, unfinished FIFO, and four FIFO tests are reused.
- Parent workspace is not a Git repository. No existing files were reset or deleted.
- Host: Apple Silicon macOS; Python 3.13.16 (bundled alternative 3.12.14), Apple Clang 21.0.0, GNU Make 3.81, Docker Engine 29.8.2 available.
- Verilator, Yosys, cocotb, KiCad CLI and ngspice are absent from PATH. A project-scoped Linux Docker toolchain is being prepared; no host system installation.
- Baseline starter FIFO has intentional unimplemented pointers/count. Its reset was asynchronous; project baseline will consistently use active-low synchronous reset, documenting the change.

### Initial gates (historical)
| Phase | State | Evidence |
|---|---|---|
| 0 audit/contracts | IN PROGRESS | Input/tool audit above |
| 1 FIFO/counter | NOT RUN | Starter retained |
| 2–3 streaming/flow control | NOT IMPLEMENTED | Contracts being written |
| 4 memory model | NOT IMPLEMENTED | No DDR PHY intended |
| 5 DMA/ring | NOT IMPLEMENTED | Single descriptor owner planned |
| 6 transport | NOT IMPLEMENTED | PCIe-like transaction abstraction only |
| 7–8 integration/regression | NOT RUN | No performance results yet |
| 9 synthesis | NOT RUN | Generic cells only planned |
| 10 power | NOT IMPLEMENTED | Separate hypothetical design |
| 11 PCB | NOT IMPLEMENTED | Separate Pi 5 adapter, design only |
| 12 portfolio | NOT IMPLEMENTED | Must be grounded in actual evidence |

## Initial next action (historical)
The initial toolchain/FIFO work below has since been completed; authoritative final gates are at the end of this file.

### Implementation checkpoint (tool build still running)
- Implemented FIFO, source, saturating gain, packing, descriptor validator, DMA writer/reader, packetizer and top-level RTL.
- Added finite Python memory, delayed bounded link, strict host receiver, 23 model test cases and cocotb regression sources (counts pending execution).
- Toolchain first build failed because `FlexLexer.h` was absent; added container-only `libfl-dev` and restarted the build. Log: `results/simulation_logs/toolchain-build.log`.
- A provisional host Python test attempt could not run: bundled Python has no pytest. This is an environment failure, not PASS; final tests will use the pinned container.
- Read/visually inspected official Pi PCIe connector v1.1 pinout and M.2 HAT+ Rev 3 schematic. FFC power is limited to 1 A total, so the reference adapter power budget must not assume a 3 A SSD can run from the FFC supply.

### Executed baseline gates
- Toolchain built successfully. Versions captured in `results/tool-versions.txt`.
- `make lint`: PASS for all 11 RTL tops after replacing an unused 65-bit carry intermediate with an explicit overflow bound comparison (no warning suppression added).
- `make test`: PASS, 39 test cases total: 23 Python models + 16 cocotb tests. Original starter's counter and four FIFO tests pass. FIFO depths 1, 3, 8, 16 pass 3,000-cycle randomized scoreboards; streaming and six end-to-end test functions pass.
- End-to-end matrix: all 15 configurations (seeds 11, 2026, 99173) match the independent golden records. Fault/reset/backpressure cases pass. Exact logs and JUnit are in `results/`; benchmark CSV/JSON and chart are generated from observed cycles.
- `make synthesis`: PASS with Yosys 0.33, hierarchy/check and no inferred latches. Technology-independent gates only; no FPGA timing/resource utilization claim.
- TI average model: DC output 3.295268 V, AC sweep executed. Transient model still executing; not yet PASS.
- Installed Ubuntu KiCad is 7.0.11, which lacks CLI ERC/DRC. A separate container upgrade is being investigated; no host system changes.

### Power and PCB execution / defects repaired
- TI average-model DC output 3.29526846 V; 241 AC points. Nine independent DC cases across 5/12/16 V and nominal 0.5/1/2 A pass.
- Switching transient first timed out at 120 seconds. A longer run was killed (-9); limiting saved vectors reduced memory. A completed 10nF soft-start run correctly failed the steady-state assertion (1.4748 V average) because the 2.5ms observation ended during soft start. Later 3.3nF run exceeded 300 seconds. Final compact experiment uses 1nF, 1.2ms window and 0.75ms load step; its actual status is recorded separately. No failed run is represented as success.
- Ubuntu 24.04 KiCad 7 lacks command-line ERC/DRC. The KiCad PPA upgrade supplied libraries but no ARM64 binary upgrade. Built a separate Ubuntu 26.04 native ARM64 KiCad 9.0.8 container successfully. No host EDA installation.
- Created 29-component electrically connected native schematic, 4-layer native board, two filled ground planes, three routed differential pairs, custom TE M-key footprint, BOM and pin map.
- Fixed generator syntax/off-grid endpoints, explicit source pin types, library resolution, board/schematic local-net names and no-connect net names. ERC is clean and netlist critical-pin contracts pass.
- Fixed pair separation at 45-degree bends using normal distance, moved breakouts to prevent pad crossings, widened/staggered via fanout, removed accidental inductor-output crossing and moved references to fabrication layer. **Earlier checkpoint: geometry DRC 0; parity 0; 71 unconnected; gate FAIL. This was later repaired in the routing continuation below.**
- KiCad zone fill on a freshly constructed unattached BOARD crashed. Saving and loading the board before filling fixed the API issue; two planes are actually filled. `xvfb-run` startup stalled in this container; a bounded explicit Xvfb startup is used instead.
- Datasheet review caught non-A TPS62130 PG floating when EN is low; changed the separate adapter to TPS62130A for shutdown isolation. The separate regulator SPICE experiment remains TPS62130 and is not an electrical validation of the whole adapter.
- Earlier checkpoint: actual KiCad 3D render produced; missing component bodies disclosed. Draft exports were withheld then, until routing was completed later in this session.

### Portfolio build validation
- Generated five-slide editable presentation with actual benchmark data as a native chart and actual EDA images. Finalizer caught the default Aptos font despite an intended Arial setting; corrected the API field to `typeface`.
- The chart initially lacked an embedded workbook relationship. Enabled the documented literal-data workbook materialization using the complete observed benchmark values. No formulas or external workbook lineage were substituted.
- Prepared README, one-page verification report, demo recording script (no video claimed), five-slide outline, resume candidates and interview FAQ.

### Final power result
- Compact switching-transient experiment **PASS**: 1 nF soft start, 1.2 ms stop time, additional 0.5 A pulse at 0.75 ms. Saved 3,002,924 solver points; final-window mean 3.295416634 V and simulated peak-to-peak 4.90747 mV. These are model results, not hardware measurements.
- Additional trace checks passed: post-startup minimum 3.28534419 V, maximum 3.30537999 V, final PG mean 3.28446841 V. Small preview CSV, startup plot, load-step detail plot, metrics and full logs are retained. Full raw text is excluded from the portable archive; rerun generates it.
- `make power` now passes the average and transient gates, then all nine DC corners. The separate adapter uses 3.3nF and the A-variant regulator; this transient is not a validation of the adapter circuit.

### Final portfolio result
- Five-slide editable PPTX passes package/layout/font/native-chart/embedded-workbook/re-import checks. Chart values are rounded to six decimal places for Excel; original JSON preserves full floating-point data. Five rendered slides visually inspected, with a five-page PDF and one-page verification PDF.
- No video was claimed; a reproducible demo script is included. No finished-board or Cadence claim is included in resume candidates.

## Final phase gates
| Phase | Final state | Evidence / remaining scope |
|---|---|---|
| 0 audit/contracts | COMPLETE | Archive provenance; interfaces and limitations |
| 1 FIFO/counter | PASS | Starter tests + 4 depths |
| 2-3 streaming/flow control | PASS | Golden gain/framing; assertions and stalls |
| 4 memory model | PASS | Latency, bursts at API, bounds, refresh abstraction |
| 5 DMA/ring | PASS | Descriptor errors, wrap, ordering and recovery |
| 6 modeled transport | PASS | Finite queue, delay, custom CRC and host checks |
| 7-8 integration/regression | PASS | 39 JUnit cases; 15 matching scenarios, CSV/plots |
| 9 generic synthesis | PASS | Yosys hierarchy/check, no latches; no physical timing claim |
| 10 power reference | PASS within modeled scope | DC/AC/transient + nine DC corners; currents assumed |
| 11 PCB reference | CAD CHECKS PASS / DESIGN REVIEW DRAFT | Native routed schematic/board; ERC 0, geometric DRC 0, parity 0, unconnected 0; draft Gerber/drill exports |
| 12 portfolio | COMPLETE with disclosed limits | README, five-slide PPTX/PDF, verification PDF, demo script, FAQ, resume candidates |

Remaining engineering: qualified parts/footprints and mechanics, power/thermal and SI/impedance review; optional licensed Cadence exercise. No real FPGA/DDR/PCIe implementation, manufactured board, purchases or GitHub push. See NEXT_SESSION.md for concrete continuation.
- Final optional waveform regression: all six end-to-end tests pass with Verilator tracing enabled. Actual 50.777 us simulation trace retained as `results/waveforms/daq_top.vcd.gz`. Fixed the Docker wrapper to forward WAVES, so the README command now actually enables tracing.
- Original starter counter/FIFO test files checked byte-for-byte against the unmodified extracted starter. Final artifact PDFs have the intended 1/5/1 pages; current verification report says transient PASS. Native presentation validation and visual previews were reviewed.

### PCB routing continuation - 2026-10-12
- Continued beyond the original 71-unconnected checkpoint. Downloaded Freerouting 2.5.0 from its official release; SHA-256 `f6f51bb02245e8e717f9359bd260cc9c5c0b1bc0acc8b7cb2cd5b8ffeb5de3c7`. Java 25 runs only in `fpga-daq-router:1`. All routing ran with Docker `--network none`, analytics/API/GUI disabled.
- Locked the existing differential pairs. Initial DSN export used default 0.2mm clearance after changing the board filename; explicitly supplied correct design constraints. A 0.1mm autorouting attempt connected most signals but produced 19 native hole-clearance errors. Increased router clearance to 0.15mm while preserving the actual KiCad 0.25mm hole-to-copper requirement; did not suppress DRC findings.
- Finished ground connections, local decoupling returns, four exposed-pad vias, a 0.8mm external input feed with parallel supply vias, and a separate 0.2mm low-current sideband supply branch. Manual routing attempts with crossings were rejected by DRC and corrected. Exact logs retained under `results/simulation_logs/pcb-*` and `autoroute-*`.
- Final native checks: **ERC 0, geometric DRC 0, unconnected 0, schematic parity 0; critical pin contracts PASS.** 400 trace/via objects; two filled continuous inner GND planes and no inner-layer signal tracks. Independent bidirectional geometric checks show all original pair routes preserved to <1um; centerline P/N skew is zero. This does not establish electrical skew/SI.
- Saved complete routing in `routing/tracks.json`, the original pair geometry, DSN/SES and local-completion scripts. `make pcb-rebuild` actually regenerated the native board and reran all checks successfully. KiCad Python's `GetDrawings()` binding failed under Python 3.14; switched the draft-label edit to the saved native text and reran successfully.
- `make pcb` now checks current native CAD instead of overwriting routing. `make pcb-rebuild` is the explicit source-regeneration command. Fabrication status remains REVIEW_REQUIRED, independent of automated CAD success.
- Exported nine actual Gerber layers plus PTH/NPTH Excellon drill files, maps and a drill report into `outputs/DRAFT_NOT_FOR_MANUFACTURE/`; verified Gerber/Excellon terminators and recorded hashes. Actual drill report: 73 plated holes, 2 unplated holes. These are draft structural exports, not CAM/DFM/manufacturing approval.
- Refreshed the actual schematic PDF and the revision 0.2 board SVG/native 3D render. Created revised five-slide `FPGA_DAQ_Portfolio_v2.pptx`, validated fonts/layout/native-chart/workbook/re-import, and exported the updated portfolio PDF. The old 71-unconnected presentation is retained only as an excluded build checkpoint.

### Final aggregate release check
- Ran `make all` after routing completion: **exit 0**. `results/full-check.json` records lint=0, test=0, synthesis=0, power=0, pcb=0, portfolio=0. Individual logs are `results/simulation_logs/final-*.log`; console summary is `all-stages-console.log`.
- This rerun again passed all 39 JUnit cases and 15 golden-matched scenarios, Yosys checks, original TI-model DC/AC/transient and nine DC corners, and native CAD checks. Re-executed `tools/power_evidence.py` on the final trace; post-startup envelope and PG assertions pass. Added this compact-evidence step to the normal `make power` target for future runs.
- Five revised slide previews and final verification/schematic PDF renders visually inspected. Final report has one page; portfolio has five pages; schematic has one A2 page. Presentation finalization reports no structural/layout findings; native PowerPoint opening is not claimed.
- Final artifact consistency check first used a wrong relative path to the original starter; fixed it to the resolved project parent, then verified both original tests byte-for-byte. The delivered PPTX matches its finalization SHA-256. Evidence consistency is recorded in `results/delivery-consistency.json`.
- Portable packaging validates every archived file against `MANIFEST.sha256` and excludes vendor models, raw large traces and build dependencies. No publication, purchase, fabrication or physical testing occurred.

## PCB engineering continuation - Rev 0.3 (2026-10-12)
User requested remaining component selection, power/thermal, mechanics and SI software review, then an updated delivery. No purchases, manufacture or GitHub push.

### Implemented and sources
- Read project rules, prior progress and handoff. Added isolated `fpga-daq-analysis:1` from the existing KiCad image, with SciPy1.16.3/Shapely2.1.2; no host installation. Exact Docker build log in `build/review-r03/docker-build.log`.
- Read official TI, Coilcraft, capacitor, TE and Wurth information and a manufacturer2242 card drawing. TDK curve-download access was403, so effective capacitance remains an acceptance gate instead of invented curve data. All30 electrical references now have candidate/selected MPNs with explicit qualification status in `BOM_selected.csv`.
- Updated inductor footprint to XAL4020, power MLCCs to1206, divider to31.6k/10k0.1%, H5 SMT support, board80x78, card22x42, four mounting holes, wide output branch, thermal copper/vias and return stitching. Shifted J3 to clear larger capacitor courtyards. Original pair centerlines unchanged.

### Failures discovered and fixed
- Larger caps intersected prior routing/courtyards; removed redundant ground segments, shifted input header and corrected route endpoints. Trial input-feed reroute collided with PWR_EN and was reverted. Omitted one unsafe thermal-via grid position, retaining eight valid EP vias.
- New return-via placement initially failed clearance/short checks. Repositioned it without moving HS traces. KiCad connectivity could silently reassign an offending GND via to a signal net; added an independent intended-net/position check against the routing snapshot. Final native checks pass.
- KiCad ZONE.GetLayerName() yielded misleading F.Cu names on inner/bottom zones; exported names using BOARD.GetLayerName(zone.GetLayer()). Actual filled polygons, including holes, feed SI/thermal scripts.
- Initial field-solver discretization fixed conductor potential at cell centers; corrected it to conductor surface and reran mesh/domain/energy checks. Replaced an unintended planarized coating with a conformal rectilinear mask; no calibrated commercial3D solver claim.
- Initial coarse thermal discretization had excessive mesh dependence. Added actual outer spreader geometry and refined1/0.5/0.25mm meshes. Later added0.25W copper heat and used125C copper-network resistance so assumed thermal losses cover its0.23677W stress result.
- Old-divider A-transient run was interrupted before completion, retained under build; not counted as passing. Final exact-divider run completed3.05ms. Observed35mV event excursion invalidated the initial20mV transient reserve; final budget uses40mV and explicitly FAILS.
- Mechanical audit of final drill report corrected an initial statement about H5: the official SMT support footprint DOES include3mm NPTH clearance. Final geometry documentation agrees with7NPTH export count.
- First evidence checker mistakenly expected48 thermal cases; actual grid is3x2x2x2=24. Corrected count without changing simulated results. The failed check log is retained. Initial3D render used unsupported `--rotate=...`; corrected to a separate quoted argument and successfully rendered. A deck launch from wrong working directory failed before execution; reran from build/portfolio.

### Executed commands and outcomes
- `make pcb-rebuild` with final return-via fix: PASS; `results/simulation_logs/pcb-r03-return-fix.log`.
- `make pcb-draft`: PASS; `pcb-draft-r03.log`. ERC0, DRC0, open0, parity0;424 tracks/vias;183 pads.9 Gerber layers plus92PTH/7NPTH Excellon, maps and export hashes. DRAFT only.
- `./tools/run-analysis python3 hardware/reference_pcie_adapter/analysis/export_geometry.py`, `geometry_checks.py`, `component_selection.py`: actual CAD geometry, plane projection, mechanical envelope and30-ref BOM PASS.
- `dc_network.py`: all126 four-of-nine output loading cases plus equal loads; KCL residual checked. Final worst drop59.397mV at125C; at75C improved119.326 to51.135mV. Graph excludes ground/contact/cable and idealizes pads.
- `field_solver.py`: actual sparse2D solves; nominal93.9369ohm, final mesh0.0529%, domain0.0905%, residual/energy/homogeneous tests PASS. Broad assumed corners83.29..106.13ohm FAIL target. `process_window.py` reproduces two tighter assumed corners90.01..98.11ohm; no manufacturer acceptance implied.
- `thermal.py`:24 cases; energy balance PASS, final mesh delta0.20384C. At1W regulator/0.25W inductor/0.25W copper/1.65W SSD coupling,40C ambient gives140.78C at h5 (FAIL) or111.67C at h10. Worst screened case160.78C. SSD/enclosure qualification open.
- `./tools/run python .../power_corners.py`:108 actual DC/AC runs,121 AC samples each. Finite AC response and DC window PASS, not phase-margin certification. Final composite voltage budget3.10821..3.48761V FAIL.
- `./tools/run bash -c 'cd hardware/reference_pcie_adapter/analysis; timeout 1800 ngspice -b adapter_transient.cir'`: official unmodified TI A model PASS.6,605,420 points;3.05ms. `transient_evidence.py`: time-weighted pre-event3.327270V, event3.292944..3.362127V, peak2.19410A, steady PG high and shutdown PG low. Raw trace retained locally under build; compact CSV/plot/JSON portable.
- `make pcb-engineering-check`: retained software-evidence assertions PASS while hardware gates remain FAIL_MARGIN/CONDITIONAL/REVIEW_REQUIRED. Full rerun command added as `make pcb-engineering`; its orchestrator was prepared, not represented as a separately completed aggregate rerun. All constituent numerical experiments above actually ran.
- Updated native schematic PDF/SVG/3D, five-page engineering review PDF, five-slide editable portfolio v3/PDF, verification report, README, evidence map and handoff. PDF pages and slide previews inspected. Full packaging verifies each archive member SHA256; final details in `results/package-summary.json`.

### Current disposition
Software/CAD engineering review complete within documented models. **Not fabrication ready.** Remaining voltage, thermal, process-tolerance, parts/cable/SSD, sequencing and assembly approvals are specific and recorded in `ENGINEERING_REVIEW.md` and `NEXT_SESSION.md`. Prior39-test RTL baseline and hypothetical power-tree evidence remain intact; no new full RTL run claimed because this continuation changed only the separate hardware reference and delivery artifacts.
- Final independent DC-solver fixtures passed: analytic single-track resistance/loss, two physical parallel traces and disconnected-graph rejection. These are3 model checks, not added to the39 RTL/model JUnit baseline. Current engineering summary has13 aggregate assertions.
- PDF helpers first ran in the simulator image without reportlab; reran successfully in the existing EDA image. A transient truncated-source read caused one checker SyntaxError; source AST validation and an immediate full checker rerun passed. No numerical results were altered to pass this tooling check.
- Final consistency verifies all recorded engineering input hashes, every draft export hash, unchanged starter hashes and the v3 PPTX finalizer hash. PDF page counts are5(review),5(portfolio),1(verification),1(schematic). The prior v2 deck is retained under excluded build history.

## Whole-system continuation and Rev0.3 corrective review - 2026-10-12

This entry supersedes the previous39-test/Rev0.3 checkpoint. User explicitly prioritized functioning end-to-end simulation after reviewing the exact PCB failures. No purchase, fabrication, physical testing or GitHub push.

### PCB failure isolation, corrections and actual reruns

- Preserved original engineering JSON/review in `results/review-r03-baseline/`. Added `analysis/review_margins.py`: unchanged3.135-3.465V,125C and81-99ohm criteria, signed before/after margins and every24-case thermal row. No requirement or original broad manufacturing tolerance was narrowed.
- Original failures: voltage lower3.108211V/-26.789mV, upper3.487610V/-22.610mV; thermal IDs3,11,17,18,19,23; high impedance106.125704ohm/-7.125704ohm and local wide fanout104.134617ohm/-5.134617ohm.
- Corrected actual native Rev0.3.1: five long SSD supply sections1.2->3mm, constrained local branch remains1.2mm, feeder1->1.3mm, expanded outer ground copper. Early wide-route trials caused PEWAKE/SW shorts and were rejected/corrected using KiCad DRC, not suppressed. Final `make pcb-rebuild` and `make pcb-draft` exit0; ERC/DRC/open/parity0, original pairs preserved,424 routing objects,183pads,4 filled zones,92PTH/7NPTH. Logs `pcb-r031-final.log`, `pcb-r031-draft.log`.
- Executed `dc_network.py`: all126 load distributions and KCL,125C worst2A drop59.397->37.161mV. Reran `power_corners.py`:108 DC/AC cases with121 finiteAC samples eachPASS. Composite voltage remains3.130447/-4.553mV and3.487610/-22.610mVFAIL. Ground/contact/dynamic/line-load allowances unchanged. `voltage_feasibility.py` proves divider-only interval does not overlap (required Rtop>=31658.44 vs<=31327.32ohm).
- Completed actual ngspice42 `adapter_loaded_corner.cir`:4.65V,1.232uH,75mohmDCR,16uF,18.580444mohm extracted output route,0.5A+1.5A event and EN shutdown;6,455,898 points over3.05ms. Load3.266353-3.342949V, +131.353/+122.051mV target margins; peakIL2.219306A; PG steady4.64845/shutdown0.06872VPASS. `loaded_transient_evidence.py` uses every solver point for extrema, true sampled preview CSV/plot. Semiconductor model remains nominal room-temperature, so no joint silicon/temperature/process qualification. Original40mV dynamic reserve retained (new regulator excursion25.013mV; older nominal~35mV).
- Reran thermal24 cases, mesh and energy checks. Five remaining failures IDs11,17,18,19,23:139.381,134.758,137.241,159.381,131.231C vs125C. Case3 improves125.778->124.381C but+0.619C is not robust hardware margin. Expanded spreader worst improvement1.397C; final mesh delta0.274C.
- Added/ran four actual heat-path sensitivity solves using10x10mm contact with covered-side convection removed. Original60C/h5/losses maintained. Totalpath60/40/25/15K/W gives127.490/119.164/109.325/99.493C. Coarse bisection49.79K/W is an unimplemented requirement, not installed hardware; SSD-region temperature still103.49C in15K/W case. No2A system rating.
- Added/ran8 field solves at four widths0.14..0.17mm using original etch+/-15um/h+/-10%/Er+/-0.2. None pass both bounds. No high-speed route change accepted; previous tighter-process result explicitly excluded as a resolution. Filled-plane geometry and mechanical checks rerun against final CAD; no unintended voids or planar card interference.
- Numerical evidence assertionsPASS while voltage/thermal/SI design gates remain FAIL/conditional. Full source files, exact commands, primary references, before/after tables and limitations in `hardware/reference_pcie_adapter/ENGINEERING_REVIEW.md`. Full-run orchestrator updated to include new stages; stages executed individually, not falsely described as a new aggregate `make pcb-engineering` run.

### End-to-end implementation and defects fixed

- Reproduced an RTL packet crossing4KiB at0x1ff8 with a real failing cocotb assertion; `results/system-audit/boundary-before-fix.xml` and `system-boundary-before-fix.log` preserve evidence. `rtl/tlp_packetizer.sv` now bounds payload by remaining words, MAX_WORDS and page remainder, with protocol assertion. Lint caught unused bits in the first function signature; narrowed the input to9 offset bits, no warning suppression.
- `rtl/dma_descriptor.sv` now validates the last addressed byte, accepting a valid8-byte record at2^64-8. Added full RTL regression for this case and cross-page transfers.
- Added bounded `HostRouter` tag ownership in `sim/host_model/receiver.py`; completion at link input can precede delayed host delivery without losing earlier contexts. Test holds host through multiple serialized RTL jobs and checks four contexts, delayed draining, independent golden records and tag release.
- `sim/pcie_transaction/transport.py` rejects out-of-range encoded fields consistently with ProtocolError and validates address/page ranges. It remains a custom transaction envelope, not wire-format PCIe or real LCRC.
- `tb/test_e2e_extended.py` executes4 tests at each of ring32/FIFO8/MAX4 and ring257/FIFO3/MAX8. New repeated-job stress contributes18 MATCH matrix scenarios. Combined with15 baseline,33 scenarios compare every host record; they are not extra JUnit cases.
- Found a critical fail-open verification wrapper: cocotb failure XML previously accompanied exit0. `tools/check_junit.py` and `rtl_tests.py` now remove stale target XML and reject missing/empty/failed/errored/skipped results. Added5 unit cases. Real intentionally failing fixture through `tools/test_failure_gate.py` returns1 and is retained outside production totals. Initial generated fixture used overriddenPYTHONPATH and failed import; corrected fixture placement and reran until failure was the intended assertion, not an import error.

### Actual complete-system verification and timing scope

- `make verify > results/simulation_logs/system-verify-final.log 2>&1`: **exit0**. Verilator5.040 lint, **39 pytest +24 cocotb=63PASS**,0 production failures/skips, generic Yosys0.33 synthesis pass. Production XML lives directly under `results/`; historical/intentional failures under `results/system-audit/` are excluded.
- `./tools/run python tools/timing_audit.py`: actual flattened netlist check,0 combinational loops,1447 genericFF on topclk, longest FF-excluded combinational path42 genericcells. Generic topology is not ns delay. No device/speed grade/vendor delay models/placed design, so physical timing analysis remainsPARTIAL and device STA blocked. Added unapproved100MHz SDC example and `make timing`.
- `docs/SYSTEM_AUDIT.md` and `results/system-audit/status.json` classify all10 requested areas with source files, actual commands/results and remaining scope. Functional RTL/FIFO/DDR abstraction/DMA/customPCIeTLM/E2E/cocotb areCOMPLETED for the bounded simulation contract; synthesis+timing, full power qualification and GitHub portfolio publication remainPARTIAL.

### Delivery and reproducibility

- Prepared read-only GitHub workflow with verified official action commit pins. Local `make verify` and timing commands pass; Ruby/Psych parses workflow syntax and verifies read-only permission/pin structure. Python YAML package was unavailable, so no host install was made. No remote Actions run or GitHub repository/push is claimed.
- Updated source-backed verification PDF, five-page exact PCB corrective review, five-slide editable v4 portfolio/PDF, current native render/SVG/schematic and draft review exports. Original layout/fonts retained; all updated review pages, verification page, schematic and slide previews visually inspected. Artifact finalizer reports no structure/layout/font/chart/reimport issues. First deck update used wrongcwd; old builder refused existing output; corrected cwd/source and generated separatev4 successfully.
- Updated README, evidence index, interface/verification contracts, resume/slide candidates, `NEXT_SESSION.md` and this log. Earlier source39-test evidence, waveforms and `full-check.json` remain historical, not mislabeled current runs. Old deck retained under excluded build history.
- Final integrity script verifies63passing cases/33MATCH scenarios, current RTL/timing and engineering hashes, intentional-failure gate, unchanged Week1 starter, native draft export hashes, current five-slidePPTX hash and PDF page counts. Portable ZIP is rebuilt with every member verified against SHA256 manifest; details in `results/package-summary.json`.

### Remaining work / blockers

Exact power, thermal, SI, component/cable/SSD/mechanical/assembly risks remain in the updated review. A new FPGA target/toolchain is needed for real deviceSTA/DDRPHY/PCIe endpoint work; current design is functioning transaction-model simulation. Qualified joint electrical/thermal/process inputs are needed before a defensible further hardware revision. Physical validation and fabrication remain deferred; publication awaits explicit approval. No unexecuted or hypothetical test is markedPASS.

## Independent verification and portfolio release preparation

This entry supersedes earlier nominal-copper/current-release interpretations. It does not supersede the immutable historical data. No production RTL or functional-model behavior was changed; current review prioritizes independent verification and truthful portfolio scope.

### Executed verification and real infrastructure corrections

- Baseline `make verify` exit0:39pytest+24cocotb=63PASS,0skips;33MATCH matrix rows. Exact stdout/source hashes/returncode: `results/release-audit/baseline-verify.{json,log}`.
- Source-only `clean-initial-verify` genuinely failed exit2 because `results/system-audit/` was missing. Fixed runner and standalone extended-test output initialization. Chart/CAD/pipeline output initialization and historical comparison inputs were also made explicit. Corrected `clean-verify` exits0.
- Built `fpga-daq-tools:release-audit` with `docker build --no-cache` from the recorded Dockerfile, actual build exit0. Verilator5.040/cocotb2.0.0/pytest8.4.2/Yosys0.33 versions and image IDs retained. A separate empty-output/source-only workspace passes `fresh-clean-verify` and timing.
- Four supplemental oracle checks use independent CRC bit arithmetic/manual packing and hand-calculated record vectors. Six isolated mutations are detected by actual runtime assertion/failedXML and nonzero exits: sample stride, saturation, ring wrap, page boundary, CRC checking and memory bounds. Counts are not added to63.
- The boundary mutant exposed a shutdown hang after the intended Verilator assertion at285ns. Initial manual termination is retained as historical mutation evidence. Added a180-second runner deadline, tested at15seconds in the isolated mutation (exit124 with REGRESSION_TIMEOUT). Five other mutations fail normally. A timeout without runtime failure cannot count as detection. Final complete clean63/33and timing reruns after the fix pass: `final-clean-verify`, `final-clean-timing`, `mutation-final`. No RTL features were added.
- Actual generic synthesis/structural analysis:0latches/combination loops,1447genericFF,oneclock,42cell topological longest path. Device delays/setup/hold/Fmax remainBLOCKED. Test independence/edge gaps explicitly reviewed in `docs/VERIFICATION_REVIEW.md`.

### PCB independent review with unchanged requirements

- Voltage terms decomposed numerically: full-load lower3.130447188V/-4.552812mV and light-loadPSM upper3.487610442V/-22.610442mV. Low copper drop budget permits32.608077mV versus37.160889mV actual model. PWMhigh3.454152860V has+10.847140mV; PSM feedback leaves22.389558mV against45mV allocated dynamics/line-load. Divider-only interval remains empty. No reserve/accuracy tolerance reduced.
- TI PSM table usesCout22uF; the16uF effective-cap stress is outside that explicit condition. The joint silicon/process/temp/mode/MLCC envelope remains unqualified. Published references are linked in current independent review; modeled outputs are not measurements.
- Original five failing thermal cases independently rerun at1/.5/.25mm grid; all remainfailed. Uniform-source exact solution and linear superposition error below1e-8C. Worst original hotspot decomposed into52.567C regulator,22.379C SSDcoupling,8.536C inductor,6.753C copper boardrise plus7.459C packagepath.
- Corrected35umthermal versus30umDC copper assumption mismatch. All24 thermal cases at30um/.5mm; sixfail IDs3,11,17,18,19,23. Fine worst160.302515C/-35.302515C; case3fine125.302515C/-0.302515C. Original159.381C is not sustainable predicted operation; linear extrapolation above125Crecommended/150Cabsolute and near160Ctypicalshutdown indicates designrejection. Unvalidated2Dsheet/heat/cooling/package/SSD assumptions remain.
- Extended finite-volume solver preserves original rectangular baseline exactly and adds tapered conductor, independent mask thickness/Er and optional nearby ground sensitivity.31solves: seven stack/width/gap candidates under originaletch+/-15um/h+/-10%/Er+/-0.2 plus copper/mask/profile sweeps.7628h.2104/Er4.4/w.30/g.20 initially81.830..97.575ohm, then79.257411ohm under publishedprofile/40.64umCu lowcorner:FAIL -1.742589ohm. No candidate adopted or tolerance narrowed.
- Actual outerGND minimum distance8.605mm for inspectedsignal segments:0.15/0.30mmcoplanar ground is hypothetical sensitivity, not claimedactualgeometry. Currentbroad106.125704ohm and localwidegap104.134617ohm remainfailed. Fullchannel3Dloss/connector/FFC/eye validation absent.
- Clean native board regeneration and DRAFT export executed withKiCad9.0.8, zeroERC/DRC/open/parity. Source-only independent studies pass numerical checks while preserving voltage/thermal/SIfailure. The full source-only108DC/AC/two-transient chain is recorded separately; final aggregate state is in `results/release-audit/reproduction-summary.json`, not inferred from earlier traces.

### Current release artifacts and limits

- Concise GitHub README separates verifiedRTL from independentPi5carrier reference. Added architecture,33-scenario benchmark and actualVCD excerpt inSVG/PNG, fullcompressedVCD andprovenance. All visuals inspected.
- Current four-page `output/pdf/Independent_Release_Review.pdf` generated with portableReportLab inEDAimage; allpages rendered and inspected. It reports failedgates and generic-vs-device timing clearly. Source-only regeneration of waveform/assets/PDF also passes (`clean-assets-wave`, `clean-assets`, `clean-portfolio`).
- Old v4PPTX/threecheckpointPDFs remain locally with historicalscope, excluded from thecurrentportablearchive. Their originalCodexartifact-runtime dependency is not presented as clean-checkout portability.
- Updated `SYSTEM_AUDIT.md`, `VERIFICATION_REVIEW.md`, `REPRODUCING.md`, `RESUME_BULLETS.md`, requirementsmatrix andhandoff. Finalintegrity checks reconstruct63/33counts, sixmutations, sourceidentity, currentmodelchecks andcurrentPDF/VCDhashes. Source-only regeneration scope and exactcommands/returncodes retained.
- Publication recommendation: ready as anRTLsimulation portfolio withlimitations visible;PCBdesign-onlyFAIL. No actualdeviceimplementation/timing, physicalmeasurement, fabrication, purchases, GitHubpush orremoteCIrun occurred.

### Final source-only PCB closure and report repair

- The source-only full chain executed108DC/AC cases and both complete3.05ms traces:6,605,420nominal and6,455,898loaded points. All numerical criteria remain consistent with retained evidence. Design voltage/thermal/SI FAILs are unchanged.
- The aggregate returned2 only at report-Markdown: it expected `## Reproduction` in its own prior generated document, which instead used `## Actual commands and logs`. Replaced self-parsing with independent `analysis/PRIMARY_REFERENCES.md`. This is a real repeatability fix, not relaxed acceptance.
- Added a narrowly scoped report-only recovery that validates every upstream engineering input SHA256 and permits only report-source changes. Reused the completed numerical data after that check; both affected report stages pass. A second Markdown generation also passes. All23 stages now have actual passing execution evidence; initial failure and recovery are retained under `results/release-audit/clean-PCB-evidence/`. Overall reproduction is PASS_AFTER_REPORT_REPAIR, not a falsely reported uninterrupted exit0.
- Clean-source independent studies, waveform/assets and current portablePDF also pass. Core fresh-image final63/33and synthesis checks remain passing. Final checker preserves requirementFAIL/BLOCKED values while confirming evidence integrity.

### Archive preflight

The preparedZIP was actually extracted with `unzip`; `make verify` from that extracted project passed all63tests/33scenarios and generic synthesis. Its release-integrity checker also returned0. Core RTL/models/tests/runner/Makefile match the final worktree byteforbyte. Final packaging adds these receipts and documentation updates, then revalidates every manifest member. The final archive hash/size is stored in `results/package-summary.json`; no GitHubpush occurred.


## Final professional portfolio curation

- Replaced the long entry page with a concise recruiter-facing README: architecture, actual waveform, 63-test/33-scenario results and real debugging findings appear first. Explicitly labeled DDR3 behavioral and custom PCIe transaction-level models. Added a clean portfolio summary and scoped resume bullets. Generic synthesis is separate from device-specific timing closure.
- Froze PCB Rev 0.3.1 as a separate Pi carrier design study. Every compact voltage, thermal and impedance result was copied byte-for-byte into `evidence/pcb/engineering/`; all FAILs remain visible. No requirements, CAD, electrical/thermal inputs or functional RTL/model behavior changed. Hash check confirms 23 core/test and 49 board/provenance source files unchanged.
- Created explicit proposed Git tracking manifest and generated-output ignore rules. Kept source, current figures, actual logs/versions/JUnit, compact synthesis, original debugging failures, mutation evidence and full prior PCB stage logs. Excluded build caches, repetitive generated history, raw traces, large netlists, old slide/PDF drafts and manufacturing outputs from the proposed set. No original evidence was deleted. The previous full delivery ZIP remains byte-identical (SHA256 `0e795c07042ba4779cbbd0b4df5512ca7fb287e07a1945d0cbf97a1b7d50d2c8`).
- Created an isolated local Git repository from the manifest and cloned it into an empty directory. First clean clone passed production verification/timing/oracles, then the supplemental failure probe hit a missing `results/simulation_logs/` directory. Original command/commit/input hashes, traceback and probe XML are retained under `evidence/debug/clean-probe-directory-failure/`. Fixed only explicit directory creation in that probe, with no test expectation change.
- A second clean clone passed all 63 tests / 33 scenarios, generic synthesis/structural timing, four oracle fixtures, the actual failing-fixture gate and six isolated mutations. Mutation assertion-plus-watchdog disclosure remains. Actual VCD/benchmark/architecture assets were regenerated. Visual review caught a color-classification error after renaming model boxes; fixed the figure generator so simulation-only DDR3/PCIe blocks remain green. No engineering model was changed.
- Publication artifacts and local paths are audited by `tools/portfolio_check.py`; `tools/portfolio_release.py` creates non-destructive manifest-only snapshots and archives with verified SHA256 members. Original evidence map preserves source paths/checksums. The final clean run and packaged-set checks are indexed by `evidence/core/` and `release/RELEASE_SUMMARY.md`.
- Recommendation: ready for publication as a functional RTL simulation portfolio with a separate design study. Device STA, physical DDR3/PCIe, measured performance, manufacturing release and PCB qualification remain unclaimed/blocked. No purchases, fabrication, physical validation, remote CI execution or GitHub push occurred.

Final frozen-source checkout `85d4c3222280431d91c0e911b1357893a964564a` completed all 14 setup/verification commands with exit 0, including production regression, generic timing, oracles, failure probe, six mutations and integrity check. The tracked checkout remained clean. Final packaging adds evidence/notes only; executable inputs match the tested snapshot byte-for-byte.

## Public portfolio publication authorization

The owner explicitly approved pushing this release to GitHub as a public portfolio while retaining every PCB FAIL and unverified limitation. Prepared a separate publication copy from the 344-file tracking manifest; kept the original engineering workspace, ZIP and evidence intact. Target is `searchyourmind/fpga-highspeed-daq`. Only publication-status documentation changed; RTL, models, tests, native CAD and numerical evidence remain unchanged. Rechecked the portfolio evidence/links and screened candidate files for private-key/access-token patterns before staging. Authentication and remote outcomes are recorded separately rather than inferred from local tests.
