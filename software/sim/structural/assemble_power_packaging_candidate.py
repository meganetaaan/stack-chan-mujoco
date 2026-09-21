"""Integrate present packaging candidates; not manufacturing assembly."""
import argparse,json,hashlib,itertools
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
paths={
'yaw_structure':'board/mechanical/prototype/yaw_support_candidate/revA/yaw_support_candidate.step',
'Tab5':'software/sim/mujoco/assets/r9_fast_turn_v1/cad/Tab5.step',
'TTL':'software/sim/mujoco/assets/r9_fast_turn_v1/cad/TTL_interface.step',
'battery':'validation/rc_battery_cad_v1_checked/battery_candidate.step',
'tray':'board/mechanical/prototype/rc_battery_tray_revB/tray.step',
'strap':'validation/battery_retention_envelope_v1/strap_envelope.step',
'UBEC_left':'validation/dual_ubec_layout_v2/left.step',
'UBEC_right':'validation/dual_ubec_layout_v2/right.step'}
shapes={n:cq.importers.importStep(p).val() for n,p in paths.items()};assembly=cq.Assembly(name='power_packaging_candidate')
for n,s in shapes.items():assembly.add(s,name=n)
assembly.save(str(a.out/'packaging.step'))
readback=cq.importers.importStep(str(a.out/'packaging.step')).val()
delta=abs(readback.Volume()-sum(s.Volume() for s in shapes.values()))
assert readback.isValid() and delta<1e-4
rows=[]
for (n,s),(m,t) in itertools.combinations(shapes.items(),2):rows.append({'a':n,'b':m,'overlap_mm3':s.intersect(t).Volume(),'distance_mm':s.distance(t)})
(a.out/'report.json').write_text(json.dumps({'step_readback':{'valid':readback.isValid(),'solids':len(readback.Solids()),'sum_volume_difference_mm3':delta},'groups':list(paths),'sources_sha256':{p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in paths.values()},'checks':rows,'scope':'Nominal static group-pair intersections; intentional touching is not clearance qualification','omitted':['Leg assemblies and full motion','Wires connectors UBEC mounts switch protection PCB','Tolerances deflection and thermal clearances','Battery strap buckle and actual material thickness'],'manufacturing_release':False},indent=2)+'\n');print([r for r in rows if r['overlap_mm3']>1e-6]);print('pairs',len(rows))
