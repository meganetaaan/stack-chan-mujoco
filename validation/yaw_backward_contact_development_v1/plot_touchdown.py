"""Recorded one-millisecond touchdown trace; no change to qualification rules."""
from pathlib import Path
import json,hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=Path(__file__).resolve().parent;trial=p/'yaw_backward_contact_trace_v1';r=json.loads((trial/'report.json').read_text());f=trial/'contact_trace.npz'
assert hashlib.sha256(f.read_bytes()).hexdigest()==r['contact_trace_sha256']
z=np.load(f);v=z['values'];v=v[(v[:,0]>=21.59)&(v[:,0]<=21.68)]
fig,axes=plt.subplots(2,1,figsize=(9,4.6),sharex=True,layout='constrained')
axes[0].plot(v[:,0],v[:,2],'.-',markersize=3);axes[0].axhline(.35,color='red',ls='--',label='Contact threshold 0.35 N');axes[0].set_ylabel('Right-foot load (N)');axes[0].legend()
axes[1].plot(v[:,0],1000*v[:,4],'.-',markersize=3);axes[1].axhline(0,color='black',lw=.7);axes[1].set_ylabel('Lowest sole point (mm)');axes[1].set_xlabel('Recorded simulation time (s)')
axes[0].set_title('A brief unload cancels landing confirmation despite later sustained support')
for ax in axes:ax.grid(alpha=.2)
fig.savefig(p/'touchdown.png',dpi=160);fig.savefig(p/'touchdown.pdf')
(p/'touchdown_metadata.json').write_text(json.dumps({'scope':__doc__,'source_sha256':{str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in [Path(__file__),f,trial/'report.json']}},indent=2)+'\n')
