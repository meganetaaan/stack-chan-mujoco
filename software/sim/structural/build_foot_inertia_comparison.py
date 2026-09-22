"""Replace legacy foot inertials once using explicit density comparison inputs."""
import argparse,hashlib,json,os,xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
import mujoco
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--out',type=Path,required=True)
for group in ['rigid','contact','metal']:p.add_argument('--'+group+'-density',type=float,required=True,help='g/cm3; comparison assumption, not material qualification')
a=p.parse_args();rho={g:getattr(a,g+'_density') for g in ['rigid','contact','metal']}
if not all(np.isfinite(v) and v>0 for v in rho.values()):raise ValueError('Positive finite densities required')
ip=Path('board/mechanical/prototype/foot_candidate/revE/inventory.json')
legacy=Path('validation/foot_inertia_allocation_v1/report.json');owner=json.loads(Path('validation/foot_body_ownership_v1/report.json').read_text())
source=Path(owner['model_path']);raw=source.read_bytes()
assert hashlib.sha256(raw).hexdigest()==owner['model_sha256']
root=ET.fromstring(raw);inv=json.loads(ip.read_text());old=json.loads(legacy.read_text())
assert not root.findall('include'), 'Handle include files explicitly before use'
rows=[];mapped=[]
for side in ['left','right']:
 items=[x for x in inv['parts'] if x['side']==side];assert len(items)==15
 masses=[];centers=[];inertias=[]
 for x in items:
  group='rigid' if x['part'] in ['boot','yoke','holder'] else 'contact' if x['part']=='contact_layer' else 'metal'
  m=x['volume_mm3']*rho[group]*1e-6;c=np.array(x['com_mm'])*1e-3;I=np.array(x['volume_inertia_about_com_mm5'])*rho[group]*1e-12
  masses.append(m);centers.append(c);inertias.append(I)
  mapped.append({'side':side,'part':x['part'],'density_group':group,'mass_kg':m})
 mass=sum(masses);com=sum((m*c for m,c in zip(masses,centers)),np.zeros(3))/mass
 I=sum((i+m*((c-com)@(c-com)*np.eye(3)-np.outer(c-com,c-com)) for m,c,i in zip(masses,centers,inertias)),np.zeros((3,3)))
 eig=np.linalg.eigvalsh(I);assert min(eig)>0 and max(eig)<sum(eig)-max(eig)
 el=root.find(f'.//body[@name="{side}_ankle_roll"]/inertial');baseline=next(x for x in old['rows'] if x['side']==side)
 assert abs(float(el.get('mass'))-baseline['mass_kg'])<1e-14
 el.attrib.clear();el.set('mass',format(mass,'.17g'));el.set('pos',' '.join(format(v,'.17g') for v in com));principal,axes=np.linalg.eigh(I)
 if np.linalg.det(axes)<0:axes[:,0]*=-1
 quat=np.empty(4);mujoco.mju_mat2Quat(quat,axes.flatten())
 el.set('diaginertia',' '.join(format(v,'.17g') for v in principal));el.set('quat',' '.join(format(v,'.17g') for v in quat))
 rows.append({'body':side+'_ankle_roll','old_mass_kg':baseline['mass_kg'],'mass_kg':mass,'com_m':com.tolist(),'inertia_kg_m2':I.tolist()})
a.out.mkdir(parents=True,exist_ok=False)
compiler=root.find('compiler');compiler.set('meshdir',os.path.relpath(source.parent/compiler.get('meshdir',''),a.out))
path=a.out/'scene.xml';ET.ElementTree(root).write(path,encoding='unicode')
m0=mujoco.MjModel.from_xml_path(str(source));m=mujoco.MjModel.from_xml_path(str(path));changed=[]
for i in range(m.nbody):
 name=mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_BODY,i)
 if name in [r['body'] for r in rows]:
  row=next(r for r in rows if r['body']==name);rotation=np.empty(9);mujoco.mju_quat2Mat(rotation,m.body_iquat[i]);R=rotation.reshape(3,3)
  assert np.allclose(R@np.diag(m.body_inertia[i])@R.T,row['inertia_kg_m2'],rtol=1e-9,atol=1e-14)
  assert np.allclose(m.body_ipos[i],row['com_m']) and abs(m.body_mass[i]-row['mass_kg'])<1e-14;changed.append(name)
 else:
  for field in ['body_mass','body_ipos','body_inertia','body_iquat']:assert np.array_equal(getattr(m,field)[i],getattr(m0,field)[i])
for field in ['body_pos','body_quat','jnt_pos','jnt_axis','jnt_range','geom_pos','geom_size']:assert np.array_equal(getattr(m,field),getattr(m0,field))
expected=sum(x['mass_kg']-x['old_mass_kg'] for x in rows);assert abs(m.body_mass.sum()-m0.body_mass.sum()-expected)<1e-12
r={'density_comparisons_g_cm3':rho,'sources_sha256':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in [ip,source,legacy]},'mapped_parts':mapped,'rows':rows,'changed_bodies':changed,'robot_mass_delta_kg':expected,'compiled_inertia_roundtrip_pass':True,'other_body_inertials_unchanged':True,'geometry_and_joint_arrays_unchanged':True,'mujoco_version':mujoco.__version__,'manufacturing_release':False,'qualified_physical_inertia':False,'limits':['Explicit densities are comparison assumptions; printed voids and actual material grade are not established.','Metal CAD envelopes are not exact threaded-part mass; all metal density is a uniform comparison.','Servo/horn hardware and harness omitted from inventory remain omitted; no full robot mass closure claimed.','Collision shapes remain legacy geometry; do not use this model to certify current foot interference.','Identity CAD-to-ankle body frame is inherited comparison convention; full assembly frame audit remains.']}
(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'masses':[x['mass_kg'] for x in rows],'mass_delta':expected,'compiled':True}))
