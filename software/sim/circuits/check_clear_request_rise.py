"""Analytic RC screen of a released sequencer output; capacitances are scenarios."""
import argparse,json,math
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
rail=3.207;r=101000.;vih=2.;vil=.8
rows=[]
for cap in (1e-12,5e-12,10e-12):
 tau=r*cap
 dt=tau*math.log((rail-vil)/(rail-vih))
 rows.append({'assumed_total_capacitance_F':cap,'logic_band_crossing_s':dt,'average_s_per_V':dt/(vih-vil),'local_s_per_V_at_VIH':tau/(rail-vih)})
result={'model':'stiff rail, ideal released driver, lumped RC, zero leakage',
        'user_requirement':'defined stop and no unintended restart',
        'design_assumptions':{'rail_V':rail,'pullup_max_ohm':r,'scenario_capacitances_not_measured':True},
        'manufacturer_lvc_edge_limit_s_per_V':1e-8,
        'local_slope_cap_limit_F':1e-8*(rail-vih)/r,
        'rows':rows,'qualification':False,
        'decision':'Do not rely on 100k pullup directly driving LVC1G06 during driver release; design input conditioning before substitution',
        'limits':['Illustrative capacitances are not production minima/maxima',
                  'Local slope screen is not a substitute for manufacturer waveform definition',
                  'Rail ramps, leakage, coupling and brownout excluded',
                  'No automatic proof of hardware failure or current AUP qualification']}
(a.out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
