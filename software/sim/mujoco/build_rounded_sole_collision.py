"""Separate frozen-r9 derivative using existing rounded sole mesh for contact."""
import argparse,hashlib,json,shutil,xml.etree.ElementTree as ET
from pathlib import Path
import mujoco,numpy as np
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--arc-segments',type=int,help='Analytic 3 mm corner radius, segments per quarter');a=p.parse_args();
if a.arc_segments is not None and not 3<=a.arc_segments<=64:p.error('arc segments must be 3..64')
root=Path(__file__).resolve().parents[3];src=root/'software/sim/mujoco/assets/r9_fast_turn_v1';a.out.mkdir(parents=True,exist_ok=False)
for n in ['models','reference']:shutil.copytree(src/n,a.out/n)
shutil.copy2(src/'robot.json',a.out/'robot.json');path=a.out/'models/scene.xml';tree=ET.parse(path);changes=[]
for side in ['left','right']:
 if a.arc_segments:
  cy=6 if side=='left' else -6;vertices=[]
  for z in [-22,-19]:
   for cx,yy,start in [(44,cy+21,0),(-36,cy+21,90),(-36,cy-21,180),(44,cy-21,270)]:
    for angle in np.linspace(start,start+90,a.arc_segments+1):
     theta=np.deg2rad(angle);vertices.append([cx+3*np.cos(theta),yy+3*np.sin(theta),z])
  ET.SubElement(tree.find('asset'),'mesh',name=side+'_rounded_contact',vertex=' '.join(map(str,(np.array(vertices)/1000).ravel())))
 node=tree.find(f'.//geom[@name="col_{side}_sole_TPU_0"]');before=dict(node.attrib);node.set('type','mesh');node.set('mesh',side+('_rounded_contact' if a.arc_segments else '_sole_TPU_mesh'));node.set('pos','0 0 0');node.attrib.pop('size');changes.append({'side':side,'before':before,'after':dict(node.attrib)})
tree.write(path,encoding='unicode');old=mujoco.MjModel.from_xml_path(str(src/'models/scene.xml'));new=mujoco.MjModel.from_xml_path(str(path));unchanged={n:bool(np.array_equal(getattr(old,n),getattr(new,n))) for n in ['body_mass','body_inertia','body_ipos','body_iquat','jnt_range']};assert all(unchanged.values())
report={'scope':__doc__,'arc_segments':a.arc_segments,'analytic_chord_error_mm':float(3*(1-np.cos(np.pi/(4*a.arc_segments)))) if a.arc_segments else None,'changes':changes,'unchanged':unchanged,'source_sha256':{str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [src/'models/scene.xml',src/'models/meshes/left_sole_TPU.stl',src/'models/meshes/right_sole_TPU.stl']},'limitations':['Rigid convex sole envelope from visual mesh or analytic rounded rectangle; no TPU deformation or pocket compliance.','Only sole collision changed; revised mechanical mass and other geometry remain pending.'],'joint_verified':False};(a.out/'collision_plan.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(unchanged))
