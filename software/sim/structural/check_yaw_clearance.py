"""B-rep yaw coupler/support clearance over continuous recorded angle ranges.

The between-sample lower bound assumes rigid single-axis rotation; deformation
and manufacturing allowances are separately subtracted, not modeled as loads.
"""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import cadquery as cq
import numpy as np

ROOT=Path(__file__).resolve().parents[3]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--step-deg', type=float, default=.25)
    p.add_argument('--include-cradle', action='store_true')
    p.add_argument('--joint-limits', action='store_true', help='Cover full model yaw limits instead of recorded interval')
    p.add_argument('--support-dir',type=Path,help='Directory with revised left/right support STEP files')
    a=p.parse_args()
    if not np.isfinite(a.step_deg) or a.step_deg<=0 or a.step_deg>5:
        p.error('step must be finite, positive and <= 5 degrees')
    a.out.mkdir(parents=True,exist_ok=False)
    design=ROOT/'software/sim/mujoco/assets/r9_fast_turn_v1'
    scene=design/'models/scene.xml'
    # qpos starts with the one free joint, followed by scalar hinge joints in XML order.
    joints=ET.parse(scene).findall('.//worldbody//joint')
    assert all(j.get('type','hinge')=='hinge' for j in joints)
    assert len(ET.parse(scene).findall('.//worldbody//freejoint'))==1
    indices={j.get('name'):7+i for i,j in enumerate(joints)}
    paths=[ROOT/f'validation/prototype_epic4_v1/actuator_fullbody_load_{direction}_v1/trace.npz' for direction in ('left','right')]
    q=[np.load(path,allow_pickle=False)['qpos'] for path in paths]
    assert all(x.shape[1]==7+len(joints) for x in q)
    criteria=dict(residual_clearance_min_mm=.5, tolerance_per_part_mm=.2,
                  assumed_deflection_per_part_mm=.2)
    plan=dict(scope=__doc__, include_cradle=a.include_cradle, angle_scope='model joint limits' if a.joint_limits else 'recorded interval', criteria=criteria, step_deg=a.step_deg,
              source_sha256={str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [scene,*paths]},
              limitations=['Only yaw coupler versus its fixed support, not the full assembly',
                           ('Model yaw limits covered; excursions beyond limits not covered' if a.joint_limits else 'Recorded angle interval assumes continuous interpolation; unrecorded excursions not covered'),
                           'Deflection allowances are requirements, not proof of actual worst-case deformation',
                           'No fastener/harness/tool shapes in this pair study'])
    (a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    results=[]
    for side,sign in [('left',1),('right',-1)]:
        column=indices[side+'_hip_yaw']
        lo=min(float(x[:,column].min()) for x in q)
        hi=max(float(x[:,column].max()) for x in q)
        if a.joint_limits:
            assert ET.parse(scene).find('compiler').get('angle')=='radian'
            lo,hi=map(float,next(j for j in joints if j.get('name')==side+'_hip_yaw').get('range').split())
        angles=np.linspace(lo,hi,max(2,int(np.ceil(np.rad2deg(hi-lo)/a.step_deg))+1))
        moving_path=design/'cad'/f'{side}_yaw_coupler.step'
        moving=cq.importers.importStep(str(moving_path)).val()
        moving_paths=[moving_path]
        if a.include_cradle:
            cradle_path=ROOT/'software/sim/mujoco/assets/r8_yaw_offset_flange_v1/cad'/f'{side}_fixed_roll_cradle.step'
            cradle=cq.importers.importStep(str(cradle_path)).val().translate((0,sign*4,0))
            moving=cq.Compound.makeCompound([moving,cradle])
            moving_paths.append(cradle_path)
        pivot=(-5,sign*26,62)
        b=moving.BoundingBox()
        radius=max(np.hypot(x-pivot[0],y-pivot[1]) for x,y in itertools.product([b.xmin,b.xmax],[b.ymin,b.ymax]))
        # Every angle lies within half a grid interval of a sample. A point's
        # chord displacement is <= radius * angle_difference (radians).
        sampling_bound=radius*float(np.diff(angles).max())/2
        for variant,path in [('original',design/'cad'/f'{side}_yaw_fixed_support.step'),
                             ('ribbed_connection',(a.support_dir.resolve() if a.support_dir else ROOT/'validation/yaw_connection_development_v1/yaw_connection_v1')/f'{side}_yaw_fixed_support.step')]:
            fixed=cq.importers.importStep(str(path)).val()
            rows=[]
            for angle in angles:
                shape=moving.rotate(pivot,(pivot[0],pivot[1],pivot[2]+1),float(np.rad2deg(angle)))
                distance=float(fixed.distance(shape))
                rows.append([float(angle),distance])
            values=np.array(rows)
            worst=int(values[:,1].argmin())
            lower=float(values[worst,1])-sampling_bound-2*criteria['tolerance_per_part_mm']-2*criteria['assumed_deflection_per_part_mm']
            row=dict(side=side,variant=variant,angle_range_rad=[lo,hi],sample_count=len(angles),
                     radial_bound_mm=float(radius),sampling_miss_bound_mm=sampling_bound,
                     minimum_sampled_distance_mm=float(values[worst,1]),minimum_angle_rad=float(values[worst,0]),
                     residual_lower_bound_mm=lower,passed_screen=bool(lower>=criteria['residual_clearance_min_mm']),
                     cad_sha256={str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [*moving_paths,path]})
            np.savez_compressed(a.out/f'{side}_{variant}.npz',angle_rad=values[:,0],distance_mm=values[:,1])
            results.append(row)
            print(json.dumps(row),flush=True)
    report=dict(scope=__doc__,results=results,passed_screen=all(r['passed_screen'] for r in results),assembly_clearance_verified=False)
    (a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':
    main()
