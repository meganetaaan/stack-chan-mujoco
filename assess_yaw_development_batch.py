#!/usr/bin/env python3
"""Recompute motion and landing counts; substep safety remains evidence from the recorded probe."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from stackchan_rl.candidate_variation import sample_parameters
from stackchan_rl.maneuver_protocol import score_motion


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def assess(batch):
    manifest=json.loads((batch/'manifest.json').read_text())
    summary=json.loads((batch/'summary.json').read_text())
    seeds=manifest['seeds'];records=summary['trials']
    if len(set(seeds))!=len(seeds) or sorted(seeds)!=sorted(r['seed'] for r in records):
        raise ValueError('missing, extra, or duplicate trials')
    if summary['sources_changed']:raise ValueError('batch sources changed')
    frozen=manifest['source_sha256']
    config_path=Path('policies/r6_mounted_seed20260924/config.json')
    if sha(config_path)!=frozen[str(config_path)]:raise ValueError('baseline config changed')
    config=json.loads(config_path.read_text());rows=[]
    for entry in records:
        seed=entry['seed'];trial=batch/str(seed)
        if 'error' in entry:raise ValueError('batch contains an unreviewed process error')
        if sha(trial/'report.json')!=entry['report_sha256']:raise ValueError('report hash mismatch')
        r=json.loads((trial/'report.json').read_text())
        if sha(trial/'probe_source.py')!=frozen['probe_yaw_dynamics_candidate.py']:raise ValueError('recorded probe source mismatch')
        if r['seed']!=seed or not r['randomized'] or r['formal_acceptance']:raise ValueError('trial identity mismatch')
        expected=sample_parameters(config,np.random.default_rng(seed),True,r['parameters']['friction'],12)
        if expected!=r['parameters']:raise ValueError('randomization differs from the declared seed')
        for name in ['probe_yaw_dynamics_candidate.py','stackchan_rl/actuation.py','stackchan_rl/walk_events.py','stackchan_rl/maneuver_protocol.py']:
            matches=[v for k,v in r['source_sha256'].items() if k==name or k.endswith('/'+name)]
            if matches!=[frozen[name]]:raise ValueError('trial source mismatch: '+name)
        for name,key in [('states.npz','trajectory_sha256'),('landing_events.npz','landing_events_sha256')]:
            if sha(trial/name)!=r[key]:raise ValueError('trace hash mismatch: '+name)
        protocol=json.loads((trial/'protocol.json').read_text())
        protocol_source=Path('configs/maneuver/acceptance_v1.json')
        if sha(protocol_source)!=frozen[str(protocol_source)] or protocol!=json.loads(protocol_source.read_text()):
            raise ValueError('protocol changed')
        with np.load(trial/'states.npz',allow_pickle=False) as z:
            motion=z['motion_xy_heading'];times=z['state'][:,0]
            np.testing.assert_allclose(motion[:,0],times,atol=1e-12,rtol=0)
        scored=score_motion(protocol,motion[:,0],motion[:,1:3],motion[:,3],allow_partial=True) if len(motion)>=3 else None
        motion_pass=bool(scored and scored['motion_pass'])
        if scored and scored!=r['motion_scoring']:raise ValueError('stored motion score differs from state replay')
        with np.load(trial/'landing_events.npz',allow_pickle=False) as z:
            counts=z['segment_counts'];events=z['events'];rebuilt=np.zeros_like(counts)
            for t,index,foot in events:
                if index!=int(index) or foot not in [0,1] or not 0<=index<len(counts) or not 0<=t<=r['time_s']+1e-8:
                    raise ValueError('invalid landing event')
                rebuilt[int(index),int(foot)]+=1
            np.testing.assert_array_equal(counts,rebuilt)
            np.testing.assert_array_equal(counts,r['segment_valid_landings'])
        minimum=protocol['walking_evidence']['minimum_valid_landings_each_foot_per_moving_segment']
        landing_pass=all(s['mode']=='stop' or min(counts[i])>=minimum for i,s in enumerate(protocol['segments']))
        passed=bool(r['failure'] is None and motion_pass and landing_pass)
        if passed!=r['development_trial_pass'] or passed!=entry['development_trial_pass']:raise ValueError('success label mismatch')
        rows.append({'seed':seed,'success':passed,'motion_pass':motion_pass,'landing_pass':bool(landing_pass),'failure':r['failure']})
    successes=sum(r['success'] for r in rows)
    if successes!=summary['successes']:raise ValueError('batch total mismatch')
    return {'scope':__doc__,'formal_acceptance':False,'audited_trials':len(rows),'successes':successes,'trials':rows,
            'source_sha256':{str(p):sha(p) for p in [Path(__file__),batch/'manifest.json',batch/'summary.json']}}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--batch',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    a=parser.parse_args()
    if a.out.exists():parser.error('new output required')
    result=assess(a.batch)
    a.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['audited_trials','successes']}))
