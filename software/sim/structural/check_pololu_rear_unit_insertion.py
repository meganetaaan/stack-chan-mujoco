"""Seek a concrete failure witness for a straight rear-unit insertion route."""
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
poses=[];witness=None
for offset in plan['motion']['offsets_mm']:
 checks=[];broad_clear=0;fail=[]
 for n,s in moving.items():
  moved=s.translate((offset,0,0))
  for tn,t in fixed.items():
   if pair_bound(moved,t)>=plan['criteria']['minimum_unintended_gap_mm']+1e-7:broad_clear+=1;continue
   ov=moved.intersect(t).Volume();distance=moved.distance(t)
   intended=offset==0 and n=='rear_plate' and (tn=='body_shroud' or 'yaw_fixed_support' in tn or 'threaded_backing_plate' in tn)
   bad=ov>plan['criteria']['maximum_overlap_mm3'] or (not intended and distance+1e-8<plan['criteria']['minimum_unintended_gap_mm'])
   row={'moving':n,'fixed':tn,'overlap_mm3':ov,'distance_mm':distance,'intended_final_contact':intended,'envelope_only':n.endswith('_envelope'),'failure':bad};checks.append(row)
   if bad:fail.append(row)
 poses.append({'offset_x_mm':offset,'broad_phase_clear_pairs':broad_clear,'detailed_checks':checks,'failures':fail})
 concrete=[r for r in fail if not r['envelope_only']]
 if concrete:
  witness={'offset_x_mm':offset,'failures':concrete};break
r={'stage_removed':removed,'moving_parts':len(moving),'fixed_parts':len(fixed),'poses':poses,'first_failure_witness':witness,'straight_route_rejected':witness is not None,'continuous_path_verified':False,'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},'manufacturing_release':False};(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'tested_offsets':[p['offset_x_mm'] for p in poses],'witness':witness},indent=2))
