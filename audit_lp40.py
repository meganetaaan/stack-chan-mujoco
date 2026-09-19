#!/usr/bin/env python3
"""Audit new reward terms on synthetic states; not a physical rollout."""
from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
from stackchan_rl.config import ROOT, load_config, save_json
from stackchan_rl.rewards import reward_terms


def state(speed: float, command: float=.02, raw_delta: float=0., second_delta: float=0.):
    return dict(command=np.array([command,0.,0.]),velocity=np.array([speed,0.,0.]),
        tilt_rad=0.,height_error=0.,heading_error=0.,position_error=np.zeros(2),
        contacts=np.array([True,True]),pose_normalized=np.zeros(10),gyro=np.zeros(3),
        qd=np.zeros(10),torque_fraction_sq=0.,power_W=0.,action_delta=np.full(10,raw_delta),
        action_second_delta=np.full(10,second_delta),slip_speed_sq=0.,saturation=0.,
        self_contact=False,swing_mask=np.array([True,False]),foot_height=np.zeros(2),
        loads=np.array([4.,4.]),valid_landings_this_step=0,walk_objective_version=4,
        requested_forward_m_s=command,new_forward_distance_m=max(0.,speed)*.02,
        no_step_elapsed_s=0.,no_step_grace_s=1.5,no_step_ramp_s=1.,gait_quality={})


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,default=Path('outputs/lp40_reward_audit.json'))
    a=p.parse_args();cfg=load_config(ROOT/'configs/walk_lp40.json')
    results=[]
    for label,s in [('stopped',state(0)),('half_speed',state(.01)),('command_match',state(.02)),
                    ('overspeed_40pct',state(.028)),('double_speed',state(.04)),
                    ('raw_oscillation',state(.02,raw_delta=.437,second_delta=.848))]:
        r=reward_terms(s,cfg['reward'],'walk',.02,False)
        row={'case':label,'velocity_m_s':float(s['velocity'][0]),'terms_per_second':{k:v/.02 for k,v in r.items()},
             'total_per_second':sum(r.values())/.02}
        results.append(row)
        print(label, {k:round(row['terms_per_second'][k],5) for k in ('velocity','forward_progress','overspeed','action_rate','action_acceleration')})
    save_json(a.out,{'status':'SYNTHETIC_REWARD_FUNCTION_ONLY','physics_executed':False,
                     'note':'No gait, contact force, training convergence or performance claim.', 'cases':results})
    return 0
if __name__=='__main__':raise SystemExit(main())
