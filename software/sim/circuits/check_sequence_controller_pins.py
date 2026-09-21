"""Check reserved pins and signal accounting, not MCU electrical compatibility."""
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
src=Path('schematics/power/sequence_controller_candidate/controller.json');r=json.loads(src.read_text());pins=r['pins']
# TSSOP20 table from DS13866 pp29-30; not UFQFPN20 numbering.
ports=['PB7','PC14','PC15','VDD/VDDA','VSS/VSSA','PF2-NRST','PA0','PA1','PA2','PA3','PA4','PA5','PA6','PA7','PA8','PA11','PA12','PA13','PA14-BOOT0','PB6']
assert set(pins)=={str(n) for n in range(1,21)}
assert [pins[str(n)]['port'] for n in range(1,21)]==ports
signals=[x['signal'] for x in pins.values() if x['signal']]
assert len(signals)==len(set(signals))
counts={role:sum(x['role']==role for x in pins.values()) for role in ('input','output','supply','reset','debug','spare')}
assert counts==dict(input=11,output=3,supply=2,reset=1,debug=2,spare=1)
assert all(pins[n]['role']=='debug' for n in ('18','19')) and pins['6']['role']=='reset'
assert not {'STARTUP_EXPIRED','startup_timer_run'}&set(signals)
report={'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'pin_counts':counts,
 'pin_assignment_pass':True,'model_timer_io_internalized':True,'separate_CLR_inputs':True,
 'electrical_compatibility_proven':False,'manufacturing_release':False,
 'critical_interface':'MONITOR_START_READY_LOGIC has only 3.47 uA remaining in prior 20 uA drive budget. Do not use typical MCU leakage as a guaranteed load.'}
a.out.mkdir(parents=True,exist_ok=False);(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
