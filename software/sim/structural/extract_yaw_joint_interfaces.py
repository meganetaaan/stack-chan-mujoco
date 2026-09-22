"""Extract nominal planar contact patches from the integrated CAD, without assuming bonded contact."""
import argparse,hashlib,json
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
ip=a.candidate/'inventory.json';sp=a.candidate/'yaw_support_candidate.step'
items=json.loads(ip.read_text())['parts'];solids=cq.importers.importStep(str(sp)).val().Solids();assert len(items)==len(solids)==52
parts={}
for item,solid in zip(items,solids):
 assert abs(item['volume_mm3']-solid.Volume())<1e-5
 parts[item['name']]=solid
plan={'question':'Which actual nominal face areas carry the plate joint compression load path in the current integrated CAD?',
 'source_sha256':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in [ip,sp]},
 'method':'Intersect coplanar horizontal faces of each adjacent pair; retain holes and reliefs. Export surface patches, not filled bounding rectangles.',
 'numeric_plane_tolerance_mm':1e-6,'stop':'Two plate-shelf interfaces and three bearing interfaces per each of eight fasteners; no FE or geometry changes.',
 'limits':['Nominal coincident faces only, not actual pressure-bearing contact under tolerance/load.',
 'No bonded/tensile/friction capacity assigned to these patches.',
 'Nut and screw are simplified CAD envelopes; actual chamfers/threads absent.',
 'No preload, material allowable, plate bending or contact separation solved.']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
def faces_at(shape,z):
 return [f for f in shape.Faces() if abs(f.BoundingBox().zmin-z)<1e-6 and abs(f.BoundingBox().zmax-z)<1e-6]
rows=[]
def extract(name,left,right,z):
 lf=faces_at(parts[left],z);rf=faces_at(parts[right],z)
 patches=[]
 for f in lf:
  for g in rf:
   intersection=f.intersect(g)
   patches.extend([h for h in intersection.Faces() if h.Area()>1e-8])
 if not patches:raise ValueError(f'No planar contact: {name}')
 patch=cq.Compound.makeCompound(patches);file=a.out/(name+'.step');cq.exporters.export(patch,str(file))
 area=sum(f.Area() for f in patches)
 # Export/readback ensures the surface artifact retains its area.
 read=cq.importers.importStep(str(file)).val();assert abs(read.Area()-area)<1e-6
 rows.append({'name':name,'part_a':left,'part_b':right,'z_mm':z,'area_mm2':area,
 'nominal_mean_pressure_per_N_MPa':1/area,'patch_faces':len(patches),'surface_step':str(file),
 'surface_sha256':hashlib.sha256(file.read_bytes()).hexdigest()})
for side in ['left','right']:
 plate=side+'_mount_plate';support=side+'_yaw_fixed_support'
 extract(side+'_plate_shelf',plate,support,89.)
 for i in range(4):
  key=f'{side}_plate_{i}';washer=key+'_washer';nut=key+'_nut';screw=key+'_screw'
  extract(key+'_head_plate',screw,plate,88.)
  extract(key+'_shelf_washer',support,washer,91.)
  extract(key+'_washer_nut',washer,nut,91.9)
report={'rows':rows,'interface_count':len(rows),'geometric_contact_patches_found':len(rows)==26,
 'pressure_note':'1/area is only a nominal mean-pressure coefficient. No force allocation or allowable is supplied; local peak pressure can be higher.',
 'tensile_connection_note':'These planar interfaces alone do not carry tensile separation; screw/nut threaded engagement and bearing maintain that load path.',
 'joint_strength_verified':False,'manufacturing_release':False}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'interface_count':len(rows),'area_ranges_mm2':{kind:[min(r['area_mm2'] for r in rows if r['name'].endswith(kind)),max(r['area_mm2'] for r in rows if r['name'].endswith(kind))] for kind in ['plate_shelf','head_plate','shelf_washer','washer_nut']}},indent=2))
