"""Locate peak absolute principal stress without excluding support regions."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--analyses',type=Path,nargs='+',required=True)
p.add_argument('--out',type=Path,required=True)
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
rows=[]
for folder in a.analyses:
    plan=json.loads((folder/'plan.json').read_text())
    path=folder/'simultaneous.npz'
    with np.load(path) as d:
        principal=np.linalg.eigvalsh(np.moveaxis(d['stress_MPa'],(0,1),(-2,-1)))
        e,q,k=np.unravel_index(np.argmax(abs(principal)),principal.shape)
        rows.append({'analysis':str(folder),'mesh_mm':plan['mesh_mm'],
                     'field_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                     'principal_MPa':float(principal[e,q,k]),
                     'position_mm':d['quadrature_coordinates_mm'][:,e,q].tolist()})
(a.out/'report.json').write_text(json.dumps({'scope':__doc__,'rows':rows},indent=2)+'\n')
print(json.dumps(rows))
