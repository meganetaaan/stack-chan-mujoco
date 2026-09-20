#!/usr/bin/env python3
"""Geometry-only hip-spacing screen; not a connected CAD or dynamics candidate."""
import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path
import mujoco
import numpy as np
from stackchan_rl.residual import runtime_xml


def screen(scene, spacing_mm, angle_deg, samples, axis_x_mm=-25, foot_length_mm=94, inner_trim_mm=0, battery_dx_mm=0, side_wall_tray=False, toe_only=False):
    root = ET.fromstring(runtime_xml(scene))
    def translate(element, delta):
        pos = np.fromstring(element.get('pos', '0 0 0'), sep=' ')
        element.set('pos', ' '.join(map(str, pos + delta)))
    # Translate complete rotating assemblies and their fixed yaw cases/supports.
    # The battery tray and shell stay in place so their collisions remain visible.
    for side, sign in [('left', 1), ('right', -1)]:
        offset = sign * spacing_mm / 1000
        dx = (axis_x_mm + 25) / 1000
        yaw = root.find('.//body[@name="' + side + '_hip_yaw"]')
        translate(yaw, np.array([dx, offset, 0]))
        # Keep the original leg/cradle neutral pose while relocating its pivot.
        translate(yaw.find('body'), np.array([-dx, 0, 0]))
        for geom in yaw.findall('geom'):
            if any(part in geom.get('name', '') for part in ('fixed_roll_cradle', 'hip_roll_motor')):
                translate(geom, np.array([-dx, 0, 0]))
        for geom in root.findall('.//geom'):
            name = geom.get('name', '')
            if name.startswith(('col_' + side + '_yaw_motor_case',
                                'col_' + side + '_yaw_fixed_support')):
                translate(geom, np.array([dx, offset, 0]))
        trim = (94 - foot_length_mm) / 2000
        for part in ('foot_yoke_0', 'sole_TPU_0'):
            geom = root.find('.//geom[@name="col_' + side + '_' + part + '"]')
            size = np.fromstring(geom.get('size'), sep=' ')
            size[0] -= trim
            size[1] -= inner_trim_mm / 2000
            geom.set('size', ' '.join(map(str, size)))
            translate(geom, np.array([0, sign * inner_trim_mm / 2000, 0]))
            if toe_only:
                translate(geom, np.array([-trim, 0, 0]))
        for index, sign_x in [(3, -1), (4, 1)]:
            geom = root.find('.//geom[@name="col_' + side + '_boot_shell_' + str(index) + '"]')
            translate(geom, np.array([sign_x * trim, 0, 0]))
            if toe_only:
                translate(geom, np.array([-trim, 0, 0]))
            size = np.fromstring(geom.get('size'), sep=' ')
            size[1] -= inner_trim_mm / 2000
            geom.set('size', ' '.join(map(str, size)))
            translate(geom, np.array([0, sign * inner_trim_mm / 2000, 0]))
        inner_wall = root.find('.//geom[@name="col_' + side + '_boot_shell_2"]')
        translate(inner_wall, np.array([0, sign * inner_trim_mm / 1000, 0]))
    for geom in root.findall('.//body[@name="base"]/geom'):
        if 'battery' in geom.get('name', ''):
            translate(geom, np.array([battery_dx_mm / 1000, 0, 0]))
    if side_wall_tray:
        base = root.find('.//body[@name="base"]')
        for geom in list(base.findall('geom')):
            name = geom.get('name', '')
            if (name in ('col_battery_tray_7', 'col_battery_tray_8')
                    or name.startswith(('col_battery_yaw_detour_', 'col_battery_M3_envelope_'))):
                base.remove(geom)
        for sign in [-1, 1]:
            for name, size, pos in [
                ('arm', [0.003, 0.013, 0.0015], [(battery_dx_mm-1)/1000, sign*.049, .06005]),
                ('lug', [0.003, .001, .004], [(battery_dx_mm-1)/1000, sign*.0612, .062]),
                ('screw_envelope', [.002, .003, .002], [(battery_dx_mm-1)/1000, sign*.061, .063])]:
                ET.SubElement(base, 'geom', name=f'col_battery_side_{sign}_{name}',
                              type='box', size=' '.join(map(str, size)),
                              pos=' '.join(map(str, pos)), **{'class': 'collision'})
    # Compile after all changes so collision acceleration structures are rebuilt.
    model = mujoco.MjModel.from_xml_string(ET.tostring(root, encoding='unicode'))
    data = mujoco.MjData(model)
    worst = {}
    failed = 0
    leg_pair_failed = 0
    home = []
    for left in np.linspace(-angle_deg, angle_deg, samples):
        for right in np.linspace(-angle_deg, angle_deg, samples):
            mujoco.mj_resetDataKeyframe(model, data, 0)
            for side, angle in [('left', left), ('right', right)]:
                data.qpos[model.joint(side + '_hip_yaw').qposadr[0]] = np.deg2rad(angle)
            mujoco.mj_forward(model, data)
            bad = False
            leg_bad = False
            for contact in data.contact:
                names = [model.geom(contact.geom1).name, model.geom(contact.geom2).name]
                if 'floor' in names or contact.dist >= -1e-8:
                    continue
                bad = True
                key = ' / '.join(sorted(names))
                leg_bad |= (any(n.startswith('col_left_') for n in names)
                            and any(n.startswith('col_right_') for n in names))
                if abs(left) < 1e-9 and abs(right) < 1e-9:
                    home.append(key)
                if key not in worst or contact.dist < worst[key]['distance_m']:
                    worst[key] = {'distance_m': float(contact.dist),
                                  'yaw_deg': [float(left), float(right)]}
            failed += bad
            leg_pair_failed += leg_bad
    return {'outward_shift_per_leg_mm': spacing_mm, 'yaw_axis_x_mm': axis_x_mm,
            'foot_length_mm': foot_length_mm,
            'foot_inner_trim_mm': inner_trim_mm,
            'battery_dx_mm': battery_dx_mm,
            'side_wall_tray': side_wall_tray,
            'toe_only_shortening': toe_only,
            'yaw_range_deg': angle_deg, 'samples': samples ** 2,
            'failed_samples': failed, 'left_right_pair_failed_samples': leg_pair_failed,
            'home_penetration_pairs': sorted(set(home)), 'worst_by_pair': worst}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--axis-x-mm', type=float, nargs='+', default=[-25])
    parser.add_argument('--spacing-mm', type=float, nargs='+', default=[0, 2, 4, 6, 8])
    parser.add_argument('--angles-deg', type=float, nargs='+', default=[5, 10, 15, 20])
    parser.add_argument('--foot-length-mm', type=float, nargs='+', default=[94])
    parser.add_argument('--inner-trim-mm', type=float, nargs='+', default=[0])
    parser.add_argument('--battery-dx-mm', type=float, default=0)
    parser.add_argument('--side-wall-tray', action='store_true')
    parser.add_argument('--toe-only', action='store_true')
    args = parser.parse_args()
    if args.out.exists():
        parser.error('new output required')
    if any(not 82 <= value <= 94 for value in args.foot_length_mm):
        parser.error('foot length must be between 82 and 94 mm for this shell screen')
    if any(not 0 <= value <= 6 for value in args.inner_trim_mm):
        parser.error('inner trim must be between 0 and 6 mm')
    scene = Path('assets/r8_yaw_offset_flange_v1/models/scene.xml')
    rows = []
    for axis in args.axis_x_mm:
        for spacing in args.spacing_mm:
            for angle in args.angles_deg:
                for length in args.foot_length_mm:
                    for inner_trim in args.inner_trim_mm:
                        row = screen(scene, spacing, angle, 11, axis, length, inner_trim, args.battery_dx_mm, args.side_wall_tray, args.toe_only)
                        rows.append(row)
                        print(json.dumps({k: v for k, v in row.items() if k not in ('worst_by_pair', 'home_penetration_pairs')}), flush=True)
    report = {'scope': __doc__, 'rows': rows,
              'limitations': ['home pose only; discrete samples, no clearance margin',
                              'yaw sampled beyond existing joint limits',
                              'same-body overlaps require separate CAD inspection',
                              'shifted supports require new attachments and battery integration',
                              'relocated pivot requires redesigned coupler connection to unchanged cradle',
                              'visual meshes and inertia not regenerated; never use this as a dynamics model'],
              'source_sha256': {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in [Path(__file__), scene]}}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
