"""DC corner comparison of eFuse PG to TPS3700 INA+ receiver; not transient validation."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--out',type=Path,required=True)
p.add_argument('--detector-pdf',type=Path,required=True)
p.add_argument('--efuse-pdf',type=Path,required=True)
p.add_argument('--pg-leak-max-a',type=float,default=1.7e-6)
p.add_argument('--pg-low-max-v',type=float,default=.786)
p.add_argument('--efuse-part',default='TPS259823')
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
# Sign convention: positive current leaves PG/INA into the corresponding IC.
rows=[]
for supply,rp,rt,rb,ipg,ii in itertools.product([3.207,3.393],[148500,151500],[990000,1010000],[326700,333300],[0,a.pg_leak_max_a],[-25e-9,25e-9]):
    # KCL solved exactly after eliminating divider node.
    pg=(supply/rp-ipg-ii*rb/(rt+rb))/(1/rp+1/(rt+rb))
    sense=(pg-ii*rt)*rb/(rt+rb)
    low_sense=(a.pg_low_max_v-ii*rt)*rb/(rt+rb)
    # All pullup current plus possible comparator source leakage is an upper
    # bound on PG sink current; divider return to ground only reduces it.
    sink_bound=supply/rp+25e-9
    rows.append(dict(supply_V=supply,rp_ohm=rp,rt_ohm=rt,rb_ohm=rb,pg_leak_A=ipg,input_current_A=ii,pg_high_V=pg,sense_high_V=sense,sense_low_upper_V=low_sense,pg_sink_upper_A=sink_bound))
result={'efuse_part':a.efuse_part,'pg_leak_max_A':a.pg_leak_max_a,'pg_low_max_V':a.pg_low_max_v,'cases':len(rows),'sense_high_min_V':min(r['sense_high_V'] for r in rows),'sense_low_max_V':max(r['sense_low_upper_V'] for r in rows),'pg_sink_upper_A':max(r['pg_sink_upper_A'] for r in rows),'rising_threshold_max_V':.404,'falling_threshold_min_V':.387,'pg_low_test_current_A':26e-6,'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [a.detector_pdf,a.efuse_pdf]},'all_operating_conditions_qualified':False,'manufacturing_release':False}
result['conditional_dc_separation']=result['sense_high_min_V']>.404 and result['sense_low_max_V']<.387 and result['pg_sink_upper_A']<26e-6
(a.out/'report.json').write_text(json.dumps(result,indent=2)+'\n')
(a.out/'corners.json').write_text(json.dumps(rows,indent=2)+'\n')
print(json.dumps(result,indent=2))
