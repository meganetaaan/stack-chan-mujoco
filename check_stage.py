#!/usr/bin/env python3
"""Check *every* command in a held-out evaluation before advancing a curriculum.

Exit 0: criterion met on the supplied recorded trials. Exit 2: keep this stage.
This gate does not train, edit checkpoints, or guarantee robustness/hardware safety.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path


def check_report(report: dict, minimum_success: float) -> tuple[bool, list[dict]]:
    if not 0 < minimum_success <= 1:
        raise ValueError('minimum_success must be in (0,1]')
    groups=report.get('results')
    if not report.get('physics_executed') or not isinstance(groups,list) or not groups:
        raise ValueError('Expected evaluate.py output with real rollout results')
    outcomes=[]
    for group in groups:
        episodes=group.get('episode_results',[])
        if not episodes:
            raise ValueError('Evaluation has no per-episode evidence')
        command=float(group['command_forward_m_s'])
        def accepted(s):
            checks=s.get('success_checks',{})
            if not s.get('is_success') or not checks or not all(checks.values()):return False
            if abs(s.get('requested_forward_m_s',-1.)-command)>1e-8:return False
            if s.get('terminated') or not s.get('time_limit_reached'):return False
            if command > .003:
                return min(s.get('valid_landings',[0,0]))>=2 and min(s.get('forward_landings',[0,0]))>=1 and s['forward_m']>=.025
            return True
        rate=sum(accepted(s) for s in episodes)/len(episodes)
        outcomes.append({'command_m_s':command,'episodes':len(episodes),
                         'verified_success_rate':rate,'pass':rate>=minimum_success})
    return all(g['pass'] for g in outcomes),outcomes


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--evaluation',type=Path,required=True)
    p.add_argument('--min-success',type=float,default=.60)
    args=p.parse_args()
    ok,groups=check_report(json.loads(args.evaluation.read_text()),args.min_success)
    for g in groups:print(f"vx={g['command_m_s']:.3f}: {g['verified_success_rate']:.0%} ({g['episodes']} trials) {'PASS' if g['pass'] else 'KEEP_CURRENT_STAGE'}")
    print('READY_FOR_NEXT_STAGE_ON_THESE_TRIALS' if ok else 'KEEP_CURRENT_STAGE; do not promote from reward/elapsed timesteps alone.')
    return 0 if ok else 2

if __name__=='__main__':raise SystemExit(main())
