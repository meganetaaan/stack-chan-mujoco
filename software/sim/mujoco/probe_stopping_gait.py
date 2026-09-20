#!/usr/bin/env python3
"""Use the unchanged probe plant/servo loop with an explicit stopping reference extension."""
import argparse
from functools import partial
import hashlib
import json
from pathlib import Path
import sys
import probe_reference_gait as probe
from stopping_reference import AlignedStopReference


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--finish-shift-s',type=float,default=.3)
    parser.add_argument('--reference-mode',choices=['moving-com'],default='moving-com')
    args,remaining = parser.parse_known_args()
    probe.MovingCOMReference = partial(AlignedStopReference,finish_shift_s=args.finish_shift_s)
    sys.argv = [sys.argv[0],*remaining,'--out',str(args.out)]
    probe.main()
    path = args.out/'report.json'
    report = json.loads(path.read_text())
    files = [Path(__file__),Path(__file__).with_name('stopping_reference.py')]
    report['stopping_reference_extension'] = {
        'align_final_feet':True,'finish_shift_s':args.finish_shift_s,
        'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
    path.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')


if __name__ == '__main__':
    main()
