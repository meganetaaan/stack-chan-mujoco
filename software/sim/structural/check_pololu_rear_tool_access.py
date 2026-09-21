"""Continuous axial tool sweep against two detached rear-assembly stages."""
import argparse,hashlib,json
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser();p.add_argument('module_step',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args();paths=[]
def read(p):
 p=Path(p);paths.append(p);return json.loads(p.read_text())
plan=read(a.out/'plan.json');tool=read('docs/prototype/mechanical/pololu_mount_fasteners/rear_tool_candidate.json');md=read('schematics/power/dual_pololu_mechanical.json');assert hashlib.sha256(a.module_step.read_bytes()).hexdigest()==md['step_sha256'];paths.append(a.module_step);module=cq.importers.importStep(str(a.module_step)).val()
root=Path('validation/pololu_mount_assembly_v1');inv=read(root/'inventory.json')['parts'];sp=root/'mount_assembly.step';paths.append(sp);ss=cq.importers.importStep(str(sp)).val().Solids();assert len(ss)==len(inv)==43
base={}
for it,s in zip(inv,ss):
 assert abs(it['volume_mm3']-s.Volume())<1e-5
 if it['group'] in ['structure','rear_hardware']:base[it['name']]=s
assert len(base)==19
places=read('validation/dual_pololu_mounted_layout_v1/report.json')['placements'];modules={p['side']+'_module':module.translate(tuple(p['step_translation_mm'])) for p in places}
rows=[]
for n,nut in base.items():
 if not n.endswith('_nut'):continue
 key=n[:-4];b=nut.BoundingBox();y,z=(b.ymin+b.ymax)/2,(b.zmin+b.zmax)/2;x=plan['motion']['tip_x_mm'];travel=plan['motion']['withdrawal_x_mm'];axis=cq.Vector(1,0,0)
 shaft=cq.Solid.makeCylinder(tool['blade_diameter_mm']/2,tool['blade_length_mm']+travel,cq.Vector(x,y,z),axis)
 handle=cq.Solid.makeCylinder(max(tool['overall_dimensions_mm'][1:])/2,tool['handle_length_mm']+travel,cq.Vector(x+tool['blade_length_mm'],y,z),axis);swept=shaft.fuse(handle)
 for stage in plan['stages']:
  obs=dict(base)
  if stage=='same_with_modules':obs.update(modules)
  checks=[]
  for name,t in obs.items():
   if name in [n,key+'_screw']:continue
   intended=name==key+'_inner_washer';ov=swept.intersect(t).Volume();d=swept.distance(t)
   pcb_overlap=None
   if name.endswith('_module'):
    pcb=t.intersect(cq.Solid.makeBox(200,200,1.5748,cq.Vector(-100,-100,105.065)))
    pcb_overlap=swept.intersect(pcb).Volume()
   checks.append({'pcb_layer_overlap_mm3':pcb_overlap,'part':name,'overlap_mm3':ov,'distance_mm':d,'end_plane_contact_intended':intended,'pass':ov<=plan['criteria']['maximum_overlap_mm3'] and (intended or d+1e-8>=plan['criteria']['minimum_unintended_clearance_mm'])})
  rows.append({'nut':n,'stage':stage,'checks':checks,'failures':[c for c in checks if not c['pass']],'external_envelope_pass':all(c['pass'] for c in checks),'engagement_verified':False})
r={'rows':rows,'stage_external_envelope_pass':{s:all(r['external_envelope_pass'] for r in rows if r['stage']==s) for s in plan['stages']},'minimum_socket_recess_geometric_depth_mm':5.0,'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},'assembly_verified':False,'manufacturing_release':False};(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'stages':r['stage_external_envelope_pass'],'failures':[{'nut':x['nut'],'stage':x['stage'],'failures':x['failures']} for x in rows if x['failures']]},indent=2))
