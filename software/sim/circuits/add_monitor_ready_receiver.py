"""Connect a range-specified monitor-ready receiver; no whole-circuit startup claim."""
import argparse, hashlib, json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--out',type=Path,required=True)
a=p.parse_args()
base=Path('schematics/power/servo_power_rearm_integration_revG/assembly.json')
r=json.loads(base.read_text())
new=[{'reference':'U_MONITOR_RX','part':'SN74AUP1T50DCKR','pins':{'1':None,'2':'MONITOR_START_READY_OD','3':'GND','4':'MONITOR_START_READY_LOGIC','5':'LOGIC3V3'}},
 {'reference':'R_MONITOR_RX_OFF','part':None,'value_ohm':220000,'pins':{'1':'MONITOR_START_READY_LOGIC','2':'GND'}},
 {'reference':'C_MONITOR_RX','part':None,'value_F':100e-9,'pins':{'1':'LOGIC3V3','2':'GND'}}]
assert not ({x['reference'] for x in new}&{x['reference'] for x in r['parts']})
parts={x['reference']:x for x in r['parts']}
assert parts['U_MONITOR_START']['pins']['1']==new[0]['pins']['2']
assert parts['R_MONITOR_START']['value_ohm']==100000
r['parts']+=new
r['part_count']=len(r['parts']);r['pin_count']=sum(len(x['pins']) for x in r['parts'])
r['scope']=__doc__
r['interfaces']['MONITOR_START_READY_OD']='TPS3808 output connected to U_MONITOR_RX; local output loading and dip coverage pending'
r['interfaces']['MONITOR_START_READY_LOGIC']='Buffered startup timer status; does not imply qualified source voltage; no direct EN connection'
r['integration_limitations']+=[
 'SN74AUP1T50 receiver is rated -40..85 C; operation above 85 C not qualified and must not inherit other ICs 125 C rating',
 'Receiver LOGIC3V3 must be 3.0..3.6 V for stated input thresholds; whole rail and startup inhibition pending',
 'Receiver input capacitance typical only; TPS3808 delay loading not fully qualified',
 'Output pulldown limits leakage at VCC=0 only; intermediate voltage and downstream loading pending']
r['source_sha256']={str(base):hashlib.sha256(base.read_bytes()).hexdigest(),__file__:hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
r['manufacturing_release']=False;r['electrical_qualification']=False
# Existing STOP_AUX comparison; LOGIC3V3 range here is a receiver interface requirement.
vstop_min=3.207
rin_max=100000*1.01
rout_min=220000*.99
rout_max=220000*1.01
high=vstop_min-(.5e-6+.3e-6)*rin_max
load=3.6/rout_min
report={'classification':'datasheet_interface_budget_not_transient_simulation',
 'part':'SN74AUP1T50DCKR','source':'https://www.ti.com/lit/ds/symlink/sn74aup1t50.pdf',
 'revision':'SCES844A March 2013','datasheet_pages':[1,4,5],
 'manufacturer_constraints':{'temperature_C':[-40,85],'VCC_for_thresholds_V':[3,3.6],
  'VT_plus_max_V':1.19,'VT_minus_min_V':.5,'input_leakage_max_A':.5e-6,
  'Ioff_at_zero_supply_max_A':.5e-6,'VOH_drop_at_20uA_V':.1,'VOL_at_20uA_V':.1},
 'assumptions':['STOP_AUX3V3 minimum 3.207 V is existing conditional rail budget',
  'Resistor total tolerance +/-1 percent; exact parts pending',
  'Input leakage endpoint specification applied to actual input level',
  'No downstream load beyond the added output resistor in this calculation'],
 'bounds':{'input_high_min_V':high,'high_margin_V':high-1.19,
  'input_low_max_V':.4,'low_margin_V':.5-.4,
  'output_pulldown_max_current_A':load,'remaining_20uA_drive_budget_A':20e-6-load,
  'output_at_zero_supply_leakage_only_max_V':.5e-6*rout_max},
 'input_threshold_range_specified':True,
 'conditional_settled_interface_pass':high>1.19 and .4<.5 and load<20e-6,
 'power_on_inhibit_proven':False,'full_source_valid_proven':False,
 'temperature_change_classification':'New part constraint, not permission to lower an existing requirement; no 125 C operation claim',
 'part_count':r['part_count'],'pin_count':r['pin_count'],
 'pending':['Prove actual LOGIC3V3 range and receiver temperature against system requirements',
  'Downstream load, logic thresholds and partial power',
  'Input capacitance and supervisor timing load',
  'Short dip detection and startup sequencer inhibition'],
 'manufacturing_release':False}
a.out.mkdir(parents=True,exist_ok=False)
(a.out/'assembly.json').write_text(json.dumps(r,indent=2)+'\n')
(a.out/'integration_report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report['bounds'],indent=2))
