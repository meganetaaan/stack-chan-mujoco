"""Settled open-trace receiver voltage, no capacitance or response-time assumption."""
import argparse,itertools,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
rows=[{'Rbottom_ohm':r,'receiver_current_A':i,'sense_open_V':-i*r} for r,i in itertools.product([326700,333300],[-25e-9,25e-9])]
r={'fault':'Open PG trace between source-side pullup and receiver top resistor','cases':rows,'maximum_sense_V':max(x['sense_open_V'] for x in rows),'required_falling_threshold_min_V':.387,'conditional_low':max(x['sense_open_V'] for x in rows)<.387,'qualification':False,'limits':['Leakage-only settled comparison; negative voltage may be clamped by actual input protection','No detection-time claim; capacitance is not qualified','Open eFuse pin before source pullup remains undetectable','Receiver power validity, shared ground, resistor failures and stuck high not covered']}
(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n')
