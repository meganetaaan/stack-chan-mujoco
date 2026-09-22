"""Conditional external harness graph; no unmodeled IC paths treated as wires."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
p=ROOT/'schematics/power/system_power_integration_candidate_v1/assembly.json';raw=p.read_bytes();a=json.loads(raw)
parts={x['reference']:x for x in a['parts']}
assert parts['INLET__J_PACK']['pins']['-']=='CELL_B_MINUS'
assert parts['BAT__U_CELL_PROTECT']['pins']['17']=='CELL_B_MINUS'
assert parts['BAT__R_CELL_0']['pins']['1']=='CELL_B_MINUS'
assert not any('J_CELL' in n or 'J_BALANCE' in n for n in parts)
# Model a possible four-wire balance connector explicitly as a proposal,
# not as a connector already present in the assembly.
cases=[]
for reverse,main,balance in [(False,True,True),(True,True,True),(False,False,True),(True,True,False)]:
 edges=[]
 if main:
  edges += [('BATTERY_B3' if reverse else 'BATTERY_B0','CELL_B_MINUS','main negative wire'),
            ('BATTERY_B0' if reverse else 'BATTERY_B3','CELL_POS_UNFUSED','main positive wire')]
 if balance:
  edges += [('BATTERY_B0','CELL_B_MINUS','proposed direct balance return'),
            ('BATTERY_B1','CELL1_TAP','balance cell1'),('BATTERY_B2','CELL2_TAP','balance cell2'),('BATTERY_B3','CELL3_TAP','balance cell3')]
 parent={}
 def find(n):
  parent.setdefault(n,n)
  if parent[n]!=n:parent[n]=find(parent[n])
  return parent[n]
 for x,y,_ in edges:parent[find(x)]=find(y)
 short=find('BATTERY_B0')==find('BATTERY_B3')
 cases.append({'main_connected':main,'main_reversed':reverse,'four_wire_balance_connected':balance,
 'wire_connections':edges,'direct_B0_B3_short':short,
 'all_cell_connections_removed':not main and not balance,
 'scope':'Only explicit ideal wires; absent hard short is not a safe-fault verdict'})
assert [x['direct_B0_B3_short'] for x in cases]==[False,True,False,False]
report={'source_sha256':hashlib.sha256(raw).hexdigest(),'balance_connector_present_in_current_netlist':False,
 'assumption':'Conventional four-wire3S balance harness proposed with B0 directly tied to CELL_B_MINUS',
 'cases':cases,'counterexample':'With reversed main negative wire and correctly attached balance return, B3 and B0 meet at CELL_B_MINUS. Positive-side fuse/ideal diode cannot interrupt these two wires.',
 'not_proven':['Current unselected harness has this wiring','Current magnitude, heating or source impedance','IC input/clamp paths with no balance return','Safe cell attachment/disconnect order'],
 'decision':'Reject direct shared-return four-wire harness for a main-reversal protection claim; connector and protection architecture must be resolved first',
 'manufacturing_release':False}
out=ROOT/'validation/cell_tap_disconnect_v1';out.mkdir(exist_ok=True)
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print('4 topology cases checked; reverse-main + direct balance-return proposal shorts battery terminals')
