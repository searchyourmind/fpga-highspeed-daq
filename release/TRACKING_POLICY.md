# Proposed Git tracking policy

[tracked-files.txt](tracked-files.txt) is the exact proposed file set. `tools/portfolio_release.py` copies only that list into a new directory and verifies archive member hashes. The original engineering workspace and prior ZIP remain untouched. This separate public repository is prepared from that explicit file set under the owner's publication authorization.

## Included

- All RTL, Python functional models, cocotb/pytest tests and executable reproduction tools.
- Interface/architecture/verification documentation, current audit, progress/handoff and concise portfolio/resume material.
- Actual current test XML, scenario data, command logs/return codes, source hashes, versions and compact generic synthesis results under `evidence/core/`.
- Selected original failed assertions, the six mutation logs, prior no-cache build and source-only reproduction evidence.
- Frozen native KiCad design/routing/BOM and analysis scripts, every compact PCB engineering JSON, before/after thermal case CSVs, CAD views and prior stage logs. All FAIL results remain intact.
- Current PNG/SVG assets, compressed real VCD and the unchanged independent engineering review PDF.
- Original Week1 starter ZIP and pre-correction PCB numerical provenance.

## Excluded from the proposal; retained locally

Build trees/caches, raw SPICE/VCD files, derived multi-megabyte netlists, repeated full regressions, obsolete slide/PDF versions, transient preview CSV duplicates, Gerbers/drills, downloaded vendor models/datasheets, editor state and original package manifests. Historical delivery/integrity scripts tied to the larger checkpoint are also excluded; the portable release uses `portfolio_check.py` and `portfolio_release.py`.

`.gitignore` prevents generated outputs from appearing in a normal add. The explicit manifest remains authoritative. No `git clean`, evidence deletion or history rewriting was used. A local Git snapshot and clone validate this set; publication uses a separate repository with a fresh initial commit; no unrelated local history is included.

Historical raw logs may contain original local workspace paths. They are execution provenance, not instructions or portable paths. Downloaded vendor content is not redistributed. No open-source license has been invented for the user's work or third-party starter materials.
