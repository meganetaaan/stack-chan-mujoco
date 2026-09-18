#!/usr/bin/env python3
"""Synthetic reward-function comparisons. Does NOT run MuJoCo or learn a policy."""
from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
from stackchan_rl.config import ROOT, load_config, save_json
from stackchan_rl.rewards import reward_terms


def probe_state(cmd: float, speed: float, *, stepping: bool = False) -> dict:
    return {"command":np.array([cmd,0.,0.]), "velocity":np.array([speed,0.,0.]),
            "tilt_rad":0., "height_error":0., "heading_error":0., "position_error":np.zeros(2),
            "contacts":np.array([not stepping,True]), "loads":np.array([0.,8.]) if stepping else np.array([4.,4.]),
            "pose_normalized":np.zeros(10), "gyro":np.zeros(3), "qd":np.zeros(10),
            "torque_fraction_sq":.05, "power_W":0., "action_delta":np.zeros(10),
            "slip_speed_sq":0., "saturation":0., "self_contact":False,
            "swing_mask":np.array([True,False]), "foot_height":np.array([.006 if stepping else 0.,0.]),
            "valid_landings_this_step":0, "requested_forward_m_s":cmd,
            "new_forward_distance_m":max(0.,speed)*.02, "no_step_elapsed_s":0. if stepping else 4.,
            "no_step_grace_s":1.5, "no_step_ramp_s":1.}


def audit() -> dict:
    reports=[]
    for path in ('walk_legacy.json','walk_step1.json'):
        cfg=load_config(ROOT/'configs'/path)
        rows=[]
        for cmd in (.02,.04,.06):
            for label,speed,stepping in [('stopped',0.,False),('half_speed',cmd*.5,True),
                                         ('tracking',cmd,True),('backward',-.01,False)]:
                state=probe_state(cmd,speed,stepping=stepping)
                state['walk_objective_version']=cfg['env']['walk_objective_version']
                terms=reward_terms(state,cfg['reward'],'walk',.02,False)
                rows.append({'case':label,'command_m_s':cmd,'velocity_m_s':speed,
                             'reward_rate_synthetic':sum(terms.values())/.02,
                             'velocity_reward_rate':terms['velocity']/.02,
                             'terms_per_step':terms})
        reports.append({'config':path,'cases':rows})
    return {'scope':'SYNTHETIC_REWARD_FUNCTION_ONLY','physics_executed':False,
            'standing_or_walking_success_claimed':False,
            'note':'Ideal synthetic snapshots, not dynamically reachable trajectories; ranking alone does not prove learnability.',
            'reports':reports}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,default=Path('outputs/reward_audit.json'))
    args=p.parse_args();result=audit();save_json(args.out,result)
    for cfg in result['reports']:
        print(cfg['config'])
        for r in cfg['cases']:
            print(f"  cmd={r['command_m_s']:.2f} {r['case']:11s} velocity={r['velocity_reward_rate']:+.3f}/s total={r['reward_rate_synthetic']:+.3f}/s")
    print('SYNTHETIC ONLY: not a MuJoCo rollout or a trained result.')
    return 0

if __name__=='__main__':raise SystemExit(main())
