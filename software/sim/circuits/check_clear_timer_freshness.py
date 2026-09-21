"""Per-request clear timer protocol; sampled logic model, not a hardware timing proof."""
import argparse,json
from pathlib import Path
from check_sequence_clear_completion import complete as previous_complete

class ClearCycle:
    def __init__(self): self.phase='IDLE'
    def step(self,request,healthy,armed,permission,clr_low,timer_done):
        if not request:self.phase='IDLE'
        elif not healthy:self.phase='RESET_TIMER'
        elif self.phase=='IDLE':self.phase='RESET_TIMER'
        elif self.phase=='RESET_TIMER':
            if not timer_done:self.phase='QUALIFY'
        elif not clr_low:self.phase='RESET_TIMER'
        qualifier=request and healthy and clr_low and self.phase=='QUALIFY'
        complete=qualifier and timer_done and not armed and not permission
        return {'phase':self.phase,'reset_low_valid':bool(qualifier),'clear_may_release':bool(complete)}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
 # Tuple: request, healthy, ARMED, permission, both physical CLR low, timer DONE.
 scenarios={
 'stale_high':([(1,1,0,0,1,1)]*4,[False]*4),
 'fresh_cycle':([(1,1,1,1,0,1),(1,1,1,0,1,0),(1,1,0,0,1,0),(1,1,0,0,1,1)],[False,False,False,True]),
 'second_request_stale_high':([(1,1,0,0,1,0),(1,1,0,0,1,0),(1,1,0,0,1,1),(0,1,0,0,1,1),(1,1,0,0,1,1),(1,1,0,0,1,1)],[False,False,True,False,False,False]),
 'health_loss_requires_new_low':([(1,1,0,0,1,0),(1,1,0,0,1,0),(1,0,0,0,1,1),(1,1,0,0,1,1),(1,1,0,0,1,0),(1,1,0,0,1,1)],[False,False,False,False,False,True]),
 'clr_dropout_requires_new_low':([(1,1,0,0,1,0),(1,1,0,0,1,0),(1,1,0,0,0,1),(1,1,0,0,1,1)],[False]*4),
 'latch_outputs_must_both_clear':([(1,1,1,1,1,0),(1,1,1,1,1,0),(1,1,1,0,1,1),(1,1,0,1,1,1),(1,1,0,0,1,1)],[False,False,False,False,True])}
 traces={}
 for name,(events,expected) in scenarios.items():
  cycle=ClearCycle();trace=[]
  for event in events:trace.append({'input':event,**cycle.step(*event)})
  assert [x['clear_may_release'] for x in trace]==expected,name
  traces[name]=trace
 report={'traces':traces,'scenario_count':len(traces),'request_entry_forces_timer_reset_phase':True,'old_combinational_contract_accepts_stale_high':previous_complete(True,False,False,True,True),'hardware_implemented':False,'physical_timing_proven':False,'limits':['Observation protocol, not a clock frequency or synchronizer design','RESET_LOW_VALID generation, MR response and DONE sampling must be implemented','No ideal assignment of latch outputs','Noise, glitches, metastability and threshold validity not modeled','CLR-to-clock recovery still separate']}
 (a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'scenarios':len(traces),'passed':True,'hardware_implemented':False}))
if __name__=='__main__':main()
