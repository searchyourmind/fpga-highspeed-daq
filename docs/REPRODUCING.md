# Reproduce the portfolio

Host requirements: Docker, Make, Python 3 and Git. Run from the repository root. Published evidence is immutable under `evidence/`; reruns write ignored `results/`, `build/` and `synthesis/reports/`. A passing tool process does not change a failed PCB requirement.

## Functional simulation and generic synthesis

```sh
make tools
make verify
make timing
./tools/run python tools/independence_audit.py
./tools/run python tools/test_failure_gate.py
python3 tools/mutation_audit.py
WAVES=1 make e2e
make release-assets
python3 tools/portfolio_check.py --generated
```

Expected: **39 pytest + 24 cocotb = 63 PASS**, zero failures/skips; **15 + 18 = 33 MATCH** matrix scenarios within those tests. The supplemental oracle, negative and six mutation checks are not added to 63. The deliberately failing fixture is expected to exit nonzero internally; its verifier exits zero only when that failure propagates. One assertion-aborted mutation uses a 15-second watchdog; an assertion/failed XML must precede timeout to count as detection.

`make verify` includes lint and generic synthesis. `make timing` checks generic topology, not target setup/hold timing. Waveforms and benchmark figures use actual VCD/JSON output; no physical time, bandwidth or power is inferred. `make release-assets` regenerates the presentation assets; it intentionally changes tracked figure files. Rerunning tests and synthesis alone leaves the tracked source/evidence unchanged.

## Actual clean Git checkout

The final release was staged from [the explicit tracking list](../release/tracked-files.txt), committed in an isolated **local** repository, then cloned to an empty directory. No original `results/`, `build/`, synthesized netlist or vendor model was supplied. Actual commands, commit, source hashes, Docker image ID, return codes and stdout are retained in [core evidence](../evidence/core/). The commands above passed on that checkout. GitHub Actions is prepared; publication was subsequently authorized. See the repository Actions page for the independent remote result.

To repeat the local checkout procedure without publishing:

```sh
python3 tools/portfolio_release.py snapshot /tmp/daq-source
# /tmp/daq-source and /tmp/daq-clean must not already exist.
git -C /tmp/daq-source init -b portfolio-candidate
git -C /tmp/daq-source add --pathspec-from-file=release/tracked-files.txt
git -C /tmp/daq-source -c user.name='Local verification' -c user.email='verification@example.invalid' commit -m 'Portfolio verification snapshot'
git clone --local /tmp/daq-source /tmp/daq-clean
make -C /tmp/daq-clean verify
make -C /tmp/daq-clean timing
python3 /tmp/daq-clean/tools/portfolio_check.py --generated
```

Both paths are new disposable verification directories; no global Git identity is changed. There is no GitHub remote or push. The current release has also been checked for relative Markdown links and unchanged RTL/model/board evidence.

## Tool versions and reproducibility limits

[Version stdout](../evidence/core/versions.log) records Verilator **5.040**, cocotb **2.0.0**, pytest **8.4.2**, Yosys **0.33** and Python **3.12.3**. [Prior no-cache image build](../evidence/review/fresh-tool-image.log) is retained; the final portfolio run reused that verified image (`DAQ_TOOLS_IMAGE=fpga-daq-tools:release-audit`). Run `make tools` to build the default image yourself. Dockerfile, requirements and the Verilator source checksum are included.

Local execution is Linux ARM64 in Docker on macOS. The configured GitHub runner is x86 Linux; consult the Actions page for its result after publication. Base-image tags, apt repositories and transitive packages are not fully content locked; this demonstrates functional reproduction, not bit-identical future binaries. Use `docker build --no-cache -t fpga-daq-tools:release-audit -f tools/Dockerfile .` for another independent image build.

## Optional, separate PCB study

The PCB is frozen at Rev 0.3.1 for this release. Its voltage, thermal and impedance **FAILs are preserved** in [all numerical cases](../evidence/pcb/engineering/) and the [independent review](../hardware/reference_pcie_adapter/INDEPENDENT_REVIEW.md). This final portfolio pass did not redesign the board or rerun its lengthy numerical chain.

The preceding engineering review actually regenerated all 23 stages in a source-only workspace, with two 3.05 ms switching traces. It initially returned 2 at Markdown reporting; upstream inputs were hash-validated and corrected report stages rerun successfully. The exact state is **PASS_AFTER_REPORT_REPAIR**, not an uninterrupted exit 0. [Original failure, recovery and all stage logs](../evidence/review/pcb-reproduction/)

To regenerate that study independently:

```sh
make eda-tools
make analysis-tools
make pcb-rebuild
make pcb-engineering
make pcb-independent
make pcb-engineering-check
make portfolio
```

`pcb-rebuild` recreates native CAD from design/routing sources; preserve future manual edits first. Engineering execution can take tens of minutes and fetches the official TI model into an ignored local vendor directory. KiCad **9.0.8** is used for the board (not the KiCad 7 bundled with core tools); SciPy/Shapely are in the analysis image. Existing EDA/analysis images were reused in the prior review. No fabrication exports are needed to review this portfolio.

`make portfolio` requires fresh core results, generated assets and PCB output data; it regenerates the four-page PDF into ignored `output/pdf/`. The published [review PDF](../portfolio/Independent_Release_Review.pdf) is an unchanged prior review artifact, with source and original checksum retained. Old slides, obsolete PDFs, original raw traces and full historical logs remain in the working directory/full engineering delivery archive, outside the proposed tracking set.

## Package without publishing

```sh
python3 tools/portfolio_check.py
python3 tools/portfolio_release.py package /tmp/FPGA_HighSpeed_DAQ_Portfolio_Release.zip
```

The archive destination must be new. Every archive member is checked against its SHA256 manifest. The [tracking policy](../release/TRACKING_POLICY.md) defines included evidence and local-only history. No command here purchases, fabricates, uploads or pushes anything.
