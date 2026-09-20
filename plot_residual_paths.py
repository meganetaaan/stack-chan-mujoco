#!/usr/bin/env python3
"""Plot actual recorded free-base paths, not the kinematic reference."""
import argparse
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import hashlib

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--batch',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--title',default='Residual PPO: recorded MuJoCo paths')
    a=p.parse_args()
    if a.out.exists():p.error('use a new image path')
    m=json.loads((a.batch/'manifest.json').read_text())
    if not m['complete']:raise ValueError('complete batch required')
    fig,ax=plt.subplots(figsize=(10,4),layout='constrained');seen=set()
    source=[];annotation_index=0
    for trial in m['results']:
        folder=a.batch/trial['trial'];r=json.loads((folder/'report.json').read_text())
        file=folder/'states.npz'
        if sha(file)!=r['trajectory_sha256']:raise ValueError('state hash mismatch')
        s=np.load(file)['state'];xy=s[:,1:3]-s[0,1:3]
        kind=f"Pass ({m['successes']})" if trial['simulation_trial_pass'] else f"Fail ({len(m['results'])-m['successes']})"
        color='#257653' if trial['simulation_trial_pass'] else '#c44136'
        ax.plot(xy[:,0],xy[:,1],color=color,lw=1.4,alpha=.8,label=kind if kind not in seen else None)
        seen.add(kind);ax.scatter(*xy[-1],s=18,color=color)
        if not trial['simulation_trial_pass'] and trial['failure'] is None:
            ax.annotate(trial['trial'].replace('trial_',''),xy[-1],xytext=(7,9 if annotation_index%2==0 else -10),textcoords='offset points',fontsize=9,color=color)
            annotation_index+=1
        source.append({'trial':trial['trial'],'sha256':sha(file)})
    ax.axvline(10,color='#555',ls='--',lw=1,label='10 m forward plane')
    ax.scatter(0,0,s=35,c='black',zorder=4)
    ax.set(xlabel='Forward displacement x (m)',ylabel='Lateral displacement y (m)',
           title=f"{a.title}\n{len(m['results'])} {m['domain']} trials, 0.10 m/s command\nPass requires 10 m within 100 s and a clean stop")
    ymin,ymax=ax.get_ylim()
    if ymax-ymin<2.4:
        center=(ymin+ymax)/2;ax.set_ylim(center-1.2,center+1.2)
    ax.set_aspect('equal',adjustable='box');ax.grid(alpha=.18);ax.legend(loc='upper left',frameon=False)
    fig.savefig(a.out,dpi=160);plt.close(fig)
    a.out.with_suffix('.json').write_text(json.dumps({'source':'recorded free-base state only',
        'batch_manifest_sha256':sha(a.batch/'manifest.json'),'title':a.title,
        'trajectories':source,'plot_sha256':sha(a.out),'script_sha256':sha(__file__)},indent=2)+'\n')

if __name__=='__main__':main()
