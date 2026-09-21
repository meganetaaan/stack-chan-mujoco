"""Fuse load-budget sensitivity, not a protection coordination simulation."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
source=ROOT/'schematics/power/battery_inlet_candidate.json'
raw=source.read_bytes();candidate=json.loads(raw)
loadpath=ROOT/'validation/pololu_wiring_budget_v1/report.json'
loadraw=loadpath.read_bytes();load=json.loads(loadraw)
one_leg=max(row['shared_current_A'] for row in load['rows'])
# Nominal 5V case only; bleed term calculated from two 360ohm resistors per leg.
servo_W=5*(2*one_leg+4*5/360)
rows=[]
for vin in (9,12.6):
 for efficiency in (.80,.90,.95):
  current=servo_W/(vin*efficiency)
  rows.append({'battery_V':vin,'assumed_efficiency':efficiency,'servo_input_A':current,
               'remaining_A_at_typical_40C_fuse_recommendation':8.6-current})
r={'source_sha256':{str(source.relative_to(ROOT)):hashlib.sha256(raw).hexdigest(),str(loadpath.relative_to(ROOT)):hashlib.sha256(loadraw).hexdigest()},
   'purpose':'Expose remaining Tab5/auxiliary budget before finalizing 10A fuse',
   'servo_nominal_power_W_including_bleeds':servo_W,'rows':rows,
   'assumptions':['5V nominal only, not maximum module voltage','9V and12.6V comparison inputs, no wire drop','80/90/95% sensitivity values, not guaranteed converter efficiency','4.917A per leg is model envelope, not measured stall bound','8.6A manufacturer typical 40C recommendation is not guaranteed installed ampacity'],
   'remaining_budget_must_cover':['Tab5 including startup','logic and STOP auxiliary','battery-control and other losses'],
   'short_circuit_current_A':None,'wire_thermal_withstand_A2s':None,
   'decision':'10A remains a candidate; full load and protection coordination unproven',
   'manufacturing_release':False}
out=ROOT/'validation/battery_inlet_v1';out.mkdir(exist_ok=True)
(out/'report.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps(rows,indent=2))
