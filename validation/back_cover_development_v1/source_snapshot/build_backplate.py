"""Build a nominal 2 mm structural rear plate, retaining hole and vent geometry."""
import argparse,hashlib,json
from pathlib import Path
import cadquery as cq
ROOT=Path(__file__).resolve().parents[3]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
source=ROOT/'validation/inset_yaw_assembly_development_v1/inset_fasteners_staged_v2/rear_cover_drilled.step'
mat_path=ROOT/'board/mechanical/engineering/backplate_material.json';mat=json.loads(mat_path.read_text())
original=cq.importers.importStep(str(source)).val()
face=max((f for f in original.Faces() if f.geomType()=='PLANE' and abs(f.Center().x+64)<1e-6),key=lambda f:f.Area())
# Extrude the complete section to avoid a coincident-face Boolean union.
shape=cq.Solid.extrudeLinear(face.outerWire(),face.innerWires(),cq.Vector(2,0,0)).translate((-.2,0,0))
assert shape.isValid() and len(shape.Solids())==1
b=shape.BoundingBox();assert abs(b.xmin+64.2)<1e-6 and abs(b.xmax+62.2)<1e-6
assert abs(shape.Volume()-original.Volume()-face.Area()*.2)<1e-5
cq.exporters.export(shape,str(a.out/'rear_structural_plate.step'))
back=max((f for f in shape.Faces() if f.geomType()=='PLANE' and abs(f.Center().x+64.2)<1e-6),key=lambda f:f.Area())
flat=back.rotate((0,0,0),(1,1,1),-120).translate((0,0,64.2))
cq.exporters.export(cq.Workplane('XY').newObject(flat.Wires()),str(a.out/'rear_structural_plate.dxf'))
report={'scope':__doc__,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
 'material_sha256':hashlib.sha256(mat_path.read_bytes()).hexdigest(),'material':mat,
 'volume_mm3':shape.Volume(),'candidate_mass_kg':shape.Volume()*mat['density_kg_m3']*1e-9,
 'previous_PETG_mass_kg':original.Volume()*1.27e-6,
 'rear_extension_mm':.2,'inner_plane_x_mm':-62.2,'thickness_mm':2.,
 'dxf_coordinates':'DXF X=body Y; DXF Y=body Z; units mm, rear face projected without scale',
 'bolt_stack_change_mm':.2,'nominal_M3x16_thread_beyond_nut_mm':1.9,
 'limitations':['sheet thickness tolerance and edge finish pending','corner joints/body bosses not verified',
                'electrical insulation and chassis mounting integration pending'],'manufacturing_release':False}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
