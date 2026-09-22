"""Check revF's physical pin mapping and settled command cancellation."""
import argparse,hashlib,itertools,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
root=Path(__file__).resolve().parents[3];source=root/'schematics/power/manual_rearm_revF/assembly.json'
d=json.loads(source.read_text());parts={x['reference']:x for x in d['parts']};pins={k:v['pins'] for k,v in parts.items()}
assert parts['U3']['part']=='SN74HCS11PWR'
assert [pins['U3'][n] for n in ('3','4','5','6')]==['ENABLE_PERMISSION','SEQUENCE_ENABLE_REQUEST','RESET_N','POWER_ENABLE_COMMAND']
assert pins['U8']['2']==pins['U3']['6']
assert 'POWER_ENABLE_COMMAND' not in d['interfaces']
plan={'question':'Can retained permission or reset cancel EN command despite a stuck-high sequencer request?', 'acceptance':['No command when permission or RESET_N is low, regardless of sequencer request','Recovery without a new qualified press leaves command low','No added parts for available U3 gate','Account for extra reset fanout'], 'stop':'Pin-mapped truth table, settled fault/recovery trace and static load comparison; no analog or pulse timing claim', 'assembly_sha256':hashlib.sha256(source.read_bytes()).hexdigest()}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
table=[dict(permission=x,sequence_request=y,reset_n=z,command=x and y and z) for x,y,z in itertools.product([False,True],repeat=3)]
for row in table:
 if not row['permission'] or not row['reset_n']:assert not row['command']
trace=[];permission=True
for event,reset,new in [('running',True,False),('rail_fault_asserted',False,False),('recovered_no_press',True,False),('qualified_new_press',True,True)]:
 if not reset:permission=False
 elif new:permission=True
 trace.append(dict(event=event,reset_n=reset,permission=permission,sequence_request=True,command=permission and reset))
assert not trace[2]['command'] and trace[3]['command']
reset_inputs=[f'{ref}.{pin}' for ref, pinset in [('U3',['1','2','3','4','5','9','10','11','13']),('U6',['1','2','3','4','10','11','12','13'])] for pin in pinset if pins[ref][pin]=='RESET_N']
assert len(reset_inputs)==4
report={'truth_table':table,'stuck_high_request_trace':trace,'physical_gate_present':True,'reset_input_pins':reset_inputs,'static_comparison':{'gate_output_load_A':3.393/(220000*.99)+1e-6,'HCS_output_test_load_A':20e-6,'reset_high_lower_comparison_V':3.207-101000*(len(reset_inputs)*1e-6+.3e-6),'reset_low_sink_upper_comparison_A':3.393/99000+len(reset_inputs)*1e-6},'electrical_qualification':False,'remaining':['HCS input thresholds across actual rail and RESET_N loading','Unpowered/partial-power behavior','Propagation and fault-pulse capture','Real startup timeout and PG fault latching','All other external stop/monitor interfaces']}
assert report['static_comparison']['gate_output_load_A']<20e-6
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'reset_inputs':reset_inputs,'static_comparison':report['static_comparison'],'electrical_qualification':False},indent=2))
