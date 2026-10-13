# Evidence index

| Evidence | Purpose |
|---|---|
| [Core clean checkout](../evidence/core/) | Actual stdout, commands, return codes, source hashes, versions, 63-case JUnit, 33 scenario rows and generic synthesis |
| [Original debugging failures](../evidence/debug/) | Page-crossing failure and real failing runner fixture; excluded from passing production totals |
| [Independent review](../evidence/review/) | No-cache image build, prior clean runs, four oracle checks, six mutations and tool identities |
| [PCB numerical cases](../evidence/pcb/engineering/) | Every retained voltage/thermal/impedance result, including old five failures and corrected six failures |
| [PCB source-only reproduction](../evidence/review/pcb-reproduction/) | Actual 23-stage execution, initial report failure and validated report-only recovery |
| [Evidence origin map](../evidence/original-evidence-map.json) | SHA256 and original local path of each curated prior artifact; content is unchanged |
| [Figures and provenance](../portfolio/assets/) | Architecture, actual waveform, simulated-cycle benchmark; source/hash metadata |
| [Requirements matrix](REQUIREMENTS_MATRIX.md) | PASS, FAIL, BLOCKED and NOT TESTED remain distinct |

Curated evidence lives separately from newly generated outputs. Paths inside historical JSON/logs identify the original run and have deliberately not been rewritten. Current public locations are indexed above and by the origin map. Older logs and drafts remain in the original workspace/full engineering archive; they are not additional current successes. No original evidence was deleted during curation.
