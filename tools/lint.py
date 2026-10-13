from pathlib import Path
import subprocess
for path in sorted(Path('rtl').glob('*.sv')):
    print(f'LINT {path.stem}',flush=True)
    subprocess.run(['verilator','--lint-only','--assert','--Wall','-Wno-PINCONNECTEMPTY','--top-module',path.stem]+[str(p) for p in sorted(Path('rtl').glob('*.sv'))],check=True)
