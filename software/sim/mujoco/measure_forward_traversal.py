#!/usr/bin/env python3
"""Measure a forward-distance crossing in a probe log, not hardware acceptance."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--distance-m', type=float, default=10.)
    args = p.parse_args()
    if not math.isfinite(args.distance_m) or args.distance_m <= 0:
        p.error('distance must be positive and finite')
    trajectory = args.run/'trajectory.csv'
    report_file = args.run/'report.json'
    report = json.loads(report_file.read_text())
    with trajectory.open() as f:
        rows = list(csv.DictReader(f))
    previous_t, previous_x = 0.,0.
    result = {'scope':'Single simulated forward-distance measurement; not 20-trial or hardware acceptance',
              'time_origin':'Probe reset t=0, including initial stand',
              'distance_m':args.distance_m,'crossing':None,
              'reported_run_failure':report.get('simulation',{}).get('failure'),
              'contact_metrics':report.get('simulation',{}).get('contact_metrics'),
              'hardware_tested':False,'goal_achieved':False}
    for row in rows:
        t,x = float(row['time_s']),float(row['forward_m'])
        if not all(math.isfinite(v) for v in (t,x)) or t <= previous_t:
            p.error('nonfinite or nonincreasing trajectory time')
        if result['crossing'] is None and x >= args.distance_m:
            interpolated = previous_t+(t-previous_t)*(args.distance_m-previous_x)/(x-previous_x)
            result['crossing'] = {'previous_time_s':previous_t,'first_sample_at_distance_time_s':t,
                                  'interpolated_time_s':interpolated,
                                  'conservative_average_speed_m_s':args.distance_m/t,
                                  'sample_forward_m':x}
        previous_t,previous_x = t,x
    result['input_sha256'] = {str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in (trajectory,report_file)}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2)+'\n')
    print(result['crossing'])


if __name__ == '__main__':
    main()
