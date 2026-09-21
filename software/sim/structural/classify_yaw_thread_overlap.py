"""Recognize only CAD overlap exactly matching declared pilot-hole/shaft envelopes."""
import argparse,hashlib,json,math
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
plan={'question':'Are all remaining overlaps solely the documented thread-envelope/pilot annuli?', 'criteria_before_calculation':{'unexplained_volume_mm3':1e-6,'missing_expected_volume_mm3':1e-6,'analytic_volume_error_mm3':1e-6},'source_dimensions':{'backing_x_mm':[-53.5,-50.5],'M3_shaft_radius_mm':1.5,'M3_pilot_radius_mm':1.25,'M2_shaft_radius_mm':1,'M2_pilot_radius_mm':.8},'limits':['Threads absent in CAD: matching annuli explain overlap but do not qualify threads','No stripping, preload, tolerance, effective engagement or assembly torque proof'],'stop':'Classify existing positive-volume pairs only; do not modify CAD or general overlap threshold'}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
invpath=a.candidate/'inventory.json';steppath=a.candidate/'yaw_support_candidate.step';overpath=a.candidate/'all_pair_overlap_report.json';inv=json.loads(invpath.read_text())['parts'];solids=cq.importers.importStep(str(steppath)).val().Solids();assert len(inv)==len(solids)==52
parts={}
for i,s in zip(inv,solids):
 assert abs(s.Volume()-i['volume_mm3'])<1e-5;parts[i['name']]=s
rows=[]
for entry in json.loads(overpath.read_text())['nonzero_pairs']:
 if entry['new_overlap_mm3']<=1e-6:continue
 plate,fastener=entry['pair'];assert plate.endswith('threaded_backing_plate')
 if fastener.endswith('_keeper'):r,ri,kind=1,.8,'M2 keeper'
 elif '_rear_' in fastener and fastener.endswith('_bolt'):r,ri,kind=1.5,1.25,'M3 main bolt'
 else:raise ValueError('Unclassified pair '+str(entry['pair']))
 pb=parts[plate].BoundingBox();assert abs(pb.xmin+53.5)<1e-6 and abs(pb.xmax+50.5)<1e-6
 b=parts[fastener].BoundingBox();origin=cq.Vector(-53.5,(b.ymin+b.ymax)/2,(b.zmin+b.zmax)/2)
 annulus=cq.Solid.makeCylinder(r,3,origin,cq.Vector(1,0,0)).cut(cq.Solid.makeCylinder(ri,3,origin,cq.Vector(1,0,0)))
 actual=parts[plate].intersect(parts[fastener]);extra=actual.cut(annulus).Volume();missing=annulus.cut(actual).Volume();analytic=math.pi*(r*r-ri*ri)*3
 rows.append({'pair':entry['pair'],'kind':kind,'measured_overlap_mm3':actual.Volume(),'expected_analytic_mm3':analytic,'unexplained_mm3':extra,'missing_expected_mm3':missing,'thread_envelope_only':extra<1e-6 and missing<1e-6 and abs(actual.Volume()-analytic)<1e-6})
assert len(rows)==12
sources=[invpath,steppath,overpath,Path('software/sim/structural/build_yaw_nut_plate.py'),Path('software/sim/structural/build_yaw_backing_keeper.py')]
report={'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},'rows':rows,'all_remaining_overlap_explained_by_declared_thread_envelopes':all(r['thread_envelope_only'] for r in rows),'thread_strength_qualified':False,'manufacturing_release':False}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'classified':len(rows),'all_explained':report['all_remaining_overlap_explained_by_declared_thread_envelopes']}));assert report['all_remaining_overlap_explained_by_declared_thread_envelopes']
