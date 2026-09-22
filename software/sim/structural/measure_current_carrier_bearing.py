"""Measure current CAD bearing areas; report force-to-pressure coefficients, not strength."""
import hashlib
import json
import math
from pathlib import Path
import cadquery as cq

ROOT=Path(__file__).resolve().parents[3]
SRC=ROOT/'validation/serviceable_torso_v3'
OUT=ROOT/'validation/current_carrier_bearing_v1'
OUT.mkdir(exist_ok=True)
plan={
 'purpose':'Quantify mean seat pressure and identify missing preload/contact inputs before local mesh refinement',
 'criteria':['Twelve named nominal bearing areas are positive',
             'Exact common-face area agrees with independent annulus calculation within1e-6mm2',
             'No material strength, friction coefficient or preload silently assigned'],
 'method':'Common planar CAD faces, local cylinder clips for individual side pads',
 'load_definition':'N is actual positive compressive contact resultant in newtons; p_mean=N/A in MPa',
 'stop':'One geometric extraction and analytical cross-check; no mesh refinement or load acceptance',
 'comparison_contact_forces_N':[1,10,50,100],
 'comparison_basis':'Engineering sensitivity points only, not required or permitted assembly preload',
 'limits':['Nominal planar contact, not actual pressure distribution',
           'No preload/friction/contact separation/creep solved',
           'No print or hardware tolerance, chamfer, surface roughness or elastic deformation',
           'No whole-robot dynamic load update'],
}
(OUT/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
r=json.loads((SRC/'report.json').read_text())
ss=cq.importers.importStep(str(SRC/'assembly.step')).val().Solids()
assert len(ss)==len(r['parts'])==115
for row,solid in zip(r['parts'],ss):assert abs(row['volume_mm3']-solid.Volume())<1e-5
parts={row['name']:solid for row,solid in zip(r['parts'],ss)}
def planar(shape,axis,position):
 result=[]
 for face in shape.Faces():
  if face.geomType()!='PLANE':continue
  normal=face.normalAt().toTuple();center=face.Center().toTuple()
  if abs(abs(normal[axis])-1)<1e-8 and abs(center[axis]-position)<1e-6:result.append(face)
 return result

def area(left,right,axis,position,clip=None):
 total=0.
 for a in planar(parts[left],axis,position):
  for b in planar(parts[right],axis,position):
   common=a.intersect(b)
   # Empty/edge-only common shapes have no bearing area and cannot be clipped as solids.
   if not common.Faces():continue
   if clip is not None:common=common.intersect(clip)
   total+=common.Area()
 return total

rows=[]
def append(name,left,right,measured,outer,inner):
 reference=math.pi*(outer**2-inner**2)
 assert measured>0 and abs(measured-reference)<1e-6,(name,measured,reference)
 rows.append({'name':name,'parts':[left,right],'area_mm2':measured,
              'annulus_reference_mm2':reference,'area_error_mm2':measured-reference,
              'mean_pressure_MPa_per_N':1/measured,
              'contact_force_N_per_1MPa_mean_pressure':measured,
              'pressure_comparisons':[{'contact_force_N':n,'mean_pressure_MPa':n/measured}
                                      for n in plan['comparison_contact_forces_N']]})
for sign in [-1,1]:
 for z in [88,112]:
  for kind,left,pos,outer,inner in [
   ('side_head',f'new_{sign}_{z}_screw',64,2.75,1.7),
   ('side_pad','new_carrier',62.2,3.5,2.0)]:
   clip=cq.Solid.makeCylinder(3.5,2,cq.Vector(42,sign*(pos-1),z),cq.Vector(0,sign,0))
   append(f'{kind}_{sign}_{z}',left,'new_fixed_shell',
          area(left,'new_fixed_shell',1,sign*pos,clip),outer,inner)
for y in [-60,60]:
 for z in [52,124]:
  left=f'new_frame_screw_{y}_{z}'
  append(f'face_head_{y}_{z}',left,'new_carrier',area(left,'new_carrier',0,48.3),2.75,1.65)
assert len(rows)==12
report={'rows':rows,'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [SRC/'report.json',SRC/'assembly.step',Path(__file__)]},
 'decision':'Side screw head has smaller nominal bearing area than side pad; include outer shell seat compression/bending in preload assessment',
 'assembly_preload_N':None,'allowable_bearing_pressure_MPa':None,
 'strength_verified':False,'manufacturing_release':False,
 'failed_initial_probe':'Attempting a second boolean intersection on an empty common-face shape raised Null TopoDS_Shape; explicitly skip face-empty intersections. Other geometry exceptions are not suppressed.'}
(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
for row in rows:print(row['name'],round(row['area_mm2'],6),round(row['mean_pressure_MPa_per_N'],6))
