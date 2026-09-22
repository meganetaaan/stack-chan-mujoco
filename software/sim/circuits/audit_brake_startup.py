"""Check existing normal-load gate traces against candidate MOSFET threshold evidence."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[3]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
source=ROOT/'validation/dual_brake_development_v1/dual_normal_v2/trace.npz'
plan={'scope':__doc__,'candidate':'IRLML6344TRPbF','source':'https://www.infineon.com/assets/row/public/documents/24/49/infineon-irlml6344-datasheet-en.pdf',
 'datasheet_page':2,'threshold_min_V':.5,'threshold_max_V':1.1,'threshold_test':'TJ=25 C, VDS=VGS, ID=10 uA',
 'startup_window_s':[0,.05],'development_off_gate_limit_V':.4,
 'limit_reason':'20 percent below 25 C minimum threshold; a design target, not a full-temperature leakage guarantee',
 'trace_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
 'limitations':['Existing trace uses a 2.5 V ideal MOS switch; no actual drain-current prediction','No temperature-dependent threshold or guaranteed leakage below threshold','Startup clamp not implemented']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
d=np.load(source);t=d['time_s'];window=(t>=0)&(t<=.05);rows=[]
for i in range(2):
 gate=d[f'gate{i}_V'];on=window&(gate>=.5);over=window&(gate>.4)
 rows.append({'branch':i,'startup_peak_gate_V':float(gate[window].max()),
  'first_sample_over_min_threshold_s':float(t[on][0]) if on.any() else None,
  'last_sample_over_min_threshold_s':float(t[on][-1]) if on.any() else None,
  'bus_range_while_over_min_threshold_V':[float(d['bus_V'][on].min()),float(d['bus_V'][on].max())] if on.any() else None,
  'over_limit_sample_count':int(over.sum()),'off_target_passed':bool(not over.any())})
report={'branches':rows,'passed_development_off_target':all(r['off_target_passed'] for r in rows),
 'startup_off_verified':False,'note':'Above threshold does not quantify current, but the existing ideal-switch no-braking result does not establish real-device turn-off.'}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
