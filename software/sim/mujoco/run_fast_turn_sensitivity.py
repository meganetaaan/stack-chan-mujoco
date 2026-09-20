#!/usr/bin/env python3
"""Freeze source hashes and run two nominal plus eight one-factor turn trials."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from assess_fast_turn_trial import assess


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--design',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if a.out.exists():p.error('new output required')
    sources=[Path(n) for n in ['probe_fast_turn.py','fast_turn_reference.py','teleop_yaw.py',
                              'assess_fast_turn_trial.py','run_fast_turn_sensitivity.py']]
    sources+=list(Path('stackchan_rl').glob('*.py'))
    sources+=[f for f in a.design.rglob('*') if f.is_file() and '__pycache__' not in str(f)]
    def hashes():return {str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(sources)}
    before=hashes();a.out.mkdir(parents=True)
    conditions=[('nominal',[]),('mass095',['--mass-scale','.95']),('mass105',['--mass-scale','1.05']),
                ('friction07',['--friction','.7']),('friction09',['--friction','.9'])]
    cases=[(side,sign,name,args) for side,sign in [('left',1),('right',-1)] for name,args in conditions]
    (a.out/'plan.json').write_text(json.dumps({'cases':cases,'source_sha256':before},indent=2)+'\n')
    def run(case):
        side,sign,name,extra=case;folder=a.out/(side+'_'+name)
        command=[sys.executable,'probe_fast_turn.py','--design',str(a.design),'--out',str(folder),
                 '--inset-mm','25.5','--initial-inset-mm','25.5','--shift-fraction','.45','--period','.4',
                 '--rate-deg-s',str(sign*40),'--heading-goal-deg',str(sign*91.5),*extra]
        with (a.out/(side+'_'+name+'.log')).open('w') as log:
            result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
        if result.returncode:return {'case':side+'_'+name,'execution_error':result.returncode,'pass':False}
        report=assess(folder)
        (folder/'assessment.json').write_text(json.dumps(report,indent=2)+'\n')
        return {'case':side+'_'+name,'pass':report['nominal_development_pass'],'assessment':report}
    with ThreadPoolExecutor(max_workers=4) as pool:rows=list(pool.map(run,cases))
    unchanged=before==hashes()
    summary={'scope':__doc__,'source_unchanged':unchanged,'passed':sum(r['pass'] for r in rows),
             'total':len(rows),'rows':rows,'complete_pass':unchanged and all(r['pass'] for r in rows)}
    (a.out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary))
    if not summary['complete_pass']:sys.exit(1)


if __name__=='__main__':main()
