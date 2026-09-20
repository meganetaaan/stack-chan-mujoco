#!/usr/bin/env python3
"""Score a complete exploratory simulation suite, never hardware acceptance.

Requires 10 m within 100 s AND a clean completed run including the stopping phase.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runs',type=Path,required=True)
    p.add_argument('--variations',type=Path,default=Path('design/plant_variations'))
    p.add_argument('--out',type=Path,required=True)
    args = p.parse_args()
    manifest = json.loads((args.variations/'manifest.json').read_text())
    names = [Path(x).stem for x in manifest['cases']]
    if len(names)!=20 or len(set(names))!=20:
        p.error('requires exactly 20 distinct predefined cases')
    if any(not (args.runs/name/'report.json').exists() for name in names):
        p.error('suite incomplete; do not score missing trials as completed')
    if args.out.exists():
        p.error('use a new output directory')
    args.out.mkdir(parents=True)
    rows,sources,references = [],set(),set()
    for name in names:
        run = args.runs/name
        report = json.loads((run/'report.json').read_text())
        config = args.variations/(name+'.json')
        if report['plant_variation_input_sha256'] != hashlib.sha256(config.read_bytes()).hexdigest():
            raise ValueError('variation file mismatch: '+name)
        sources.add(json.dumps({k:report.get(k) for k in (
            'probe_sha256','plant_variation_code_sha256','source_sha256','stopping_reference_extension')},sort_keys=True))
        references.add(hashlib.sha256((run/'reference.json').read_bytes()).hexdigest())
        measurement = args.out/(name+'_traversal.json')
        if (run/'trajectory.csv').exists():
            subprocess.run([sys.executable,str(Path(__file__).with_name('measure_forward_traversal.py')),
                            '--run',str(run),'--out',str(measurement)],check=True,capture_output=True)
            crossing = json.loads(measurement.read_text())['crossing']
        elif report.get('planning_failure') is not None:
            crossing = None
        else:
            raise ValueError('missing trajectory without recorded planning failure: '+name)
        simulation = report.get('simulation',{})
        contacts = simulation.get('contact_metrics',{})
        contact_clean = all(contacts.get(k)==0 for k in (
            'self_penetration_steps','nonsole_floor_penetration_steps',
            'peak_self_contact_force_N','peak_nonsole_floor_force_N'))
        reaches = crossing is not None and crossing['conservative_average_speed_m_s'] >= .1
        clean_finish = simulation.get('completed_reference_without_model_failure') is True and contact_clean
        passed = reaches and clean_finish and simulation.get('external_root_forces_used') is False
        rows.append({'case':name,'crossing':crossing,'failure':simulation.get('failure'),
                     'duration_s':simulation.get('duration_s'),'forward_m':simulation.get('forward_m'),
                     'contact_clean':contact_clean,'clean_finish':clean_finish,
                     'ten_metres_within_100s':reaches,'simulation_screen_pass':passed})
    if len(sources)!=1 or len(references)!=1:
        raise ValueError('mixed code/models/controllers or changed nominal reference within suite')
    result = {'scope':'Exploratory assumed-uncertainty simulation, not hardware acceptance',
              'hardware_acceptance':False,'hardware_trials_performed_by_this_task':0,
              'case_count':20,'ten_metres_within_100s_count':sum(r['ten_metres_within_100s'] for r in rows),
              'clean_complete_run_count':sum(r['simulation_screen_pass'] for r in rows),
              'shared_reference_sha256':next(iter(references)),
              'uniform_source_signature':json.loads(next(iter(sources))), 'results':rows}
    (args.out/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(result['clean_complete_run_count'],'/ 20 clean complete simulated runs')


if __name__ == '__main__':
    main()
