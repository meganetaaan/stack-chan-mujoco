"""Compare MCU maximum leakage with the monitor receiver's 20 uA drive condition."""
import argparse,json,hashlib
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
# Apply the entire published product leakage allowance to this one output,
# rather than assuming an undocumented per-pin allocation of the 10 uA term.
leak=10e-6+44*70e-9
rows=[]
for resistance in (220000,560000,1000000):
 load=3.6/(resistance*.99)+leak
 rows.append({'pulldown_ohm':resistance,'total_high_load_upper_A':load,
  'margin_to_20uA_A':20e-6-load,'conditional_20uA_drive_check':load<=20e-6,
  'receiver_only_off_voltage_V':.5e-6*resistance*1.01,
  'off_voltage_scope':'Receiver Ioff only at VCC=0; excludes MCU/board leakage, not full off-state voltage'})
r={'scope':__doc__,
 'original_candidate':{'part':'STM32C011F6P6','source':'https://www.st.com/resource/en/datasheet/stm32c011f4.pdf','revision':'DS13866 Rev 5','page':60,
 'finding':'Ilkg values are in Typ column; Max blank; footnote refers to Ilkg(Max). No maximum inferred.',
 'guaranteed_input_load_available':False},
 'alternative':{'part':'STM32G030F6P6','source':'https://www.st.com/resource/en/datasheet/stm32g030f6.pdf','revision':'DS12991 Rev 6','pages':[1,29,61],
 'standard_input_leakage_max_A':70e-9,'product_leakage_offset_A':10e-6,
 'conservative_pad_count':44,'whole_product_leakage_budget_A':leak,
 'conditions':['Every driven pad between GND and its VDDIO1',
 'FT_e switchable diodes disabled; internal pulls disabled',
 'All bonded logical pads must be accounted for; TSSOP20 includes multi-bonded pins',
 'Common valid LOGIC3V3 for receiver and MCU; no power-off or overshoot claim'],
 'not_drop_in':'Pin aliases, reset/power features and firmware differ from C011; no automatic substitution'},
 'design_assumptions':['Pull resistor total +/-1 percent; exact part unselected',
 'Use entire product leakage on this path conservatively; no board leakage included'],
 'rows':rows,
 'settled_logic_margins_V':{'high_min':3.0-.1-.7*3.0,'low_min':.3*3.0-.1},
 'decision':'C011 load remains unbounded by inspected table. G030 plus larger pulldown merits further pin/power review; existing 220k exceeds the selected drive condition.',
 'not_proven':['MCU integration','Power-off, reset and transient behavior','Board leakage budget','Timer output loading and propagation','Other controller connections'],
 'manufacturing_release':False}
a.out.mkdir(parents=True,exist_ok=False);(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(rows,indent=2))
