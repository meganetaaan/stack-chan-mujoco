#!/usr/bin/env python3
"""Read evaluation JSON; explain failed checks and compare paired rollouts.

No renderer, MuJoCo, SB3 or checkpoint modification. Missing metrics are reported
as missing, never inferred from forward distance or a success flag.
"""
from __future__ import annotations
import argparse
from collections import Counter
import json
import math
from pathlib import Path
import numpy as np

FIELDS = ('forward_m', 'mean_abs_forward_velocity_error_m_s', 'pitch_rate_rms_rad_s',
          'roll_rate_rms_rad_s', 'body_pitch_peak_to_peak_deg', 'action_delta_rms',
          'action_second_difference_rms', 'mean_excess_load_cost',
          'target_delta_rms_rad_mean', 'distance_tracking_abs_error_m', 'step_repeat_fraction')


def episodes(report: dict) -> list[dict]:
    if not report.get('physics_executed') or report.get('status') == 'IN_PROGRESS':
        raise ValueError('Expected a completed physical evaluate.py result, not a partial/synthetic report')
    groups = report.get('results', [report])
    result = []
    for g in groups:
        result.extend(g.get('episode_results', []))
    if not result:
        raise ValueError('No per-episode evidence')
    return result


def summarize(report: dict) -> dict:
    eps = episodes(report)
    failed = Counter()
    for e in eps:
        failed.update(k for k, ok in e.get('success_checks', {}).items() if not ok)
        failed.update('quality/'+k for k, ok in e.get('quality_checks', {}).items() if not ok)
    result = {'episodes': len(eps), 'success_rate': sum(bool(e.get('is_success')) for e in eps)/len(eps),
              'failure_reasons': dict(Counter(e.get('failure_reason') or 'time_limit' for e in eps)),
              'failed_checks': dict(failed), 'commands': {}, 'missing_metrics': []}
    for v in sorted({float(e['requested_forward_m_s']) for e in eps}):
        xs = [e for e in eps if float(e['requested_forward_m_s']) == v]
        m = {'episodes':len(xs), 'success_rate':float(np.mean([bool(e.get('is_success')) for e in xs])),
             'valid_landings_mean':np.mean([e['valid_landings'] for e in xs], axis=0).tolist(),
             'forward_landings_mean':np.mean([e.get('forward_landings',[0,0]) for e in xs],axis=0).tolist()}
        for name in FIELDS:
            if all(name in e and isinstance(e[name],(int,float)) and math.isfinite(e[name]) for e in xs):
                m[name] = {'mean':float(np.mean([e[name] for e in xs])), 'max':float(max(e[name] for e in xs))}
            else:
                result['missing_metrics'].append(name)
        if all('peak_sole_load_bw' in e for e in xs):
            m['peak_sole_load_bw'] = {'mean':float(np.mean([max(e['peak_sole_load_bw']) for e in xs])),
                                     'max':float(max(max(e['peak_sole_load_bw']) for e in xs))}
        result['commands'][f'{v:.6f}'] = m
    result['missing_metrics'] = sorted(set(result['missing_metrics']))
    return result


def compare(old: dict, new: dict) -> dict:
    """Experimental paired criteria, not a significance test or hardware rating."""
    a, b = episodes(old), episodes(new)
    def key(s):return (float(s['requested_forward_m_s']), s.get('seed'))
    ka,kb=[key(s) for s in a],[key(s) for s in b]
    if any(k[1] is None for k in ka+kb) or len(set(ka)) != len(ka) or len(set(kb)) != len(kb) or set(ka) != set(kb):
        raise ValueError('Baseline/candidate must use the same commands and distinct episode seeds')
    if old.get('no_noise') != new.get('no_noise'):
        raise ValueError('Baseline and candidate use different reset noise settings')
    if not old.get('config') or not new.get('config'):
        raise ValueError('Re-evaluate both checkpoints with the SAME explicit evaluation config before comparison')
    for k in ('env','reward','success'):
        if old['config'][k] != new['config'][k]:
            raise ValueError('Different evaluation configuration: '+k)
    if old.get('interface') != new.get('interface') or not old.get('interface'):
        raise ValueError('Missing or mismatched model / policy I/O interface')
    for s in a+b:
        if s.get('quality_samples',0)<=0:
            raise ValueError('Missing substep quality evidence; old CSV cannot reconstruct it')
    oa,nb=summarize(old),summarize(new)
    checks={}; changes={}
    for cmd in oa['commands']:
        x,y=oa['commands'][cmd],nb['commands'][cmd]
        if float(cmd) <= .003:continue
        prefix=cmd+'/'
        v4 = new['config']['env']['walk_objective_version'] == 4
        if v4:
            criteria = new['config']['success']
            command_episodes = [s for s in b if abs(s['requested_forward_m_s']-float(cmd)) < 1e-9]
            expected = float(np.mean([s['commanded_distance_m'] for s in command_episodes]))
            checks[prefix+'command_distance_band'] = criteria['refine_distance_ratio_min']*expected <= y['forward_m']['mean'] <= criteria['refine_distance_ratio_max']*expected
            checks[prefix+'distance_error_not_worse'] = y['distance_tracking_abs_error_m']['mean'] <= x['distance_tracking_abs_error_m']['mean']+1e-9
            checks[prefix+'velocity_error_not_worse'] = y['mean_abs_forward_velocity_error_m_s']['mean'] <= x['mean_abs_forward_velocity_error_m_s']['mean']+1e-9
            checks[prefix+'target_rate_not_worse'] = y['target_delta_rms_rad_mean']['mean'] <= 1.05*x['target_delta_rms_rad_mean']['mean']+1e-9
            checks[prefix+'repeat_fraction_not_worse'] = y['step_repeat_fraction']['mean'] <= x['step_repeat_fraction']['mean']+1e-9
            checks[prefix+'pitch_rate_not_worse'] = y['pitch_rate_rms_rad_s']['mean'] <= 1.05*x['pitch_rate_rms_rad_s']['mean']+1e-9
        else:
            checks[prefix+'retain_forward_85pct'] = y['forward_m']['mean'] >= max(.08,.85*x['forward_m']['mean'])
            checks[prefix+'pitch_rate_down_10pct'] = y['pitch_rate_rms_rad_s']['mean'] <= .9*x['pitch_rate_rms_rad_s']['mean']
        checks[prefix+'steps_both_feet'] = min(y['forward_landings_mean']) >= 2
        checks[prefix+'action_rate_not_worse'] = y['action_delta_rms']['mean'] <= 1.05*x['action_delta_rms']['mean']+1e-9
        checks[prefix+'peak_load_not_worse'] = y['peak_sole_load_bw']['max'] <= 1.05*x['peak_sole_load_bw']['max']+1e-9
        fields = ['forward_m','pitch_rate_rms_rad_s','action_delta_rms','body_pitch_peak_to_peak_deg','peak_sole_load_bw']
        if v4:
            fields += ['target_delta_rms_rad_mean', 'distance_tracking_abs_error_m', 'step_repeat_fraction',
                       'mean_abs_forward_velocity_error_m_s']
        for f in fields:
            changes[prefix+f]={'baseline':x[f]['mean'],'candidate':y[f]['mean'], 'delta':y[f]['mean']-x[f]['mean']}
    if not checks:raise ValueError('At least one positive movement command is required')
    checks['no_more_terminations']=sum(bool(s['terminated']) for s in b)<=sum(bool(s['terminated']) for s in a)
    checks['no_more_contact_violations']=sum(s.get('bad_contact_steps',0)+s.get('self_contact_steps',0) for s in b)<=sum(s.get('bad_contact_steps',0)+s.get('self_contact_steps',0) for s in a)
    return {'checks':checks,'criteria_met':all(checks.values()),'changes':changes,
            'note':'Paired-trial engineering criteria only; not statistical significance, proof of convergence or hardware safety.'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--evaluation',type=Path,required=True)
    p.add_argument('--baseline',type=Path)
    p.add_argument('--out',type=Path)
    args=p.parse_args()
    report=json.loads(args.evaluation.read_text(encoding='utf-8'))
    result={'current':summarize(report)}
    print('不合格条件:',result['current']['failed_checks'])
    print('終了理由:',result['current']['failure_reasons'])
    for command,m in result['current']['commands'].items():
        print('command=',command,json.dumps(m,ensure_ascii=False))
    if result['current']['missing_metrics']:
        print('未計測（推定しません）:',', '.join(result['current']['missing_metrics']))
    if args.baseline:
        result['comparison']=compare(json.loads(args.baseline.read_text(encoding='utf-8')),report)
        print('比較条件:',json.dumps(result['comparison']['checks'],ensure_ascii=False))
        print('CRITERIA_MET' if result['comparison']['criteria_met'] else 'REVIEW_FAILED_COMPARISON_CHECKS')
    if args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
    return 0

if __name__=='__main__':raise SystemExit(main())
