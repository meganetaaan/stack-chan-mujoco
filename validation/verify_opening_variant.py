#!/usr/bin/env python3
"""Verify a bottom-opening variant preserves components and joint geometry."""
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import mujoco


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline', required=True, type=Path)
    p.add_argument('--candidate', required=True, type=Path)
    p.add_argument('--out', required=True, type=Path)
    args = p.parse_args()
    old, new = args.baseline, args.candidate
    a = json.loads((old/'robot.json').read_text())
    b = json.loads((new/'robot.json').read_text())
    meshes = sorted(path.name for path in (old/'models/meshes').glob('*.stl'))
    new_meshes = sorted(path.name for path in (new/'models/meshes').glob('*.stl'))
    changed = [name for name in meshes if not (new/'models/meshes'/name).exists()
               or (old/'models/meshes'/name).read_bytes() != (new/'models/meshes'/name).read_bytes()]

    def joints(path):
        return [(body.get('name'), body.get('pos'), body.find('joint').attrib)
                for body in ET.parse(path).findall('.//body') if body.find('joint') is not None]

    model = mujoco.MjModel.from_xml_path(str((new/'models/scene.xml').resolve()))
    checks = {'same_component_mesh_names': meshes == new_meshes,
              'only_shroud_mesh_changed': changed == ['body_shroud.stl'],
              'kinematics_unchanged': a['kinematics'] == b['kinematics'],
              'body_parameters_unchanged': a['body'] == b['body'],
              'joint_origins_axes_limits_unchanged': joints(old/'models/scene.xml') == joints(new/'models/scene.xml'),
              'model_dimensions': (model.nq,model.nv,model.nu) == (17,16,10)}
    report = {'scope':'Component and joint invariance, not strength or walking validation',
              'checks':checks,'passed':all(checks.values()),'changed_meshes':changed,
              'compiled_mass_kg':float(sum(model.body_mass)),
              'model_sha256':hashlib.sha256((new/'models/scene.xml').read_bytes()).hexdigest()}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2)+'\n')
    print('PASS' if report['passed'] else 'FAIL')
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
