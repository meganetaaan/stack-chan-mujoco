"""Continuous nominal rear insertion of support subassemblies and rear plate."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--as-module',action='store_true');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
base=Path('validation/yaw_integrated_candidate_v2');paths=[base/n for n in ['inventory.json','geometric_moments.json','yaw_support_candidate.step']]
plan={'question':'Can the revised support groups and rear plate be inserted from the rear before servos/electronics/legs?',
 'method':'Per-group axis-aligned bounding box swept continuously 150 mm in -X from final pose; tests the whole corridor, no angle/time sampling.',
 'sequence':['Insert left/right 17-part support groups in either order, rear plate absent.','Insert empty rear structural plate, supports held in final pose.','Install rear main screws/washers and body corner hardware afterwards; tightening/access outside this check.'],
 'criterion_intersection_mm3':.01,'contact_policy':'Intended final rail/plate contact allowed at zero distance; no positive manufacturing clearance claimed.',
 'stop':'One straight direction and three groups; bounding-box collision is inconclusive for actual shapes, not an automatic physical failure.',
 'limits':['No servo, Tab5, battery, wires, legs or moving couplers installed during these steps','Hand/grip/jig space, gravity stability, tools and tightening not verified','No tolerance or misalignment coverage','Requires supporting groups before rear fasteners are installed; temporary fixture not yet designed','No manufacturing release']}
if a.as_module:
 plan['sequence']=['Attach both support groups to rear plate using the eight rear main screws and washers outside the body.','Translate the resulting 51-part module together into the empty shroud.','Install body corner fasteners afterwards; torque, hand space and body fastener access remain unverified.']
 plan['limits']=[x for x in plan['limits'] if not x.startswith('Requires supporting')]
 plan['stop']='Three group corridors and 16 rear-hardware corridors, sharing one 150 mm X translation; no size or angle sweep.'
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
inv=json.loads(paths[0].read_text())['parts'];mom=json.loads(paths[1].read_text())['parts'];solids=cq.importers.importStep(str(paths[2])).val().Solids();assert len(inv)==len(mom)==len(solids)==52
parts={}
for record,m,s in zip(inv,mom,solids):
 assert record['name']==m['name'] and abs(record['volume_mm3']-s.Volume())<1e-5
 assert np.allclose(np.array(s.Center().toTuple())*.001,m['com_assembly_m'],atol=1e-8,rtol=0)
 parts[record['name']]=s
groups={};names={}
for side in ['left','right']:
 names[side]=[n for n in parts if n.startswith(side+'_') and not n.startswith(side+'_rear_')];assert len(names[side])==17
 groups[side]=cq.Compound.makeCompound([parts[n] for n in names[side]])
groups['rear_plate']=parts['rear_plate'];names['rear_plate']=['rear_plate'];rows=[]
if a.as_module:
 for name in parts:
  if '_rear_' in name:groups[name]=parts[name];names[name]=[name]
 assert sum(len(n) for n in names.values())==51
for name,s in groups.items():
 b=s.BoundingBox();corridor=cq.Solid.makeBox(b.xlen+150,b.ylen,b.zlen,cq.Vector(b.xmin-150,b.ymin,b.zmin));cq.exporters.export(corridor,str(a.out/f'{name}_corridor.step'))
 targets={'body_shroud':parts['body_shroud']}
 if name=='rear_plate':targets.update({k:groups[k] for k in ['left','right']})
 elif name in ['left','right'] and not a.as_module:targets['other_support']=groups['right' if name=='left' else 'left']
 checks=[]
 for target,fixed in targets.items():
  volume=corridor.intersect(fixed).Volume();checks.append({'target':target,'intersection_mm3':volume,'distance_mm':corridor.distance(fixed),'nominal_corridor_pass':volume<=.01})
 rows.append({'group':name,'parts':names[name],'final_bounds_mm':[b.xmin,b.xmax,b.ymin,b.ymax,b.zmin,b.zmax],'start_group_front_x_mm':b.xmax-150,'checks':checks})
result={'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},'rows':rows,'module_parts':51 if a.as_module else None,'all_nominal_corridors_pass':all(c['nominal_corridor_pass'] for r in rows for c in r['checks']),'manufacturing_release':False}
(a.out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps([{'group':r['group'],'checks':r['checks']} for r in rows],indent=2))
