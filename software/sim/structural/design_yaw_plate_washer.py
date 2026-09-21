"""Separate yaw washer candidate, with eccentric nut and shelf footprint checks."""
import argparse,hashlib,json,math
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
spec={'part_number':'SCW-YAW-PLATE-WASHER-01','revision':'A-candidate','quantity_if_adopted':8,'units':'mm','material':'SUS304 candidate, certificate required','process':'turned/faced, bore finished and edges deburred; capability unverified','outer_diameter':{'nominal':6.4,'min':6.35,'max':6.4},'inner_diameter':{'nominal':2.3,'min':2.3,'max':2.35},'thickness':{'nominal':.9,'min':.85,'max':.95},'edge_break_radial_max':.05,'face_flatness_max':.02,'face_parallelism_max':.02,'status':'comparison_candidate_not_adopted','note':'Replaces only eight yaw plate washers if adopted. Foot washers unchanged. Thickness limits include face form variation.'}
(a.out/'specification.json').write_text(json.dumps(spec,indent=2)+'\n')
plan={'question':'Does a separate larger washer address the known eccentric outer-footprint shortfall without encroaching on adjacent shelf features?',
 'stop':'One size candidate at eight nominal joints, plus eight offset directions per joint. No size sweep or strength simulation.',
 'criteria':{'nut_outer_margin_mm':0,'nominal_unintended_overlap_mm3':.01},
 'diagnostic':'Flat bearing annulus into shelf over a 0.01 mm slab. Missing area is reported, not discarded or declared a strength failure.',
 'limits':['Nominal 2 mm shank and coaxial nut; actual thread radial play unknown','Directional footprint sampling is not a continuous tolerance proof','No preload/contact-pressure/material allowable or pull-through proof','No adoption into current assembly']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
def annulus(x,y,z,ro,ri,h):return cq.Solid.makeCylinder(ro,h,cq.Vector(x,y,z)).cut(cq.Solid.makeCylinder(ri,h,cq.Vector(x,y,z)))
assembly_path=Path('board/mechanical/prototype/yaw_support_candidate/revB/yaw_support_candidate.step');fixed=cq.importers.importStep(str(assembly_path)).val();hashes={str(assembly_path):hashlib.sha256(assembly_path.read_bytes()).hexdigest()}
axes=[(side,x,cy+dy) for side,cy in [('left',26),('right',-26)] for x in [-34,8.1] for dy in [-10,10]]
for side,x,y in axes:fixed=fixed.cut(annulus(x,y,91,3,1.15,.9))
rows=[]
for side,x,y in axes:
 path=Path(f'validation/yaw_connector_shelf_relief_v2/{side}_yaw_fixed_support.step');hashes[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest();shelf=cq.importers.importStep(str(path)).val()
 washer=annulus(x,y,91,3.2,1.15,.9);assert washer.isValid() and len(washer.Solids())==1
 overlap=washer.intersect(fixed).Volume();cq.exporters.export(washer,str(a.out/f'{side}_{x}_{y}_washer.step'))
 probe_ro=6.35/2-.05;probe_ri=2.35/2+.05;expected=math.pi*(probe_ro**2-probe_ri**2);samples=[]
 for degrees in range(0,360,45):
  rad=math.radians(degrees);dx=.175*math.cos(rad);dy=.175*math.sin(rad)
  probe=annulus(x+dx,y+dy,90.99,probe_ro,probe_ri,.01);area=probe.intersect(shelf).Volume()/.01
  samples.append({'direction_deg':degrees,'supported_flat_area_mm2':area,'missing_flat_area_mm2':max(0,expected-area)})
 rows.append({'side':side,'axis_xy_mm':[x,y],'nominal_unintended_overlap_mm3':overlap,'nominal_overlap_pass':overlap<=.01,'flat_annulus_area_mm2':expected,'offset_samples':samples})
margin=6.35/2-.05-4/math.sqrt(2)-.175
cq.exporters.export(annulus(0,0,0,3.2,1.15,.9),str(a.out/'washer_local.step'))
result={'source_sha256':hashes,'nut_outer_margin_at_known_offset_mm':margin,'additional_relative_offset_before_zero_outer_margin_mm':margin,'rows':rows,'outer_footprint_screen_pass':margin>=0,'all_nominal_overlap_pass':all(r['nominal_overlap_pass'] for r in rows),'maximum_sampled_missing_flat_area_mm2':max(s['missing_flat_area_mm2'] for r in rows for s in r['offset_samples']),'manufacturing_release':False}
(a.out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['source_sha256','rows']},indent=2))
