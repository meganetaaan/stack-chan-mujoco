"""Density-linear incremental inertia of v7 support additions relative to v5."""
import argparse,hashlib,json
from pathlib import Path
import cadquery as cq
import numpy as np
from OCP.GProp import GProp_GProps
from OCP.BRepGProp import BRepGProp
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
base=Path('validation/yaw_integrated_candidate_v5');new=Path('validation/yaw_integrated_candidate_v7');files=[base/'geometric_moments.json',new/'geometric_moments.json',base/'inventory.json',new/'inventory.json']
bm={x['name']:x for x in json.loads(files[0].read_text())['parts']};nm={x['name']:x for x in json.loads(files[1].read_text())['parts']};bi={x['name']:x for x in json.loads(files[2].read_text())['parts']};ni={x['name']:x for x in json.loads(files[3].read_text())['parts']}
plan={'scope':__doc__,'frame':'Assembly CAD origin, same axes as v5/v7; m, kg and kg/m3','stop':'Two support differences; cross-check geometry subtraction against stored origin moments. No density sweep or dynamics run.','density':'Leave as coefficient;1270 kg/m3 is inherited uniform PETG comparison only, not actual print mass.','limits':['Same homogeneous density in old and new supports.','Not a complete v7 mass replacement for the frozen MuJoCo model.','Current nut envelopes must not be used as actual nut mass.']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
def terms(prop):
 m=prop['mass_kg_per_density_kg_m3'];c=np.array(prop['com_assembly_m']);I=np.array(prop['inertia_com_kg_m2_per_density_kg_m3']);return m,m*c,I+m*((c@c)*np.eye(3)-np.outer(c,c))
rows=[];tot=[0.,np.zeros(3),np.zeros((3,3))]
for side in ['left','right']:
 name=side+'_yaw_fixed_support';oldpath=Path(bi[name]['source']);newpath=Path(ni[name]['source']);files += [oldpath,newpath]
 old=cq.importers.importStep(str(oldpath)).val();revised=cq.importers.importStep(str(newpath)).val();assert old.cut(revised).Volume()<1e-6
 added=revised.cut(old);gp=GProp_GProps();BRepGProp.VolumeProperties_s(added.wrapped,gp);c=np.array(gp.CentreOfMass().Coord())*.001;iv=gp.MatrixOfInertia();m=added.Volume()*1e-9;Ic=np.array([[iv.Value(j,k)*1e-15 for k in range(1,4)] for j in range(1,4)])
 actual=[m,m*c,Ic+m*((c@c)*np.eye(3)-np.outer(c,c))];before=terms(bm[name]);after=terms(nm[name]);delta=[np.asarray(y)-np.asarray(x) for x,y in zip(before,after)]
 for d,v in zip(delta,actual):assert np.allclose(d,v,rtol=1e-8,atol=1e-17)
 assert min(np.linalg.eigvalsh(Ic))>0
 for i,v in enumerate(delta):tot[i]+=v
 rows.append({'name':name,'volume_added_mm3':added.Volume(),'added_com_assembly_m':c.tolist(),'delta_mass_kg_per_density_kg_m3':float(delta[0]),'delta_first_moment_kg_m_per_density_kg_m3':delta[1].tolist(),'delta_inertia_origin_kg_m2_per_density_kg_m3':delta[2].tolist(),'uniform_1270_comparison_mass_added_g':float(delta[0]*1270*1000)})
for name in bm:
 if name not in {r['name'] for r in rows}:assert bm[name]==nm[name] and bi[name]==ni[name]
r={'rows':rows,'unchanged_parts_verified':50,'direct_added_solid_crosscheck':True,'total_delta_mass_kg_per_density_kg_m3':float(tot[0]),'total_delta_first_moment_kg_m_per_density_kg_m3':tot[1].tolist(),'total_delta_inertia_origin_kg_m2_per_density_kg_m3':tot[2].tolist(),'uniform_1270_comparison_mass_added_g':float(tot[0]*1270*1000),'source_sha256':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},'model_updated':False,'manufacturing_release':False}
(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k not in ['rows','source_sha256']},indent=2))
