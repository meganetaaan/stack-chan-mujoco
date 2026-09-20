#!/usr/bin/env python3
"""Check frozen batch hashes and recorded state timing, independently of scores.

The trajectory is sampled at policy boundaries; the substep contact/protection
checks are in the environment. This audit cannot replace those finer checks.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from stackchan_rl.residual import sha


def audit(batch):
    batch=Path(batch);manifest=json.loads((batch/'manifest.json').read_text())
    if not manifest['complete']:raise ValueError('batch incomplete')
    if sha(batch/'config.json')!=manifest['evaluation_config_sha256']:raise ValueError('config hash mismatch')
    if len(manifest['results'])!=manifest['expected_trials']:raise ValueError('trial count mismatch')
    if len({x['seed'] for x in manifest['results']})!=len(manifest['results']):raise ValueError('duplicate seeds')
    result=[]
    for entry in manifest['results']:
        folder=batch/entry['trial'];report=json.loads((folder/'report.json').read_text())
        if sha(folder/'report.json')!=entry['report_sha256']:raise ValueError('report hash mismatch')
        if sha(folder/'states.npz')!=report['trajectory_sha256']:raise ValueError('state hash mismatch')
        if report['seed']!=entry['seed'] or report['simulation_trial_pass']!=entry['simulation_trial_pass']:
            raise ValueError('trial identity or score mismatch')
        with np.load(folder/'states.npz',allow_pickle=False) as trace:
            states=trace['state'];actions=trace['action'];observations=trace['observation']
            if not all(np.isfinite(a).all() for a in (states,actions,observations)):
                raise ValueError('nonfinite trajectory')
            if len(states)!=len(actions)+1 or len(observations)!=len(states):raise ValueError('unaligned trace')
            # mjSTATE_INTEGRATION begins with time, qpos (17), qvel (16).
            times=states[:,0];forward=states[:,1]-states[0,1]
            if times[0]!=0 or np.any(np.diff(times)<=0) or np.any(np.diff(times)>.020000001):
                raise ValueError('invalid trajectory timing')
            if abs(times[-1]-report['time_s'])>1e-9 or abs(forward[-1]-report['forward_m'])>1e-9:
                raise ValueError('state and report disagree')
            crossings=np.flatnonzero(forward>=10.)
            observed=float(times[crossings[0]]) if len(crossings) else None
            reported=report['crossing_time_s']
            if reported is not None and (observed is None or not observed-.020000001<=reported<=observed+1e-9):
                raise ValueError('crossing time inconsistent with state samples')
            # Tracking diagnostic over whole sampled intervals while walking,
            # avoiding stand/stop. It is not an independent acceptance rule.
            vx=np.diff(forward)/np.diff(times);active=(times[1:]>=2.)&(times[1:]<=108.)
            rmse=float(np.sqrt(np.mean((vx[active]-.1)**2))) if np.any(active) else None
            avg=float((forward[-1]-forward[0])/(times[-1]-times[0]))
            result.append({'trial':entry['trial'],'sampled_crossing_s':observed,
                'substep_crossing_s':reported,'whole_run_average_speed_m_s':avg,
                'instantaneous_velocity_rmse_m_s':rmse,'recorded_frames':len(states),
                'trial_pass':report['simulation_trial_pass']})
    successes=sum(x['trial_pass'] for x in result)
    if successes!=manifest['successes']:raise ValueError('success count mismatch')
    return {'schema':'r6-residual-state-audit-v1','batch_manifest_sha256':sha(batch/'manifest.json'),
        'audit_source_sha256':sha(__file__),'trials':len(result),'successes':successes,
        'hashes_and_recorded_states_consistent':True,'substep_safety_rechecked':False,'results':result}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--batch',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if a.out.exists():p.error('use a new output path')
    result=audit(a.batch);a.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='results'},indent=2))


if __name__=='__main__':main()
