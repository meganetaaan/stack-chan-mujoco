"""Full-yoke static screening with rigid horn supports and equivalent sole traction."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from elasticity import tetrahedralize,analyze
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--mesh-mm',type=float,default=3);a=p.parse_args();root=Path(__file__).resolve().parents[3];a.out.mkdir(parents=True,exist_ok=False)
source=root/'validation/ankle_mount_load_mapping_v1/report.json';meta=json.loads(source.read_text());case=max((r for r in meta['cases'] if r['side']=='left'),key=lambda r:r['peak_moment_norm_Nmm']);trace=root/'validation/ankle_mount_load_mapping_v1'/(case['name']+'.npz')
with np.load(trace) as d:
 w=d['wrench_N_Nmm'];i=int(np.linalg.norm(w[:,3:],axis=1).argmax());load=-w[i].copy();time=float(d['time_s'][i])
# Move the equivalent balancing load from z=-16 to the sole plane z=-19.
load[3:]-=np.cross([0,0,-3],load[:3]);step=root/'validation/native_horn_yoke_development_v1/v4/left_foot_yoke.step'
plan={'scope':__doc__,'mesh_mm':a.mesh_mm,'source_case':case['name'],'sample_index':i,'time_s':time,'wrench_N_Nmm':load.tolist(),'origin_mm':[1,6,-19],'E_MPa':1120,'poisson':.35,'criteria':{'displacement_mm':.2,'absolute_principal_MPa':5.6},'source_sha256':{str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [step,trace,source]},'limitations':['Rigid clamping of horn annuli overestimates support stiffness.','Affine sole traction is an equivalent static load, not measured pressure; inertia and actual contact distribution omitted.','Single mesh, no bolt contact, anisotropy, creep or buckling; not acceptance.']};(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
mesh=tetrahedralize(step,a.out/'yoke.msh',a.mesh_mm)
fixed=lambda x: ((abs(x[0]-3)<1e-6)|(abs(x[0]+26)<1e-6)) & (x[1]**2+x[2]**2<10.2**2) & (x[1]**2+x[2]**2>4**2)
loaded=lambda x:abs(x[2]+19)<1e-6
r,arrays=analyze(mesh,fixed,loaded,[1,6,-19],load,young=1120,poisson=.35);r['screening_gates']={'displacement':r['max_displacement_mm']<=.2,'stress':r['max_absolute_principal_MPa']<=5.6};r['joint_strength_verified']=False
np.savez_compressed(a.out/'fields.npz',**arrays);(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
