"""Composed settled sequencing reference: fault memory is not a held latch clear."""
import argparse,hashlib,itertools,json
from pathlib import Path


def advance(mode, permission, healthy, new_press, pg, expired):
    # new_press represents the existing release-qualified fresh-button event.
    # One step models a settled observation; no physical duration is implied.
    clear_before = not healthy or mode == 'CLEAR'
    permission = False if clear_before else permission or new_press
    if not healthy:
        mode = 'CLEAR'
    elif mode == 'CLEAR':
        if not permission:
            mode = 'WAIT_NEW_PRESS'
    elif mode in ('OFF', 'WAIT_NEW_PRESS'):
        if permission:
            mode = 'START'
    elif mode == 'START':
        if not permission or expired:
            mode = 'CLEAR'
        elif pg:
            mode = 'RUN'
    elif mode == 'RUN':
        if not permission or not pg:
            mode = 'CLEAR'
    clear_after = not healthy or mode == 'CLEAR'
    if clear_after:
        permission = False
    request = healthy and mode in ('START', 'RUN')
    return mode, permission, {'sequence_enable_request': request,
                              'sequence_clear_asserted': mode == 'CLEAR',
                              'reset_n': not clear_after,
                              'physical_command_boolean': request and permission and not clear_after}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    root=Path(__file__).resolve().parents[3];assembly=root/'schematics/power/manual_rearm_revF/assembly.json'
    plan={'question':'Can the sequencer cancel permission and still allow a new manual request without PG/clear deadlock?',
          'acceptance':['Fault drops request and clears permission','Clear request releases only after permission-low acknowledgement','Release of clear never erases fault waiting state or grants enable','New qualified press is required after recovery','Persistent independent unhealthy input inhibits every mode'],
          'stop':'Finite Boolean state/transition exploration and concrete traces; no timer value or circuit timing inference',
          'assembly_sha256':hashlib.sha256(assembly.read_bytes()).hexdigest(),
          'scope':'Design reference only. CLEAR acknowledgement and pulse width require real hardware implementation.'}
    (a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    modes=('OFF','START','RUN','CLEAR','WAIT_NEW_PRESS');checks=0
    for mode,permission,healthy,new,pg,expired in itertools.product(modes,[False,True],[False,True],[False,True],[False,True],[False,True]):
        nxt,q,out=advance(mode,permission,healthy,new,pg,expired)
        assert healthy or not out['physical_command_boolean']
        if mode=='WAIT_NEW_PRESS' and not permission and not new:
            assert not out['physical_command_boolean']
        if mode=='RUN' and not pg:
            assert not out['physical_command_boolean']
        if mode=='START' and expired:
            assert not out['physical_command_boolean']
        if mode=='CLEAR':assert not out['physical_command_boolean']
        checks+=1
    events=[('new_enable',True,True,False,False),('PG_established',True,False,True,False),
            ('PG_lost',True,False,False,False),('permission_low_ack',True,False,False,False),
            ('PG_recovers_without_press',True,False,True,False),('new_qualified_press',True,True,False,False),
            ('startup_deadline',True,False,False,True),('permission_low_ack_2',True,False,False,False),
            ('held_button_no_new_event',True,False,True,False)]
    mode,q='OFF',False;trace=[]
    for event,h,new,pg,expired in events:
        mode,q,out=advance(mode,q,h,new,pg,expired)
        trace.append(dict(event=event,mode=mode,permission=q,**out))
    assert trace[4]['mode']=='WAIT_NEW_PRESS' and not trace[4]['physical_command_boolean']
    assert trace[5]['mode']=='START' and trace[5]['physical_command_boolean']
    assert not trace[-1]['physical_command_boolean']
    # Fault-latch directly driving CLR cannot accept even a qualified press.
    fault_memory=True; qualified_press=True
    wrong_permission = qualified_press and not fault_memory
    report={'transition_cases_checked':checks,'trace':trace,
            'held_fault_clear_candidate':'rejected_no_manual_recovery',
            'held_fault_clear_permission_after_new_press':wrong_permission,
            'new_interface':'SEQUENCE_CLEAR_REQUEST sink to RESET_N, asserted until ENABLE_PERMISSION low is acknowledged; separate from fault-memory state',
            'physical_implementation':False,'electrical_qualification':False,
            'remaining':['Actual PG input circuit','Startup time/energy bounds','State storage, clear sink and acknowledgement hardware','Minimum clear pulse and propagation/race analysis','Existing button/raw input and partial-power qualification']}
    (a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'transition_cases_checked':checks,'final_mode':mode,'physical_implementation':False}))


if __name__=='__main__':main()
