"""Test a candidate persistent unexpected-current detector on existing display traces."""
import gzip,hashlib,json
from pathlib import Path
import numpy as np
root=Path('validation/brake_fault_detection_screen_v1');plan=json.loads((root/'plan.json').read_text());t=plan['thresholds'];out={}
for name,folder in plan['cases'].items():
 p=Path(folder);f=p/'display_trace.dat.gz';raw=gzip.decompress(f.read_bytes());names=raw.decode().splitlines()[0].split();data=np.loadtxt(raw.decode().splitlines()[1:]);col={key:data[:,i] for i,key in enumerate(names)};time=col['time'];case=json.loads((p/'plan.json').read_text());R=case['active_brake_each_ohm'];assert np.isfinite(data).all() and np.all(np.diff(time)>0)
 armed=(col['v(aux)']>=t['aux_ready_V'])&(col['v(bus)']>=t['bus_min_V'])&(col['v(bus)']<=t['bus_max_V']);branches=[]
 for b in range(2):
  current=(col['v(bus)']-col[f'v(drain{b})'])/R;condition=armed&(col[f'v(gate{b})']<=t['gate_off_max_V'])&(current>=t['unexpected_current_min_A']);start=None;first=None;longest=0.
  for i,on in enumerate(condition):
   if not on:start=None;continue
   if start is None:start=time[i]
   duration=time[i]-start;longest=max(longest,duration)
   if duration>=t['persistence_s']-1e-10 and first is None:first=float(time[i])
  branches.append({'branch':b,'first_detection_s':first,'longest_sampled_condition_s':longest})
 expected=[] if name=='normal' else ([0] if name=='primary_stuck_on' else [0,1])
 passed=all((row['first_detection_s'] is not None and row['first_detection_s']<=plan['criteria']['stuck_on_detect_before_s']) if row['branch'] in expected else row['first_detection_s'] is None for row in branches)
 out[name]={'branches':branches,'sampled_case_pass':passed,'trace_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'maximum_sample_interval_s':float(np.diff(time).max())}
(root/'report.json').write_text(json.dumps({'cases':out,'hardware_detection_verified':False},indent=2)+'\n');print(json.dumps(out,indent=2))
