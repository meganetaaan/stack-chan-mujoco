#!/usr/bin/env python3
"""Reassess all 40 completed formal trials; never execute or replace a trial."""
import argparse
import json
from pathlib import Path
from run_yaw_acceptance import verify_result
from yaw_acceptance import PROTOCOL, PROTOCOL_SHA, sha


def assess(snapshot_path, trials):
    snapshot=json.loads(snapshot_path.read_text())
    protocol=json.loads(PROTOCOL.read_text())
    if sha(PROTOCOL)!=PROTOCOL_SHA or snapshot['protocol_sha256']!=PROTOCOL_SHA:
        raise ValueError('protocol changed')
    snapshot_hash=sha(snapshot_path)
    summary=json.loads((trials/'summary.json').read_text())
    if not summary['formal_acceptance'] or summary['snapshot_sha256']!=snapshot_hash:
        raise ValueError('formal snapshot identity mismatch')
    for key in ['fixed_seeds','randomized_seeds','required_successes']:
        if snapshot[key]!=protocol[key]:raise ValueError('acceptance criteria changed')
    if summary['sources_changed']:raise ValueError('sources changed during trials')
    expected={(group,seed) for group,key in [('fixed','fixed_seeds'),('randomized','randomized_seeds')]
              for seed in protocol[key]}
    rows=summary['trials']
    if len(rows)!=40 or {(r['group'],r['seed']) for r in rows}!=expected:
        raise ValueError('all 40 unique prescribed trials required')
    actual={(p.parent.name,int(p.name)) for group in ['fixed','randomized']
            for p in (trials/group).iterdir() if p.is_dir()}
    if actual!=expected:raise ValueError('missing or extra trial directories')
    checked=[]
    for row in rows:
        result=verify_result(trials/row['group']/str(row['seed']),row['seed'],row['group'],snapshot_hash)
        if result!=row:raise ValueError('trial summary differs from recorded evidence')
        checked.append(result)
    totals={g:sum(r['pass'] for r in checked if r['group']==g) for g in ['fixed','randomized']}
    passed=all(totals[g]>=n for g,n in protocol['required_successes'].items())
    if (summary['completed']!=40 or summary['successes']!=totals or summary['pass']!=passed
            or summary['required_successes']!=protocol['required_successes']):
        raise ValueError('aggregate result mismatch')
    return {'scope':__doc__,'formal_acceptance':True,'audited_trials':40,'successes':totals,
            'pass':passed,'snapshot_sha256':snapshot_hash,'trials':checked,
            'limitation':'Substep physical safety uses the frozen probe report, not reconstruction from 20 ms samples.',
            'source_sha256':{str(p):sha(p) for p in [Path(__file__),Path('run_yaw_acceptance.py'),snapshot_path,trials/'summary.json']}}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot',type=Path,required=True)
    parser.add_argument('--trials',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    if args.out.exists():parser.error('new output required')
    result=assess(args.snapshot,args.trials)
    args.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['audited_trials','successes','pass']}))
