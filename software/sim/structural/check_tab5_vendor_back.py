"""Sample vendor STL rear surfaces at cover contact sites; not an area/strength proof."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
import trimesh
ROOT=Path(__file__).resolve().parents[3];p=argparse.ArgumentParser();p.add_argument('stl',type=Path);args=p.parse_args();out=ROOT/'validation/tab5_vendor_back_v1';out.mkdir(exist_ok=True)
expected='5e8e6398d85e4183af9040e9b12b1462fe74629b0ee6065581c7c897a8ba1a74';sha=hashlib.sha256(args.stl.read_bytes()).hexdigest();assert sha==expected
mesh=trimesh.load(args.stl,force='mesh');cs=mesh.split(only_watertight=False);selected=[i for i,c in enumerate(cs) if c.bounds[0,1]>0];assert selected==[0,3,4,7,8]
m=trimesh.util.concatenate([cs[i] for i in selected]);v=m.vertices.copy();m.vertices=np.column_stack((64+v[:,2],v[:,0]-64,v[:,1]+48-.8901450634002686))
# Exact ray/triangle barycentric intersection in YZ; parallel faces excluded.
a,b,c=np.moveaxis(m.triangles,1,0);den=(b[:,1]-a[:,1])*(c[:,2]-a[:,2])-(b[:,2]-a[:,2])*(c[:,1]-a[:,1]);valid=np.abs(den)>1e-12;den=np.where(valid,den,1.0)
rows=[]
for y in [-54.5,54.5]:
 for z in [88,112]:
  for dy in [-.4,0,.4]:
   for dz in [-3,0,3]:
    with np.errstate(divide='ignore',invalid='ignore'):
     u=((y+dy-a[:,1])*(c[:,2]-a[:,2])-(z+dz-a[:,2])*(c[:,1]-a[:,1]))/den
     w=((b[:,1]-a[:,1])*(z+dz-a[:,2])-(b[:,2]-a[:,2])*(y+dy-a[:,1]))/den
    x=a[:,0]+u*(b[:,0]-a[:,0])+w*(c[:,0]-a[:,0]);hit=valid&(u>=-1e-8)&(w>=-1e-8)&(u+w<=1+1e-8)&(x>=51.8)
    first=float(x[hit].min()) if hit.any() else None
    rows.append({'cover_center_yz_mm':[y,z],'probe_yz_mm':[y+dy,z+dz],'first_surface_x_mm':first,'forward_gap_mm':None if first is None else first-51.8})
result={'source_url':'https://raw.githubusercontent.com/m5stack/M5_Hardware/master/Products/C145_Tab5/Structures/Tab5.stl','sha256':sha,'all_component_bounds':[c.bounds.tolist() for c in cs],'selected_component_indices':selected,'selection_reason':'Positive-Y assembled group; negative-Y copies are exploded/displaced parts','transform_robot_xyz':'(64+vendorZ, vendorX-64, vendorY+48-0.8901450634002686)','aligned_bounds_mm':m.bounds.tolist(),'samples':rows,'all_samples_have_surface':all(x['first_surface_x_mm'] is not None for x in rows),'manufacturing_release':False,'scope':'36 point samples; not full contact area, exact assembly pose certification or tolerance proof'}
(out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print([(r['cover_center_yz_mm'],r['forward_gap_mm']) for r in rows])
