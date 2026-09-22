"""Add local shutdown pulldowns and derive requirements for the unresolved driver."""
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
src=Path('schematics/power/series_clamp_stage_revB/assembly.json');r=json.loads(src.read_text())
for side in ['L','R']:
 u=next(x for x in r['parts'] if x['ref']==f'U_{side}');u['pins']['6']=f'{side}_SHDN'
 for ref,value,pins in [(f'RSD_SER_{side}',1000,{'1':'SHDN_DRIVER_PORT','2':f'{side}_SHDN'}),(f'RSD_PD_{side}',10000,{'1':f'{side}_SHDN','2':'GND'})]:
  r['parts'].append({'ref':ref,'part':None,'pins':pins,'value_ohm':value,'total_tolerance_allocation':.01})
r['ports_per_branch'].remove('SHDN_PORT');r['shared_ports']=['SHDN_DRIVER_PORT','GND']
r['source_sha256']={str(src):hashlib.sha256(src.read_bytes()).hexdigest()}
r['shutdown_driver_requirements']={
 'local_off_threshold_V':.4,'local_enable_threshold_max_V':2.1,
 'comparison_driver_high_min_V':2.4,
 'max_combined_positive_leakage_at_off_boundary_A':.4/10100,
 'remaining_driver_leakage_after_SHDN_source8uA_A':.4/10100-8e-6,
 'max_SHDN_sink_current_at_high_boundary_A':(2.4-2.1)/1010-2.1/9900,
 'minimum_reset_low_s':100e-6,
 'reset_scope':'Low pulse alone is insufficient during timer cooldown; follow current timer/reset requirements.',
 'limitations':['2.4V loaded driver high is a proposed interface requirement, not an existing U8 guarantee at the new load.',
 'SHDN sourcing8uA is specified at0.4V; boundary analysis does not prove arbitrary startup/brownout behavior.',
 'High-state SHDN input current and transient drive need qualification.',
 'No attachment to existing MAIN_EFUSE_EN after its series resistor; doing so changes its load budget.',
 'Default-low resistor is not proof against a stuck-high driver.']}
r['interface_constraints'][0]='SHDN has local 10k pulldowns and 1k series resistors. Shared driver port remains unqualified; no default-off claim during brownout.'
r['checks']['local_SHDN_pulldowns_present']=True
r['missing'][0]='UV qualification and loaded shutdown driver/reset/brownout integration'
a.out.mkdir(parents=True,exist_ok=False);(a.out/'assembly.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r['shutdown_driver_requirements']))
