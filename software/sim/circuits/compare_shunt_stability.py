"""Compare shunt configurations under the same temperature and solder-change assumptions."""
import argparse,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
rows=[]
for name,count,value,tcr,absolute in [('WSLP25128L200FEA',1,.0082,75,.0005),('WSLF25124L000FEA',2,.004,70,0)]:
 r0=count*value;initial=[r0*.99,r0*1.01];shift=.005*initial[1]+count*absolute
 low=(initial[0]-shift)*(1-tcr*1e-6*125);high=(initial[1]+shift)*(1+tcr*1e-6*125)
 rows.append({'part':name,'quantity_per_leg':count,'nominal_total_ohm':r0,'range_after_solder_and_TCR_ohm':[low,high],
 'current_limit_A':[.045/high,.055/low],'remaining_positive_error_V':.045-4.917*high,
 'shunt_total_max_limit_loss_W':.055**2/low})
a.out.mkdir(parents=True,exist_ok=False)
report={'sources':{'WSLP':'https://www.vishay.com/docs/30122/wslp.pdf','WSLF':'https://www.vishay.com/docs/30193/wslf.pdf'},
 'WSLF_revision':'10-Jun-2026','common_comparison_temperature_C':[-55,150],
 'temperature_scope':'Intersection of documented TCR ranges; excludes 150..155C, not a relaxed robot temperature requirement.',
 'assumptions':['Initial 1% and independent same-sign extremes for both series parts; no statistical cancellation.',
 'Solder test changes transferred conditionally; actual assembly process applicability still unverified.',
 'Shared interconnect resistance is excluded from resistor-only bounds and consumes remaining error budget.'],
 'rows':rows,'decision':'Prefer evaluating two series WSLF 4mOhm parts for the LT4363 alternative; lower solder-shift sensitivity at cost of another footprint and shared interconnect.',
 'selection_complete':False,'manufacturing_release':False,
 'remaining':['Layout and Kelvin pickup for two series resistors','Full temperature and process scope','Supply/IC/FET compatibility and SOA','Part availability']}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(rows))
