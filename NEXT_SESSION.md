# Portfolio checkpoint

Read `README.md`, `release/RELEASE_SUMMARY.md`, `docs/SYSTEM_AUDIT.md`, `docs/REQUIREMENTS_MATRIX.md` and `docs/REPRODUCING.md` first.

## Current scope

The professional portfolio is ready for publication as an RTL functional-simulation project plus a separate PCB design study. The owner explicitly authorized publication as a public GitHub portfolio. Target: https://github.com/searchyourmind/fpga-highspeed-daq. Physical validation, fabrication and purchases remain unauthorized. The evidence below describes the pre-publication local verification; consult GitHub for publication/CI state.

- 11 RTL modules; DDR3 **behavioral model**; custom PCIe **transaction-level model**. One descriptor, one clock, capture followed by readback, stallable synthetic source.
- Production tests: **63 PASS** (39 pytest + 24 cocotb), zero failures/skips; **33 MATCH** scenario rows inside those tests.
- Generic synthesis: no latches/loops, 1,447 generic FF, 42-cell topological path. Device implementation/STA remains BLOCKED; no target/speed grade, placed/routed netlist, slack or Fmax.
- Separate Pi 5 carrier Rev 0.3.1 is frozen. Voltage FAIL at 3.130447188–3.487610442 V; corrected thermal 6/24 FAIL, fine worst 160.302515 °C; broad impedance high 106.125704 Ω and expanded candidate low 79.257411 Ω remain FAIL. Requirements were not relaxed.
- All engineering inputs and selected historical evidence are hash checked. Original raw evidence, older slides/PDFs, full archive and build history remain local. The explicit proposed tracking list is `release/tracked-files.txt`; immutable public evidence is under `evidence/`.

## Finalization defect and evidence

A real clean Git clone passed the 63-case regression/synthesis, then the supplemental failure-probe wrapper failed because its log directory did not exist. Fixed only its output-directory initialization. Original traceback, command record, source snapshot and intentional failure XML remain under `evidence/debug/clean-probe-directory-failure/`. Subsequent clean runs must include the probe as well as production tests; never count the intentional failed case among the 63 passes.

Actual local Git commit/clone commands, versions, image IDs, source hashes and return codes are under `evidence/core/`. The final run reused the core Docker image that was built without cache in the preceding review; EDA/analysis were not rebuilt in this finalization. Remote x86 CI is separate from these local receipts; consult GitHub Actions. Bit-identical future network builds remain unverified.

## Reproduction

```sh
make tools
make verify
make timing
./tools/run python tools/independence_audit.py
./tools/run python tools/test_failure_gate.py
python3 tools/mutation_audit.py
python3 tools/portfolio_check.py --generated
```

For a new isolated local Git verification (existing destination refused):

```sh
python3 tools/clean_portfolio_verify.py build/portfolio-next-check --check
```

This defaults to the existing `fpga-daq-tools:release-audit` image. Set `DAQ_TOOLS_IMAGE=fpga-daq-tools:1` to use the image produced by `make tools`.

`WAVES=1 make e2e; make release-assets` regenerates real figures. Optional PCB commands and the historical PASS_AFTER_REPORT_REPAIR distinction are in `docs/REPRODUCING.md`; no new PCB analysis/redesign is needed for portfolio publication. Historical `tools/release_audit.py`, `system_audit.py` and `package.py` describe the larger earlier checkpoint and are intentionally outside the proposed Git set. Use `portfolio_check.py` and `portfolio_release.py` for this release.

## Remaining gates

1. Public GitHub publication to `searchyourmind/fpga-highspeed-daq` is now authorized. Preserve the FAILs, model scope and unverified hardware limits in all publication updates.
2. Device timing/physical DDR/PCIe need a separately authorized hardware target and toolchain.
3. PCB needs qualified component/process/cable/SSD/cooling/assembly inputs and retained voltage/thermal/SI failures closed before any hardware-release claim.
4. No feature additions or PCB redesign unless the user changes scope or a genuine defect is found. No teaching session requested yet.
