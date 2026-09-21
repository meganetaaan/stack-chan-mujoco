"""Two TPS3700 source-voltage windows; static corners, not fault response proof."""
import argparse,itertools,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
p.add_argument('--ov-top-ohm',type=float,default=127000)
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
plan={'normal_source_comparison_V':[4.75,5.25],'resistor_total_tolerance_assumption':.01,
 'UV_top_ohm':102000,'OV_top_ohm':a.ov_top_ohm,'bottom_ohm':10000,
 'positive_threshold_V':[.396,.404],'negative_threshold_V':[.387,.400],
 'UV_input_leakage_abs_A':25e-9,'OV_input_leakage_abs_A':15e-9,
 'decision_basis':'Allow normal 5V +/-5% source; early low-voltage indication above 3.7V servo limit, final allowable branch drop and fault timing remain unqualified',
 'source':'https://www.ti.com/lit/ds/symlink/tps3700.pdf',
 'limits':['Published input leakage test points applied as comparison; application coverage needs review','Monitor supply valid for 450us before status use','Does not measure voltage at servo terminals']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
results={}
for mode,rt,leak in [('UV',102000,25e-9),('OV',a.ov_top_ohm,15e-9)]:
 ranges={}
 for edge,threshold in [('rising',[.396,.404]),('falling',[.387,.400])]:
  vals=[v*(1+top/bottom)+current*top for v,top,bottom,current in itertools.product(threshold,[rt*.99,rt*1.01],[9900,10100],[-leak,leak])]
  ranges[edge]=[min(vals),max(vals)]
 pinmax=(12.6/(rt*.99)+leak)/(1/(rt*.99)+1/10100)
 results[mode]={'thresholds_V':ranges,'sense_at_12p6_max_V':pinmax}
assert results['UV']['thresholds_V']['rising'][1]<4.75
assert results['OV']['thresholds_V']['rising'][0]>5.25
assert all(x['sense_at_12p6_max_V']<6.5 for x in results.values())
parts=[]
for side in ('LEFT','RIGHT'):
 valid=side+'_SOURCE_WINDOW_OD'
 parts.append({'reference':side+'_U_WINDOW','part':'TPS3700DDCR','pins':{'1':valid,'2':'GND','3':side+'_SOURCE_UV_SENSE','4':side+'_SOURCE_OV_SENSE','5':'STOP_AUX3V3','6':valid}})
 for mode,rt in [('UV',102000),('OV',a.ov_top_ohm)]:
  sense=side+'_SOURCE_'+mode+'_SENSE'
  for suffix,val,nets in [('TOP',rt,[side+'_REGULATOR_OUT',sense]),('BOTTOM',10000,[sense,'GND'])]:
   parts.append({'reference':side+'_R_SOURCE_'+mode+'_'+suffix,'part':None,'value_ohm':val,'total_tolerance_budget':.01,'pins':dict(zip(['1','2'],nets))})
 parts.append({'reference':side+'_R_WINDOW_PULLUP','part':None,'value_ohm':10000,'pins':{'1':'STOP_AUX3V3','2':valid}})
 parts.append({'reference':side+'_C_WINDOW','part':None,'value_F':1e-7,'pins':{'1':'STOP_AUX3V3','2':'GND'}})
assembly={'parts':parts,'interfaces':{'STOP_AUX3V3':'Dedicated monitor supply; startup inhibition required','LEFT_SOURCE_WINDOW_OD':'Raw OD voltage-window status, not sequencer-qualified','RIGHT_SOURCE_WINDOW_OD':'Raw OD voltage-window status, not sequencer-qualified'},'manufacturing_release':False}
(a.out/'connectivity.json').write_text(json.dumps(assembly,indent=2)+'\n')
(a.out/'report.json').write_text(json.dumps({'results':results,'normal_no_trip_comparison_pass':True,'normal_recovery_comparison_pass':results['OV']['thresholds_V']['falling'][0]>5.25,'whole_power_qualified':False},indent=2)+'\n');print(json.dumps(results))
