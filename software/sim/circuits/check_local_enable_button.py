"""Contact-current budget for B3U-1000P with external pullup and raw receiver."""
import argparse,itertools,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
rows=[]
for rail,internal,external,leak in itertools.product([3.207,3.393],[32000,100000],[2970,3030],[-1e-6,1e-6]):
    resistance=1/(1/internal+1/external)
    closed=(rail/resistance-leak)/(1/resistance+1/.1)
    contact=closed/.1
    opened=rail-leak*resistance
    rows.append(dict(rail_V=rail,internal_pullup_ohm=internal,external_pullup_ohm=external,receiver_leak_A=leak,closed_voltage_V=closed,contact_current_A=contact,open_voltage_V=opened))
r={'rows':rows,'contact_current_A':[min(v['contact_current_A'] for v in rows),max(v['contact_current_A'] for v in rows)],'closed_voltage_max_V':max(v['closed_voltage_V'] for v in rows),'open_voltage_min_V':min(v['open_voltage_V'] for v in rows),'criteria':{'contact_current_A':[.001,.05],'open_supply_V':[3,12]},'assumptions':['external resistor total +/-1% not yet tied to an order code','initial contact resistance .1 ohm; no life-end resistance guarantee','raw receiver +/-1uA comparison; PCB leakage not included','normal supply only; no ESD/transient or whole-interface qualification'],'manufacturing_release':False}
assert r['contact_current_A'][0]>=.001 and r['contact_current_A'][1]<=.05
(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:r[k] for k in ['contact_current_A','closed_voltage_max_V','open_voltage_min_V']}))
