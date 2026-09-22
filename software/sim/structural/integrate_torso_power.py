"""Combine current yaw candidate and Pololu mount; retain installed yaw fasteners."""
import hashlib,itertools,json
from pathlib import Path
import cadquery as cq
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'validation/torso_power_integration_v1'
OUT.mkdir(exist_ok=True)
plan={'scope':__doc__,'criteria':{'overlap_flag_mm3':.01,'near_gap_flag_mm':.5},
 'replacement':'Replace rear_plate only. The16 yaw rear fasteners removed for insertion must be present in the final assembly.',
 'stop':'One nominal final-position cross-subassembly overlap screen; no new geometry or mesh refinement.',
 'limits':['No articulated legs/feet or harness','Electronics use module envelopes; new protection PCB not placed','Contact flags require joint-specific review; no automatic exemptions','Nominal static geometry, no tolerance or deformation qualification']}
(OUT/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
files=[];parts={};meta={}
def read(p):
 p=ROOT/p;files.append(p);return json.loads(p.read_text())
def load(p):
 p=ROOT/p;files.append(p);return cq.importers.importStep(str(p)).val()
def add(n,s,group,item):
 assert n not in parts and s.isValid()
 parts[n]=s;meta[n]={'name':n,'group':group,'volume_mm3':s.Volume(),'source_item':item}
ptr=read('board/mechanical/prototype/yaw_support_candidate/current.json')
inv=read(ptr['inventory'])['parts'];ss=load(ptr['assembly']).Solids();assert len(inv)==len(ss)==52
for it,s in zip(inv,ss):
 assert abs(it['volume_mm3']-s.Volume())<1e-5
 if it['name']=='rear_plate':continue
 add('yaw__'+it['name'],s,'yaw',it['name'])
inv=read('validation/pololu_mount_assembly_v1/inventory.json')['parts'];ss=load('validation/pololu_mount_assembly_v1/mount_assembly.step').Solids()
assert len(inv)==len(ss)==43
for it,s in zip(inv,ss):
 assert abs(it['volume_mm3']-s.Volume())<1e-5
 add('power__'+it['name'],s,'power',it['name'])
for n,p in {'tray':'board/mechanical/prototype/rc_battery_tray_revB/tray.step','battery':'validation/rc_battery_cad_v1_checked/battery_candidate.step','Tab5':'software/sim/mujoco/assets/r9_fast_turn_v1/cad/Tab5.step','TTL':'software/sim/mujoco/assets/r9_fast_turn_v1/cad/TTL_interface.step',**{side+'_module_envelope':f'validation/dual_pololu_mounted_layout_v1/{side}_envelope.step' for side in ['left','right']}}.items():
 add(n,load(p),'payload',p)
retained=[n for n in parts if n.startswith('yaw__') and '_rear_' in n and (n.endswith('_bolt') or n.endswith('_rear_washer'))]
assert len(parts)==100 and len(retained)==16
rows=[];broad_count=0
for n,m in itertools.combinations(parts,2):
 if meta[n]['group']==meta[m]['group'] and meta[n]['group']!='payload':continue
 a,b=parts[n].BoundingBox(),parts[m].BoundingBox()
 gap=sum(max(0,getattr(a,k+'min')-getattr(b,k+'max'),getattr(b,k+'min')-getattr(a,k+'max'))**2 for k in 'xyz')**.5
 if gap>=.5:
  broad_count+=1;continue
 s,t=parts[n],parts[m];d=s.distance(t)
 if d<.5:
  v=s.intersect(t).Volume()
  rows.append({'parts':[n,m],'distance_mm':d,'overlap_mm3':v,'overlap_flag':v>.01})
print(json.dumps({'parts':len(parts),'broad_clear':broad_count,'near_pairs':len(rows),'overlap_flags':sum(x['overlap_flag'] for x in rows)}),flush=True)
cq.exporters.export(cq.Compound.makeCompound(list(parts.values())),str(OUT/'torso_candidate.step'))
report={'parts':list(meta.values()),'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},'part_count':len(parts),'retained_yaw_rear_fasteners':retained,'replaced':['yaw rear_plate'],'broad_clear_pairs':broad_count,'near_pairs':rows,'full_interference_verified':False,'manufacturing_release':False}
(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
