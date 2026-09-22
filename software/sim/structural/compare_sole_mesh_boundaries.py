"""Compare boundary triangle coordinates independently of node/element numbering."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np,meshio
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--baseline',type=Path,required=True);p.add_argument('--variant',type=Path,required=True);p.add_argument('--mesh-mm',default='0.5');p.add_argument('--out',type=Path,required=True);a=p.parse_args();rows=[]
def key(xyz):
 return sorted(tuple(sorted(tuple(q) for q in tri)) for tri in np.round(xyz,10))
for part in ['boss','spacer']:
 paths=[folder/part/f'{part}_{a.mesh_mm}.msh' for folder in [a.baseline,a.variant]];meshes=[meshio.read(f) for f in paths];patches={}
 for label,(_,dim) in meshes[0].field_data.items():
  if dim!=2:continue
  keys=[]
  for m in meshes:
   tri=m.cells_dict['triangle'][m.cell_data_dict['gmsh:physical']['triangle']==m.field_data[label][0]];keys.append(key(m.points[tri]))
  patches[label]={'matching':keys[0]==keys[1],'triangle_counts':[len(k) for k in keys]}
 exterior=[]
 for m in meshes:
  tet=m.cells_dict['tetra'];faces=np.concatenate([tet[:,idx] for idx in [[0,1,2],[0,1,3],[0,2,3],[1,2,3]]]);unique,count=np.unique(np.sort(faces,axis=1),axis=0,return_counts=True);assert np.all(count<=2),'Non-manifold tetrahedral faces';exterior.append(key(m.points[unique[count==1]]))
 rows.append({'exterior_triangles_match':exterior[0]==exterior[1],'exterior_triangle_counts':[len(x) for x in exterior],'part':part,'patches':patches,'nodes':[len(m.points) for m in meshes],'tetrahedra':[len(m.cells_dict['tetra']) for m in meshes],'source_sha256':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in paths}})
result={'coordinate_rounding_decimal_places_mm':10,'rows':rows,'all_exported_physical_patches_match':all(v['matching'] for r in rows for v in r['patches'].values()),'all_exterior_triangles_match':all(r['exterior_triangles_match'] for r in rows),'scope':'Physical patches and complete tetrahedral boundary, including untagged facets'};a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
