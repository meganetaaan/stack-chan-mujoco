"""Compare resistor loading and clamp current; no transient qualification."""
import argparse, itertools, json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--out', type=Path, required=True)
a=p.parse_args(); a.out.mkdir(parents=True, exist_ok=False)
# Existing source targets, not newly relaxed acceptance thresholds.
criteria={'normal_max_V':5.25,'servo_max_V':6.0,'pin_max_V':1.5,'clamp_min_current_A':0.0001}
rows=[]
for high,low,upper,lower in [(35700,10000,1000,20000),(35700,10000,10000,200000),(3570,1000,1000,20000),(3570,1000,10000,200000)]:
    trips=[]; clamps=[]; currents=[]
    for rh,rl,ra,rb in itertools.product(*[[r*.999,r*1.001] for r in (high,low,upper,lower)]):
        for ref,leak in itertools.product([1.176,1.224],[-.1e-6,.1e-6]):
            trips.append(ref*(1+rh/rl+rh/(ra+rb))+leak*rh)
        for vref,iref in itertools.product([1.215,1.265],[0,.9e-6]):
            vc=vref*(1+ra/rb)+iref*ra
            clamps.append(vc)
            # At source voltage where unregulated loaded divider reaches pin limit.
            vin=1.5*(1+rh/rl+rh/(ra+rb))
            currents.append((vin-vc)/rh-vc/rl-vc/(ra+rb)-iref-.1e-6)
    rows.append({'divider_ohm':[high,low],'clamp_feedback_ohm':[upper,lower],
      'resistor_only_trip_V':[min(trips),max(trips)],'conditional_clamp_V':[min(clamps),max(clamps)],
      'minimum_cathode_current_at_loaded_pin_limit_A':min(currents),
      'resistor_loading_screen_pass':min(trips)>5.25 and max(trips)<6,
      'conditional_clamp_screen_pass':min(clamps)>1.224 and max(clamps)<1.5 and min(currents)>=.0001})
r={'criteria':criteria,'candidate':'TLV431AI; not selected for assembly','source':'https://www.ti.com/lit/ds/symlink/tlv431.pdf','source_revision':'SLVS139Z June 2024 sections 5.3 and 5.6','rows':rows,'qualified':False,'limits':['Feedback resistors load the OVLO divider even before regulation. Trip values omit unknown pre-regulation cathode current and are not guaranteed trip bounds.','Reference range 1.215..1.265V is specified at 10mA; actual lower current accuracy remains unbounded here.','Iref 0..0.9uA is a comparison envelope, not a whole-state guarantee.','Only initial resistor tolerance is covered; temperature and aging need allocation.','No capacitance, stability or transient overshoot proof; do not integrate on this screen alone.']}
(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps(rows,indent=2))
