# Published engineering evidence

- `core/`: final portfolio clean-checkout outputs, actual command/return-code records, source hashes, tool versions, JUnit, E2E scenarios, generic synthesis and the real compressed VCD.
- `debug/`: original production failure and deliberately failing probe evidence. These are not passing production tests.
- `review/`: unchanged prior independent-review receipts, selected mutation/no-cache-build logs and complete prior PCB stage logs/failure recovery.
- `pcb/`: frozen native CAD checks/views and every compact engineering result. Voltage, thermal and impedance FAILs are retained.
- `original-evidence-map.json`: exact original local path and SHA256 of copied prior artifacts. Historical paths in logs/JSON are preserved rather than rewritten.
- `engineering-preservation.json`: unchanged RTL/model/test/board engineering inputs and the untouched prior full delivery archive.

New test runs write ignored generated directories. They do not overwrite published evidence. The verified generation commands and clean-checkout scope are documented in `../docs/REPRODUCING.md`. The preceding four-page PDF remains an unchanged review artifact; it is not a newly measured or newly executed hardware result.
