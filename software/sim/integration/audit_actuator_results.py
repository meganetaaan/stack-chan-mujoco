"""Independently recalculate component acceptance from saved numeric traces.

Run from repository root. This audit does not infer collision absence from
positions: the runner's contact/protection observations remain separate evidence.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np


def audit(root):
    def read(path):
        return json.loads(path.read_text())
    def arrays(path):
        with np.load(path) as data:
            result = {k: data[k] for k in data.files}
        assert all(np.isfinite(v).all() for v in result.values()), path
        return result
    suite = root / 'actuator_suite_v2'
    workload = root / 'actuator_workload_v2'
    contract = read(workload / 'requirements.json')
    joints = read(Path('board/mechanical/prototype/joints.json'))
    specs = read(Path('software/sim/actuator/catalog.json'))['models']
    joint_map = {j['name']: j for j in joints}
    plan = read(suite / 'plan.json')
    for name, digest in plan['sources'].items():
        path = Path(name)
        if path.parts[0] == 'outputs':
            path = root.joinpath(*path.parts[1:])
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, name
    sources = {}
    for name, digest in contract['source_sha256'].items():
        assert hashlib.sha256((workload/name).read_bytes()).hexdigest() == digest
        sources[name] = arrays(workload/name)
    for i, requirement in enumerate(contract['joint_requirements']):
        assert requirement['joint'] == joints[i]['name']
        bounds = [min(d['q_rad'][:, i].min() for d in sources.values()),
                  max(d['q_rad'][:, i].max() for d in sources.values())]
        np.testing.assert_allclose(bounds, requirement['required_motion_rad'], atol=1e-12)
        peak = max(abs(d['torque_Nm'][:, i]).max() for d in sources.values())
        assert abs(peak-abs(requirement['external_fixture_load_Nm'])) < 1e-12
        selected = sources[requirement['source_peak_file']]
        k = np.argmax(abs(selected['torque_Nm'][:, i]))
        assert abs(selected['time'][k]-requirement['source_peak_time_s']) < 1e-12
        assert abs(selected['torque_Nm'][k, i]+requirement['external_fixture_load_Nm']) < 1e-12
    worst_error = 0.
    for case in plan['cases']:
        folder = suite / case['name']
        report = read(folder/'report.json')
        d = arrays(folder/'trace.npz')
        t = d['time']
        assert len(t) == 7000 and abs(t[-1]-7) < 1e-8
        np.testing.assert_allclose(np.diff(t), .001, atol=1e-12)
        error = d['q_rad']-d['desired_rad']
        peak = abs(error).max()
        worst_error = max(worst_error, float(peak))
        assert peak <= contract['leg_gates']['peak_joint_tracking_error_rad']
        assert np.all(np.sqrt(np.mean(error**2, axis=0)) <= contract['leg_gates']['rms_joint_tracking_error_rad'])
        voltage = report['parameters']['voltage']
        assert abs(d['motor_terminal_V']).max() <= voltage+1e-10
        for i, name in enumerate(report['joint_names']):
            joint = joint_map[name]
            spec = specs[joint['motor'].split()[-1]]
            lo, hi = joint['mechanical_range_rad']
            assert d['q_rad'][:,i].min() >= lo-.001
            assert d['q_rad'][:,i].max() <= hi+.001
            assert abs(d['motor_current_A'][:,i]).max() <= spec['analysis_current_limit_A']+1e-10
            assert abs(d['torque_Nm'][:,i]).max() <= spec['analysis_torque_limit_Nm']+1e-10
        losses = sum(d[k] for k in ['copper_loss_W','gear_loss_W','idle_loss_W'])
        assert losses.min() >= -1e-12
        np.testing.assert_allclose(d['supply_power_W'], d['mechanical_power_W']+losses, atol=1e-12)
        np.testing.assert_allclose(d['supply_current_A']*voltage, d['supply_power_W'], atol=1e-12)
        assert d['case_temperature_C'].max() < 70
        weight = report['fixture_weight_N']
        if case['mode'] == 'support':
            assert d['floor_load_N'][t>=4].min() >= .9*weight
        elif case['mode'] == 'transfer':
            window = ((t>=1)&(t<=1.9))|((t>=3.4)&(t<=3.9))|(t>=6)
            assert abs(d['floor_load_N'][window]-d['expected_floor_load_N'][window]).max() <= .15*weight
        else:
            assert abs(d['floor_load_N']).max() < 1e-12
        assert report['failure'] is None and all(report['gates'].values())
    for joint in joints:
        d = arrays(suite/'single_joint'/(joint['name']+'.npz'))['trace']
        assert len(d) == 5000 and abs(d[-1,0]-5) < 1e-8
        error = abs(d[:,2]-d[:,1])
        gates = contract['single_joint_gates']
        assert error.max() <= gates['transient_error_rad']
        assert error[d[:,0]>=3.4+gates['settling_s']].max() <= gates['steady_error_rad']
        spec = specs[joint['motor'].split()[-1]]
        assert abs(d[:,5]).max() <= spec['analysis_current_limit_A']+1e-10
        assert abs(d[:,4]).max() <= spec['analysis_torque_limit_Nm']+1e-10
        lo, hi = joint['mechanical_range_rad']
        assert d[:,2].min() >= lo-.001 and d[:,2].max() <= hi+.001
    export_peaks = {}
    for side in ['left','right']:
        source = arrays(root/f'actuator_fullbody_load_{side}_v1/trace.npz')
        export = arrays(root/f'load_export_{side}_v1/loads.npz')
        for key in ['joint_wrench_local_force_moment','motor_current_A','torque_Nm','supply_current_A','supply_power_W']:
            np.testing.assert_array_equal(source[key], export[key])
        draw = np.maximum(source['supply_current_A'],0).sum(axis=1)
        regeneration = -np.minimum(source['supply_current_A'],0).sum(axis=1)
        np.testing.assert_allclose(export['draw_A'], draw, atol=1e-12)
        np.testing.assert_allclose(export['regeneration_A'], regeneration, atol=1e-12)
        np.testing.assert_allclose(export['net_A'], draw-regeneration, atol=1e-12)
        np.testing.assert_allclose(export['simultaneous_drive_fraction'], (abs(source['motor_current_A'])>=.05).sum(axis=1)/12)
        export_peaks[side] = float(draw.max())
    return {'passed':True, 'source_hashes_checked':len(plan['sources']),
            'workload_motions':len(sources), 'single_joint_cases':len(joints),
            'leg_cases':len(plan['cases']), 'worst_leg_error_rad':worst_error,
            'export_peak_draw_A':export_peaks,
            'limitations':['Collision and protection absence relies on runner observations.',
                           'Does not validate real hardware or certify continuous ratings.',
                           'Thermal sweep and overloaded step cases have separate evidence.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('outputs'))
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.root)
    args.out.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))
