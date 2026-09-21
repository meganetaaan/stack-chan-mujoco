"""Test a provisional board/component reservation against current static packaging."""
import argparse,hashlib,json
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--layout',choices=['horizontal','vertical','vertical_raised'],default='horizontal');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
ref=Path('board/mechanical/prototype/power_packaging_revA/report.json');paths=json.loads(ref.read_text())['sources_sha256']
# Reservation dimensions are design proposals, not dimensions of a routed PCB.
plan={'board_box_mm':{'min':[-50,-35,77],'size':[60,70,1.6]},'component_box_mm':{'min':[-50,-35,78.6],'size':[60,70,16]},'fixed_clearance_screen_mm':.5,'criteria':['No nominal overlap with any existing solid','Minimum nominal distance >=0.5mm to existing geometry'],'limits':['Provisional 60x70 board area does not prove routing 98 components','Support and fastener envelope not included','Wires, connectors, thermal spacing, full motion and service paths not included','0.5mm is a retained screening allowance, not printer tolerance proof']}
if a.layout in ('vertical','vertical_raised'):
 plan['board_box_mm']={'min':[0,-40,97],'size':[1.6,80,25]}
 plan['component_box_mm']={'min':[1.6,-40,97],'size':[16,80,25]}
 plan['limits'][0]='Provisional 80x25 board area does not prove routing 98 components'
if a.layout=='vertical_raised':
 plan['board_box_mm']['min'][2]=99
 plan['component_box_mm']['min'][2]=99
plan['layout']=a.layout
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
shapes={}
for name,key in [('board','board_box_mm'),('components','component_box_mm')]:
 b=plan[key];shapes[name]=cq.Solid.makeBox(*b['size'],cq.Vector(*b['min']));cq.exporters.export(shapes[name],str(a.out/(name+'.step')))
rows=[]
for path,expected in paths.items():
 assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==expected
 obstacle=cq.importers.importStep(path).val()
 for name,shape in shapes.items():
  solids=obstacle.Solids();vol=sum(shape.intersect(s).Volume() for s in solids);distance=min(shape.distance(s) for s in solids)
  rows.append({'reservation':name,'obstacle':path,'overlap_mm3':vol,'distance_mm':distance,'pass':vol<1e-6 and distance>=.5-1e-7})
report={'checks':rows,'static_reservation_pass':all(x['pass'] for x in rows),'routed_PCB_fit_proven':False,'manufacturing_release':False}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
