"""Back-cover screen with simultaneous left/right support loads and ideal corner mounts."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from elasticity import tetrahedralize,analyze_regions_many
ROOT=Path(__file__).resolve().parents[3]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--out',type=Path,required=True);p.add_argument('--step',type=Path)
p.add_argument('--mesh-mm',type=float,default=3.)
p.add_argument('--material-config',type=Path)
p.add_argument('--conformal-patches',action='store_true')
p.add_argument('--circle-points',type=int,default=32)
a=p.parse_args()
if not np.isfinite(a.mesh_mm) or a.mesh_mm<=0:p.error('positive finite mesh size required')
a.out.mkdir(parents=True,exist_ok=False)
root=ROOT/'validation/inset_yaw_assembly_development_v1'
step=a.step or root/'inset_fasteners_staged_v2/rear_cover_drilled.step'
case=json.loads((root/'yaw_inset_strength_v1/plan.json').read_text())['source_case']
paths=[root/'inset_bolt_group_v1'/f'actuator_fullbody_load_right_v1_{side}.npz' for side in ['left','right']]
w=[];times=[]
for path in paths:
 with np.load(path) as data:
  index=int(np.argmin(abs(data['time_s']-case['selected_time_s'])))
  times.append(float(data['time_s'][index]));w.append(data['wrench_at_bolt_group_N_Nmm'][index])
assert abs(times[0]-times[1])<1e-10 and abs(times[0]-case['selected_time_s'])<1e-8
w=np.array(w)
material=json.loads(a.material_config.read_text()) if a.material_config else {'young_MPa':1120.,'poisson':.35,'allowable_MPa':5.6}
plan={'scope':__doc__,'selected_time_s':times[0],'wrenches_N_Nmm':w.tolist(),
      'source_sha256':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in paths},
      'geometry_sha256':hashlib.sha256(step.read_bytes()).hexdigest(),
      'young_MPa':material['young_MPa'],'poisson':material['poisson'],'material':material,'mesh_mm':a.mesh_mm,
      'boundary_method':'CAD physical groups' if a.conformal_patches else 'facet centroid selection',
      'criteria':{'displacement_mm':.2,'stress_MPa':material['allowable_MPa'],'relative_superposition_error':1e-8},
      'fixed':'inner-face disks radius 4.6 mm at (y,z)=(+/-59,8 or 120); ideal corner support',
      'load':'inner-face disks radius 6 mm at y=+/-19,+/-33; z=58,82, separated by side',
      'limitations':['one simultaneous recorded time only','facet-centroid approximation of load patches',
                     'ideal corner clamp; no shell boss compliance, screw contact or preload',
                     'linear isotropic material screen; no joint/fatigue/temperature characterization',
                     'single mesh; no convergence demonstrated']}
if a.conformal_patches:
 plan['circle_points']=a.circle_points
 plan['limitations'][1]='linear chord approximation of CAD-partitioned patch curves'
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
if a.conformal_patches:
 from mesh_backplate_patches import build_mesh
 mesh=build_mesh(step,a.out/'cover.msh',a.mesh_mm,a.circle_points)
else:
 mesh=tetrahedralize(step,a.out/'cover.msh',a.mesh_mm)
def disk_union(x,centers,radius):
 result=np.zeros(x.shape[1],dtype=bool)
 for y,z in centers:result|=(x[1]-y)**2+(x[2]-z)**2<=radius**2
 return (abs(x[0]+62.2)<1e-6)&result
fixed=lambda x:disk_union(x,[(y,z) for y in [-59,59] for z in [8,120]],4.6)
regions=[]
for sign in [1,-1]:
 centers=[(sign*26+dy,70+dz) for dy in [-7,7] for dz in [-12,12]]
 regions.append((lambda x,centers=centers:disk_union(x,centers,6),[-62.2,sign*26,70]))
if a.conformal_patches:
 fixed='fixed'
 regions=[('left',[-62.2,26,70]),('right',[-62.2,-26,70])]
loads=[np.array([w[0],np.zeros(6)]),np.array([np.zeros(6),w[1]]),w]
rows=[];fields=[]
for name,(report,data) in zip(['left_only','right_only','simultaneous'],analyze_regions_many(mesh,fixed,regions,loads,plan['young_MPa'],plan['poisson'])):
 rows.append(dict(name=name,**report));fields.append({k:data[k].copy() for k in ['displacement_mm','stress_MPa']})
 np.savez_compressed(a.out/(name+'.npz'),**data)
 print(json.dumps({'case':name,'displacement_mm':report['max_displacement_mm'],'stress_MPa':report['max_absolute_principal_MPa']}),flush=True)
errors={k:float(np.linalg.norm(fields[2][k]-fields[0][k]-fields[1][k])/max(np.linalg.norm(fields[2][k]),1e-30)) for k in fields[0]}
r=rows[-1];gates={'displacement':r['max_displacement_mm']<=.2,
 'stress':max(r['max_absolute_principal_MPa'],r['max_von_mises_MPa'])<=plan['criteria']['stress_MPa'],
 'superposition':all(v<1e-8 for v in errors.values())}
report={'scope':__doc__,'rows':rows,'gates':gates,'relative_superposition_errors':errors,'passed_screen':all(gates.values()),'load_path_verified':False}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(gates))
