"""Additive CAD-frame inertia comparison for assigned current torso parts."""
import hashlib,json
from pathlib import Path
import cadquery as cq
import numpy as np
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'validation/current_torso_inertia_v1';OUT.mkdir(exist_ok=True)
paths=[ROOT/'validation/current_torso_mass_v2/report.json',ROOT/'validation/torso_print_conditions_v1/report.json',ROOT/'validation/serviceable_torso_v3/assembly.step',ROOT/'validation/tab5_frame_print_v1/carrier_print.step']
ledger,printed=[json.loads(p.read_text()) for p in paths[:2]]
plan={'frame':'Assembly CAD origin and axes; mm converted to m; not MuJoCo body frame','criteria':['One row per current CAD part','Reject missing masses in complete aggregate','Independent translated cuboid and two-body parallel-axis checks','Use pre-insertion carrier shape consistently for both mass and moments'],'stop':'One CAD moment aggregation, no dynamics or strength acceptance','assumption':'Each allocated part has uniform mass distribution within its chosen CAD shape, including electronics/fasteners; comparison only'}
(OUT/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
def moments(shape,m):
 c=np.array(shape.Center().toTuple())*1e-3
 I=np.array(cq.Shape.matrixOfInertia(shape))*m/shape.Volume()*1e-6
 return m,m*c,I+m*((c@c)*np.eye(3)-np.outer(c,c))
def aggregate(terms):
 m=sum(t[0] for t in terms);f=sum((t[1] for t in terms),np.zeros(3));io=sum((t[2] for t in terms),np.zeros((3,3)));c=f/m;ic=io-m*((c@c)*np.eye(3)-np.outer(c,c))
 assert np.allclose(ic,ic.T,atol=1e-12) and np.linalg.eigvalsh(ic).min()>0
 return {'mass_kg':m,'first_moment_kg_m':f.tolist(),'com_CAD_m':c.tolist(),'inertia_origin_kg_m2':io.tolist(),'inertia_com_kg_m2':ic.tolist()}
def complete(rows):
 if any(r['mass_kg'] is None for r in rows):raise ValueError('Unassigned part masses: complete aggregate forbidden')
 return aggregate([(r['mass_kg'],np.array(r['first_moment_kg_m']),np.array(r['inertia_origin_kg_m2'])) for r in rows])
# Analytic independent checks, with millimetre CAD dimensions.
box=cq.Workplane('XY').box(20,40,60).translate((100,200,300)).val();m,f,io=moments(box,2.)
c=np.array([.1,.2,.3]);expected=np.diag(2/12*np.array([.04**2+.06**2,.02**2+.06**2,.02**2+.04**2]))+2*((c@c)*np.eye(3)-np.outer(c,c))
err=float(np.max(np.abs(io-expected)));assert err<1e-12 and np.allclose(f,2*c)
a=cq.Workplane('XY').box(10,10,10).translate((-100,0,0)).val();b=a.translate((200,0,0));pair=aggregate([moments(a,1),moments(b,1)])
expected=np.diag([2*.01**2/6,2*(.01**2/6+.1**2),2*(.01**2/6+.1**2)])
err2=float(np.max(np.abs(np.array(pair['inertia_com_kg_m2'])-expected)));assert err2<1e-12
solids=cq.importers.importStep(str(paths[2])).val().Solids();assert len(solids)==len(ledger['rows'])==115
pm={r['name']:r for r in printed['parts']};terms=[];rows=[]
for item,s in zip(ledger['rows'],solids):
 assert abs(s.Volume()-item['cad_volume_mm3'])<1e-5
 n=item['name'];mass=item['mass_kg'];basis=item['category']
 if n in pm:
  assert mass is None
  mass=pm[n]['homogeneous_comparison_mass_kg'];basis='uniform_print_comparison'
  if n=='new_carrier':s=cq.importers.importStep(str(paths[3])).val()
  assert abs(s.Volume()-pm[n]['material_volume_mm3'])<1e-5
 row={'name':n,'mass_kg':mass,'basis':basis,'distribution_assumption':'uniform CAD shape, not measured COM/inertia'}
 if mass is not None:
  t=moments(s,mass);terms.append(t);row.update(first_moment_kg_m=t[1].tolist(),inertia_origin_kg_m2=t[2].tolist())
 else:row.update(first_moment_kg_m=None,inertia_origin_kg_m2=None)
 rows.append(row)
try:complete(rows)
except ValueError:rejects_missing=True
else:raise AssertionError('Missing masses silently accepted')
partial=aggregate(terms);assert abs(partial['mass_kg']-(ledger['numeric_comparison_subtotal_kg']+printed['homogeneous_printed_comparison_subtotal_kg']))<1e-12
r={'plan':plan,'rows':rows,'assigned_count':len(terms),'unknown_count':115-len(terms),'partial_uniform_CAD_comparison':partial,'complete_torso_inertia':None,'whole_robot_inertia':None,'missing_mass_rejection_verified':rejects_missing,'analytic_errors':{'translated_cuboid_kg_m2':err,'two_body_parallel_axis_kg_m2':err2},'model_updated':False,'manufacturing_release':False,'limits':['Unknown30CADparts and non-CAD motors/legs/electrical allocations remain','No internal component COM/inertia guarantee','Not an upper/lower load bound','Carrier insertion redistributes polymer; pre-insertion inertia is approximate','CAD-to-MuJoCo frame transform not applied'],'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
(OUT/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:r[k] for k in ['assigned_count','unknown_count','partial_uniform_CAD_comparison','analytic_errors']}))
