"""Fail closed on missing, empty, failed, errored or skipped test evidence."""
from pathlib import Path
import xml.etree.ElementTree as ET

def require_pass(path):
    p=Path(path)
    tree=ET.parse(p)
    cases=list(tree.iter('testcase'))
    failures=list(tree.iter('failure'))+list(tree.iter('error'))
    skipped=list(tree.iter('skipped'))
    if not cases or failures or skipped:
        raise RuntimeError(f'{p}: tests={len(cases)}, failures/errors={len(failures)}, skipped={len(skipped)}')
    return len(cases)

if __name__=='__main__':
    import sys
    print(f'JUnit PASS: {require_pass(sys.argv[1])} cases')
