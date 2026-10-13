"""Curate an explicit Git proposal; preserve all excluded local evidence."""
from pathlib import Path
import argparse, hashlib, json, shutil, zipfile
R = Path(__file__).resolve().parents[1]
ROOT_FILES = {'README.md','AGENTS.md','NEXT_SESSION.md','Makefile','requirements.txt','.gitignore','.dockerignore'}
DOCS = {'architecture.md','interface_contracts.md','design_decisions.md','assumptions_and_limitations.md','sources.md','verification_plan.md','VERIFICATION_REVIEW.md','SYSTEM_AUDIT.md','REQUIREMENTS_MATRIX.md','REPRODUCING.md','RESUME_BULLETS.md','EVIDENCE_INDEX.md','PROGRESS.md'}
OLD_TOOLS = {'Dockerfile.kicad-ppa-attempt','clean_snapshot.py','delivery_check.py','export_slide_pdf.py','package.py','portfolio.py','release_audit.py','system_audit.py'}
SKIP_PARTS = {'build','.git','__pycache__','.pytest_cache','vendor','outputs','reports','node_modules'}

def selected():
    paths=[]
    for folder in ('rtl','sim','tb','tests','tools','hardware','provenance','.github','synthesis','docs','portfolio','evidence','release'):
        for p in (R/folder).rglob('*'):
            if not p.is_file() or p.is_symlink(): continue
            q=p.relative_to(R); s=q.as_posix()
            if any(x in SKIP_PARTS for x in q.parts): continue
            if p.suffix in ('.pyc','.vcd','.raw','.kicad_prl') or p.name in ('transient.txt','average_ac.txt','average_dc.txt'): continue
            if folder=='tools' and p.name in OLD_TOOLS: continue
            if folder=='docs' and (len(q.parts)!=2 or p.name not in DOCS): continue
            if folder=='portfolio' and not (s.startswith('portfolio/assets/') or p.name in ('README.md','Independent_Release_Review.pdf')): continue
            if folder=='release' and p.name not in ('tracked-files.txt','TRACKING_POLICY.md','RELEASE_SUMMARY.md'): continue
            if folder=='synthesis' and not (s.startswith(('synthesis/scripts/','synthesis/constraints/')) or p.name=='README.md'): continue
            paths.append(s)
    return sorted(set(paths)|ROOT_FILES|{'release/tracked-files.txt'})

def read_manifest():
    files=(R/'release/tracked-files.txt').read_text().splitlines()
    assert len(files)==len(set(files)) and files==sorted(files)
    for f in files:
        assert f and not Path(f).is_absolute() and '..' not in Path(f).parts
        assert (R/f).is_file() and not (R/f).is_symlink(), f
    return files

def manifest():
    files=selected(); (R/'release').mkdir(exist_ok=True)
    (R/'release/tracked-files.txt').write_text('\n'.join(files)+'\n')
    print(f'{len(files)} proposed files, {sum((R/f).stat().st_size for f in files):,} bytes')

def snapshot(dest):
    files=read_manifest(); dest=Path(dest).resolve(); assert not dest.exists(), 'Preserve prior snapshots'
    for f in files:
        out=dest/f;out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/f,out)
    print(dest)

def package(dest):
    files=read_manifest(); dest=Path(dest).resolve(); assert not dest.exists(),'Preserve prior archives'
    checks={f:hashlib.sha256((R/f).read_bytes()).hexdigest() for f in files}
    with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as z:
        for f in files:z.write(R/f,'fpga-highspeed-daq/'+f)
        z.writestr('fpga-highspeed-daq/MANIFEST.sha256',''.join(f'{h}  {f}\n' for f,h in checks.items()))
    with zipfile.ZipFile(dest) as z:
        assert z.testzip() is None
        for f,h in checks.items():assert hashlib.sha256(z.read('fpga-highspeed-daq/'+f)).hexdigest()==h
    print(json.dumps({'archive':str(dest),'files':len(files)+1,'bytes':dest.stat().st_size,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'member_checksums':'PASS'},indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('manifest','snapshot','package'));p.add_argument('destination',nargs='?');a=p.parse_args()
    if a.action=='manifest':manifest()
    else:
        assert a.destination,'Destination required'
        (snapshot if a.action=='snapshot' else package)(a.destination)
