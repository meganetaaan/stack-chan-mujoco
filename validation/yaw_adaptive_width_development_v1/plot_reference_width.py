"""Plot kinematic reference audit, not measured walking success."""
from pathlib import Path
import json,hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=Path(__file__).resolve().parent
z=np.load(p/'feet_audit/feet.npz');v=z['values'];width=(v[:,2]-v[:,5])*1000
fig,axes=plt.subplots(2,1,figsize=(11,5),layout='constrained')
for ax,(start,end) in zip(axes,[(0,32),(56,116)]):
 mask=(v[:,0]>=start)&(v[:,0]<=end);ax.plot(v[mask,0],width[mask],color='#147b85')
 ax.set_xlim(start,end);ax.set_ylim(61.8,64.2);ax.set_yticks([62,63,64]);ax.set_ylabel('Foot-center spacing (mm)');ax.grid(alpha=.2)
axes[-1].set_xlabel('Reference time (s)')
axes[0].set_title('Generated joint targets: swing-foot placement changes width continuously')
fig.savefig(p/'reference_width.png',dpi=160)
(p/'reference_width_metadata.json').write_text(json.dumps({'scope':__doc__,'source_sha256':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in [Path(__file__),p/'feet_audit/feet.npz']}},indent=2)+'\n')
