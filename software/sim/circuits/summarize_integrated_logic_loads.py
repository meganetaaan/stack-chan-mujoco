"""Keep logic-output reference allocations separate from battery-side branch loads."""
import hashlib,json
from pathlib import Path
root=Path('validation/integrated_logic_loads_v1');source=Path('schematics/power/servo_power_logic_integration_candidate_v1/assembly.json');assembly=json.loads(source.read_text());sha=hashlib.sha256(source.read_bytes()).hexdigest()
out=json.loads((root/'output/report.json').read_text());ic=json.loads((root/'ic_catalog.json').read_text());assert out['source_sha256'][str(source)]==ic['source_sha256']==sha
parts={p['reference']:p for p in assembly['parts']};cap=parts['C_LOGIC_LDO_OUT'];assert cap['pins']=={'1':'LOGIC3V3','2':'GND'}
leak=cap['qualification']['leakage_A_at_25C_5min'];core=json.loads(Path('validation/sequence_mcu_current_v1/report.json').read_text())['core_reference_A']
logic=out['logic_direct_plus_output_plus_reservation_A']+ic['reference_subtotal_uA']['LOGIC3V3']*1e-6+core+leak
bleed=parts['R_LOGIC_INPUT_BLEED'];assert bleed['pins']=={'1':'BATTERY_RAW','2':'GND'}
raw=12.6/(bleed['value_ohm']*.99)
for top,bottom in [('R_LOGIC_UV_TOP','R_LOGIC_UV_BOTTOM'),('R_LOGIC_OV_TOP','R_LOGIC_OV_BOTTOM')]:
 assert parts[top]['pins']['1']=='BATTERY_RAW' and parts[bottom]['pins']['2']=='LOGIC_PROTECT_RTN'
 raw+=12.6/(.99*(parts[top]['value_ohm']+parts[bottom]['value_ohm']))
r={'assembly_sha256':sha,'logic_reference_A':logic,'polymer_leakage_reference_A_at_25C_5min':leak,'engineering_continuous_target_A':.02,'unallocated_reference_margin_A':.02-logic,'battery_side_resistor_reference_A_at_12p6V':raw,'complete_current_budget':False,'excluded':['MCU peripheral and dynamic currents; MCU remains unimplemented','MAX6816 internal switch pullup load','All capacitor leakage outside specified reference conditions','Logic intermediate input/dynamic currents and board leakage','TPS26601 bias/ILIM current and TPS709 ground current','Whole-robot UBEC, servo, STOP and Tab5 supply current'],'rules':['Battery-side resistor current is not LOGIC3V3 output load','IC supply bias is not automatically equal to current through protected pass FET','Reference sum is not a guaranteed simultaneous-state upper bound','20mA target is not an input current limit or validated peak']}
(root/'summary.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
