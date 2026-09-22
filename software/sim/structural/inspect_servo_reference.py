"""Inspect an explicitly supplied manufacturer STEP without redistributing it."""
import argparse,hashlib,json
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--step',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
s=cq.importers.importStep(str(a.step)).val();assert s.isValid()
rows=[]
for i,solid in enumerate(s.Solids()):
 b=solid.BoundingBox();rows.append({'index':i,'volume_mm3':solid.Volume(),'min_mm':[b.xmin,b.ymin,b.zmin],'max_mm':[b.xmax,b.ymax,b.zmax]})
r={'source_url':'https://www.robotis.com/service/download.php?no=1987','download_url':'https://www.dropbox.com/s/qlzmp8mlvzrxmzu/XL,XC-330.stp?dl=1',
 'source_sha256':hashlib.sha256(a.step.read_bytes()).hexdigest(),'valid':True,'solids':rows,
 'interpretation':'Manufacturer native coordinates in mm. Drawing visual inspection suggests solids 13 and 14 are the two connector housings; bounding-box centres are not verified mating datums.',
 'robot_transform_verified':False,'connector_mating_datum_verified':False,'manufacturing_release':False}
a.out.mkdir(parents=True,exist_ok=True);(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n')
