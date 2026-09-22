"""Verify CAD-to-frozen-base frame using retained Tab5 geometry and explicit XML pose."""
import hashlib,json,xml.etree.ElementTree as ET
from pathlib import Path
import cadquery as cq
import numpy as np
import trimesh
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'validation/current_torso_frame_v1';OUT.mkdir(exist_ok=True)
model=ROOT/'software/sim/mujoco/assets/r9_fast_turn_v1';xml=model/'models/scene.xml';tree=ET.parse(xml);base=tree.find('.//body[@name="base"]');geom=base.find('geom[@name="vis_Tab5"]');asset=tree.find('asset/mesh[@name="Tab5_mesh"]')
assert geom.get('mesh')=='Tab5_mesh' and geom.get('pos')=='0 0 0'
assert not any(k in geom.attrib for k in ['quat','euler','axisangle','xyaxes','zaxis'])
scale=np.fromstring(asset.get('scale'),sep=' ');assert np.allclose(scale,[.001]*3)
meshpath=model/'models'/tree.find('compiler').get('meshdir')/asset.get('file');mesh=trimesh.load(str(meshpath),force='mesh');mesh_bounds=np.asarray(mesh.bounds)*scale
sources=[xml,meshpath,model/'FROZEN_FILES.json',ROOT/'validation/serviceable_torso_v3/report.json',ROOT/'validation/serviceable_torso_v3/assembly.step',ROOT/'validation/current_torso_inertia_v1/report.json']
frozen=json.loads(sources[2].read_text())
for p in [xml,meshpath]:assert frozen[str(p.relative_to(model))]==hashlib.sha256(p.read_bytes()).hexdigest()
report=json.loads(sources[3].read_text());solids=cq.importers.importStep(str(sources[4])).val().Solids();assert len(solids)==len(report['parts'])
idx=next(i for i,p in enumerate(report['parts']) if p['name']=='Tab5');shape=solids[idx];assert abs(shape.Volume()-report['parts'][idx]['volume_mm3'])<1e-5
bb=shape.BoundingBox();cad_bounds=np.array([[bb.xmin,bb.ymin,bb.zmin],[bb.xmax,bb.ymax,bb.zmax]])*.001
error=float(np.max(abs(cad_bounds-mesh_bounds)));assert error<1e-6
collision=base.find('geom[@name="col_Tab5_0"]');center=np.fromstring(collision.get('pos'),sep=' ');half=np.fromstring(collision.get('size'),sep=' ')
assert np.allclose((cad_bounds[0]+cad_bounds[1])/2,center,atol=1e-6) and np.allclose((cad_bounds[1]-cad_bounds[0])/2,half,atol=1e-6)
inertia=json.loads(sources[5].read_text());partial=inertia['partial_uniform_CAD_comparison'];c=np.array(partial['com_CAD_m']);I=np.array(partial['inertia_com_kg_m2']);m=partial['mass_kg']
# Validate parallel-axis inverse separately from the identity frame mapping.
io=np.array(partial['inertia_origin_kg_m2']);recovered=io-m*((c@c)*np.eye(3)-np.outer(c,c));assert np.allclose(recovered,I,atol=1e-12)
r={'frame_mapping':'Coordinates already in base-local axes/origin after mm-to-m conversion; no world body pose subtraction','rotation_CAD_to_base':np.eye(3).tolist(),'translation_CAD_to_base_m':[0,0,0],'Tab5_bounds_max_error_m':error,'retained_reference_checks':['Frozen STL and XML hashes','Direct child visual geom has zero position and no orientation override','Three-axis CAD/STL bounds','Collision box center and half-extents'],'base_world_initial_pos_m':np.fromstring(base.get('pos'),sep=' ').tolist(),'world_pose_used_for_local_transform':False,'partial_com_base_m':c.tolist(),'partial_inertia_com_base_kg_m2':I.tolist(),'mjcf_fullinertia_order':['Ixx','Iyy','Izz','Ixy','Ixz','Iyz'],'partial_fullinertia_for_review_only':[float(I[0,0]),float(I[1,1]),float(I[2,2]),float(I[0,1]),float(I[0,2]),float(I[1,2])],'unknown_CAD_mass_count':inertia['unknown_count'],'complete_model_export_allowed':False,'model_updated':False,'manufacturing_release':False,'limits':['Frame identity verified against explicit geometry convention; not measured assembly alignment','Whole mass/inertia remains incomplete and internal distributions assumed','Does not change joint axes or validate new moving link coordinates'],'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}}
(OUT/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'bounds_error_m':error,'frame':'identity after mm-to-m','model_export_allowed':False}))
