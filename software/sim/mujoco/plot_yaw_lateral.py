#!/usr/bin/env python3
"""Plot measured lateral RMSE and mean drift from saved diagnostic reports."""
import argparse
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--baseline',type=Path,required=True)
parser.add_argument('--candidate',type=Path,required=True)
parser.add_argument('--out',type=Path,required=True)
args=parser.parse_args()
if args.out.exists():parser.error('new output directory required')
reports=[json.loads(p.read_text()) for p in [args.baseline,args.candidate]]
names=[r['name'] for r in reports[0]['segments'] if 'stop' not in r['name']]
fig,ax=plt.subplots(figsize=(12,4.5),layout='constrained')
x=np.arange(len(names));width=.35
for j,(report,label) in enumerate(zip(reports,['64 mm stance','62 mm stance'])):
    values={row['name']:row for row in report['segments']}
    y=[values[name]['rmse_m_s'] if name in values else np.nan for name in names]
    ax.bar(x+(j-.5)*width,y,width,label=label)
    ax.scatter(x+(j-.5)*width,[abs(values[name]['mean_lateral_m_s']) if name in values else np.nan for name in names],marker='_',color='black',s=35)
ax.axhline(.03,color='red',linestyle='--',label='Frozen RMSE limit: 0.030 m/s')
ax.set_xticks(x,names,rotation=60,ha='right')
ax.set_ylabel('Body lateral velocity (m/s)')
ax.set_title('Recorded 205 s development motion; black marks show absolute mean drift')
ax.legend(loc='upper left',ncols=3,fontsize=8)
args.out.mkdir(parents=True)
for suffix in ['png','pdf']:fig.savefig(args.out/('lateral_comparison.'+suffix),dpi=160)
(args.out/'metadata.json').write_text(json.dumps({'scope':__doc__,'missing_segments_shown_as_gaps':True,
    'inputs_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),args.baseline,args.candidate]}},indent=2)+'\n')
