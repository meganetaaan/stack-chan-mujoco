"""Integrate independent left/right source monitors; raw status requires startup qualification."""
import argparse,copy,hashlib,json
from pathlib import Path
from assembly_net_aliases import net_aliases
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
bp=Path('schematics/power/servo_power_rearm_integration_revE/assembly.json')
mp=Path('schematics/power/source_window_monitor_revB/connectivity.json')
r=copy.deepcopy(json.loads(bp.read_text()));monitor=json.loads(mp.read_text())
assert not ({x['reference'] for x in r['parts']} & {x['reference'] for x in monitor['parts']})
r['parts']+=monitor['parts']
for side in ('LEFT','RIGHT'):
 r['interfaces'][side+'_SOURCE_WINDOW_OD']='Raw window comparator output to unimplemented sequencer qualification; invalid during startup/power loss; not direct enable'
r['interfaces']['STOP_AUX3V3']='Stop supervisors plus two source-window ICs; full load and power sequencing qualification pending'
r['scope']=__doc__;r['part_count']=len(r['parts']);r['pin_count']=sum(len(p['pins']) for p in r['parts'])
r['source_sha256']={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (bp,mp)}
r['integration_limitations']=[s for s in r['integration_limitations'] if s!='Startup sequencer and source-voltage monitors absent']
r['integration_limitations']+=['Voltage monitor circuitry connected to actual converter sources; startup-qualified status and sequencer hardware absent','Raw window outputs not tied to EN or RESET; monitor output invalidity must be handled before use','Window divider/capacitor exact parts and full tolerance, leakage, timing and fault coverage pending']
alias=net_aliases(r);parts={x['reference']:x for x in r['parts']};checks=[]
for side in ('LEFT','RIGHT'):
 u=parts[side+'_U_WINDOW'];power=parts[side+'_U_POWER']
 assert u['pins']['5']=='STOP_AUX3V3'
 assert u['pins']['1']==u['pins']['6']==side+'_SOURCE_WINDOW_OD'
 for mode,pin in [('UV','3'),('OV','4')]:
  top=parts[side+'_R_SOURCE_'+mode+'_TOP'];bottom=parts[side+'_R_SOURCE_'+mode+'_BOTTOM']
  assert alias[top['pins']['1']]==alias[power['pins']['5']]
  assert top['pins']['2']==bottom['pins']['1']==u['pins'][pin]
  assert bottom['pins']['2']=='GND'
 assert alias[u['pins']['1']]!=alias['MAIN_EFUSE_EN']
 assert alias[u['pins']['1']]!=alias['RESET_N']
 checks.append({'side':side,'monitor_supply':'STOP_AUX3V3','monitored_source':power['pins']['5'],'raw_status':u['pins']['1']})
assert alias['LEFT_SOURCE_WINDOW_OD']!=alias['RIGHT_SOURCE_WINDOW_OD']
r['manufacturing_release']=False;r['electrical_qualification']=False
(a.out/'assembly.json').write_text(json.dumps(r,indent=2)+'\n')
(a.out/'integration_report.json').write_text(json.dumps({'part_count':r['part_count'],'pin_count':r['pin_count'],'checks':checks,'raw_status_directly_controls_power':False,'manufacturing_release':False},indent=2)+'\n')
print(r['part_count'],r['pin_count'],checks)
