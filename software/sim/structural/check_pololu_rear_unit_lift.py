"""Certify a lifted translation route with swept bounds and Lipschitz distance bounds."""
import argparse,hashlib,json,math
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();paths=[]
def read(p):
 p=Path(p);paths.append(p);return json.loads(p.read_text())
def load(p):
 p=Path(p);paths.append(p);return cq.importers.importStep(str(p)).val()
def pair_bound(s,t):
 a,b=s.BoundingBox(),t.BoundingBox()
 gaps=[max(0,getattr(a,k+'min')-getattr(b,k+'max'),getattr(b,k+'min')-getattr(a,k+'max')) for k in 'xyz']
 return math.sqrt(sum(g*g for g in gaps))
plan=read(a.out/'plan.json');root=Path('validation/yaw_integrated_candidate_v7');inv=read(root/'inventory.json')['parts'];ss=load(root/'yaw_support_candidate.step').Solids();assert len(inv)==len(ss)==52;fixed={};removed=[]
for it,s in zip(inv,ss):
 assert abs(s.Volume()-it['volume_mm3'])<1e-5
 n=it['name']
 if n=='rear_plate' or ('_rear_' in n and (n.endswith('_bolt') or n.endswith('_rear_washer'))):removed.append(n)
 else:fixed[n]=s
assert len(removed)==17
for n,f in {'tray':'board/mechanical/prototype/rc_battery_tray_revB/tray.step','battery':'validation/rc_battery_cad_v1_checked/battery_candidate.step','Tab5':'software/sim/mujoco/assets/r9_fast_turn_v1/cad/Tab5.step','TTL':'software/sim/mujoco/assets/r9_fast_turn_v1/cad/TTL_interface.step'}.items():fixed[n]=load(f)
root=Path('validation/pololu_mount_assembly_v1');inv=read(root/'inventory.json')['parts'];ss=load(root/'mount_assembly.step').Solids();assert len(inv)==len(ss)==43;moving={}
for it,s in zip(inv,ss):
 assert abs(s.Volume()-it['volume_mm3'])<1e-5
 moving[it['name']]=s
for side in ['left','right']:moving[side+'_module_envelope']=load('validation/dual_pololu_mounted_layout_v1/'+side+'_envelope.step')
def bb(s):
 b=s.BoundingBox();return [b.xmin,b.ymin,b.zmin],[b.xmax,b.ymax,b.zmax]
def gap(a,b):return math.sqrt(sum(max(0,a[0][i]-b[1][i],b[0][i]-a[1][i])**2 for i in range(3)))
fb={n:bb(s) for n,s in fixed.items()};mb={n:bb(s) for n,s in moving.items()};eps=plan['criteria']['cad_numerical_allowance_mm'];threshold=plan['criteria']['minimum_unintended_gap_mm'];segments=[]
for si,(start,end) in enumerate(zip(plan['waypoints_mm'],plan['waypoints_mm'][1:])):
 rows=[]
 for n,s in moving.items():
  bounds=([mb[n][0][i]+min(start[i],end[i]) for i in range(3)],[mb[n][1][i]+max(start[i],end[i]) for i in range(3)])
  sweepbox=None
  for tn,t in fixed.items():
   row={'moving':n,'fixed':tn};broad=gap(bounds,fb[tn])-eps
   intended=n=='rear_plate' and (tn=='body_shroud' or 'yaw_fixed_support' in tn or 'threaded_backing_plate' in tn)
   if intended and bounds[1][0]<=fb[tn][0][0]+eps:
    row.update(method='contact_halfspace',pass_nominal=True,x_separation_mm=fb[tn][0][0]-bounds[1][0]);rows.append(row);continue
   if broad>=threshold:row.update(method='swept_aabb_pair',lower_bound_mm=broad,pass_nominal=True);rows.append(row);continue
   if sweepbox is None:sweepbox=cq.Solid.makeBox(*[bounds[1][i]-bounds[0][i] for i in range(3)],cq.Vector(*bounds[0]))
   bound=sweepbox.distance(t)-eps
   if bound>=threshold:row.update(method='swept_box_to_fixed_shape',lower_bound_mm=bound,pass_nominal=True);rows.append(row);continue
   stack=[(start,end)];leaves=[];cache={};failed=None
   while stack:
    u,v=stack.pop();mid=tuple((u[i]+v[i])/2 for i in range(3));length=math.sqrt(sum((v[i]-u[i])**2 for i in range(3)))
    if mid not in cache:cache[mid]=s.translate(mid).distance(t)
    d=cache[mid];lower=d-length/2-eps
    if d+eps<threshold:
     failed={'status':'sampled_clearance_failure','translation_mm':mid,'distance_mm':d,'envelope_only':n.endswith('_envelope')};break
    if lower>=threshold:leaves.append({'start':u,'end':v,'lower_bound_mm':lower});continue
    if length<=plan['minimum_interval_mm']+1e-9:
     failed={'status':'unresolved_bound','start':u,'end':v,'midpoint_distance_mm':d,'lower_bound_mm':lower};break
    stack.extend([(u,mid),(mid,v)])
   row.update(method='adaptive_translation_distance',evaluations=len(cache),certified_intervals=leaves,pass_nominal=failed is None,failure=failed);rows.append(row)
 segments.append({'index':si,'start_mm':start,'end_mm':end,'checks':rows,'pass_nominal':all(r['pass_nominal'] for r in rows)})
 print(json.dumps({'segment':si,'pass':segments[-1]['pass_nominal'],'failures':[r for r in rows if not r['pass_nominal']]}),flush=True)
 if not segments[-1]['pass_nominal']:break
r={'segments':segments,'continuous_nominal_route_verified':len(segments)==len(plan['waypoints_mm'])-1 and all(s['pass_nominal'] for s in segments),'stage_removed':removed,'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},'manufacturing_release':False};(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n')
