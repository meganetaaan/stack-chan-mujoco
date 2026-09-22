"""Expose signal-selection blind spots; no hardware fault qualification."""
import json
from pathlib import Path
p=Path('validation/brake_fault_observability_v1')
plan=json.loads((p/'plan.json').read_text())
# name, absorption command, measured gate high, measured branch current high
states=[('normal_idle',0,0,0),('normal_absorption',1,1,1),
        ('mos_short_after_command_off',0,0,1),('driver_stuck_high',0,1,1),
        ('detector_output_open_with_pullup',1,1,1),
        ('gate_path_open_during_regeneration',1,0,0),
        ('current_sensor_stuck_low_during_mos_short',0,0,0)]
rows=[]
for name,command,gate,current in states:
    rows.append({'state':name,'command_high':bool(command),'gate_high':bool(gate),
                 'measured_current_high':bool(current),
                 'old_low_gate_high_current':bool(not gate and current),
                 'proposed_off_command_high_current':bool(not command and current)})
report={'scope':plan['question'],'rows':rows,'all_faults_detected':False,
        'physical_timing_verified':False,'decision':'Use command mismatch for stuck-on path; independent voltage/sensor diagnostics still required'}
(p/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
