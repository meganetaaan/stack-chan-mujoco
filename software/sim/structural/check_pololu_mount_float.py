"""Check existing hardware shifted independently for four PCB hole-error corners."""
import hashlib,itertools,json,math
from pathlib import Path
import cadquery as cq
ROOT=Path(__file__).resolve().parents[3]
out=ROOT/'validation/pololu_mount_float_v1';out.mkdir(exist_ok=True)
invpath=ROOT/'validation/pololu_mount_assembly_v1/inventory.json'
steppath=invpath.with_name('mount_assembly.step')
inv=json.loads(invpath.read_text())['parts'];ss=cq.importers.importStep(str(steppath)).val().Solids()
assert len(inv)==len(ss)==43
parts={}
for row,s in zip(inv,ss):
 assert abs(row['volume_mm3']-s.Volume())<1e-5
 parts[row['name']]=s
plan={'question':'Does existing nominal bracket permit individual screw/nut/spacer shift without cutting new slots?',
 'PCB_error_per_coordinate_mm':.1,'hardware_shift_per_coordinate_mm':.05,
 'PCB_hole_diameter_mm':2.18,'screw_envelope_diameter_mm':2.,
 'criteria':{'maximum_overlap_mm3':.01,'minimum_nominal_radial_margin_mm':0},
 'stop':'32 specified corner poses; check own bracket and projected spacer seat only.',
 'limits':['Nominal CAD, print errors excluded','Assumed independent Cartesian PCB hole location errors','Translation only; no fastener tilt or nut rotation','Corner samples do not prove arbitrary assembly paths or all configurations','Bearing area is geometric, not a strength criterion']}
(out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
rows=[]
for side,i,sx,sy in itertools.product(['left','right'],range(4),[-1,1],[-1,1]):
 delta=(sx*.05,sy*.05,0)
 bracket=parts[side+'_bracket']
 moved={k:parts[f'{side}_module_{i}_{k}'].translate(delta) for k in ['screw','nut','spacer']}
 overlaps={k:s.intersect(bracket).Volume() for k,s in moved.items()}
 spacer=moved['spacer'];b=spacer.BoundingBox()
 # A thin downward-translated spacer layer probes the actual planar support footprint.
 h=.001
 layer=spacer.intersect(cq.Solid.makeBox(10,10,h,cq.Vector(b.xmin-1,b.ymin-1,b.zmin)))
 area=layer.translate((0,0,-h)).intersect(bracket).Volume()/h
 residual=math.hypot(.1-.05,.1-.05)
 margin=(2.18-2)/2-residual
 rows.append({'side':side,'hole_index':i,'translation_mm':delta,'own_bracket_overlap_mm3':overlaps,
 'PCB_radial_margin_mm':margin,'projected_spacer_seat_mm2':area,
 'nominal_corner_screen_pass':max(overlaps.values())<=.01 and margin>=0})
report={'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [invpath,steppath]},
 'rows':rows,'all_nominal_corners_pass':all(x['nominal_corner_screen_pass'] for x in rows),
 'minimum_projected_seat_mm2':min(x['projected_spacer_seat_mm2'] for x in rows),
 'continuous_tolerance_fit_verified':False,'manufacturing_release':False}
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ['rows','source_sha256']},indent=2))
