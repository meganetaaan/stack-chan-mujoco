"""Reconcile nominal purchased screw masses with v7 names without inventing inertia."""
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
oldpath=Path('board/mechanical/prototype/yaw_support_candidate/revA/inventory.json');newpath=Path('validation/yaw_integrated_candidate_v7/inventory.json');masspath=Path('validation/yaw_hardware_catalog_mass_v1/report.json');rearpath=Path('docs/prototype/mechanical/yaw_support/rear_bolt_candidate.json')
old={x['name']:x for x in json.loads(oldpath.read_text())['parts']};new={x['name']:x for x in json.loads(newpath.read_text())['parts']};catalog=json.loads(masspath.read_text());rear=json.loads(rearpath.read_text());assert rear['part']=='SNS-M3-16';rows=[]
for n,v in new.items():
 if n.endswith('_keeper') or ('_plate_' in n and n.endswith('_screw')):
  part='SLH-M2-10';assert part in v['note']
 elif '_rear_' in n and n.endswith('_bolt'):part=rear['part']
 else:continue
 assert v==old[n],n
 rows.append({'name':n,'selected_candidate':part,'catalog_nominal_mass_g':catalog['parts'][part]['nominal_mass_g'],'inventory_unchanged_from_revA':True,'com_m':None,'inertia_kg_m2':None})
assert len(rows)==20 and sum(x['selected_candidate']=='SLH-M2-10' for x in rows)==12
r={'rows':rows,'nominal_screw_total_g':sum(x['catalog_nominal_mass_g'] for x in rows),'source_sha256':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in [oldpath,newpath,masspath,rearpath]},'manufacturer_rechecked_on':'2026-09-22','manufacturer_sources':catalog['parts'],'limits':['Nominal masses only; not guaranteed maxima or measured values.','SNS candidate is12.9; legacy8.8 calculations are not upgraded by this mapping.','Unchanged inventory does not prove purchased geometry or joint strength.','COM/inertia remain null; do not scale collision envelopes.'],'model_updated':False,'manufacturing_release':False}
(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'mapped':len(rows),'mass_g':r['nominal_screw_total_g']}))
