"""Screen a four-bolt yaw-support connection over all recorded load samples.

This does not prove plate strength, clamp retention, contact or fatigue. A
prying multiplier is an explicit screening assumption, not an FE-derived factor.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

ROOT=Path(__file__).resolve().parents[3]


def skew(r):
    x,y,z=r
    return np.array([[0,-z,y],[z,0,-x],[-y,x,0]])


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    config_path=ROOT/'board/mechanical/engineering/yaw_fasteners.json'
    config=json.loads(config_path.read_text())
    positions=np.array(config['pattern_relative_mm'])
    mapping=np.hstack([np.vstack((np.eye(3),skew(r))) for r in positions])
    transfer=mapping.T@np.linalg.inv(mapping@mapping.T)
    np.testing.assert_allclose(mapping@transfer,np.eye(6),atol=1e-12)
    evidence=ROOT/'validation/prototype_epic4_v1'
    sources=sorted((evidence/'actuator_suite_v2').glob('*/trace.npz'))+sorted(evidence.glob('actuator_fullbody_load_*/trace.npz'))
    plan={'scope':__doc__,'config':config,'config_sha256':hashlib.sha256(config_path.read_bytes()).hexdigest(),
          'source_sha256':{str(s.relative_to(ROOT)):hashlib.sha256(s.read_bytes()).hexdigest() for s in sources},
          'criteria':{'bolt_equivalent_stress_MPa':config['bolt']['proof_stress_MPa']/config['bolt']['safety_factor'],
                      'plastic_bearing_MPa':config['plastic_bearing_screen']['allowable_MPa']}}
    (a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    sys.path.insert(0,str(ROOT/'software/sim/actuator'))
    from fixtures import full_body
    sim,_=full_body()
    rows=[]
    for source in sources:
        report=json.loads(source.with_name('report.json').read_text());names=report['joint_names']
        with np.load(source) as archive:
            data={k:archive[k] for k in ['time','joint_wrench_local_force_moment']}
            data['q']=archive['q_rad'] if 'q_rad' in archive else archive['qpos']
            full='q_rad' not in archive
        for side in ['left','right']:
            joint=side+'_hip_yaw'
            if joint not in names:continue
            j=names.index(joint)
            q=data['q'][:,sim.m.joint(joint).qposadr[0] if full else j]
            w=data['joint_wrench_local_force_moment'][:,j].copy()
            for offset in [0,3]:
                x=w[:,offset].copy();y=w[:,offset+1].copy()
                w[:,offset]=np.cos(q)*x-np.sin(q)*y
                w[:,offset+1]=np.sin(q)*x+np.cos(q)*y
            w=-w
            w[:,3:]*=1000
            center=np.array(config[f'group_center_{side}_base_mm'])
            joint_origin=np.array([-5,26 if side=='left' else -26,62])
            w[:,3:]+=np.cross(joint_origin-center,w[:,:3])
            bolt=(w@transfer.T).reshape(-1,4,3)
            residual=bolt.reshape(-1,12)@mapping.T-w
            assert abs(residual).max()<1e-8
            design=bolt*config['prying_multiplier_assumed']
            axial=abs(design[:,:,0]);shear=np.linalg.norm(design[:,:,1:],axis=2)
            area=config['bolt']['nominal_tensile_area_mm2']
            equiv=np.sqrt(axial**2+3*shear**2)/area
            bearing=shear/(config['plastic_bearing_screen']['diameter_mm']*config['plastic_bearing_screen']['thickness_mm'])
            worst=np.unravel_index(np.argmax(equiv),equiv.shape)
            row={'source':str(source.relative_to(ROOT)),'side':side,'samples':len(q),
                 'peak_axial_design_N':float(axial.max()),'peak_shear_design_N':float(shear.max()),
                 'peak_bolt_equivalent_MPa':float(equiv.max()),'peak_plastic_bearing_MPa':float(bearing.max()),
                 'worst_bolt_index':int(worst[1]),'worst_time_s':float(data['time'][worst[0]]),
                 'passed_screen':bool(equiv.max()<=plan['criteria']['bolt_equivalent_stress_MPa'] and bearing.max()<=plan['criteria']['plastic_bearing_MPa'])}
            label=source.parent.name+'_'+side
            np.savez_compressed(a.out/(label+'.npz'),time_s=data['time'],wrench_at_bolt_group_N_Nmm=w,
                                bolt_force_N=bolt,design_force_N=design,bolt_equivalent_MPa=equiv,plastic_bearing_MPa=bearing)
            rows.append(row)
    result={'scope':__doc__,'rows':rows,'passed_screen':all(r['passed_screen'] for r in rows),
            'total_group_time_samples':sum(r['samples'] for r in rows),
            'max_bolt_equivalent_MPa':max(r['peak_bolt_equivalent_MPa'] for r in rows),
            'max_plastic_bearing_MPa':max(r['peak_plastic_bearing_MPa'] for r in rows),
            'connection_verified':False}
    (a.out/'report.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['rows','scope']}))


if __name__=='__main__':main()
