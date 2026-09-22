"""Extract actual boot/yoke bore cylinders and screen radial assembly tolerance."""
import hashlib,json,math
from pathlib import Path
import cadquery as cq
from OCP.BRepAdaptor import BRepAdaptor_Surface
out=Path('validation/boot_bore_clearance_v1');out.mkdir(exist_ok=True)
rows=[];hashes={}
for side,sign in [('left',1),('right',-1)]:
 sources={'boot':Path(f'validation/boot_low_head_candidate_v1/cad/{side}_boot_shell.step'),'yoke':Path(f'validation/sole_recessed_seat_v3/{side}_yoke.step')}
 for part,path in sources.items():
  hashes[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
  shape=cq.importers.importStep(str(path)).val()
  for x in (-34,36):
   for y in (sign*6-20.5,sign*6+20.5):
    found=[]
    for face in shape.Faces():
     if face.geomType()!='CYLINDER':continue
     cylinder=BRepAdaptor_Surface(face.wrapped).Cylinder();axis=cylinder.Axis();p=axis.Location()
     if abs(abs(axis.Direction().Z())-1)>1e-8 or abs(p.X()-x)>1e-6 or abs(p.Y()-y)>1e-6:continue
     box=face.BoundingBox()
     if box.zmax < -19 or box.zmin > -13:continue
     found.append({'radius_mm':cylinder.Radius(),'z_mm':[box.zmin,box.zmax]})
    if not found:raise ValueError((side,part,x,y))
    rows.append({'side':side,'part':part,'xy_mm':[x,y],'cylinders':found})
comparison=[]
for radius in (1.15,1.4,1.5):
 # Existing independent +/-0.2 boundary assumption applied to hole radius;
 # separate +/-0.2 hole position is a comparison only, not established capability.
 comparison.append({'hole_radius_mm':radius,'radial_gap_nominal_mm':radius-1,
 'radial_gap_after_0p2_inward_boundary_mm':radius-1-.2,
 'two_hole_relative_offset_capacity_mm':2*(radius-1-.2),
 'head_bearing_annulus_nominal_mm2':math.pi*(1.9**2-radius**2),
 'head_bearing_radial_width_after_0p2_outward_boundary_mm':1.9-radius-.2})
report={'rows':rows,'source_sha256':hashes,'comparison':comparison,
 'screw_radius_mm':1,'screw_max_radius_qualified':False,
 'decision':'Nominal 2.3 mm bores cannot guarantee 2 mm screw passage under retained 0.2 mm inward boundary assumption. Enlarging trades clearance against head bearing; do not adopt on clearance alone.',
 'limits':['Bore error is an assumption, not measured printer capability.','Actual screw diameter tolerance, hole-axis correlation, nut float and thread lead-in pending.','Annular area is ideal concentric seating, not local bearing strength.'],
 'manufacturing_release':False}
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'bore_positions':len(rows),'radii_mm':sorted(set(round(c['radius_mm'],5) for r in rows for c in r['cylinders'])),'comparison':comparison}))
