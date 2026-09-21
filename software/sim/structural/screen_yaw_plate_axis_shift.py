"""One relocated attachment pattern, before editing ribs or extending the shelf."""
import argparse,json,hashlib
from pathlib import Path
import cadquery as cq
ROOT=Path(__file__).resolve().parents[3];p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
plan={'question':'Does moving plate attachment axes inside the rib corridor clear heads without rib removal?', 'pattern':{'x_mm':[-34,7.5],'relative_y_mm':[-10,10]},'reason':'5 mm ribs occupy lateral edges; move heads inward, then move X beyond case end faces for 0.9 mm clearance.', 'stop':'One new pattern, 8 heads; identify required plate/shelf extension without modifying ribs.', 'criteria':{'nonmating_clearance_mm':.9,'overlap_mm3':.01},'limits':['No shaft holes at new axes yet','No tools or complete assembly','Only nominal head clearance','Washer support checked separately by footprint deficit']};(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');rows=[];sources={}
sp=ROOT/'validation/x330_manufacturer_cad_v1/XL_XC_330.stp';raw=cq.importers.importStep(str(sp)).val().Solids();sources[str(sp.relative_to(ROOT))]=hashlib.sha256(sp.read_bytes()).hexdigest()
for side,cy in [('left',26),('right',-26)]:
 path=ROOT/f'validation/yaw_metal_seat_v2/{side}_yaw_fixed_support.step';support=cq.importers.importStep(str(path)).val();sources[str(path.relative_to(ROOT))]=hashlib.sha256(path.read_bytes()).hexdigest()
 case=cq.Compound.makeCompound([s.rotate((0,0,0),(1,1,0),180).translate((-5,cy,68.5)) for i,s in enumerate(raw) if i not in [10,11,12]])
 for x in [-34,7.5]:
  for y in [cy-10,cy+10]:
   head=cq.Solid.makeCylinder(1.9,1.3,cq.Vector(x,y,86.7))
   for n,t in [('support',support),('case',case)]:
    d=float(head.distance(t));v=float(head.intersect(t).Volume()) if d<1e-6 else 0;rows.append({'side':side,'x_mm':x,'y_mm':y,'target':n,'distance_mm':d,'overlap_mm3':v,'pass':d>=.9 and v<=.01})
r={'rows':rows,'source_sha256':sources,'plate_required_x_for_3_5_mm_edge_distance':[-37.5,11],'shelf_current_xmax_mm':10,'front_washer_xmax_mm':10.5,'manufacturing_release':False,'limits':plan['limits']};(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'failures':[r for r in rows if not r['pass']],'minimum_case_gap':min(r['distance_mm'] for r in rows if r['target']=='case')},indent=2))
