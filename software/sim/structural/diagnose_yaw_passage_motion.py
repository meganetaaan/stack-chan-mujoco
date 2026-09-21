"""Relative opening motion under two rigid-seat fits; diagnostic, not a joint/contact solution."""
import argparse, hashlib, json
from pathlib import Path
import numpy as np
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--envelope',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
seatpath=Path('validation/yaw_metal_seat_v4/report.json');openingpath=Path('validation/yaw_connector_shelf_relief_v2/plan.json')
axes=np.array(json.loads(seatpath.read_text())['rows'][0]['plate_support_axes'])
opening=json.loads(openingpath.read_text());cx,cy=opening['centres_xy_mm']['left'][0]
plan={'question':'How different is support opening motion from a rigid seat-following diagnostic, and how sensitive is that result to the fit region?',
 'source_sha256':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in [a.envelope/'plan.json',a.envelope/'report.json',seatpath,openingpath]},
 'fits':['all nodes on the loaded Z89 plane','Z89 nodes within 3.2 mm of the four support screw axes'],
 'opening_neighbourhood':'Opening bounding rectangle expanded by 1 mm in X/Y, support nodes Z86..91. Nodal samples only.',
 'stop':'Postprocess six existing response fields at 38 archived selected loads. No new FE solve, mesh refinement or threshold modification.',
 'limits':['Equal-node-weight rigid fits are kinematic diagnostics, not solved plate/servo motion.',
 'Two fits do not bracket the physical solution and their spread is not an error bound.',
 'No bolt/contact/plate flexibility or connector compliance; no finite-deformed CAD gap.',
 'Selected times are not the complete load envelope; nominal reserved corridor is not the real cable.'],
 'manufacturing_release':False}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
fields=[];nodes=None
for i in range(6):
 path=a.envelope/f'unit_{i}.npz'
 with np.load(path) as f:
  if nodes is None:nodes=f['nodes_mm'].copy()
  else:assert np.array_equal(nodes,f['nodes_mm'])
  fields.append(f['displacement_mm'].copy())
u=np.array(fields)
seat=(abs(nodes[:,2]-89)<1e-6)&(nodes[:,0]>=-37.5)&(nodes[:,0]<=11.6)&(nodes[:,1]>=9.5)&(nodes[:,1]<=42.5)
patches=np.linalg.norm(nodes[:,None,:2]-axes[None,:,:],axis=2)<=3.2
patch=seat&patches.any(axis=1)
assert all((seat&patches[:,i]).sum()>=3 for i in range(4))
width=opening['opening_mm']['width'];depth=opening['opening_mm']['depth']
local=(abs(nodes[:,0]-cx)<=width/2+1)&(abs(nodes[:,1]-cy)<=depth/2+1)&(nodes[:,2]>=86)&(nodes[:,2]<=91)
assert local.sum()>0
origin=np.array([cx,cy,89.]);r=nodes-origin
A=np.zeros((len(nodes),3,6));A[:,:,:3]=np.eye(3)
A[:,0,4]=r[:,2];A[:,0,5]=-r[:,1];A[:,1,3]=-r[:,2];A[:,1,5]=r[:,0];A[:,2,3]=r[:,1];A[:,2,4]=-r[:,0]
fits={}
for name,mask in [('whole_seat',seat),('screw_patches',patch)]:
 matrix=A[mask].reshape(-1,6);assert np.linalg.matrix_rank(matrix)==6
 fits[name]=np.linalg.lstsq(matrix,u[:,mask,:].reshape(6,-1).T,rcond=None)[0]
rows=[]
for case in json.loads((a.envelope/'report.json').read_text())['rows']:
 wrench=np.array(case['selected_wrench_N_Nmm']);disp=np.tensordot(wrench,u,axes=(0,0));predictions={};metrics={}
 assert np.isclose(np.linalg.norm(disp,axis=1).max(),case['selected_actual_displacement_mm'],rtol=1e-10,atol=1e-12)
 for name,fit in fits.items():
  rigid=fit@wrench;pred=np.einsum('ijk,k->ij',A[local],rigid);predictions[name]=pred
  residual=disp[local]-pred
  metrics[name]={'translation_at_opening_mm':rigid[:3].tolist(),'rotation_rad':rigid[3:].tolist(),
   'opening_max_relative_vector_mm':float(np.linalg.norm(residual,axis=1).max()),
   'opening_max_abs_relative_components_mm':np.max(abs(residual),axis=0).tolist()}
 rows.append({'source':case['source'],'side':case['side'],'time_s':case['selected_time_s'],
  'support_max_absolute_displacement_mm':float(np.linalg.norm(disp,axis=1).max()),'fits':metrics,
  'max_fit_prediction_difference_at_opening_mm':float(np.linalg.norm(predictions['whole_seat']-predictions['screw_patches'],axis=1).max())})
report={'seat_nodes':int(seat.sum()),'screw_patch_nodes':int(patch.sum()),'nodes_per_screw_patch':[int((seat&patches[:,i]).sum()) for i in range(4)],
 'opening_neighbourhood_nodes':int(local.sum()),'rows':rows,
 'max_relative_by_fit_mm':{name:max(row['fits'][name]['opening_max_relative_vector_mm'] for row in rows) for name in fits},
 'max_fit_prediction_difference_mm':max(row['max_fit_prediction_difference_at_opening_mm'] for row in rows),
 'actual_relative_gap_verified':False,'manufacturing_release':False}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='rows'},indent=2))
