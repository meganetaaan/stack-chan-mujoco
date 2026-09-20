#!/usr/bin/env python3
"""Independently recompute saved turn/landing evidence and check release linkage."""
import argparse
import hashlib
import json
from pathlib import Path
import mujoco
import numpy as np
from assess_fast_turn_trial import assess
from stackchan_rl.config import DEFAULT
from stackchan_rl.walk_events import WalkEventTracker
from stackchan_rl.residual import runtime_xml


def verify(design, archive):
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    scene=design/'models/scene.xml';scene_hash=sha(scene)
    summary=json.loads((archive/'trials/summary.json').read_text())
    if not summary['complete_pass'] or not summary['source_unchanged'] or summary['total']!=10:
        raise ValueError('complete frozen 10-trial suite required')
    expected={s+'_'+c for s in ['left','right'] for c in ['nominal','mass095','mass105','friction07','friction09']}
    folders={p.name:p for p in (archive/'trials').iterdir() if p.is_dir()}
    if set(folders)!=expected:raise ValueError('missing or unexpected trials')
    checked=[]
    for name,folder in sorted(folders.items()):
        report=json.loads((folder/'report.json').read_text())
        if scene_hash not in report['source_sha256'].values():raise ValueError('model mismatch: '+name)
        score=assess(folder)
        if not score['nominal_development_pass']:raise ValueError('turn failure: '+name)
        with np.load(folder/'contact_trace.npz',allow_pickle=False) as s:
            trace=s['trace'];saved_events=s['landings']
        if trace.shape[1]!=7 or not np.isfinite(trace).all() or not np.allclose(np.diff(trace[:,0]),.001,atol=1e-9):
            raise ValueError('invalid 1 ms contact trace')
        tracker=WalkEventTracker(.001,DEFAULT['env']);events=[]
        for row in trace:
            event=tracker.update(row[1:3]>.35,row[3:5],np.zeros((2,2)),0.,row[0]>2)
            # XY only affects forward-distance credit, not qualified landings.
            for foot in event['valid_landing_feet']:events.append([row[0],foot])
            if not np.array_equal(tracker.counts,row[5:7]):raise ValueError('landing counts mismatch: '+name)
        events=np.array(events).reshape(-1,2)
        if events.shape!=saved_events.shape or not np.allclose(events,saved_events,atol=1e-9):
            raise ValueError('landing events mismatch: '+name)
        if not np.array_equal(tracker.counts,[3,3]):raise ValueError('six alternating qualified landings required')
        if np.any(np.diff(events[:,1])==0):raise ValueError('nonalternating footfalls')
        with np.load(folder/'states.npz',allow_pickle=False) as s:
            times=s['time'];velocity=s['qvel']
        # In addition to yaw/tilt/contact criteria, require the body to settle.
        quiet=(np.linalg.norm(velocity[:,:3],axis=1)<=.02)&(np.linalg.norm(velocity[:,3:6],axis=1)<=np.deg2rad(10))
        persistent=np.logical_and.accumulate(quiet[::-1])[::-1]
        indices=np.flatnonzero(persistent&(times>=2)&(times<=times[-1]-1))
        if not len(indices):raise ValueError('body never settles: '+name)
        body_settle=float(times[indices[0]]-2)
        completion=max(score['stable_stop_onset_s'],float(events[-1,0]-2),body_settle)
        if completion>=3:raise ValueError('confirmed completion exceeds time goal')
        checked.append({'case':name,'completion_s':completion,'body_settle_s':body_settle,
                        'last_confirmed_landing_s':float(events[-1,0]-2),'landings':tracker.counts.tolist(),
                        'final_error_deg':score['final_error_deg'],'state_sha256':sha(folder/'states.npz'),
                        'contact_sha256':sha(folder/'contact_trace.npz')})
    for side in ['left','right']:
        cad=json.loads((archive/(side+'_cad_audit.json')).read_text())
        if cad['parts']!=45 or len(cad['rows'])!=63 or cad['worst_intersections']:
            raise ValueError('CAD audit incomplete or colliding')
    invariants=json.loads((archive/'physics_invariants.json').read_text())
    if not all(invariants['physics_invariants'].values()) or invariants['failed_samples']:
        raise ValueError('physics invariants or yaw grid failed')
    old=json.loads((archive/'prior_acceptance_recheck.json').read_text())
    if not old['pass'] or old['successes']!={'fixed':20,'randomized':18}:raise ValueError('r8 preservation check failed')
    model=mujoco.MjModel.from_xml_string(runtime_xml(scene))
    if model.neq or model.nexclude or model.nmocap or np.any(model.body_gravcomp):
        raise ValueError('unapproved assistance or collision exclusions')
    return {'scope':__doc__,'pass':True,'cases':checked,'model_sha256':scene_hash,
            'mass_kg':float(model.body_mass.sum()),'completion_range_s':[min(r['completion_s'] for r in checked),max(r['completion_s'] for r in checked)],
            'body_settle_limits':{'linear_speed_m_s':.02,'angular_speed_deg_s':10,'minimum_followup_s':1},
            'evidence_limits':['MuJoCo only','10 one-factor trials, not randomized reliability',
                               '63 CAD poses per direction, not continuous swept-volume proof',
                               'prototype fasteners and strength; hardware validation deferred']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--design',type=Path,required=True);p.add_argument('--archive',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if a.out.exists():p.error('new output required')
    report=verify(a.design,a.archive)
    a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
