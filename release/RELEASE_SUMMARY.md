# Portfolio release summary

**Publication recommendation: READY for an explicitly scoped RTL simulation portfolio, with the separate PCB shown as a design study.** The owner has authorized public publication at [github.com/searchyourmind/fpga-highspeed-daq](https://github.com/searchyourmind/fpga-highspeed-daq). Hardware release remains blocked. Local clean-checkout results below precede publication; live remote CI status is separate.

## Repository structure

```text
README.md                     Recruiter entry: architecture, waveforms, results, debugging
rtl/                          11 SystemVerilog modules
sim/                          DDR3 behavioral model, PCIe transaction model, host model
tb/ + tests/                  cocotb tests, independent record oracle, pytest tests
synthesis/                    Generic synthesis scripts and illustrative constraints
tools/ + .github/             Docker wrappers, checks, regeneration, local/CI commands
docs/                         Contracts, verification review, audit, resume bullets
portfolio/                    Summary, actual figures, independent review PDF
hardware/                     Separate Pi carrier study and hypothetical power tree
evidence/core/                Clean-checkout test/synthesis/version evidence
evidence/debug/ + review/     Original failures and independent review evidence
evidence/pcb/                 Frozen numeric cases, FAILs and native CAD views
provenance/                   Starter ZIP and pre-correction PCB data
release/                      Exact proposed tracking list and release policy
NEXT_SESSION.md               Handoff and boundaries
```

## Verification

Final commands are recorded with stdout, tool versions, source hashes and actual exit codes in [core evidence](../evidence/core/). The proposed files were committed only in an isolated local Git repository and cloned to an empty build directory. The original workspace and full delivery archive are preserved.

- Production regression: **63 PASS = 39 pytest + 24 cocotb**, zero failures or skips.
- End-to-end: **33 MATCH = 15 baseline + 18 extended** matrix scenarios inside those tests.
- Generic synthesis: **1,447 generic flip-flops**, no inferred latches or combinational loops, **42-cell** longest topological path.
- Supplemental checks: four independent oracle fixtures, fail-closed JUnit probe and six selected mutations detected; these are not added to the production count. One mutation requires watchdog exit 124 after the actual boundary assertion.
- Architecture/waveform/benchmark figures derive from real source/VCD/scenario data. No measured bandwidth, board temperature or timing slack is claimed.
- Original RTL, functional models and PCB engineering inputs remain unchanged in this finalization. Documentation, presentation, release curation and a real clean-checkout log-directory fix in the supplemental failure probe are the only changes.

Final isolated test commit: `85d4c3222280431d91c0e911b1357893a964564a`. All 14 recorded setup/verification commands returned 0, including the final integrity check; `git status --porcelain` was empty afterward. The final package adds these receipts and release notes to that snapshot. Every executable reproduction input remains byte-identical to the tested checkout; the archive is checked separately by member SHA256.

## Retained blockers and limitations

| Gate | Disposition |
|---|---|
| Device-specific implementation/timing | **BLOCKED**: no selected FPGA/speed grade, vendor IP, placed/routed design or STA |
| DDR3 / PCIe hardware | **NOT TESTED**: DDR3 behavioral model and custom PCIe transaction-level model only |
| PCB voltage | **FAIL**: 3.130447188–3.487610442 V vs 3.135–3.465 V |
| PCB thermal | **FAIL**: 6/24 minimum-copper cases; fine worst 160.302515 °C vs 125 °C |
| PCB impedance | **FAIL**: current broad corner 106.125704 Ω vs 99 Ω; candidate low 79.257411 Ω vs 81 Ω |
| Physical qualification | **BLOCKED**: parts/cable/SSD/cooling/process/assembly/full-channel validation unresolved |
| Remote CI | Local evidence covers Linux ARM64; see [live workflow runs](https://github.com/searchyourmind/fpga-highspeed-daq/actions) for the separate GitHub x86 result |
| Future bit-identical builds | **NOT GUARANTEED**: apt/base/transitive inputs are not fully locked |
| Publication | **APPROVED** by the owner for a public simulation portfolio; see [repository](https://github.com/searchyourmind/fpga-highspeed-daq) |

These hardware limitations do not block publication with the stated simulation/design-study scope. They do block any claim of a functioning physical DAQ board, qualified PCB, real DDR/PCIe interface or device timing closure. No additional feature work or PCB redesign is necessary for the proposed portfolio release.

[Reproduction commands](../docs/REPRODUCING.md) · [Full matrix](../docs/REQUIREMENTS_MATRIX.md) · [Resume bullets](../docs/RESUME_BULLETS.md) · [Tracking policy](TRACKING_POLICY.md)
