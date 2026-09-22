"""Select actual simultaneous load samples from the EPIC 4 evidence.

No safety factor is embedded and no maxima from different times are combined.
Each sample retains every joint's wrench and drive current, its source and hash.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[3]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT/'validation/prototype_epic4_v1')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    sources = sorted((args.source/'actuator_suite_v2').glob('*/trace.npz'))
    sources += sorted(args.source.glob('actuator_fullbody_load_*/trace.npz'))
    selected = []
    provenance = []
    for path in sources:
        report = json.loads(path.with_name('report.json').read_text())
        names = report['joint_names']
        with np.load(path) as data:
            time = data['time']
            wrenches = data['joint_wrench_local_force_moment']
            currents = data['motor_current_A']
            torque = data['torque_Nm']
        assert wrenches.shape == (len(time), len(names), 6)
        assert np.isfinite(wrenches).all() and np.isfinite(currents).all()
        source = str(path.relative_to(ROOT))
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        provenance.append({'path':source,'sha256':digest,'samples':len(time),
                           'fixture':report.get('mode','fullbody'),
                           'parameters':report.get('parameters',report.get('settings'))})
        for j, name in enumerate(names):
            for criterion, magnitude in [('force_norm_N',np.linalg.norm(wrenches[:,j,:3],axis=1)),
                                         ('moment_norm_Nm',np.linalg.norm(wrenches[:,j,3:],axis=1)),
                                         ('shaft_torque_abs_Nm',abs(torque[:,j]))]:
                index = int(np.argmax(magnitude))
                selected.append({'joint':name,'criterion':criterion,'value':float(magnitude[index]),
                                 'source':source,'source_sha256':digest,'sample_index':index,
                                 'time_s':float(time[index]),'joint_names':names,
                                 'simultaneous_wrenches':wrenches[index].tolist(),
                                 'simultaneous_motor_current_A':currents[index].tolist()})
    envelope = []
    for joint in sorted({r['joint'] for r in selected}):
        for criterion in ['force_norm_N','moment_norm_Nm','shaft_torque_abs_Nm']:
            envelope.append(max((r for r in selected if r['joint']==joint and r['criterion']==criterion),key=lambda r:r['value']))
    result = {'schema_version':1,'status':'derived_load_input_not_structural_acceptance',
              'source_cases':provenance,'all_selected_samples':selected,'envelope_samples':envelope,
              'frame':'joint body local axes at joint origin; parent-on-child interface resultant',
              'order':['Fx_N','Fy_N','Fz_N','Mx_Nm','My_Nm','Mz_Nm'],'load_multiplier':1.,
              'limitations':['Transform each sample using its joint pose before application to global CAD.',
                             'Joint reactions do not describe internal bearing load distribution.',
                             'Fixture and free-body load cases are distinguished in provenance.',
                             'Peaks alone are not a fatigue spectrum or nonlinear load history.',
                             'Updated CAD mass/inertia requires load re-evaluation.']}
    (args.out/'loads.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'source_cases':len(sources),'selected':len(selected),'envelope':len(envelope)}))


if __name__ == '__main__':
    main()
