"""Open-loop thermal sensitivity projection, not a continuous-duty rating."""
import argparse
import itertools
import json
from pathlib import Path
import numpy as np
from scipy.signal import lfilter
from drive import CATALOG


def response(loss,dt,resistance,capacity,ambient):
    decay=np.exp(-dt/(resistance*capacity))
    return ambient+lfilter([resistance*(1-decay)],[1,-decay],loss,axis=0)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--trace',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if a.out.exists():p.error('new output required')
    a.out.mkdir(parents=True)
    with np.load(a.trace) as source:
        times=source['time'];loss=source['copper_loss_W']+source['gear_loss_W']+source['idle_loss_W']
        currents=source['motor_current_A']
    dt=float(np.median(np.diff(times)))
    if not np.isfinite(loss).all() or np.any(loss<0) or not np.allclose(np.diff(times),dt,atol=1e-8):raise ValueError('invalid loss waveform')
    duration=600.;count=round(duration/dt)
    repeated=np.tile(loss,(int(np.ceil(count/len(loss))),1))[:count]
    aparams=CATALOG['assumptions'];threshold=aparams['case_temperature_analysis_limit_C'];rows=[]
    for resistance,capacity,ambient in itertools.product(aparams['thermal_resistance_K_W']['cases'],aparams['thermal_capacity_J_K']['cases'],[25.,40.]):
        temp=response(repeated,dt,resistance,capacity,ambient)
        indices=np.flatnonzero(np.any(temp>=threshold,axis=1))
        row={'thermal_resistance_K_W':resistance,'thermal_capacity_J_K':capacity,'ambient_C':ambient,
             'peak_predicted_case_C':float(temp.max()),'time_to_screen_limit_s':float((indices[0]+1)*dt) if len(indices) else None,
             'within_screen_for_600s':not len(indices)}
        rows.append(row)
    peak_rows=[]
    for name,spec in CATALOG['models'].items():
        resistance_e=5./spec['stall_current_A'][1]
        full_peak_loss=resistance_e*spec['analysis_current_limit_A']**2+5.*spec['standby_current_A']
        for rth,ambient in itertools.product(aparams['thermal_resistance_K_W']['cases'],[25.,40.]):
            conditional_limit=np.sqrt(max(0.,(threshold-ambient)/rth-5.*spec['standby_current_A'])/resistance_e)
            peak_rows.append({'motor':name,'thermal_resistance_K_W':rth,'ambient_C':ambient,
                              'predicted_steady_case_at_peak_current_C':ambient+rth*full_peak_loss,
                              'conditional_stationary_RMS_current_limit_A':float(conditional_limit),
                              'manufacturer_continuous_torque_rating_Nm':None})
    report={'scope':__doc__,'projection_duration_s':duration,'source_cycle_s':len(loss)*dt,
            'cycle_motor_RMS_current_A':np.sqrt(np.mean(currents**2,axis=0)).tolist(),
            'cycle_mean_loss_W':np.mean(loss,axis=0).tolist(),'rows':rows,'peak_current_hold_cases':peak_rows,
            'limitations':['thermal parameters are engineering scenarios, not measured bounds',
                          'repeat-cycle projection does not feed temperature derating back into motion',
                          'case temperature proxy cannot certify winding hot spots',
                          'conditional current limits are not manufacturer continuous ratings']}
    (a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'cases':len(rows),'within_screen':sum(r['within_screen_for_600s'] for r in rows),
                      'worst_case_C':max(r['peak_predicted_case_C'] for r in rows),
                      'peak_hold_can_exceed_screen':any(r['predicted_steady_case_at_peak_current_C']>threshold for r in peak_rows)}))


if __name__=='__main__':main()
