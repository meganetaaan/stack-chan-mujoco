"""Conditional DC clamp sizing; reference/current test-point corrections remain open."""
import argparse,itertools,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
t=.001
# Clamp REF divider: upper30.1k, lower332k. Iref comparison includes25C max + temp deviation.
clamps=[v*(1+ra/rb)+ir*ra for v,ra,rb,ir in itertools.product([1.224,1.259],[30100*(1-t),30100*(1+t)],[332000*(1-t),332000*(1+t)],[0,0.9e-6])]
vmin,vmax=min(clamps),max(clamps)
rows=[]
for high,low in [(35700.,10000.),(3570.,1000.)]:
    trip=[];available=[]
    # Evaluate available cathode current at input where *unclamped original* pin reaches1.5V.
    # Conservative current comparison holds clamp at its upper comparison voltage.
    for rh,rl,ra,rb in itertools.product([high*(1-t),high*(1+t)],[low*(1-t),low*(1+t)],[30100*(1-t),30100*(1+t)],[332000*(1-t),332000*(1+t)]):
        vin=1.5*(1+rh/rl)
        available.append((vin-vmax)/rh-vmax/rl-vmax/(ra+rb)-.9e-6-.1e-6)
        for ref,leak in itertools.product([1.176,1.224],[-.1e-6,.1e-6]):
            # Only resistor loading included here; pre-regulation shunt current not assumed zero in qualification.
            trip.append(ref*(1+rh/rl+rh/(ra+rb))+leak*rh)
    rows.append({'OV_high_ohm':high,'OV_low_ohm':low,'trip_with_clamp_resistor_loading_only_V':[min(trip),max(trip)],'minimum_available_cathode_current_at_original_1_5V_crossing_A':min(available),'exceeds_100uA_comparison':min(available)>100e-6})
r={'clamp_divider_ohm':[30100,332000],'clamp_voltage_comparison_V':[vmin,vmax],'rows':rows,'qualified':False,'limits':['Reference limits are at10mA, actual cathode current differs; dynamic impedance is not a complete DC correction guarantee','Pre-regulation cathode leakage at actual REF voltage not bounded','Capacitance, stability, startup and transient overshoot not modeled','Iref0..0.9uA is a sizing comparison using0.5uA plus0.4uA deviation, not whole-state guarantee']}
(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
