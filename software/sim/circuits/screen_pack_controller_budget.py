"""Partial manufacturer-based budget; missing terms remain explicit, never zero."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'validation/pack_controller_budget_v1';OUT.mkdir(exist_ok=True)
p=ROOT/'schematics/power/pack_start_controller_candidate_v1/assembly.json'
a=json.loads(p.read_text())
assumptions={'rail_screen_V':3.6,'resistance_total_variation_fraction':.01,
 'pack_screen_V':[9.,12.6],'regulator_output_for_loss_V':3.3,
 'thermal_reference_RthetaJA_C_W':212.1,
 'thermal_scope':'TI DBV reference board figure, not the actual PCB or thermal acceptance',
 'resistor_scope':'Sum V/Rmin for every resistor individually; deliberately overcounts divider/network states',
 'mcu_scope':'ST DS12991 Rev6 Table25 Range1 Flash 85C VDD3.6; peripherals off, characterized not production tested'}
(OUT/'plan.json').write_text(json.dumps({'assumptions':assumptions,'criteria':['Do not represent partial sum as full maximum current','Compare old 750ohm feed against the 64MHz MCU term alone before proposing reuse'],'stop':'One static budget and feed rejection; no arbitrary transient sweep'},indent=2)+'\n')
res=[]
for part in a['parts']:
 if 'value_ohm' in part:
  res.append({'reference':part['reference'],'nominal_ohm':part['value_ohm'],
              'allocated_A':3.6/(part['value_ohm']*.99)})
res_sum=sum(x['allocated_A'] for x in res)
rows=[]
for freq,current in [(16,.0029),(32,.0049),(64,.0083)]:
 subtotal=current+res_sum+19e-6
 loss=(12.6-3.3)*subtotal
 rows.append({'MCU_MHz':freq,'MCU_characterized_max_A':current,
              'partial_screen_sum_A':subtotal,'LDO_output_load_loss_W':loss,
              'reference_board_temperature_rise_C':loss*212.1})
unknown=['MCU enabled peripherals/oscillator differences, external I/O loads and switching',
         'TPS3808 at actual voltage and reset state (5uA figure only at3.3V reset released)',
         'Logic gates/buffer/latch static and transition current at actual levels',
         'Capacitor charging/leakage, startup, debug and new interface loads',
         'TPS709 ground current at actual load, input-protection current and loss']
result={'source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'resistor_allocations':res,
 'resistor_envelope_A':res_sum,'watchdog_spec_max_A':19e-6,'rows':rows,
 'unknown_budget_terms':unknown,'total_controller_max_current_A':None,
 'legacy_750ohm_feed_screen':{'pack_V':9.,'MCU_only_A':.0083,
    'ideal_LDO_input_V':9-750*.0083,'assumed_diode_drop_V':0,
    'can_support_this_current_at3_3V':9-750*.0083>=3.3,
    'conclusion':'Cannot reuse old feed for this budget point; actual undervoltage dynamics not simulated'},
 'manufacturing_release':False}
(OUT/'report.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'resistor_envelope_A':res_sum,'rows':rows,'legacy_feed':result['legacy_750ohm_feed_screen']},indent=2))
