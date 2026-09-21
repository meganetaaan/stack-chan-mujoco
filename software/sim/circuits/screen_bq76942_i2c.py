"""Passive pullup and bus-capacitance design screen, not a digital bus test."""
import json
from math import log
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
a=json.loads((ROOT/'schematics/power/battery_protection_integration_candidate_v1/assembly.json').read_text())
c=a['communications_candidate'];r=c['pullup_ohm'];allocation=.01
rmax=r*(1+allocation);rmin=r*(1-allocation)
rows=[]
for capacitance in [50e-12,100e-12,200e-12,400e-12]:
 rise=log(9)*rmax*capacitance
 rows.append({'C_F':capacitance,'rise_10_90_s':rise,'within_100k_rise_spec':rise<=1e-6,'within_400k_rise_spec':rise<=300e-9})
report={'scope':'RC 10%-90% rise and zero-volt sink current; no MCU fall-time or logic-level qualification',
 'source':'TI BQ76942 Rev B sections7.27/7.28',
 'source_rise_definition':'10% to90%, NOT I2C common30% to70%',
 'pullup_ohm':r,'resistance_total_design_allocation_fraction':allocation,
 'allocation_scope':'engineering allowance including tolerance/temperature/process; not a measured resistance bound',
 'rows':rows,'C_max_100k_F':1e-6/(log(9)*rmax),'C_max_400k_F':300e-9/(log(9)*rmax),
 'max_current_per_I2C_line_A_at3V6':3.6/rmin,
 'all_three_lines_low_current_A_at3V6':2*3.6/rmin+3.6/(10000*(1-allocation)),
 'minimum_pullup_ohm_spec':1500,'pullup_above_minimum':rmin>=1500,
 'remaining':['total bus capacitance after PCB/host selection','MCU sink/high/low thresholds','BQ VOL at3.3V; 5V table conditions cannot be copied','fall time, setup, hold and clock duty at receiver','CRC, timeout and reset handling','power-off backfeed and reference-domain routing'],
 'manufacturing_release':False}
out=ROOT/'validation/bq76942_i2c_v1';out.mkdir(exist_ok=True)
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
