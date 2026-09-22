"""Single-mesh nominal preload probe on imprinted nut/spacer patches."""
import argparse,json,meshio,numpy as np
from skfem.io import from_meshio
from elasticity import analyze
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);a=p.parse_args();mesh=from_meshio(meshio.read(a.source/'boss_1.msh'))
r,arr=analyze(mesh,'spacer_bearing','nut_bearing',[35,6,-14.2],[0,0,-20,0,0,0],young=1120,poisson=.35,support_mode='normal_z');r['joint_verified']=False;r['scope']='Single mesh bilateral normal support, 20 N; no opening or spacer compliance';(a.source/'probe_1mm.json').write_text(json.dumps(r,indent=2)+'\n');np.savez_compressed(a.source/'probe_1mm.npz',**arr)
