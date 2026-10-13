# Pi 5 FFC to M.2 M-key reference adapter - Rev 0.3.1

**DESIGN REVIEW DRAFT - NOT RELEASED FOR MANUFACTURE.** This is a separate PCB exercise, not a board implementing the DAQ RTL. No board, FPGA, SSD or Pi was purchased, fabricated, powered or tested.

Read the current [INDEPENDENT_REVIEW.md](INDEPENDENT_REVIEW.md) for retained failures and corrected minimum-copper thermal results. [ENGINEERING_REVIEW.md](ENGINEERING_REVIEW.md) retains the preceding detailed review. The current [four-page review PDF](../../portfolio/Independent_Release_Review.pdf) summarizes both project scopes. [BOM_selected.csv](BOM_selected.csv) records 30 manufacturer part selections, conditional approvals and the legacy FFC hold.

Published [CAD views and all numerical cases](../../evidence/pcb/) are preserved separately from ignored regenerated `outputs/`. The board is frozen; no redesign occurred during portfolio finalization.

## Implemented and checked
- Native KiCad 9 schematic and 80 x 78 mm, four-layer board. 30 electrical references, four board-only mounting holes, M.2 support and a corrected 22 x 42 mm card envelope.
- 424 trace/via objects, two filled inner GND planes plus outer power-area GND spreaders. Eight QFN thermal vias and four added TX return vias.
- **ERC 0, geometric DRC 0, unconnected 0, schematic parity 0.** Pin contracts and saved differential geometry pass. Zero planar pair skew excludes connector/via electrical effects.
- Actual schematic PDF, board SVG, native 3D render and DRAFT-only Gerber/drill exports in `outputs/`. Some 3D bodies are unavailable. Final drill report: 92 plated / 7 unplated holes, including H5 center clearance.
- 108 power DC/AC cases; official TPS62130A nominal and loaded-corner startup/load-event/shutdown models; 126 copper load distributions; 24 thermal cases; actual mechanical/filled-plane checks; 2D field solution with convergence checks. `results/engineering-check-summary.json` separates numerical execution from failed design margins.

## Results that prevent release
| Area | Current conclusion |
|---|---|
| Voltage | Nominal and loaded external-component A transients pass, but conservative composite range 3.130447-3.487610 V exceeds the 3.135-3.465 V target. |
| Heat | Corrected 30 um minimum-copper screen: 6/24 FAIL. Fine-grid worst 160.302515 C, margin -35.302515 C against 125 C. Original 35 um five failures and 159.381 C estimate retained. Extrapolated rejection, not sustainable operation. No 2 A continuous rating. |
| SI | Nominal 93.94 ohm. Broad assumed process corners 83.29-106.13 ohm exceed target. Four width candidates under the original broad assumptions fail; tighter tolerances are not accepted as closure. |
| Components | Real candidate MPNs recorded. MLCC effective capacitance, hot/fault inductor behavior, superseded FFC/cable and final connector approval remain open. |
| Mechanics/assembly | Planar envelope passes. Actual SSD, height tolerances, screw engagement, enclosure and via-in-pad assembly remain open. |

## Electrical scope
External regulated, current-limited 5 V enters J3. The 2 A SSD load is a design stress target, not an approved rating. At 4.65 V input and assumed 85% efficiency, its power-core input budget is approximately 1.684 A. Actual cable/mating contacts require approval. The unkeyed input has no reverse-polarity or hot-plug protection.

U1 is **TPS62130A**, with 31.6k/10k 0.1% feedback (3.328 V nominal), 2.2 uH and two nominal 22 uF output capacitors. The A suffix is required: PG pulls low on EN shutdown while VIN remains present. Its official A-model transient is distinct from the older, separate hypothetical 12 V power-tree experiment.

FFC pins 1/2 feed detection only through 3.6k/6.8k; they do not join EXT_5V. All grounds share the reference plane. PWR_EN has a 100k pulldown. PG drives NC7SB3157 CLKREQ isolation; Q1 gates PERST, Q2/Q3 translate open-drain wake. Full missing-supply and IO sequencing is not qualified. J4 external SUSCLK is DNP by default; a selected SSD must not require it for the baseline.

M.2 host-side pin 69 is grounded as in the official Pi reference. Pi RX_P connects to PETP0 pin 43; Pi TX_P to PERP0 pin 49. No additional AC coupling capacitors are inserted; actual endpoint/cable requirements remain an approval item.

The custom TE land pattern follows G-2199230 Rev B3 sheet 3. **1-2199230-4 is M-key; unprefixed 2199230-4 is E-key and must not be substituted.** The drawing and part-specific current approval are distinct.

## Stackup and SI scope
Reference JLC04161H-3313: nominal 1.6 mm, outer copper 35 um, outer prepreg 99.4 um/Er 4.1, inner copper 15.2 um and core 1.265 mm/Er 4.6. These are preliminary design inputs, not a vendor commitment. Adjacent inner planes reference F.Cu/B.Cu pairs. Trunks use 0.14 mm width / 0.152 mm gap; connector/via breakouts expand.

The new quasi-static 2D solver includes an assumed mask and is a screening result. The old 92.11 ohm empirical formula in `outputs/impedance-estimate.json` is a historical approximation. Neither result establishes connector/cable loss, via 3D behavior, eye diagrams, TDR or PCIe compliance. Actual plane projection has no unintended reference voids; TX ground-return vias are within 0.891 mm of each transition.

## Sources, reproduction and constraints
`design.py` is the electrical source; `build.py` creates native CAD; `apply_routing.py` replays `routing/tracks.json`. `make pcb` checks current CAD. `make pcb-rebuild` explicitly regenerates it; preserve future manual changes first.

`make analysis-tools` builds isolated dependencies. `make pcb-engineering` runs the entire numerical review and creates the review PDF; it can take tens of minutes. `make pcb-engineering-check` checks retained evidence. `make pcb-draft` emits review-only files. No command orders hardware or pushes GitHub.

Detailed sources, failed attempts, limits and next work are in `ENGINEERING_REVIEW.md`, `docs/PROGRESS.md` and `NEXT_SESSION.md`. The actual model files are fetched from TI and excluded from the portable archive. Cadence hands-on remains **NOT COMPLETED**.
