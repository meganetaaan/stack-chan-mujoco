"""Subtract candidate sole spatial inertia from floor load; density sensitivity only."""
import argparse,gzip,json,hashlib
from pathlib import Path
import numpy as np,cadquery as cq
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();root=Path(__file__).resolve().parents[3];a.out.mkdir(parents=True,exist_ok=False)
plan={'densities_kg_m3':[1000,1200,1400],'scope':__doc__,'limitations':['Assumed densities, not selected TPU specification.','Recorded frozen-foot motion reused with candidate sole; not rerun dynamics.','Rigid sole inertia only; deformation, adhesion and retention absent.','Rectangular COP check is necessary, not sufficient.']};(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');cases=json.loads((root/'validation/sole_contact_cone_v1/report.json').read_text())['cases'];results=[]
for case in cases:
 side=case['side'];src=root/f"validation/rounded_sole_posture_v1/inset{case['inset_mm']}/foot_loads.jsonl.gz"
 with gzip.open(src,'rt') as f:
  for idx,line in enumerate(f):
   if idx==case['sample_index']:row=json.loads(line);break
 foot=row['feet'][0 if side=='left' else 1];R=np.array(foot['xmat']).reshape(3,3);O=np.array(foot['subtree_com_root']);x=np.array(foot['xpos']);v=np.array(foot['cvel']);acc=np.array(foot['cacc']);step=root/f'validation/boot_low_head_candidate_v1/cad/{side}_sole_TPU.step';shape=cq.importers.importStep(str(step)).val();com=np.array(shape.Center().toTuple())/1000;rel=x+R@com-O;center=np.array([1,6 if side=='left' else -6,-19]);trials=[]
 for density in plan['densities_kg_m3']:
  mass=shape.Volume()*density*1e-9;J=R@(np.array(cq.Shape.matrixOfInertia(shape))*density*1e-15)@R.T;J+=mass*(np.dot(rel,rel)*np.eye(3)-np.outer(rel,rel));h=mass*rel
  def mul(q):return np.r_[J@q[:3]+np.cross(h,q[3:]),mass*q[3:]-np.cross(h,q[:3])]
  iv=mul(v);inert=mul(acc)+np.r_[np.cross(v[:3],iv[:3])+np.cross(v[3:],iv[3:]),np.cross(v[:3],iv[3:])];F=R.T@inert[3:];M=1000*R.T@(inert[:3]+np.cross(O-x,inert[3:]))-np.cross(center,F);trans=np.array(case['wrench_N_Nmm'])-np.r_[F,M];cop=[1-trans[4]/trans[2],center[1]+trans[3]/trans[2]];outside=max(-39-cop[0],cop[0]-47,center[1]-24-cop[1],cop[1]-center[1]-24,0)
  trials.append({'density_kg_m3':density,'sole_mass_kg':mass,'sole_inertial_wrench_N_Nmm':np.r_[F,M].tolist(),'transmitted_to_yoke_N_Nmm':trans.tolist(),'cop_mm':cop,'outside_rectangle_mm':outside})
 results.append({'inset_mm':case['inset_mm'],'side':side,'sample_index':case['sample_index'],'step_sha256':hashlib.sha256(step.read_bytes()).hexdigest(),'trials':trials})
r={'cases':results,'joint_verified':False};(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps([{'inset':x['inset_mm'],'side':x['side'],'outside_mm':[t['outside_rectangle_mm'] for t in x['trials']]} for x in results],indent=2))
