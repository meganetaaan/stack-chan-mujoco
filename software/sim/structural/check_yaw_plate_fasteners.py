"""Known candidate fastener envelopes at widened metal plate attachment axes."""
import argparse,json
from pathlib import Path
import cadquery as cq
ROOT=Path(__file__).resolve().parents[3];p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
plan={'scope':__doc__,'parts':['NBK SLH-M2-10','PTS A56202','SCW-SOLE-SPACER-01 reused as custom rigid washer candidate'], 'stop':'One nominal arrangement, 8 joints; no dimension sweep', 'criteria':{'intersection_mm3':.01,'nonmating_gap_mm':.9},'limitations':['No tool access or preload proof','Nominal fastener envelopes','Square nut replaced by circumcircle','Spacers remain custom parts, not qualified washers']};(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');rows=[]
raw=cq.importers.importStep(str(ROOT/'validation/x330_manufacturer_cad_v1/XL_XC_330.stp')).val().Solids()
for side,cy in [('left',26),('right',-26)]:
 case=cq.Compound.makeCompound([s.rotate((0,0,0),(1,1,0),180).translate((-5,cy,68.5)) for i,s in enumerate(raw) if i not in [10,11,12]])
 for x in [-31.5,6.5]:
  for y in [cy-13,cy+13]:
   def cyl(r,h,z):return cq.Solid.makeCylinder(r,h,cq.Vector(x,y,z))
   shapes={'head':cyl(1.9,1.3,86.7),'shaft':cyl(1,10,88),'washer':cyl(3,.9,91).cut(cyl(1.15,.9,91)),'nut':cyl(2.829,1.2,91.9).cut(cyl(1,1.2,91.9))}
   for n,s in shapes.items():
    d=float(s.distance(case));v=float(s.intersect(case).Volume()) if d<1e-6 else 0;rows.append({'side':side,'x_mm':x,'y_mm':y,'part':n,'case_gap_mm':d,'case_overlap_mm3':v,'pass':d>=.9 and v<=.01})
r={'rows':rows,'nominal_nut_top_z_mm':93.1,'screw_tip_z_mm':98,'nominal_projection_mm':4.9,'plate_edge_distance_mm':3.5,'washer_radius_mm':3,'edge_margin_mm':.5,'manufacturing_release':False};(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'failures':[r for r in rows if not r['pass']]}))
