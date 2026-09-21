"""Supply legacy stop supervisors from a separate battery-fed 3.3 V LDO candidate."""
import argparse,copy,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
src=Path('schematics/power/servo_power_rearm_integration_revA/assembly.json')
r=copy.deepcopy(json.loads(src.read_text()));changed=[]
for part in r['parts']:
 for pin,net in part['pins'].items():
  if net=='EFUSE_INPUT_5V':
   part['pins'][pin]='STOP_AUX3V3';changed.append(f"{part['reference']}.{pin}")
  elif net=='CLAMP_MR_5V':part['pins'][pin]='CLAMP_MR_STOP_AUX'
r['parts'] += [
 {'reference':'U_STOP_LDO','part':'TPS70933DBVR','pins':{'1':'BATTERY_REVERSE_PROTECTED','2':'GND','3':None,'4':None,'5':'STOP_AUX3V3'},'note':'TPS709 pinout, not TPS709A/B; EN intentionally floating per TI table 5-1'},
 {'reference':'C_STOP_IN','part':None,'value_F':2.2e-6,'pins':{'1':'BATTERY_REVERSE_PROTECTED','2':'GND'},'requirement':'Select voltage rating, effective capacitance and transient suitability'},
 {'reference':'C_STOP_OUT','part':None,'value_F':4.7e-6,'pins':{'1':'STOP_AUX3V3','2':'GND'},'requirement':'At least 2.2uF effective per TI; exact part and bias/temperature/ESR qualification pending'}]
assert len({x['reference'] for x in r['parts']})==len(r['parts'])
assert not any(n=='EFUSE_INPUT_5V' for x in r['parts'] for n in x['pins'].values())
r['interfaces'].pop('EFUSE_INPUT_5V',None)
r['interfaces']['BATTERY_REVERSE_PROTECTED']='Battery after unimplemented reverse/branch protection; independent of servo converter output'
r['interfaces']['STOP_AUX3V3']='Dedicated stop-monitor supply, separate from LOGIC3V3; load and power sequence unqualified'
r['scope']=__doc__;r['part_count']=len(r['parts']);r['pin_count']=sum(len(x['pins']) for x in r['parts'])
r['source_sha256']={str(src):hashlib.sha256(src.read_bytes()).hexdigest()}
r['integration_limitations'] += ['Stop supply moved from legacy 5V to dedicated 3.3V; previous 5V clamp timing/level calculations cannot be reused','Stop LDO load, thermal, capacitor effective value and startup/brownout order unresolved','Stop LDO own failure and shared battery loss not covered','EN_UVLO drive remains unimplemented']
r['manufacturing_release']=False;r['electrical_qualification']=False
(a.out/'assembly.json').write_text(json.dumps(r,indent=2)+'\n')
report={'changed_supply_pins':changed,'part_count':r['part_count'],'pin_count':r['pin_count'],'old_5V_net_remaining':False,'TPS709_EN_floating':True,'electrical_qualification':False}
(a.out/'integration_report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
