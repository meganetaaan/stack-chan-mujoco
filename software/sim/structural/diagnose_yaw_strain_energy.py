"""Locate elastic compliance in the existing yaw support; no new FE solve."""
import argparse, hashlib, json
from pathlib import Path
import meshio
import numpy as np
from skfem import Basis, ElementVector, ElementTetP2
from skfem.io import from_meshio
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--out',type=Path,required=True)
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
root=Path('validation/yaw_current_archive_envelope_v1')
plan={'question':'Which longitudinal regions store elastic energy in the largest directly evaluated archived displacement case?', 'stop':'One postprocessing pass of six existing unit responses, no geometry, material, mesh or criterion changes.', 'limits':['Selected case is not proven worst over every time sample.', 'Energy localization is not a sensitivity derivative or proof that local thickening is effective.', 'Ideal clamp, bonded loading and isotropic assumed material remain unchanged.'], 'manufacturing_release':False}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
r=json.loads((root/'report.json').read_text());case=max(r['rows'],key=lambda x:x['selected_actual_displacement_mm']);w=np.array(case['selected_wrench_N_Nmm'])
units=[np.load(root/f'unit_{i}.npz') for i in range(6)]
b=Basis(from_meshio(meshio.read(root/'support.msh')),ElementVector(ElementTetP2()))
xyz=units[0]['quadrature_coordinates_mm']
assert np.allclose(b.global_coordinates(),xyz,rtol=0,atol=1e-9)
s=sum(w[i]*units[i]['stress_MPa'] for i in range(6))
u=sum(w[i]*units[i]['displacement_mm'] for i in range(6))
f=sum(w[i]*units[i]['load_N'] for i in range(6))
E=1120.;nu=.35
density=((1+nu)*np.sum(s*s,axis=(0,1))-nu*np.trace(s,axis1=0,axis2=1)**2)/(2*E)
assert density.min()>-1e-12
# Tetrahedral quadrature includes negative weights; integrate whole elements.
energy=np.sum(density*b.dx,axis=1)
assert energy.min()>-1e-12
centers=b.mesh.p[:,b.mesh.t].mean(axis=1)
work=float(np.sum(f*u));total=float(energy.sum())
assert abs(2*total/work-1)<1e-6
cuts=[-float('inf'),-50,-30,-10,float('inf')];rows=[]
for lo,hi in zip(cuts[:-1],cuts[1:]):
 mask=(centers[0]>=lo)&(centers[0]<hi)
 e=float(energy[mask].sum());rows.append({'x_min_mm':lo if np.isfinite(lo) else None,'x_max_mm':hi if np.isfinite(hi) else None,'energy_Nmm':e,'fraction':e/total})
assert abs(sum(x['fraction'] for x in rows)-1)<1e-12
imax=int(np.argmax(np.linalg.norm(u,axis=1)))
files=[root/'report.json',root/'support.msh',*[root/f'unit_{i}.npz' for i in range(6)],Path(__file__).resolve().relative_to(Path.cwd())]
result={'case':case,'regions':rows,'strain_energy_Nmm':total,'external_work_Nmm':work,'energy_balance_relative_error':abs(2*total/work-1),'max_displacement_mm':float(np.linalg.norm(u[imax])),'max_displacement_location_mm':units[0]['nodes_mm'][imax].tolist(),'source_sha256':{str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in files},'manufacturing_release':False}
(a.out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['case','source_sha256']},indent=2))
