"""Canonical LF/UTF-8 files before a cross-platform hash-based release review."""
import argparse
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
EXT={'.py','.json','.csv','.md','.yml','.yaml','.html','.css','.js','.txt','.svg','.xml'}

def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();changed=[]
    for path in ROOT.rglob('*'):
        if not path.is_file() or any(x in path.parts for x in ['.git','__pycache__','.venv','.cache','node_modules']):continue
        if path.suffix not in EXT:continue
        raw=path.read_bytes();canonical=raw.decode('utf-8-sig').replace('\r\n','\n').encode('utf-8')
        if raw!=canonical:
            changed.append(str(path.relative_to(ROOT)))
            if not a.check:path.write_bytes(canonical)
    if a.check and changed:raise SystemExit('Noncanonical text: '+', '.join(changed))
    print(('Checked' if a.check else 'Normalized')+f' UTF-8/LF: {len(changed)} files needed changes.')

if __name__=='__main__':main()
