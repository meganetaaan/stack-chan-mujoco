#!/usr/bin/env python3
"""Fetch public manufacturer reference files and verify the reviewed version."""
import argparse,hashlib,json,re
from pathlib import Path
from urllib.request import urlopen
from urllib.parse import urlparse


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if a.out.exists():p.error('new output required')
    sources=json.loads(Path('design/x330_manufacturer_reference.json').read_text())['sources']
    a.out.mkdir(parents=True)
    for name,filename in [('drawing','drawing.pdf'),('cad','motor.stp'),('inertia','inertia.pdf')]:
        source=sources[name]
        with urlopen(source['source'],timeout=30) as response:page=response.read().decode()
        links=re.findall(r"call_url\('([^']+)'\)",page)
        if not links or links[-1]!=source['redirect']:raise ValueError('manufacturer redirect changed: '+name)
        url=links[-1]
        if urlparse(url).scheme!='https' or urlparse(url).hostname!='www.dropbox.com':raise ValueError('unexpected download host')
        with urlopen(url,timeout=60) as response:data=response.read()
        if hashlib.sha256(data).hexdigest()!=source['sha256']:raise ValueError('manufacturer file version changed: '+name)
        (a.out/filename).write_bytes(data)
    (a.out/'sources.json').write_text(json.dumps(sources,indent=2)+'\n')
    print('Verified three manufacturer reference files.')


if __name__=='__main__':main()
