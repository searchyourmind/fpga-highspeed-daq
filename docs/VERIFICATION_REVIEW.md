# Independent verification review

Scope: independently rerun and challenge the current implementation, without adding new functional features. "Independent" here means a fresh workspace, independent expected-value arithmetic, negative/mutation tests and source/log review; it does not mean a separate organization or formally verified oracle.

## Counts and evidence

Production: 39 pytest cases and 24 cocotb cases, all PASS, no skips. The 33 E2E matrix rows (15 baseline + 18 extended) are exercised within these 63 cases. Supplemental CRC fixtures, mutation runs, CAD checks and thermal solves are not added to that count.

- Current actual Git clone: [core logs, receipts and XML](../evidence/core/).
- Prior clean-directory failure: [clean-initial-verify.log](../evidence/review/clean-initial-verify.log), exit 2; corrected final [verify](../evidence/review/final-clean-verify.log) and [timing](../evidence/review/final-clean-timing.log) exit 0.
- [Actual no-cache image build](../evidence/review/fresh-tool-image.log) and [versions](../evidence/review/fresh-versions.log).
- [Six mutation cases](../evidence/review/mutation-summary.json) and [four independent oracle fixtures](../evidence/review/independent-oracles.json).
- Production XML is in `evidence/core/junit/`; original and intentional failures are in `evidence/debug/` and `evidence/review/`. They are never counted as passing production cases.

Each command receipt stores actual return code, elapsed time and source hashes. All production RTL and simulation model hashes match the pre-review baseline; only output initialization and verification/reproduction tooling changed.

## Independence and sensitivity

`tb/reference_model.py` computes packed records from integer sequence/frame/gain arithmetic without reading DUT signals or memory to derive expected payload. Host data is compared word by word. Memory and custom-link classes also have unit tests for delays, bounds, atomic failures, corruption and ownership. Shared specification constants still permit common-mode misunderstandings.

`tools/independence_audit.py` adds a bitwise CRC32 implementation, the standard `123456789` check, an explicit manually packed header/payload and fixed manually calculated record vectors. It does not reuse Packet serialization or the reference model to construct those expected values. Four supplemental checks pass; see `independent-oracles.json`.

`tools/mutation_audit.py` copies sources into isolated build workspaces and injects one defect at a time. Six defects are detected: sample stride, saturation endpoint, ring wrap, page-boundary split, CRC rejection disabled and memory bounds weakened. Detection requires real runtime assertion/failed JUnit plus nonzero exit; build/import errors alone are rejected. The page-boundary mutation triggers the RTL assertion at 285 ns; its simulator shutdown stalls, so the bounded watchdog terminates it. The mutation receipt discloses this; it is not described as a normal regression exit or standalone timeout detection. Five other mutations fail normally. Production sources remain unchanged.

## Edge-case review

| Area | Exercised | Remaining scope gaps |
|---|---|---|
| FIFO | Depth 1/3/8/16, simultaneous push/pop, empty/full, stalls, reset | No asynchronous clock crossing; not exhaustive every depth/width |
| Streaming | Gain 0/1/255 and saturation, frame metadata, payload stability | Sequence/frame counter rollover and every frame length not exhaustively covered |
| Descriptor/DMA | Ownership, invalid ranges, wrap, reset/error recovery, final 64-bit address, multiple jobs | Full 16-bit maximum length and every ring/parameter combination not swept; no concurrent capture/readback |
| Packets/host | 4 KiB boundary at 0x1ff8, custom CRC/errors, delayed delivery, multiple retained tags | MAX_WORDS=512 and all payload/page alignments not exhaustively swept; no real PCIe credits/replay/TLPs |
| Memory | Bursts, bounded addresses, latency/stalls, abstract refresh and atomic errors | No JEDEC timings, banks, PHY or controller calibration |
| Test infrastructure | Missing/empty/failing/error/skipped XML rejected, actual failing fixture, clean directories | No formal proof, line/toggle coverage percentage or hardware X/metastability assurance |

These gaps limit claims; none is evidence of a current defect requiring new features. Deterministic seeds support reproducibility, not a statistical reliability claim. A stallable synthetic source cannot establish losslessness for a fixed-rate physical ADC.

## Synthesis and timing distinction

`tools/synthesize.py` actually executes Yosys and saves stdout; `tools/timing_audit.py` checks the generated generic netlist, latches, combinational loops and clock domains. The current result is 1,447 generic flip-flops and a 42-cell maximum topological combinational path. Source hashes are stored in `synthesis/reports/timing-audit.json`.

No device-specific mapping, placement/routing, extracted delays, setup/hold slack or Fmax calculation has run. `synthesis/constraints/example.sdc` is an illustrative 100 MHz scenario only. Device STA is BLOCKED until a device/speed grade, clock/pin constraints, vendor IP and target toolchain are selected. A passing functional simulation does not resolve that blocker.

## Reproduction defect corrected

The initial clean run failed because `tb/test_e2e_extended.py` wrote `results/system-audit/extended-ring-32.json` into a nonexistent directory. The top-level working folder had hidden this dependency. The runner now initializes output directories and the standalone test writer is safe too. A clean chart writer and CAD checker received the same directory initialization. No test expectation or requirement was relaxed.

The no-cache image build is retained separately from the previous tools image. Core versions remain Verilator 5.040, cocotb 2.0.0, pytest 8.4.2 and Yosys 0.33. All resolved dependencies and image IDs are in release receipts; these are not falsely described as cryptographically locked future builds.

## Assertion-shutdown defect and bounded runner

The page-boundary mutation demonstrated a real infrastructure failure: Verilator reported the intended assertion at285ns and emitted failed XML, then cocotb shutdown stalled. `tools/rtl_tests.py` now has a180-second per-invocation wall deadline (configurable viaDAQ_SIM_TIMEOUT_S) that exits124 with REGRESSION_TIMEOUT. The isolated mutation uses15seconds and verifies the assertion plus nonzero termination. A timeout alone is still not counted as mutation detection. Final clean63-test/33-scenario and timing reruns after this correction are `final-clean-verify` and `final-clean-timing`; actual clean-source hashes are in `final-clean-inputs.json` and those receipts. Production RTL/models remain unchanged.

## Final portfolio clean-checkout finding

The final curation pass used a real isolated Git commit/clone. Production regression, generic synthesis and oracle checks passed. The supplemental `tools/test_failure_gate.py` then failed because `results/simulation_logs/` did not exist. The intentional cocotb failure ran, but its wrapper could not save the log. [Original failing command and traceback](../evidence/debug/clean-probe-directory-failure/failure-gate.log) are retained with the input Git commit/hashes and probe XML.

The fix initializes the probe's log and evidence directories explicitly. It changes no RTL, functional model, test expectation or requirement. A subsequent clean clone reruns the full suite and the real failing probe; the probe verifier passes only after confirming the underlying runner returned nonzero. The original failed clean run is not relabeled PASS.
