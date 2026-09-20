#!/usr/bin/env python3
"""Run a fixed exploratory plant suite; this is not physical acceptance."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import subprocess
import sys


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--design',type=Path,required=True)
    p.add_argument('--variations',type=Path,default=Path('design/plant_variations'))
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--workers',type=int,default=4)
    args = p.parse_args()
    if args.out.exists() or not 1 <= args.workers <= 4:
        p.error('use a new output directory and 1..4 workers')
    args.out.mkdir(parents=True)
    manifest = json.loads((args.variations/'manifest.json').read_text())
    jobs = []
    for filename in manifest['cases']:
        name = Path(filename).stem
        command = [sys.executable,'probe_reference_gait.py','--design',str(args.design),
                   '--speed','.1','--step-period','.27','--height-offset-mm','-2',
                   '--com-forward-offset-mm','-3','--com-inset-mm','24','--static-compensation',
                   '--slew','6','--steps','400','--plant-variation',str(args.variations/filename),
                   '--out',str(args.out/name)]
        jobs.append({'name':name,'command':command})
    (args.out/'commands.json').write_text(json.dumps(jobs,indent=2)+'\n')

    def run(job):
        with (args.out/(job['name']+'.log')).open('w') as log:
            result = subprocess.run(job['command'],stdout=log,stderr=subprocess.STDOUT)
        row = {'name':job['name'],'returncode':result.returncode}
        path = args.out/job['name']/'report.json'
        if path.exists():
            report = json.loads(path.read_text());s = report.get('simulation',{})
            row.update(planning_failure=report['planning_failure'],duration_s=s.get('duration_s'),
                       forward_m=s.get('forward_m'),failure=s.get('failure'),
                       contact_metrics=s.get('contact_metrics'))
        return row

    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = [executor.submit(run,job) for job in jobs]
        for future in as_completed(futures):
            row = future.result();results.append(row)
            (args.out/'summary.json').write_text(json.dumps(sorted(results,key=lambda r:r['name']),indent=2)+'\n')
            print(json.dumps(row),flush=True)
    return 0 if all(r['returncode']==0 for r in results) else 1


if __name__ == '__main__':
    raise SystemExit(main())
