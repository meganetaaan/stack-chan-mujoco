"""Screen nominal mated EH envelope against current structural supports."""
import argparse,hashlib,json
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
source=Path('validation/yaw_connector_obstacles_v3/report.json');r=json.loads(source.read_text())
ptr=Path('board/mechanical/prototype/yaw_support_candidate/current.json');current=json.loads(ptr.read_text());invpath=Path(current['inventory']);inv=json.loads(invpath.read_text());parts={x['name']:x for x in inv['parts']}
a.out.mkdir(parents=True,exist_ok=False)
plan={'source':'https://www.jst-mfg.com/product/pdf/eng/eEH.pdf','pages':[2,3],
 'dimensions_mm':{'header_height_above_PCB':6,'mated_height_above_PCB':8.1,'housing_width':9.5,'thickness':3.8},
 'placement_assumption':'PCB plane inferred as header mating-side bbox Z maximum minus 6 mm; mating +Z. Envelope centred on nominal header.',
 'criteria':{'nominal_overlap_limit_mm3':.01,'residual_clearance_min_mm':.5,'tolerance_per_part_mm':.2,'deflection_per_part_mm':.2},
 'scope':'Reference-dimension envelope; no wires, housing tolerance, assembly stroke or all fasteners.'}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
rows=[];hashes={str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in [source,ptr,invpath]}
for port in r['rows']:
 side=port['side'];lo=port['bounds_min_mm'];hi=port['bounds_max_mm'];pcb=hi[2]-6
 centre=[(lo[i]+hi[i])/2 for i in range(2)]
 envelope=cq.Solid.makeBox(9.5,3.8,8.1,cq.Vector(centre[0]-4.75,centre[1]-1.9,pcb))
 for name in [side+'_yaw_fixed_support',side+'_mount_plate']:
  path=Path(parts[name]['source']);digest=hashlib.sha256(path.read_bytes()).hexdigest();assert digest==parts[name]['source_sha256'];hashes[str(path)]=digest
  shape=cq.importers.importStep(str(path)).val();distance=envelope.distance(shape);v=envelope.intersect(shape).Volume();residual=distance-.8
  rows.append({'side':side,'port':port['manufacturer_solid_index'],'neighbour':name,'PCB_plane_z_mm':pcb,'mated_top_z_mm':pcb+8.1,'overlap_mm3':v,'distance_mm':distance,'allocated_residual_mm':residual,'passes_allocated_screen':v<=.01 and residual>=.5})
report={'source_sha256':hashes,'rows':rows,'decision':'Nominal housing fits but allocated clearance screen fails. Resolve cable exit and local relief before adopting this routing.', 'full_fit_qualified':False,'manufacturing_release':False}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(rows))
