"""Resolve envelope flags against manufacturer common STEP, not 5V qualification."""
import argparse,hashlib,json
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser();p.add_argument('step',type=Path);a=p.parse_args()
root=Path('validation/torso_power_integration_v1');out=Path('validation/torso_module_contacts_v1');out.mkdir(exist_ok=True)
spec=json.loads(Path('schematics/power/dual_pololu_mechanical.json').read_text())
assert hashlib.sha256(a.step.read_bytes()).hexdigest()==spec['step_sha256']
r=json.loads((root/'report.json').read_text());ss=cq.importers.importStep(str(root/'torso_candidate.step')).val().Solids()
assert len(ss)==len(r['parts'])==100
parts={}
for row,s in zip(r['parts'],ss):
 assert abs(row['volume_mm3']-s.Volume())<1e-5
 parts[row['name']]=s
plan={'scope':__doc__,'criteria':{'maximum_overlap_mm3':.01},'stop':'Evaluate exactly the16 flagged envelope/hardware pairs; do not change geometry or criteria.', 'limits':['Generic STEP differs from 5V drawing in component height','Nominal fit only; threads modeled as envelopes','No tolerance/PCB deflection/thermal validation']}
(out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
module=cq.importers.importStep(str(a.step)).val()
places=json.loads(Path('validation/dual_pololu_mounted_layout_v1/report.json').read_text())['placements']
placed={x['side']+'_module_envelope':module.translate(tuple(x['step_translation_mm'])) for x in places}
rows=[]
for row in r['near_pairs']:
 if not row['overlap_flag']:continue
 n,m=row['parts'];assert m in placed
 hardware=parts[n];real=placed[m]
 v=hardware.intersect(real).Volume()
 rows.append({'hardware':n,'module':m,'previous_envelope_overlap_mm3':row['overlap_mm3'],'common_STEP_overlap_mm3':v,'distance_mm':hardware.distance(real),'common_STEP_overlap_flag':v>.01})
assert len(rows)==16
report={'rows':rows,'common_STEP_flag_count':sum(x['common_STEP_overlap_flag'] for x in rows),
 'source_sha256':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in [a.step,root/'report.json',root/'torso_candidate.step',Path('schematics/power/dual_pololu_mechanical.json'),Path('validation/dual_pololu_mounted_layout_v1/report.json')]},
 'variant_specific_fit_verified':False,'manufacturing_release':False,'limits':plan['limits']}
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(rows,indent=2))
