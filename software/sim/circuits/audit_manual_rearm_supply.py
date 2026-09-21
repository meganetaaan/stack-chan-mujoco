"""Separate reference IC currents from conservative resistor currents and missing rail loads."""
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--current',action='store_true');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
root=Path(__file__).resolve().parents[3];paths=['schematics/power/manual_rearm_revH/assembly.json','schematics/power/manual_rearm_resistors.json']
if a.current:
    current=json.loads((root/'schematics/power/manual_rearm_current.json').read_text())
    paths=[current['assembly'],current['resistor_selection']]
assembly,spec=[json.loads((root/x).read_text()) for x in paths]
resistors=list(spec['resistors'])
refs={x['reference']:x for x in assembly['parts']}
if a.current and 'R15' in refs:
    local_path='schematics/power/local_enable_button_candidate.json';paths.append(local_path)
    local=json.loads((root/local_path).read_text())
    assert refs['R15']['pins']=={'1':'LOGIC3V3','2':'BUTTON_RAW'}
    assert refs['R15']['part'].startswith('3k ') and local['external_pullup_ohm']==3000
    resistors.append({'reference':'R15','value_ohm':local['external_pullup_ohm']})
assert {r['reference'] for r in resistors}=={r for r in refs if r.startswith('R')}

# Maxima at manufacturer test conditions; not all are maxima at the actual inputs.
reference_uA={'MAX6816EUS+T':20,'SN74LVC1G04DBVR':10,'SN74HCS11PWR':2,'SN74HCS74PW':2,'74LVC1G17GV':4,'TPS3808G33DBVR':6,'TPS3808G01DBVR':6,'TPS3700DDCR':13,'74AUP1G06GW':1.4}
power_pin={'MAX6816EUS+T':'4','SN74HCS11PWR':'14','SN74HCS74PW':'14','TPS3808G33DBVR':'6','TPS3808G01DBVR':'6'}
ics=[]
for part in assembly['parts']:
    if not part['reference'].startswith('U'):continue
    name=part['part'];rail=part['pins'][power_pin.get(name,'5')]
    assert rail in ['LOGIC3V3','EFUSE_INPUT_5V']
    ics.append({'reference':part['reference'],'part':name,'supply_net':rail,'reference_current_A':reference_uA[name]*1e-6,'actual_input_current_qualified':False})
rs=[]
for r in resistors:
    rail='EFUSE_INPUT_5V' if r['reference']=='R8' else 'LOGIC3V3'
    voltage=5.25 if rail=='EFUSE_INPUT_5V' else 3.393
    rs.append({'reference':r['reference'],'assigned_supply':rail,'resistor_current_bound_A':voltage/(r['value_ohm']*.99)})
rails={}
for rail in ['LOGIC3V3','EFUSE_INPUT_5V']:
    rails[rail]={'IC_reference_sum_A':sum(x['reference_current_A'] for x in ics if x['supply_net']==rail),'resistor_independent_bounds_sum_A':sum(x['resistor_current_bound_A'] for x in rs if x['assigned_supply']==rail),'qualified_total_current_A':None}
report={'ICs':ics,'resistors':rs,'rails':rails,'source_sha256':{x:hashlib.sha256((root/x).read_bytes()).hexdigest() for x in paths},'method':'Each external resistor treated as full rail to ground for conservative comparison, even if states are mutually exclusive or series paths double counted','important_exception':'U11 VCC=EFUSE_INPUT_5V but High input comes from LOGIC3V3. Quiescent 4uA specification at rail inputs does not bound this condition. Published deltaICC at VCC-0.6V is not a guarantee at the actual level.','missing':['Input-level-dependent CMOS supply current and switching current','Internal MR pullups and SENSE currents of supervisors','MAX6816 input pullup current when pressed','Future sequencer and external fault/stop interfaces','Local enable button candidate not integrated','Capacitor charging, LDO ground current, loss and thermal implementation'],'electrical_qualification':False}
if a.current:
    report['missing']=[x for x in report['missing'] if x!='Local enable button candidate not integrated']
    report['missing'].append('Local button raw-node protection/layout leakage and transient loads')
    report['assembly_revision']=current['candidate_revision']
    report['resistor_coverage']={'assembly_count':len([r for r in refs if r.startswith('R')]),'evaluated_count':len(rs)}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(rails,indent=2))
