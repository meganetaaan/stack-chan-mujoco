#!/usr/bin/env python3
"""Plot a controlled comparison of two recorded right-foot landing traces."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--original',type=Path,required=True);p.add_argument('--candidate',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if a.out.exists():p.error('new output required')
    paths=[a.original,a.candidate];reports=[json.loads((path/'report.json').read_text()) for path in paths]
    for key in ('parameters','motor_parameters','seed'):
        if reports[0][key]!=reports[1][key]:raise ValueError('comparison changed '+key)
    data=[]
    for path,report in zip(paths,reports):
        if sha(path/'contact_trace.npz')!=report['contact_trace_sha256']:raise ValueError('contact trace hash mismatch')
        with np.load(path/'contact_trace.npz') as z:
            columns=z['columns'].tolist();values=z['values']
        if len(columns)!=13 or values.shape[1]!=13 or not np.isfinite(values).all():raise ValueError('invalid contact trace')
        data.append(values)
    fig,axes=plt.subplots(2,2,figsize=(10,5.5),sharex=True,sharey='row')
    first_landings=[]
    for col,(title,values) in enumerate(zip(['Original reference','Changed phase timing'],data)):
        v=values[(values[:,0]>=4.1)&(values[:,0]<=5.25)]
        axes[0,col].plot(v[:,0],v[:,2],lw=1)
        axes[0,col].axhline(.35,color='r',ls='--',lw=.8,label='contact threshold 0.35 N')
        axes[1,col].plot(v[:,0],1000*v[:,4],lw=1)
        land=np.flatnonzero(np.diff(values[:,12])>0)+1
        first=float(values[land[0],0]) if len(land) else None;first_landings.append(first)
        if first is not None:
            for ax in axes[:,col]:ax.axvline(first,color='g',ls=':',label=f'qualified landing {first:.3f} s')
        if reports[col]['failure']:
            for ax in axes[:,col]:ax.axvline(reports[col]['time_s'],color='k',ls='--',label='trial stopped')
        axes[0,col].set_title(title);axes[0,col].legend(fontsize=7)
        axes[1,col].set_xlabel('Simulation time (s)')
        for ax in axes[:,col]:ax.grid(alpha=.2);ax.set_xlim(4.1,5.25)
    axes[0,0].set_ylabel('Right sole load (N)');axes[1,0].set_ylabel('Right sole bottom height (mm)')
    fig.suptitle(f"Same randomized plant, seed {reports[0]['seed']}; unchanged landing criterion")
    fig.tight_layout();a.out.mkdir(parents=True)
    fig.savefig(a.out/'landing_comparison.png',dpi=180);fig.savefig(a.out/'landing_comparison.pdf');plt.close(fig)
    metadata={'first_qualified_right_landing_s':first_landings,'plotted_interval_s':[4.1,5.25],
              'source_sha256':{str(path):sha(path) for path in [Path(__file__),*[d/'report.json' for d in paths],*[d/'contact_trace.npz' for d in paths]]}}
    (a.out/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n');print(json.dumps(metadata))


if __name__=='__main__':main()
