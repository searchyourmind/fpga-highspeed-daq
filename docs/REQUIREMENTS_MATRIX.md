# Final pass/fail requirements matrix

Software execution success does not override a failed design requirement. These are simulation and design-study results, not physical measurements.

| ID | Requirement | Status | Actual result / margin | Evidence |
|---|---|---|---|---|
| RTL-01 | Lint and production regression | **PASS** | 63: 39 pytest + 24 cocotb; 0 failures/skips | [Clean log](../evidence/core/verify.log), [JUnit](../evidence/core/junit/) |
| E2E-01 | Every host record matches reference | **PASS** | 33/33 MATCH scenarios within the 63 tests | [Scenario data](../evidence/core/scenarios/) |
| VER-01 | Independent oracle / selected defect detection | **PASS** | Four fixtures; six injected defects detected; boundary assertion precedes watchdog 124 | [Review](VERIFICATION_REVIEW.md) |
| REP-01 | Final clean Git checkout | **PASS** | Isolated local commit/clone, fresh output directories; regression and structural checks return 0 | [Commands and source hashes](../evidence/core/commands.json) |
| SYN-01 | Generic synthesis / structural checks | **PASS** | 1,447 generic FF, no latches/loops; 42-cell topological path | [Synthesis evidence](../evidence/core/synthesis/) |
| STA-01 | Device timing closure | **BLOCKED** | No FPGA part/speed grade, vendor timing model or placed/routed netlist; no slack/Fmax | [Scope](../synthesis/README.md) |
| PHY-01 | Physical DDR3 / PCIe operation | **NOT TESTED** | Behavioral DDR3 and custom PCIe transaction-level model only | [Contracts](interface_contracts.md) |
| CAD-01 | Native CAD connectivity/geometry | **PASS** | Prior source rebuild: ERC/DRC/unconnected/parity = 0 | [Native checks](../evidence/pcb/check-summary.json) |
| PWR-01 | Composite rail stays 3.135–3.465 V | **FAIL** | 3.130447188–3.487610442 V; **−4.552812 / −22.610442 mV** | [All voltage terms](../evidence/pcb/engineering/voltage-root-cause.json) |
| THM-01 | Every screened Tj ≤125 °C | **FAIL** | 30 µm copper: **6/24 fail**; fine worst 160.302515 °C, **−35.302515 °C**. New case 3: 125.302515 °C, **−0.302515 °C** | [All thermal cases](../evidence/pcb/engineering/thermal-independent-review.json) |
| SI-01 | Broad impedance 81–99 Ω | **FAIL** | Current high 106.125704 Ω, **−7.125704 Ω**; local fanout 104.134617 Ω, **−5.134617 Ω** | [Original corners](../evidence/pcb/engineering/field-solver.json) |
| SI-02 | Candidate stack/profile qualification | **FAIL** | Expanded 7628 candidate low 79.257411 Ω, **−1.742589 Ω**; not adopted | [31 sensitivity solves](../evidence/pcb/engineering/si-independent-review.json) |
| MECH-01 | Documented planar envelope/reference checks | **PASS** | 2D envelope and return geometry only; no assembly qualification | [Mechanical checks](../evidence/pcb/engineering/mechanical.json) |
| QUAL-01 | Parts/cable/SSD/cooling/process qualification | **BLOCKED** | Effective MLCC, hot limits, real mating/3D assembly, heat exit and full channel unresolved | [Independent review](../hardware/reference_pcie_adapter/INDEPENDENT_REVIEW.md) |
| REP-02 | Prior full PCB numerical reproduction | **PASS AFTER REPAIR** | Original aggregate exit 2 retained; 23 stages complete after hash-validated report-only repair. Design FAILs remain | [Failure and recovery](../evidence/review/pcb-reproduction/) |
| ART-01 | Reproducible source, visuals and evidence | **PASS** | Current PNG/SVG/real VCD, logs and source; review PDF retained from prior clean regeneration | [Artifacts](../portfolio/README.md) |
| PUB-01 | GitHub publication / remote CI | **APPROVED / SEE LIVE CI** | Owner authorized public publication; local verification does not imply remote CI success | [Release summary](../release/RELEASE_SUMMARY.md) |
| HW-01 | Hardware validation | **DEFERRED** | No fabrication, purchase, physical operation or measurement | [Handoff](../NEXT_SESSION.md) |

Thermal estimates beyond absolute maximum/near shutdown reject the assumed design; they are not sustainable operating predictions. Original 35 µm thermal results (five failures, 159.381092 °C maximum) remain in the preserved evidence. Requirements and process tolerances were not relaxed. [Exact commands](REPRODUCING.md)
