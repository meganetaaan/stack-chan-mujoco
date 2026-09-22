"""Preserve simultaneous force vectors when screening tray load directions."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,default=Path('validation/battery_translation_load_v1'));p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
rows=[]
for path in sorted(a.source.glob('*.npz')):
 with np.load(path) as d:f=d['force_on_mount_base_N'];t=d['time'];ix=d['interior_indices']
 moment=np.cross(np.array([0,0,.015]),f)
 selected=[]
 for j,axis in enumerate('XYZ'):
  for name,op in [('min',np.argmin),('max',np.argmax)]:
   i=int(ix[op(f[ix,j])]);selected.append({'criterion':axis+'_'+name,'index':i,'time_s':float(t[i]),'force_base_N':f[i].tolist(),'force_transfer_moment_about_floor_center_Nm':moment[i].tolist()})
 i=int(ix[np.argmax(np.linalg.norm(moment[ix],axis=1))])
 rows.append({'source':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'selected':selected,'peak_force_transfer_moment_Nm':float(np.linalg.norm(moment[i])),'peak_moment_time_s':float(t[i]),'peak_moment_vector_Nm':moment[i].tolist(),'simultaneous_force_N':f[i].tolist()})
(a.out/'report.json').write_text(json.dumps({'scope':'Force transfer to floor center only; excludes rotational inertial couple and preload','reference_base_m':[.029,0,.065],'center_offset_m':[0,0,.015],'acceptance':False,'cases':rows},indent=2)+'\n');print([(r['source'],r['peak_force_transfer_moment_Nm']) for r in rows])
