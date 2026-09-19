#!/usr/bin/env python3
"""Run all 40 predeclared trials once for an immutable candidate snapshot."""
import argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import mujoco
import numpy as np
from stackchan_rl.maneuver_protocol import score_motion
from yaw_acceptance import CONTROLS,PROTOCOL,sha,validate_trial
from stackchan_rl.candidate_variation import sample_parameters
from stackchan_rl.residual import runtime_xml


def verify_result(trial,seed,group,snapshot_hash):
    report=json.loads((trial/'report.json').read_text())
    if report['seed']!=seed or report['randomized']!=(group=='randomized') or not report['formal_acceptance']:
        raise ValueError('formal trial identity mismatch')
    if report['acceptance']['manifest_sha256']!=snapshot_hash:raise ValueError('snapshot mismatch')
    source_hashes=[v for k,v in report['source_sha256'].items() if k=='probe_yaw_dynamics_candidate.py' or k.endswith('/probe_yaw_dynamics_candidate.py')]
    if source_hashes!=[sha(trial/'probe_source.py')]:raise ValueError('recorded probe source mismatch')
    if sha(trial/'states.npz')!=report['trajectory_sha256']:raise ValueError('state hash mismatch')
    if sha(trial/'landing_events.npz')!=report['landing_events_sha256']:raise ValueError('event hash mismatch')
    protocol=json.loads(PROTOCOL.read_text())
    config=json.loads(Path(protocol['physics_baseline']).read_text())
    model=mujoco.MjModel.from_xml_string(runtime_xml(Path(report['design'])/'models/scene.xml'))
    expected=sample_parameters(config,np.random.default_rng(seed),group=='randomized',model.geom_friction[model.geom('floor').id,0],12)
    if expected!=report['parameters']:raise ValueError('randomization differs from declared seed')
    if json.loads((trial/'protocol.json').read_text())!=protocol:raise ValueError('protocol mismatch')
    with np.load(trial/'states.npz',allow_pickle=False) as z:
        motion=z['motion_xy_heading']
        np.testing.assert_allclose(motion[:,0],z['state'][:,0],atol=1e-12,rtol=0)
    scored=score_motion(protocol,motion[:,0],motion[:,1:3],motion[:,3],allow_partial=True) if len(motion)>=3 else None
    if scored and scored!=report['motion_scoring']:raise ValueError('motion score mismatch')
    with np.load(trial/'landing_events.npz',allow_pickle=False) as z:
        counts=z['segment_counts'];rebuilt=np.zeros_like(counts)
        for t,index,foot in z['events']:
            if index!=int(index) or foot not in (0,1) or not 0<=index<len(counts) or not 0<=t<=report['time_s']+1e-8:
                raise ValueError('invalid landing event')
            rebuilt[int(index),int(foot)]+=1
        np.testing.assert_array_equal(counts,rebuilt)
        np.testing.assert_array_equal(counts,report['segment_valid_landings'])
    minimum=protocol['walking_evidence']['minimum_valid_landings_each_foot_per_moving_segment']
    landings=all(s['mode']=='stop' or min(counts[i])>=minimum for i,s in enumerate(protocol['segments']))
    passed=bool(report['failure'] is None and scored and scored['motion_pass'] and landings)
    if passed!=report['acceptance_pass']:raise ValueError('acceptance label mismatch')
    return {'seed':seed,'group':group,'pass':passed,'failure':report['failure'],'time_s':report['time_s'],
            'motion_pass':bool(scored and scored['motion_pass']),'landing_pass':bool(landings),
            'report_sha256':sha(trial/'report.json')}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--workers',type=int,default=4)
    a=parser.parse_args()
    if a.out.exists() or not 1<=a.workers<=12:parser.error('new output and 1..12 workers required')
    snapshot=json.loads(a.snapshot.read_text());snapshot_hash=sha(a.snapshot)
    validate_trial(SimpleNamespace(**CONTROLS,acceptance_manifest=a.snapshot,protocol=PROTOCOL,
                   design=Path(snapshot['design']),reference=Path(snapshot['reference']),
                   seed=snapshot['fixed_seeds'][0],randomize=False))
    # Exclusive claim prevents a failed seed from silently being rerun elsewhere.
    claim=a.snapshot.parent/'run_claim.json'
    with claim.open('x') as f:
        json.dump({'snapshot_sha256':snapshot_hash,'output':str(a.out.resolve())},f,indent=2)
    jobs=[(group,seed) for pair in zip(snapshot['fixed_seeds'],snapshot['randomized_seeds'])
          for group,seed in zip(['fixed','randomized'],pair)]
    if len(jobs)!=40 or len(set(jobs))!=40:raise ValueError('all 40 unique trials required')
    a.out.mkdir(parents=True)
    (a.out/'manifest.json').write_text(json.dumps({'snapshot':str(a.snapshot),'snapshot_sha256':snapshot_hash,
        'jobs':jobs,'workers':a.workers,'failures_replaced':False,'runner_sha256':sha(__file__)},indent=2)+'\n')
    command=[sys.executable,'probe_yaw_dynamics_candidate.py','--design',snapshot['design'],
             '--reference',snapshot['reference'],'--protocol',str(PROTOCOL),'--acceptance-manifest',str(a.snapshot)]
    for key,value in CONTROLS.items():
        if value is not None:command.extend(['--'+key.replace('_','-'),str(value)])

    def run(group,seed):
        trial=a.out/group/str(seed);trial.parent.mkdir(exist_ok=True)
        args=command+['--seed',str(seed),'--out',str(trial)]+(['--randomize'] if group=='randomized' else [])
        with (trial.parent/(str(seed)+'.log')).open('w') as log:
            result=subprocess.run(args,stdout=log,stderr=subprocess.STDOUT)
        if result.returncode:return {'seed':seed,'group':group,'pass':False,'process_error':result.returncode}
        try:return verify_result(trial,seed,group,snapshot_hash)
        except Exception as exc:return {'seed':seed,'group':group,'pass':False,'verification_error':str(exc)}

    rows=[]
    with ThreadPoolExecutor(max_workers=a.workers) as pool:
        for future in as_completed([pool.submit(run,*job) for job in jobs]):
            row=future.result();rows.append(row)
            with (a.out/'progress.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
            print(json.dumps(row),flush=True)
    changed=[name for name,digest in snapshot['source_sha256'].items() if sha(name)!=digest]
    if sha(a.snapshot)!=snapshot_hash:changed.append(str(a.snapshot))
    totals={group:sum(r['pass'] for r in rows if r['group']==group) for group in ['fixed','randomized']}
    passed=not changed and all(totals[k]>=v for k,v in snapshot['required_successes'].items())
    summary={'formal_acceptance':True,'snapshot_sha256':snapshot_hash,'completed':len(rows),
             'successes':totals,'required_successes':snapshot['required_successes'],'sources_changed':changed,
             'pass':passed,'trials':sorted(rows,key=lambda r:(r['group'],r['seed']))}
    (a.out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(totals),flush=True)


if __name__=='__main__':main()
