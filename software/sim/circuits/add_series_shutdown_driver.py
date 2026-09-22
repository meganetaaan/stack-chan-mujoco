"""Screen and connect a dedicated shutdown buffer; retain failed original series resistor."""
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
src=Path('schematics/power/series_clamp_stage_revC/assembly.json');r=json.loads(src.read_text())
# Actual selected buffer guaranteed HIGH at3V,-24mA,-40..85C is2.3V, not proposed2.4V.
old_high=2.3*9900/(9900+1010)
new_high=2.3*9900/(9900+470*1.01)
assert old_high<2.1<new_high
for part in r['parts']:
 if part['ref'].startswith('RSD_SER_'):part['value_ohm']=470
r['parts'] += [
 {'ref':'U_SHDN','part':'74LVC1G17GV','pins':{'1':None,'2':'SHDN_COMMAND_PORT','3':'GND','4':'SHDN_DRIVER_PORT','5':'LOGIC3V3_PORT'}},
 {'ref':'R_SHDN_CMD_PD','part':None,'pins':{'1':'SHDN_COMMAND_PORT','2':'GND'},'value_ohm':10000,'total_tolerance_allocation':.01},
 {'ref':'C_SHDN_BYPASS','part':None,'pins':{'1':'LOGIC3V3_PORT','2':'GND'},'value_F':100e-9}]
r['shared_ports']=['SHDN_COMMAND_PORT','LOGIC3V3_PORT','GND']
r['source_sha256']={str(src):hashlib.sha256(src.read_bytes()).hexdigest()}
r['shutdown_driver_requirements']['comparison_driver_high_min_V']=2.3
r['shutdown_driver_requirements']['max_SHDN_sink_current_at_high_boundary_A']=(2.3-2.1)/(470*1.01)-2.1/9900
r['shutdown_driver_requirements']['limitations'][0]='2.3V uses selected buffer table at VCC3.0V and -24mA, -40..85C. Actual logic rail/temperature and load conditions must be maintained.'
r['shutdown_driver_screen']={'source':'https://assets.nexperia.com/documents/data-sheet/74LVC1G17.pdf','revision':'16.1, 3 September 2024',
 'old_1k_no_input_sink_high_V':old_high,'old_1k_screen_pass':False,
 'new_470ohm_no_input_sink_high_V':new_high,'new_resistor_only_screen_pass':True,
 'buffer_Ioff_max_A':2e-6,'buffer_VOL_at_100uA_max_V':.1,
 'fully_qualified':False,
 'remaining':['Actual SHDN HIGH input sink bound','Input threshold and sequencer output under10k load','Output load at actual logic supply','Low-state SHDN sourcing below0.4V and supply collapse','Brownout and stuck-high shutdown independence','Reset timing/cooldown']}
r['interface_constraints'][0]='Dedicated 74LVC1G17GV drives two470ohm/10k SHDN networks; command and logic supply ports remain unqualified.'
r['missing'][0]='UV and shutdown command/rail/reset/brownout qualification'
a.out.mkdir(parents=True,exist_ok=False);(a.out/'assembly.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r['shutdown_driver_screen']))
