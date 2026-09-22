"""Reject PG-to-CLR startup deadlock; specify sequencing, not an IC macro-model."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path


def next_state(state, healthy, fresh_request, pg, startup_expired):
    # 'healthy' excludes PG and includes independent stop/supply/monitor validity.
    if not healthy:
        return 'FAULT'
    if state in ('OFF', 'FAULT'):
        return 'START' if fresh_request else state
    if state == 'START':
        # Conservative priority: an expired startup deadline wins over coincident PG.
        if startup_expired:
            return 'FAULT'
        return 'RUN' if pg else 'START'
    return 'RUN' if pg else 'FAULT'


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--datasheet', type=Path, required=True)
    a = p.parse_args()
    a.out.mkdir(parents=True, exist_ok=False)
    plan = {
        'question': 'Can power-good be wired directly into the enable latch clear?',
        'acceptance_before_evaluation': [
            'A healthy disabled system can accept a fresh request and begin startup',
            'Independent stop takes priority in every state',
            'PG loss after RUN cancels permission; no recovery without a fresh request',
            'Failure to establish PG requires a bounded startup deadline',
        ],
        'stop': 'One causal counterexample and finite sequencing table; no invented startup time or analog qualification',
        'source': 'https://www.ti.com/lit/ds/symlink/tps25982.pdf',
        'revision': 'SLVSEI3D May 2026',
        'source_sha256': hashlib.sha256(a.datasheet.read_bytes()).hexdigest(),
        'source_pages_1_based': [5, 6, 9, 28, 29],
    }
    (a.out / 'plan.json').write_text(json.dumps(plan, indent=2) + '\n')
    # In the disabled initial state PG=0. CLR=0 dominates every DFF clock.
    direct_trace = []
    enable = False
    for event in ('power_valid', 'release_qualified', 'fresh_press', 'wait'):
        pg = enable  # Optimistic zero-delay PG still cannot escape the initial state.
        reset_n = pg
        enable = bool(reset_n and (enable or event == 'fresh_press'))
        direct_trace.append(dict(event=event, pg=pg, reset_n=reset_n, enable=enable))
    rows = []
    for state in ('OFF', 'START', 'RUN', 'FAULT'):
        for healthy, request, pg, expired in itertools.product((False, True), repeat=4):
            nxt = next_state(state, healthy, request, pg, expired)
            assert healthy or nxt == 'FAULT'
            assert not (state == 'FAULT' and not request and nxt != 'FAULT')
            assert not (state == 'RUN' and not pg and nxt != 'FAULT')
            assert not (state == 'START' and expired and nxt != 'FAULT')
            rows.append(dict(state=state, healthy=healthy, fresh_request=request,
                             pg=pg, startup_expired=expired, next_state=nxt))
    assert next_state('OFF', True, True, False, False) == 'START'
    assert next_state('START', True, False, True, False) == 'RUN'
    assert not any(row['enable'] for row in direct_trace)
    report = {
        'direct_pg_to_reset': 'rejected_startup_deadlock',
        'direct_counterexample': direct_trace,
        'pg_pin': 13,
        'dedicated_fault_pin_present': False,
        'dc_comparisons_not_qualification': {
            'PG_unpowered_low_max_V_at_26uA': .786,
            'pullup_current_A_at_3p393V_99kohm_and_0p786V': (3.393-.786)/99000,
            'including_3uA_powered_input_comparison_A': (3.393-.786)/99000 + 3e-6,
            'PG_high_leakage_max_A_at_published_test': 1.7e-6,
            'shared_reset_high_lower_comparison_V': 3.207 - 101000*(3.3e-6+1.7e-6),
        },
        'abstract_transition_count': len(rows),
        'physical_circuit_qualified': False,
        'unresolved': [
            'Fresh request must come from qualified release then press, not a held button',
            'Startup deadline derived from actual power stage and energy limits; no numeric value assigned',
            'PG receiver thresholds, pullup, unpowered pin current and timing',
            'Independent absolute servo overvoltage detection; PG is not a 6V clamp',
            'Hardware state storage/timer/output default-off implementation',
            'PG stuck-high needs independent coverage, not solved by sequencing',
        ],
    }
    (a.out/'transitions.json').write_text(json.dumps(rows, indent=2)+'\n')
    (a.out/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
