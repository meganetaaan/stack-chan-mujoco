"""Download pinned Ubuntu tools into the workspace without root installation."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]
lock = json.loads(Path(__file__).with_name('debian_packages.json').read_text())
downloads = ROOT/'.tools/debs'
destination = ROOT/'.tools/root'
downloads.mkdir(parents=True, exist_ok=True)
destination.mkdir(parents=True, exist_ok=True)
for package in lock['packages']:
    match = next((p for p in downloads.glob('*.deb')
                  if hashlib.sha256(p.read_bytes()).hexdigest()==package['sha256']), None)
    if match is None:
        subprocess.run(['apt-get','download',package['Package']+'='+package['Version']],cwd=downloads,check=True)
        match = next((p for p in downloads.glob('*.deb')
                      if hashlib.sha256(p.read_bytes()).hexdigest()==package['sha256']), None)
    if match is None:
        raise RuntimeError('Package digest mismatch: '+package['Package'])
    subprocess.run(['dpkg-deb','-x',str(match),str(destination)],check=True)
print('Pinned binaries extracted into '+str(destination))
