"""Select explicit ramp capacitor with a conditional charge-current comparison."""
import copy,csv,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'schematics/power/pack_control_ramp_candidate_v1';OUT.mkdir(exist_ok=True)
source=ROOT/'schematics/power/pack_control_input_candidate_v1/assembly.json'
a=json.loads(source.read_text());parts=copy.deepcopy(a['parts'])
u=next(p for p in parts if p['reference']=='U_CTRL_INPUT_LIMIT')
assert u['pins']['20'] is None
u['pins']['20']='CTRL_INPUT_DVDT'
u['intentionally_unused_open_pins'].remove(20)
parts.append({'reference':'C_CTRL_INPUT_DVDT','part':'GRM31C5C1H104JA01L','value_F':1e-7,
              'pins':{'1':'CTRL_INPUT_DVDT','2':'CTRL_INPUT_PROTECT_RTN'},
              'note':'Existing 100nF C0G candidate reused; total +/-6% comparison allocation, not qualified process bound'})
values={'GRM31C5C1H104JA01L':(1e-7,1.06),'GRM31CR71H475KA12L':(4.7e-6,1.10*1.15),
        'MKS2C042201K00JSSD':(2.2e-6,1.06)}
caps=[]
for p in parts:
 if p['part'] in values and set(p['pins'].values()) in [{'CONTROL_INPUT_PROTECTED','PACK_RETURN'},{'CTRL3V3','PACK_RETURN'}]:
  c,factor=values[p['part']]
  caps.append({'reference':p['reference'],'nominal_F':c,'upper_comparison_F':c*factor})
cmax=sum(p['upper_comparison_F'] for p in caps)
rates={'open_typical':23.9/.0016,'100nF_nominal':24.6*4.7e-6/1e-7,
       '100nF_slow_comparison':23.75*4e-6/(1e-7*1.06),
       '100nF_fast_comparison':25.5*5.5e-6/(1e-7*.94)}
budget_path=ROOT/'validation/pack_controller_budget_v1/report.json'
budget=json.loads(budget_path.read_text());load=budget['rows'][-1]['partial_screen_sum_A']
rows=[{'case':name,'slew_V_s':rate,'capacitor_current_A':cmax*rate,
       'with_partial_load_A':cmax*rate+load,'ramp_0_to12_6_s':12.6/rate} for name,rate in rates.items()]
a.update(parts=parts,status='explicit_ramp_candidate_not_startup_qualified',
         source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [source,budget_path]})
a['remaining']=[s for s in a['remaining'] if 'dVdT open' not in s]
a['remaining'].insert(0,'Verify TPS709 turn-on and current-limited charging; do not assume output slope tracks eFuse input slope')
a['checks']['ramp_cap_to_RTN']=parts[-1]['pins']['2']==u['pins']['15']
(OUT/'assembly.json').write_text(json.dumps(a,indent=2)+'\n')
report={'capacitor_inventory':caps,'upper_comparison_total_F':cmax,'rows':rows,
 'partial_load_A':load,'nominal_ILIM_A':12/118,
 'assumptions':['C0G and film +/-6% total allocation unqualified',
                'X7R positive tolerance10% times temperature15%; combined actual capacitance unqualified',
                'LDO output follows input ramp; delayed internal startup could violate this assumption',
                'MCU/peripheral/logic/ground current budget incomplete',
                'TI ramp electrical table test at24V, not full validation at3S'],
 'decision':'Prefer100nF over open pin; open typical ramp exceeds nominal current limit under assumed concurrent charging',
 'startup_pass':None,'manufacturing_release':False}
(OUT/'ramp_report.json').write_text(json.dumps(report,indent=2)+'\n')
for name,header,rows_out in [('bom.csv',['reference','part'],[(p['reference'],p['part']) for p in parts]),
 ('connections.csv',['reference','pin','net'],[(p['reference'],pin,n or '') for p in parts for pin,n in p['pins'].items()])]:
 with (OUT/name).open('w',newline='') as f:
  w=csv.writer(f,lineterminator='\n');w.writerow(header);w.writerows(rows_out)
print(json.dumps({'capacitance_F':cmax,'rows':rows},indent=2))
