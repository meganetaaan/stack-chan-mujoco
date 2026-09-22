"""Replace direct source-to-OVLO dividers with a source-window driven candidate."""
import argparse, csv, hashlib, itertools, json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
base=Path('schematics/power/servo_power_rearm_integration_revM/assembly.json')
r=json.loads(base.read_text()); parts={x['reference']:x for x in r['parts']}
for side in ['LEFT','RIGHT']:
    hi=parts[side+'_R_OV_TOP'];lo=parts[side+'_R_OV_BOTTOM']
    assert hi['pins']=={'1':side+'_REGULATOR_OUT','2':side+'_OVLO_SENSE'}
    hi.update(part='TNPW060329K4BYEA',value_ohm=29400,total_tolerance_budget=.01,status='conditional_window_drive_candidate')
    hi['pins']['1']=side+'_WINDOW_FAULT'
    lo.update(part='TNPW060321K0BYEA',value_ohm=21000,total_tolerance_budget=.01,status='conditional_window_drive_candidate')
    r['parts'] += [
      {'reference':side+'_U_OV_DRIVE','part':'SN74LVC1G14DBVR','pins':{'1':None,'2':side+'_SOURCE_WINDOW_OD','3':'GND','4':side+'_WINDOW_FAULT','5':'STOP_AUX3V3'}},
      {'reference':side+'_C_OV_DRIVE','part':'GRM31C5C1H104JA01L','value_F':1e-7,'pins':{'1':'STOP_AUX3V3','2':'GND'},'placement':'Local inverter VCC/GND bypass'}]
    r['interfaces'][side+'_SOURCE_WINDOW_OD']='Source UV/OV window output to sequencer and Schmitt inverter. Low requests OVLO shutdown directly; validity during rail startup/drop remains unqualified.'
    r['interfaces'][side+'_OVLO_SENSE']='From inverted source-window output through 29.4k/21k; no direct regulator feedthrough. Conditional DC only.'
r['scope']=__doc__;r['source_sha256']={str(base):hashlib.sha256(base.read_bytes()).hexdigest()}
r['part_count']=len(r['parts']);r['pin_count']=sum(len(x['pins']) for x in r['parts'])
r['integration_limitations'] += ['revN replaces direct source OVLO divider with source-window driven Schmitt inverter. Source trip now follows existing TPS3700 window. Normal low uses active-low enable function; leakage bound below 0.5V is not specified.', 'Monitor startup, STOP rail loss, unpowered eFuse, window wire faults, response time and overshoot remain unqualified; firmware must not be the sole shutdown path. revM divider limits are historical.']
# Criteria are fixed before corner evaluation. The rail envelope remains conditional.
criteria={'fault_pin_min_exclusive_V':1.224,'fault_pin_max_V':1.5,'normal_pin_max_exclusive_V':1.074,'driver_load_max_A':100e-6}
high=[];low=[];load=[]
for rh,rl in itertools.product([29400*.99,29400*1.01],[21000*.99,21000*1.01]):
    for current in [-.1e-6,.1e-6]:
        for v in [3.207-.1,3.393]:high.append((v-current*rh)*rl/(rh+rl))
        for v in [0,.1]:low.append((v-current*rh)*rl/(rh+rl))
    load.append(3.393/(rh+rl)+.1e-6)
report={'criteria':criteria,'source_assembly':str(base),'part_count':r['part_count'],'pin_count':r['pin_count'],
 'fault_pin_conditional_V':[min(high),max(high)],'normal_pin_conditional_V':[min(low),max(low)],'max_driver_DC_load_A':max(load),
 'fault_pin_DC_screen_pass':min(high)>1.224 and max(high)<1.5,'driver_load_screen_pass':max(load)<100e-6,
 'whole_protection_qualified':False,'sources':['https://www.ti.com/lit/ds/symlink/sn74lvc1g14.pdf','https://www.ti.com/lit/ds/symlink/tps25981.pdf','https://www.ti.com/lit/ds/symlink/tps3700.pdf'],
 'limits':['STOP rail 3.207..3.393V is a conditional existing envelope, not a qualified supply.', 'LVC VOH/VOL at 100uA support output sizing; transient charging current and signal ringing excluded.', 'Normal-state calculation extrapolates OVLO leakage below 0.5V, so normal_pin range is diagnostic only. Active-low enable is explicitly supported by eFuse pin description.', 'Schmitt input threshold table is at discrete supplies; actual rail interpretation and TPS3700 loaded output must be verified.', 'TPS3700 OV threshold replaces the old direct eFuse threshold; no timing equivalence is claimed.', 'Total resistor tolerance 1% is an allocation; selected initial 0.1% plus temperature/aging qualification remains.', 'Existing monitor startup gating and manual rearm remain necessary. Source-window stuck-high/open and STOP power-loss faults are not covered by this DC screen.']}
assert report['fault_pin_DC_screen_pass'] and report['driver_load_screen_pass']
a.out.mkdir(parents=True,exist_ok=False)
(a.out/'assembly.json').write_text(json.dumps(r,indent=2)+'\n')
(a.out/'screen.json').write_text(json.dumps(report,indent=2)+'\n')
with (a.out/'candidate_bom.csv').open('w') as f:
 w=csv.writer(f,lineterminator='\n');w.writerow(['reference','part_candidate','value_ohm','value_F'])
 for x in r['parts']:w.writerow([x['reference'],x['part'],x.get('value_ohm',''),x.get('value_F','')])
print(json.dumps(report,indent=2))
