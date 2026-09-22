"""LT4363 series-clamp sizing at stated datasheet comparison points."""
import argparse,itertools,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
plan={'controller_candidate':'LT4363IMS-1#PBF','source':'https://www.analog.com/media/en/technical-documentation/data-sheets/4363fb.pdf','revision':'Rev. C (document content; URL retains fb)',
 'normal_source_max_V':5.25,'servo_max_V':6.,'battery_feedthrough_comparison_V':12.6,
 'feedback_top_ohm':33200,'feedback_bottom_ohm':10000,'feedback_total_tolerance_allocation':.01,
 'sense_resistor_ohm':.0082,'sense_total_tolerance_allocation':.01,
 'VFB_test_range_V':[1.25,1.3],'IFB_test_abs_A':1e-6,'sense_test_range_V':[.045,.055],
 'test_point_limits':['FB range at VCC12V GATE12V OUT8V; actual 5V rail coverage must be established.', 'Sense range at VCC12V OUT3..12V; do not assume it covers all normal/fault supply states.', '1us maximum OV delay is specified for FB step0..1.5V with OUT0V, not a complete clamping transient guarantee.']}
values=[v*(1+hi/lo)+i*hi for v,hi,lo,i in itertools.product([1.25,1.3],[33200*.99,33200*1.01],[10000*.99,10000*1.01],[-1e-6,1e-6])]
lo,hi=min(values),max(values);imin=.045/(.0082*1.01);imax=.055/(.0082*.99)
envelope=json.loads(Path('validation/model_dc_envelope_v2/report.json').read_text())
report={'clamp_comparison_V':[lo,hi],'DC_voltage_screen_pass':lo>5.25 and hi<6.,
 'limit_comparison_A':[imin,imax],'normal_model_per_leg_A':envelope['per_leg_draw_upper_A'],
 'model_load_screen_pass':imin>envelope['per_leg_draw_upper_A'],
 'sense_loss_at_limit_max_W':.055**2/(.0082*.99),
 'pass_FET_power_requirement_comparison_W':(12.6-lo)*imax,
 'energy_requirement_J_per_ms_at_comparison_power':(12.6-lo)*imax*.001,
 'qualified':False,'decision':'Proceed to pass-FET SOA and timing selection; no integration or manufacturing release yet.',
 'remaining':['Select MOSFET with applicable linear SOA at hot initial temperature, not only low RDS(on).', 'Select sense resistor and timer from actual energy/time limits; no arbitrary shutdown time.', 'Verify gate drive at low input, reverse current path, rail drop and startup.', 'Keep load-side regeneration absorption: a series clamp cannot absorb energy injected downstream.', 'Check fault latching and manual rearm interface; do not assume existing eFuse PG/FLT wiring is compatible.']}
assert report['DC_voltage_screen_pass'] and report['model_load_screen_pass']
a.out.mkdir(parents=True,exist_ok=False)
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
