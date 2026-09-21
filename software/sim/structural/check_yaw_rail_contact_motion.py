"""Check signed free motion at actual rail footprint; do not bond a unilateral seat."""
import argparse,hashlib,json
from pathlib import Path
import cadquery as cq
import numpy as np
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
field=Path('validation/yaw_rail_seat_deformation_location_v1/field.npz');bodypath=Path('validation/yaw_tool_access_v1/body_shroud.step');d=np.load(field);body=cq.importers.importStep(str(bodypath)).val()
plan={'question':'Does the unbonded support move into or away from the retained body rail in the archived case?', 'source_field':str(field),'body':str(bodypath),'contact_plane_z_mm':52.2,'body_probe_below_plane_mm':.005,'signed_normal':'Positive Z opens the gap; negative Z penetrates a stationary rail','diagnostic_zero_mm':1e-6,'stop':'Postprocess existing displacement field only; no mesh refinement, contact reaction or capacity claim','limits':['Body treated as stationary only for free-motion diagnostic','Nodes are point samples, not area-integrated contact','One archived load; no full load envelope','Zero initial gap assumed from nominal CAD; print tolerance unknown']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');nodes=d['nodes_mm'];u=d['displacement_mm'];indices=np.flatnonzero(np.abs(nodes[:,2]-52.2)<1e-6)
selected=[int(i) for i in indices if body.isInside(cq.Vector(float(nodes[i,0]),float(nodes[i,1]),52.195),1e-7)]
assert selected,'No sampled nodes in actual rail footprint'
z=u[selected,2];tol=plan['diagnostic_zero_mm'];rows=[{'node_index':i,'position_mm':nodes[i].tolist(),'displacement_mm':u[i].tolist()} for i in selected]
report={'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [field,bodypath]},'plane_nodes':len(indices),'footprint_nodes':len(selected),'opening_nodes':int((z>tol).sum()),'penetrating_nodes':int((z< -tol).sum()),'near_zero_nodes':int((np.abs(z)<=tol).sum()),'normal_displacement_range_mm':[float(z.min()),float(z.max())],'samples':rows,'contact_solution':False,'manufacturing_release':False}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='samples'},indent=2))
