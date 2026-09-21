"""Two flip-flop connection semantics with bounded abstract delays."""
import json
from pathlib import Path
out=Path('validation/manual_rearm_two_ff_v1')
rows=[]
for debounce in (20,50,80):
 for qualification in (180,300,420):
  arm=enable=False;raw_old=debounced=clk_old=timer_old=False
  stable=0;released=None;first=None
  for t in range(1100):
   healthy=20<=t<1000
   raw=10<=t<120 or t>=700
   if raw!=raw_old:stable=t
   if t-stable>=debounce:debounced=raw
   if healthy and not raw and not debounced:
    if released is None:released=t
   else:released=None
   timer=released is not None and t-released>=qualification
   old_arm=arm
   if not healthy:arm=enable=False
   else:
    if timer and not timer_old:arm=True
    if debounced and not clk_old:enable=old_arm
   if enable and first is None:first=t
   assert not enable or (700<=t<1000)
   raw_old=raw;clk_old=debounced;timer_old=timer
  assert first==700+debounce
  assert not enable and not arm
  rows.append({'debounce_ms':debounce,'qualification_ms':qualification,'first_enable_ms':first,'stop_clears_both':True})
(out/'report.json').write_text(json.dumps({'cases':rows,'connection_logic_pass':True,'hardware_verified':False},indent=2)+'\n')
print('9 delay combinations passed; hardware not verified')
