from pathlib import Path
import subprocess
core=sorted(Path('rtl').glob('*.sv'))
board=sorted(Path('fpga/rtl').glob('*.sv'))
# Core modules lint against core sources only; board modules also see the core.
for path,sources in [(p,core) for p in core]+[(p,core+board) for p in board]:
    print(f'LINT {path.stem}',flush=True)
    subprocess.run(['verilator','--lint-only','--assert','--Wall','-Wno-PINCONNECTEMPTY','--top-module',path.stem]+[str(p) for p in sources],check=True)
