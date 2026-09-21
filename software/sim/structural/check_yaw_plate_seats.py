"""Nominal bearing-footprint audit before using clamp load in structural models."""
import argparse,hashlib,json,math
from pathlib import Path
import cadquery as cq
ROOT=Path(__file__).resolve().parents[3];p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
plan={'question':'Do the washer and underside screw head have complete nominal bearing footprints, with no fastener overlap?', 'stop':'Eight joints, fixed planar 0.01 mm footprint prism; no mesh/load analysis.', 'method':'Intersect bearing annulus extruded 0.01 mm into the receiving solid; volume/depth gives section area for this planar region.', 'criteria':{'maximum_unintended_overlap_mm3':.01,'maximum_missing_nominal_bearing_area_mm2':.001}, 'criteria_origin':'Numerical full-seat geometry checks, not material strength acceptance.', 'limits':['Nominal geometry only','No pressure distribution, flatness, preload or creep','No real screw underhead fillet','No positive retention or stiffness proof from bearing area alone']};(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');rows=[];sources={}
for side,cy in [('left',26),('right',-26)]:
 parts={}
 for n in ['mount_plate','yaw_fixed_support']:
  path=ROOT/f'validation/yaw_metal_seat_v2/{side}_{n}.step';sources[str(path.relative_to(ROOT))]=hashlib.sha256(path.read_bytes()).hexdigest();parts[n]=cq.importers.importStep(str(path)).val()
 for x in [-31.5,6.5]:
  for y in [cy-13,cy+13]:
   def cyl(r,h,z):return cq.Solid.makeCylinder(r,h,cq.Vector(x,y,z))
   for name,r,z,target in [('washer',3,90.99,'yaw_fixed_support'),('head',1.9,88,'mount_plate')]:
    probe=cyl(r,.01,z).cut(cyl(1.15,.01,z));expected=math.pi*(r*r-1.15**2);actual=probe.intersect(parts[target]).Volume()/.01
    rows.append({'side':side,'x_mm':x,'y_mm':y,'check':name+'_bearing','expected_area_mm2':expected,'supported_area_mm2':actual,'missing_area_mm2':max(0,expected-actual),'pass':abs(expected-actual)<=.001})
   for name,s in [('head',cyl(1.9,1.3,86.7)),('shaft',cyl(1,10,88))]:
    for target,t in parts.items():
     v=float(s.intersect(t).Volume());rows.append({'side':side,'x_mm':x,'y_mm':y,'check':name+'_overlap_'+target,'overlap_mm3':v,'pass':v<=.01})
r={'rows':rows,'source_sha256':sources,'all_nominal_seat_checks_pass':all(r['pass'] for r in rows),'manufacturing_release':False,'strength_verified':False,'limits':plan['limits']};(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'failures':[r for r in rows if not r['pass']]},indent=2))
