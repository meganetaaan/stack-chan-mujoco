#!/usr/bin/env python3
"""Verify collision additions preserve dynamics parameters and detect known CAD hits."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import mujoco


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline',type=Path,required=True)
    p.add_argument('--candidate',type=Path,required=True)
    p.add_argument('--baseline-replay',type=Path,required=True)
    p.add_argument('--candidate-replay',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    args = p.parse_args()
    old = mujoco.MjModel.from_xml_path(str((args.baseline/'models/scene.xml').resolve()))
    new = mujoco.MjModel.from_xml_path(str((args.candidate/'models/scene.xml').resolve()))
    fields = ('body_mass','body_inertia','body_ipos','body_iquat','body_pos','body_quat',
              'jnt_pos','jnt_axis','jnt_range','dof_damping','dof_frictionloss','dof_armature',
              'actuator_gear','actuator_ctrlrange','actuator_forcerange','key_qpos')
    checks = {name:bool(np.array_equal(getattr(old,name),getattr(new,name))) for name in fields}
    meshes = list((args.baseline/'models/meshes').glob('*.stl'))
    checks['visual_mesh_bytes_unchanged'] = all(
        p.read_bytes() == (args.candidate/'models/meshes'/p.name).read_bytes() for p in meshes)
    checks['parent_contact_filter_disabled'] = bool(new.opt.disableflags & int(mujoco.mjtDisableBit.mjDSBL_FILTERPARENT))
    checks['no_root_assistance'] = new.neq == 0 and not np.any(new.body_gravcomp)
    baseline = json.loads(args.baseline_replay.read_text())
    candidate = json.loads(args.candidate_replay.read_text())
    checks['baseline_replay_matches_model'] = baseline['model_sha256'] == hashlib.sha256((args.baseline/'models/scene.xml').read_bytes()).hexdigest()
    checks['candidate_replay_matches_model'] = candidate['model_sha256'] == hashlib.sha256((args.candidate/'models/scene.xml').read_bytes()).hexdigest()
    checks['same_trajectory'] = baseline['trajectory_sha256'] == candidate['trajectory_sha256']
    before = {r['row']:r['contacts'] for r in baseline['results']}
    after = {r['row']:r['contacts'] for r in candidate['results']}
    checks['control_poses_remain_clear'] = all(not after.get(i, [None]) for i in (0,50,100,200,300))
    for row in (315,320):
        checks[f'row_{row}_old_missed'] = row in before and not before[row]
        for part in ('thigh_yoke','shin_yoke'):
            checks[f'row_{row}_{part}_now_detected'] = any(
                any(c[k].startswith('col_left_'+part+'_') for k in ('a','b')) and
                any(c[k].startswith('col_left_ankle_gimbal_') for k in ('a','b'))
                for c in after.get(row,[]))
    inputs = [args.baseline_replay,args.candidate_replay,
              args.baseline/'models/scene.xml',args.candidate/'models/scene.xml']
    report = {'scope':'Known-contact regression and physical-parameter invariance; not whole-robot collision coverage',
              'passed':all(checks.values()),'checks':checks,
              'input_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2)+'\n')
    print('PASS' if report['passed'] else 'FAIL')
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
