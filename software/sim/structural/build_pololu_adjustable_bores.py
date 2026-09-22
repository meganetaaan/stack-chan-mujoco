"""Enlarge bracket through-bores only; preserve existing nut anti-rotation slots."""
import hashlib,itertools,json,math
from pathlib import Path
import cadquery as cq
ROOT=Path(__file__).resolve().parents[3];out=ROOT/'validation/pololu_adjustable_bores_v1';out.mkdir(exist_ok=True)
ip=ROOT/'validation/pololu_mount_assembly_v1/inventory.json';sp=ip.with_name('mount_assembly.step');pp=ROOT/'validation/dual_pololu_mounted_layout_v1/report.json'
inv=json.loads(ip.read_text())['parts'];ss=cq.importers.importStep(str(sp)).val().Solids();assert len(inv)==len(ss)==43
parts={}
for it,s in zip(inv,ss):
 assert abs(it['volume_mm3']-s.Volume())<1e-5
 parts[it['name']]=s
places=json.loads(pp.read_text())['placements']
plan={'question':'Does enlarging only printed bracket bores to2.4mm permit more screw adjustment without widening the nut slot?',
 'change':{'bore_diameter_old_mm':2.2,'bore_diameter_new_mm':2.4,'nut_slot_width_unchanged_mm':4.2},
 'criteria':{'maximum_overlap_mm3':.01,'remaining_connected_solids':1,'PCB_radial_margin_min_mm':0},
 'comparison_error_per_axis_mm':.15,'hardware_shift_per_axis_mm':.09,
 'error_origin':'PCB +/-0.1 plus hypothetical print position +/-0.05; sensitivity case, not certified print capability',
 'stop':'One bore revision, eight holes and32 offset poses; do not widen nut slots or run strength FE here.',
 'limits':['Bore and nut sizes nominal','Seat geometry not strength or preload qualification','Own-bracket contact only; no assembly path or full tolerance proof']}
(out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
old_brackets={side:parts[side+'_bracket'] for side in ['left','right']}
changes=[]
for place in places:
 n=place['side']+'_bracket';old=parts[n];new=old
 for x,y,z in place['mount_axes_mm']:
  new=new.cut(cq.Solid.makeCylinder(1.2,30,cq.Vector(x,y,85)))
 new=new.clean();assert new.isValid() and len(new.Solids())==1
 # New material cannot create new external nominal interference.
 assert new.cut(old).Volume()<1e-6
 # Pocket itself remains open; only through-bore material is removed.
 changes.append({'part':n,'removed_volume_mm3':old.Volume()-new.Volume(),'new_volume_mm3':new.Volume(),'solids':len(new.Solids())})
 parts[n]=new;cq.exporters.export(new,str(out/(n+'.step')))
rows=[]
for side,i,sx,sy in itertools.product(['left','right'],range(4),[-1,1],[-1,1]):
 delta=(sx*.09,sy*.09,0);bracket=parts[side+'_bracket']
 moved={k:parts[f'{side}_module_{i}_{k}'].translate(delta) for k in ['screw','nut','spacer']}
 overlaps={k:s.intersect(bracket).Volume() for k,s in moved.items()}
 old_overlaps={k:s.intersect(old_brackets[side]).Volume() for k,s in moved.items()}
 spacer=moved['spacer'];b=spacer.BoundingBox();h=.001
 layer=spacer.intersect(cq.Solid.makeBox(10,10,h,cq.Vector(b.xmin-1,b.ymin-1,b.zmin)))
 area=layer.translate((0,0,-h)).intersect(bracket).Volume()/h
 margin=(2.18-2)/2-math.sqrt(2)*(.15-.09)
 rows.append({'side':side,'index':i,'offset_mm':delta,'own_bracket_overlap_mm3':overlaps,'old_bracket_overlap_mm3':old_overlaps,'projected_seat_mm2':area,'PCB_radial_margin_mm':margin,'nominal_corner_pass':max(overlaps.values())<=.01 and margin>=0})
# Preserve names and source identities; replace only bracket geometry quantities.
for it in inv:
 s=parts[it['name']];it['volume_mm3']=s.Volume()
 b=s.BoundingBox();it['bounds_mm']=[getattr(b,k) for k in ['xmin','xmax','ymin','ymax','zmin','zmax']]
 if it['name'].endswith('_bracket'):it['geometry_revision']='through-bore2.4; original4.2 nut slot retained'
sha={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ip,sp,pp]}
(out/'inventory.json').write_text(json.dumps({'parts':inv,'source_sha256':sha,'manufacturing_release':False},indent=2)+'\n')
cq.exporters.export(cq.Compound.makeCompound(list(parts.values())),str(out/'mount_assembly.step'))
r={'source_sha256':sha,'changes':changes,'rows':rows,'all_nominal_corners_pass':all(x['nominal_corner_pass'] for x in rows),'minimum_projected_seat_mm2':min(x['projected_seat_mm2'] for x in rows),'strength_verified':False,'manufacturing_release':False}
(out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k not in ['rows','source_sha256']},indent=2))
