"""Build the minimum-thickness spacer tolerance case, including edge chamfers."""
import argparse, json, hashlib
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--out',type=Path,required=True)
a=p.parse_args(); a.out.mkdir(parents=True,exist_ok=False)
src=Path('docs/prototype/mechanical/sole_spacer/specification.json')
s=json.loads(src.read_text()); ro=s['outer_diameter']['min']/2; ri=s['inner_diameter']['max']/2; t=s['thickness']['min']; c=s['edge_break_radial_max']
plan={'scope':__doc__,'spec_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'outer_radius_mm':ro,'inner_radius_mm':ri,'thickness_mm':t,'chamfer_mm':c,'top_z_mm':-19,'assumption':'45-degree chamfer at all four circular edges; flatness and parallelism errors omitted','criteria':{'valid_single_solid':True}}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
w=cq.Workplane('XY').workplane(offset=-19-t).center(35,6).circle(ro).circle(ri).extrude(t).edges('%Circle').chamfer(c)
shape=w.val(); assert shape.isValid() and len(shape.Solids())==1
cq.exporters.export(shape,str(a.out/'spacer.step'))
(a.out/'report.json').write_text(json.dumps({'valid_single_solid':True,'volume_mm3':shape.Volume(),'joint_verified':False},indent=2)+'\n')
