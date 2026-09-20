"""Rerun both finite r9 turns; independently check settling and contact events."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import numpy as np
from result_bundle import ROOT,write_bundle
from verify_migration import verify

SIM=ROOT/'software/sim/mujoco'
sys.path.insert(0,str(SIM))
from assess_fast_turn_trial import assess
from stackchan_rl.walk_events import WalkEventTracker
from stackchan_rl.config import DEFAULT


def score(folder):
    score=assess(folder)
    report=json.loads((folder/'report.json').read_text())
    with np.load(folder/'states.npz') as states:
        times=states['time'];vel=states['qvel']
    quiet=(np.linalg.norm(vel[:,:3],axis=1)<=.02)&(np.linalg.norm(vel[:,3:6],axis=1)<=np.deg2rad(10))
    persistent=np.logical_and.accumulate(quiet[::-1])[::-1]
    indices=np.flatnonzero(persistent&(times>=2)&(times<=times[-1]-1))
    body_stop=float(times[indices[0]]-2) if len(indices) else None
    with np.load(folder/'contact_trace.npz') as contacts:
        trace=contacts['trace'];saved=contacts['landings']
    if not np.isfinite(trace).all() or not np.allclose(np.diff(trace[:,0]),.001,atol=1e-9):
        raise ValueError('invalid physics-rate contact trace')
    tracker=WalkEventTracker(.001,DEFAULT['env']);events=[]
    for row in trace:
        event=tracker.update(row[1:3]>.35,row[3:5],np.zeros((2,2)),0.,row[0]>2)
        for foot in event['valid_landing_feet']:events.append([row[0],foot])
        if not np.array_equal(tracker.counts,row[5:7]):raise ValueError('landing trace mismatch')
    events=np.array(events).reshape(-1,2)
    same=events.shape==saved.shape and np.allclose(events,saved,atol=1e-9)
    six=same and np.array_equal(tracker.counts,[3,3]) and np.all(np.diff(events[:,1])!=0)
    completion=None
    if six and body_stop is not None and score['stable_stop_onset_s'] is not None:
        completion=max(body_stop,score['stable_stop_onset_s'],float(events[-1,0]-2))
    return {**score,'body_settle_s':body_stop,'completion_s':completion,
            'landings':tracker.counts.tolist(),
            'passed':bool(score['nominal_development_pass'] and six and completion is not None and completion<3)}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--skip-teleop',action='store_true',help='diagnostic only; cannot pass the complete baseline gate')
    a=p.parse_args();out=a.out.resolve()
    if out.exists():p.error('new output folder required')
    out.mkdir(parents=True);commands=[];gates=[]
    preserved=verify();(out/'preservation.json').write_text(json.dumps(preserved,indent=2)+'\n')
    gates.append({'criterion':'all frozen files unchanged','passed':preserved['passed']})
    model=SIM/'assets/r9_fast_turn_v1'
    for side,sign in [('left',1),('right',-1)]:
        folder=out/side
        command=['probe_fast_turn.py','--design',str(model),'--out',str(folder),
                 '--rate-deg-s',str(sign*40),'--heading-goal-deg',str(sign*91.5),
                 '--period','.4','--shift-fraction','.45','--inset-mm','25.5','--initial-inset-mm','25.5']
        commands.append({'cwd':'software/sim/mujoco','argv':[sys.executable,*command]})
        with (out/(side+'.log')).open('w') as log:
            process=subprocess.run([sys.executable,*command],cwd=SIM,stdout=log,stderr=subprocess.STDOUT)
        if process.returncode:result={'passed':False,'exit_code':process.returncode}
        else:result=score(folder)
        (out/(side+'_assessment.json')).write_text(json.dumps(result,indent=2)+'\n')
        gates.append({'criterion':side+': six landings, 90 +/-1 deg, body settles before 3 s for >=1 s, no physics failure','passed':result['passed']})
    teleop=False
    if not a.skip_teleop:
        args=['-m','unittest','tests.test_teleop_yaw','tests.test_teleop_r9','tests.test_velocity_control','tests.test_crab_control','-v']
        commands.append({'cwd':'software/sim/mujoco','argv':[sys.executable,*args]})
        with (out/'teleop.log').open('w') as log:
            teleop=subprocess.run([sys.executable,*args],cwd=SIM,stdout=log,stderr=subprocess.STDOUT).returncode==0
    gates.append({'criterion':'r8/r9 keyboard, command changes, velocity and lateral control regressions','passed':teleop})
    report=write_bundle(out,'mujoco',commands,[model/'models/scene.xml',ROOT/'docs/prototype/migration_manifest.json'],
                        [{'name':'actuator_identification','value':False,'unit':'boolean','status':'assumed','source':'historical r9 datasheet approximation, not hardware measurement'}],gates,
                        ['Nominal simulation baseline, not hardware acceptance or a new 20-trial reliability claim.'])
    print(json.dumps({'passed':report['passed'],'gates':gates,'out':str(out)},indent=2))
    raise SystemExit(0 if report['passed'] else 1)


if __name__=='__main__':main()
