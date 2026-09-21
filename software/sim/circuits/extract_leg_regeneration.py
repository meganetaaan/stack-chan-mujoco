"""Extract sampled DC return energy per isolated leg from EPIC4 load bundles."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
rows=[];hashes={}
for turn in ['left','right']:
 folder=Path(f'validation/prototype_epic4_v1/load_export_{turn}_v1')
 schema=json.loads((folder/'schema.json').read_text());names=schema['joint_names'];dt=schema['sample_period_s']
 for f in [folder/'schema.json',folder/'loads.npz']:hashes[str(f)]=hashlib.sha256(f.read_bytes()).hexdigest()
 with np.load(folder/'loads.npz') as d:
  t=d['time_s'];current=d['supply_current_A'];power=d['supply_power_W']
  assert np.allclose(np.diff(t),dt) and current.shape==power.shape==(len(t),12)
  assert np.isfinite(current).all() and np.isfinite(power).all() and dt>0
  for leg in ['left','right']:
   indices=[i for i,n in enumerate(names) if n.startswith(leg+'_')];assert len(indices)==6
   gross_i=np.maximum(-current[:,indices],0).sum(axis=1)
   net_i=np.maximum(-current[:,indices].sum(axis=1),0)
   gross_p=np.maximum(-power[:,indices],0).sum(axis=1)
   net_p=np.maximum(-power[:,indices].sum(axis=1),0)
   # Exported power/current are start-of-interval values, so rectangle integration is intentional.
   events=[];start=None
   for i,active in enumerate(np.r_[net_i>0,False]):
    if active and start is None:start=i
    elif not active and start is not None:
     events.append({'start_sample':start,'end_sample_exclusive':i,'duration_s':(i-start)*dt,'charge_C':float(net_i[start:i].sum()*dt),'energy_J':float(net_p[start:i].sum()*dt)})
     start=None
   rows.append({'turn':turn,'leg':leg,'record_duration_s':len(t)*dt,
    'sum_individual_return_peak_A':float(gross_i.max()),'sum_individual_return_charge_C':float(gross_i.sum()*dt),'sum_individual_return_energy_J':float(gross_p.sum()*dt),
    'net_bus_return_peak_A':float(net_i.max()),'net_bus_return_charge_C':float(net_i.sum()*dt),'net_bus_return_energy_J':float(net_p.sum()*dt),
    'net_return_event_count':len(events),'largest_net_return_event':max(events,key=lambda x:x['energy_J']) if events else None})
r={'sources_sha256':hashes,'integration':'Rectangle rule over exported start-of-interval samples; sum all N intervals, not trapezoid over N-1.',
 'rows':rows,'qualified_hardware_bound':False,'limits':['Only two retained 7s turning records; no latest prototype payload, shutdown, fault or arbitrary gait coverage.',
 'DC current and power follow the existing ideal bridge model, not measured servo regeneration or PWM spikes.',
 'Net bus return includes consumption by other servos on the same leg. Sum of individual negative currents does not credit that consumption.',
 'Consumption on the other leg must not cancel return energy because the power buses are isolated.',
 'Neither observed peak nor total energy is a worst-case bound; do not replace the existing stress case or model envelope with these smaller values.']}
a.out.mkdir(parents=True,exist_ok=False);(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(rows,indent=2))
