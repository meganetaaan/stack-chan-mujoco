"""Contact-current budget for B3U-1000P with external pullup and raw receiver."""
import argparse,itertools,json,hashlib
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--assembly',type=Path);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
binding=None
if a.assembly:
    assembly=json.loads(a.assembly.read_text());refs={x['reference']:x for x in assembly['parts']}
    assert refs['SW1']['part']=='B3U-1000P'
    assert refs['U1']['part']=='MAX6816EUS+T' and refs['U15']['part']=='74LVC1G17GV'
    assert refs['SW1']['pins']=={'1':'BUTTON_RAW','2':'GND'}
    assert refs['R15']['pins']=={'1':'LOGIC3V3','2':'BUTTON_RAW'}
    assert refs['R15']['part'].startswith('3k ')
    assert refs['U15']['pins']=={'1':None,'2':'BUTTON_RAW','3':'GND','4':'RAW_RELEASED_CONDITIONED','5':'LOGIC3V3'}
    assert refs['U1']['pins']['2']=='BUTTON_RAW' and refs['U1']['pins']['4']=='LOGIC3V3'
    assert refs['U3']['pins']['2']=='RAW_RELEASED_CONDITIONED'
    raw={(r['reference'],pin) for r in assembly['parts'] for pin,net in r['pins'].items() if net=='BUTTON_RAW'}
    assert raw=={('SW1','1'),('R15','2'),('U1','2'),('U15','2')}
    binding={'assembly_sha256':hashlib.sha256(a.assembly.read_bytes()).hexdigest(),'raw_node_connections':sorted(raw),'pin_mapping_matches_comparison':True}
rows=[]
for rail,internal,external,leak in itertools.product([3.207,3.393],[32000,100000],[2970,3030],[-1e-6,1e-6]):
    resistance=1/(1/internal+1/external)
    closed=(rail/resistance-leak)/(1/resistance+1/.1)
    contact=closed/.1
    opened=rail-leak*resistance
    rows.append(dict(rail_V=rail,internal_pullup_ohm=internal,external_pullup_ohm=external,receiver_leak_A=leak,closed_voltage_V=closed,contact_current_A=contact,open_voltage_V=opened))
r={'rows':rows,'contact_current_A':[min(v['contact_current_A'] for v in rows),max(v['contact_current_A'] for v in rows)],'closed_voltage_max_V':max(v['closed_voltage_V'] for v in rows),'open_voltage_min_V':min(v['open_voltage_V'] for v in rows),'criteria':{'contact_current_A':[.001,.05],'open_supply_V':[3,12]},'assumptions':['external resistor total +/-1% not yet tied to an order code','initial contact resistance .1 ohm; no life-end resistance guarantee','raw receiver +/-1uA comparison; PCB leakage not included','normal supply only; no ESD/transient or whole-interface qualification'],'manufacturing_release':False}
if binding:
    r['assembly_binding']=binding
    r['receiver_leak_test_condition']='VI=5.5V or GND, VCC=0..5.5V; actual input voltage and PCB leakage are not separately bounded by this calculation'
    r['switch_temperature_C']=[-25,70]
    r['additional_sink_leakage_budget_A_for_1mA_contact']=(3.207-.001*.1)*(1/100000+1/3030)-.001-1e-6
    r['leakage_budget_scope']='Derived conditional budget at limiting corner, not a selected PCB leakage specification or measured margin'
    r['electrical_qualification']=False
assert r['contact_current_A'][0]>=.001 and r['contact_current_A'][1]<=.05
(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:r[k] for k in ['contact_current_A','closed_voltage_max_V','open_voltage_min_V']}))
