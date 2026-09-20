"""Plot recorded integration motion and reported per-segment lateral metrics."""
from pathlib import Path
import hashlib
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT=Path(__file__).resolve().parent
fig,axes=plt.subplots(1,2,figsize=(12,5),layout='constrained')
sources={}
for name,label in [('yaw_backshift0.22_fixed205_v1','Fixed 310501'),
                   ('yaw_backshift0.22_random205_v1','Randomized 310613')]:
    folder=ROOT/name
    report=json.loads((folder/'report.json').read_text())
    state=folder/'states.npz'
    digest=hashlib.sha256(state.read_bytes()).hexdigest()
    assert digest==report['trajectory_sha256']
    sources[name]={'state_sha256':digest,'report_sha256':hashlib.sha256((folder/'report.json').read_bytes()).hexdigest()}
    with np.load(state,allow_pickle=False) as z:
        motion=z['motion_xy_heading']
    axes[0].plot(motion[:,1],motion[:,2],label=label,lw=1)
    axes[0].scatter(*motion[0,1:3],marker='o',s=35)
    axes[0].scatter(*motion[-1,1:3],marker='x',s=50)
    segments=report['motion_scoring']['segments']
    axes[1].plot(range(len(segments)),[s['metrics']['smoothed_lateral_velocity_rmse_m_s'] for s in segments],'.-',label=label)
axes[0].set(xlabel='World X [m]',ylabel='World Y [m]',title='Actual base trajectory (circle: start, cross: end)')
axes[0].axis('equal')
axes[1].axhline(.03,color='red',ls='--',label='Frozen threshold: 0.030 m/s')
axes[1].set(xlabel='Protocol segment index',ylabel='Smoothed lateral velocity RMSE [m/s]',title='205 s / all 24 segments',xticks=range(0,24,2),ylim=(0,.033))
for ax in axes:
    ax.grid(alpha=.25);ax.legend(fontsize=8)
fig.suptitle('Backward transfer 22% — development trials, not formal acceptance')
for suffix in ['png','pdf']:fig.savefig(ROOT/('actual_motion.'+suffix),dpi=180)
(ROOT/'actual_motion_sources.json').write_text(json.dumps(sources,indent=2)+'\n')
