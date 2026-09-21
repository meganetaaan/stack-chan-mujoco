"""Verify separated fault-cause wiring and settled recovery; not transient simulation."""
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
root=Path(__file__).resolve().parents[3];src=root/'schematics/power/manual_rearm_revE/assembly.json'
d=json.loads(src.read_text());r={x['reference']:x['pins'] for x in d['parts']}
assert r['U9']['1']==r['U7']['3']==r['U11']['2']=='RAIL_HEALTH_N'
assert r['U10']['1']=='MAIN_EFUSE_EN' and r['U10']['3']==r['U11']['4']=='CLAMP_MR_5V'
assert r['U9']['1']!=r['U10']['1']
plan={'question':'Does forwarding U9 fault cause to U7 MR remove the settled threshold-mismatch restart counterexample?', 'acceptance':['Either supervisor trip clears permission','Recovery alone leaves permission cleared','Qualified new request can rearm','Normal EN low does not pull fault cause low'], 'scope':'Settled logic only, independent source5V valid; actual pulse/propagation and sequencer not qualified', 'assembly_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'static_assumptions':['LOGIC3V3 3.207..3.393V, upstream5V 4.75..5.25V','10k pullup total +/-1%','Leakage comparison at published test conditions; not all supply states']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
traces=[]
for u7,u9 in [(3.07*.985,3.07*1.015),(3.07*1.015,3.07*.985)]:
 permission=True;trace=[]
 for name,v,new in [('enabled',3.3,False),('settled_dip',3.07,False),('recovered_no_press',3.3,False),('qualified_new_press',3.3,True)]:
  cause=v>=u9;clear=(v<u7) or not cause
  if clear: permission=False
  elif new: permission=True
  trace.append({'event':name,'U9_cause_healthy':cause,'clear_permission':clear,'permission':permission,'EN_after_sequencer_honors_permission':permission and cause})
 assert not trace[2]['permission'] and trace[3]['permission']
 traces.append({'U7_threshold':u7,'U9_threshold':u9,'events':trace})
report={'retained_permission_counterexample_removed_in_settled_logic':True,'traces':traces,'static_comparisons':{'cause_high_lower_V':3.207-10100*1.3e-6,'cause_low_sink_upper_A':3.393/9900+3.393/70000+1e-6,'cause_low_upper_V':.4,'U7_MR_low_limit_V':.3*3.207,'U11_output_load_upper_A':5.25/70000,'U11_high_lower_V':4.75-.1,'U10_MR_high_upper_requirement_V':.7*5.25,'U11_low_upper_V':.1,'U10_MR_low_lower_requirement_V':.3*4.75},'electrical_qualification':False,'open_items':['U11 input thresholds across full supply interval','Full source5V supply loss and reverse-bias paths','U9 to U7 pulse width and delay; U10 clamp response','Actual sequencer must cancel POWER_ENABLE_COMMAND on permission loss','External stop/fault integration and passive exact parts']}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
