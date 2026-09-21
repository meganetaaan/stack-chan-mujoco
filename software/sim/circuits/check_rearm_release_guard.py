"""Bounded reference logic for rejecting delayed presses, not firmware."""
import json
from pathlib import Path
p=Path('validation/manual_rearm_release_guard_v1')
rows=[]
for delay in (20,50,80):
    for press_time in (0,10,19):
        # Fault clears at20; held until120; new valid press at320.
        q=False;armed=False;release_since=None;stable_since=0;last_raw=False;deb=False;last_deb=False
        first_enable=None
        for t in range(500):
            raw=press_time<=t<120 or t>=320
            healthy=t>=20
            if raw!=last_raw:stable_since=t
            if t-stable_since>=delay:deb=raw
            if not healthy:
                q=False;armed=False;release_since=None
            else:
                if not armed:
                    if not raw and not deb:
                        if release_since is None:release_since=t
                        if t-release_since>80:armed=True
                    else:release_since=None
                if armed and raw and deb and not last_deb:q=True
            if q and first_enable is None:first_enable=t
            assert not q or t>=320
            last_raw=raw;last_deb=deb
        assert first_enable is not None
        rows.append({'debounce_ms':delay,'faulted_press_ms':press_time,'first_enable_ms':first_enable})
(p/'report.json').write_text(json.dumps({'cases':rows,'counterexample_rejected':True,'new_press_accepted':True,'hardware_verified':False,'time_grid_ms':1,'qualification':'healthy raw and debounced release continuously longer than 80 ms; abstract bound not selected timer'},indent=2)+'\n')
print(json.dumps({'cases':len(rows),'counterexample_rejected':True,'new_press_accepted':True,'hardware_verified':False}))
