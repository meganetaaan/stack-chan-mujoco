"""Diagnostic r9 yaw-support screen under one recorded simultaneous wrench.

An ideal bonded back face is deliberately used as an optimistic support. A
failure warrants redesign; a pass would not certify fasteners or contact.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import cadquery as cq
import numpy as np
from elasticity import tetrahedralize, analyze

ROOT=Path(__file__).resolve().parents[3]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--loads',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--step',type=Path)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    loads=json.loads(a.loads.read_text())
    selected=next(r for r in loads['envelope_samples'] if r['joint']=='left_hip_yaw' and r['criterion']=='moment_norm_Nm')
    source=ROOT/selected['source']
    assert hashlib.sha256(source.read_bytes()).hexdigest()==selected['source_sha256']
    trace=np.load(source);index=selected['sample_index'];joint_index=selected['joint_names'].index('left_hip_yaw')
    if 'q_rad' in trace:
        angle=float(trace['q_rad'][index,joint_index])
    else:
        sys.path.insert(0,str(ROOT/'software/sim/actuator'))
        from fixtures import full_body
        sim,names=full_body()
        angle=float(trace['qpos'][index,sim.m.joint('left_hip_yaw').qposadr[0]])
    c,s=np.cos(angle),np.sin(angle)
    rotation=np.array([[c,-s,0],[s,c,0],[0,0,1]])
    local=np.array(selected['simultaneous_wrenches'][joint_index])
    # Parent-on-child reaction becomes the load on the parent support.
    applied=np.r_[-rotation@local[:3],-1000*rotation@local[3:]]
    material=json.loads((ROOT/'board/mechanical/engineering/materials.json').read_text())['PETG']
    step=a.step or ROOT/'software/sim/mujoco/assets/r9_fast_turn_v1/cad/left_yaw_fixed_support.step'
    plan={'scope':__doc__,'source_case':selected,'angle_rad':angle,'wrench_N_Nmm':applied.tolist(),
          'origin_mm':[-5,26,62],'geometry_sha256':hashlib.sha256(step.read_bytes()).hexdigest(),
          'fixed':'entire back face x=-61.5 mm; ideal bonded restraint',
          'load':'bottom shelf z=88 mm, face-centroid within motor projection x[-29.5,4.5], y[16,36]',
          'young_MPa':material['printed_modulus_lower_MPa'],'poisson':material['poisson_ratio_assumed'],
          'mesh_mm':[4.,3.,2.],'max_displacement_mm':.2,'allowable_MPa':material['nominal_allowable_MPa']}
    (a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    rows=[]
    for size in plan['mesh_mm']:
        mesh=tetrahedralize(step,a.out/f'support_{size}.msh',size)
        report,data=analyze(mesh,lambda x:abs(x[0]+61.5)<1e-6,
            lambda x:(abs(x[2]-88)<1e-6)&(x[0]>=-29.5)&(x[0]<=4.5)&(x[1]>=16)&(x[1]<=36),
            plan['origin_mm'],applied,plan['young_MPa'],plan['poisson'])
        report['mesh_mm']=size;rows.append(report)
        np.savez_compressed(a.out/f'support_{size}.npz',**data)
        print(json.dumps(report),flush=True)
    final=rows[-1]
    gates={'displacement':final['max_displacement_mm']<=plan['max_displacement_mm'],
           'stress':max(final['max_von_mises_MPa'],final['max_absolute_principal_MPa'])<=plan['allowable_MPa'],
           'displacement_convergence':abs(final['max_displacement_mm']/rows[-2]['max_displacement_mm']-1)<=.05,
           'stress_convergence':abs(final['max_absolute_principal_MPa']/rows[-2]['max_absolute_principal_MPa']-1)<=.1}
    result={'scope':__doc__,'rows':rows,'gates':gates,'passed_screen':all(gates.values()),
            'production_design_verified':False,'limitations':['one load sample only','ideal back-face bond','no fastener/contact/buckling validation']}
    (a.out/'report.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':main()
