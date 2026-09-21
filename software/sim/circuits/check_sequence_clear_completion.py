"""Verify clear-completion contract without making latch response instantaneous."""
import argparse
import itertools
import json
from pathlib import Path


def complete(healthy, armed, permission, reset_low_observed, hold_done):
    return healthy and not armed and not permission and reset_low_observed and hold_done


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args(); a.out.mkdir(parents=True,exist_ok=False)
    rows=[]
    for values in itertools.product([False,True],repeat=5):
        h,armed,permission,seen,held=values
        done=complete(*values)
        rows.append(dict(healthy=h,armed=armed,permission=permission,reset_low_observed=seen,hold_done=held,clear_may_release=done))
        if done: assert h and not armed and not permission and seen and held
    # Independent observations; no assumed nanosecond propagation delay.
    sequence=[('fault_entry',True,True,True,False,False),
              ('permission_clears_first',True,True,False,True,False),
              ('both_outputs_low_but_width_unqualified',True,False,False,True,False),
              ('width_qualified_and_both_clear',True,False,False,True,True)]
    trace=[dict(event=e,clear_may_release=complete(h,armed,q,seen,held)) for e,h,armed,q,seen,held in sequence]
    assert [t['clear_may_release'] for t in trace]==[False,False,False,True]
    # Previous single-ack condition accepts the second event: underconstrained,
    # not evidence that actual SN74HCS74 silicon fails under a valid pulse.
    report={'cases':rows,'trace':trace,'old_single_ack_accepts_incomplete_clear':not sequence[1][3],
            'all_cases':len(rows),'physical_timing_proven':False,'hardware_implemented':False,
            'limits':['observed reset low and hold_done must come from qualified implementation, not ideal assignment',
                      'hold starts at both actual CLR pins meeting Low threshold',
                      'recovery/setup interval before next clock is separate',
                      'loss of valid power invalidates acknowledgements']}
    (a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'cases':len(rows),'old_contract_underconstrained':report['old_single_ack_accepts_incomplete_clear']}))

if __name__=='__main__': main()
