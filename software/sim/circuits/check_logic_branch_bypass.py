"""Conditional capacitance check; not transient qualification."""
import argparse,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
d=json.loads(Path('schematics/power/logic_input_branch_candidate_v1/branch.json').read_text())
rows=[]
for net in ['BATTERY_RAW','LOGIC_PROTECTED_INPUT']:
 caps=[c for c in d['capacitors'] if c['pins']['1']==net]
 lo=sum(c['value_F']*(1-c['initial_tolerance'])*(1-30e-6*100) for c in caps)
 hi=sum(c['value_F']*(1+c['initial_tolerance'])*(1+30e-6*100) for c in caps)
 rows.append({'net':net,'references':[c['ref'] for c in caps],'C_25_to_125C_F':[lo,hi],'exceeds_0p1uF':lo>=1e-7,'charge_at_12p6V_C':hi*12.6,'stored_energy_at_12p6V_J':.5*hi*12.6**2})
r={'criterion_before_calculation':'Each local pair >=0.1uF including initial tolerance and specified 25..125C temperature coefficient','rows':rows,'qualified':False,'limits':['Temperature coefficient cited only for 25..125C; cold capacitance not qualified','No DC bias/process/aging/PCB parasitic verification','50V rating is not a system surge clamp','Upstream pair is outside eFuse inrush control','Downstream charging and LDO output charging are separate loads; no inferred shared ramp']}
(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');assert all(x['exceeds_0p1uF'] for x in rows);print(json.dumps(r,indent=2))
