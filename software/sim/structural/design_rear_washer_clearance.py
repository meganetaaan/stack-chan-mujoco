"""Design a rear washer bore around the selected bolt's underhead envelope."""
import argparse, hashlib, json, math
from pathlib import Path
import cadquery as cq
import numpy as np
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--out',type=Path,required=True)
a=p.parse_args()
bolt_path=Path('docs/prototype/mechanical/yaw_support/rear_bolt_candidate.json')
inv_path=Path('board/mechanical/prototype/yaw_support_candidate/revA/inventory.json')
ledger_path=Path('validation/base_print_mass_v1/report.json')
b=json.loads(bolt_path.read_text()); inv=json.loads(inv_path.read_text()); ledger=json.loads(ledger_path.read_text())
# Design limits, not supplier tolerances or measured properties.
spec={'part':'SCW-YAW-REAR-WASHER-01','revision':'A-proposal','quantity':8,
 'material':'SUS304; reference density only, certification pending',
 'process':'machine from sheet or tube and finish bore and bearing faces; supplier capability unconfirmed',
 'outer_diameter_mm':{'nominal':7.,'min':6.95,'max':7.},
 'inner_diameter_mm':{'nominal':3.7,'min':3.7,'max':3.8},
 'thickness_mm':{'nominal':.5,'min':.45,'max':.55},
 'edge_break_radial_max_mm':.05,'required_radial_clearance_mm':.05,
 'reference_density_kg_m3':7930,'manufacturing_release':False}
gap=(spec['inner_diameter_mm']['min']-b['underhead']['da_max_mm'])/2
assert gap+1e-12 >= spec['required_radial_clearance_mm']
# Conservative bearing patch at minimum head diameter and largest bore+edge break.
bearing_inner=spec['inner_diameter_mm']['max']+2*spec['edge_break_radial_max_mm']
bearing_area=math.pi/4*(b['head_diameter_mm']['min']**2-bearing_inner**2)
assert bearing_area>0
sources={str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in [bolt_path,inv_path,ledger_path,Path('validation/yaw_metal_mass_v1/report.json')]}
a.out.mkdir(parents=True,exist_ok=False)
parts={}; subtotal={k:np.asarray(v) for k,v in ledger['subtotal_origin_terms'].items()}
for item in inv['parts']:
 name=item['name']
 if not name.endswith('rear_washer'):continue
 path=Path(item['source']); sha=hashlib.sha256(path.read_bytes()).hexdigest();assert sha==item['source_sha256'];sources[str(path)]=sha
 old=cq.importers.importStep(str(path)).val().translate((-.2,0,0))
 center=old.Center(); bb=old.BoundingBox(); assert abs(bb.xlen-.5)<1e-6
 bore=cq.Solid.makeCylinder(3.7/2,1.,cq.Vector(bb.xmin-.25,center.y,center.z),cq.Vector(1,0,0))
 new=old.cut(bore);assert new.isValid() and len(new.Solids())==1
 expected=math.pi/4*(7**2-3.7**2)*.5
 assert abs(new.Volume()-expected)<1e-6
 # A pure bore enlargement cannot create new nominal external intersections.
 assert new.cut(old).Volume()<1e-8
 cq.exporters.export(new,str(a.out/f'{name}.step'))
 mass=new.Volume()*7930*1e-9;c=np.array(new.Center().toTuple())*.001
 I=np.array(cq.Shape.matrixOfInertia(new))*7930*1e-15
 terms={'mass_kg':mass,'first_moment_kg_m':mass*c,'inertia_origin_kg_m2':I+mass*(c@c*np.eye(3)-np.outer(c,c))}
 parts[name]={k:np.asarray(v).tolist() for k,v in terms.items()}
 for k,v in terms.items():subtotal[k]=subtotal[k]+v
assert len(parts)==8
report={'source_sha256':sources,'specification':spec,'radial_clearance_at_limits_mm':gap,
 'concentric_projected_head_overlap_area_mm2':bearing_area,
 'uniform_projected_pressure_per_N_MPa':1/bearing_area,
 'parts':parts,'subtotal_origin_terms':{k:v.tolist() for k,v in subtotal.items()},
 'checks':{'nominal_volume':True,'subset_of_old_envelope':True,'bolt_da_clearance':True},
 'limits':['Projected area assumes concentric head and washer and a flat head face to its OD; actual bearing face, eccentricity and contact redistribution unresolved. This is not a guaranteed contact area.',
 'Thickness bounds require rerunning full axial stack and thread engagement.',
 'No washer bending or bearing stress allowable established; pressure per newton is not capacity.',
 'Candidate CAD is not yet substituted into released assembly or MuJoCo.',
 'Density is the existing SUS304 reference, not guaranteed maximum mass.'],
 'remaining': [x for x in ledger['remaining'] if not x.startswith('8 rear washers')],
 'whole_base_complete':False,'manufacturing_release':False}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'radial_gap_mm':gap,'head_contact_area_mm2':bearing_area,'washer_mass_g':sum(x['mass_kg'] for x in parts.values())*1000,'subtotal_g':float(subtotal['mass_kg'])*1000}))
