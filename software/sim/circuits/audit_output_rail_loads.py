"""Account output-fed resistor paths separately from direct pullups."""
import argparse,hashlib,json
from pathlib import Path
from assembly_net_aliases import net_aliases
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--assembly',type=Path,default=Path('schematics/power/servo_power_clear_pullup_candidate_v1/assembly.json'));p.add_argument('--direct-report',type=Path,default=Path('validation/direct_rail_loads_v2/report.json'));a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
source=a.assembly;direct=a.direct_report
assembly=json.loads(source.read_text());parts={x['reference']:x for x in assembly['parts']};aliases=net_aliases(assembly)
def same(a,b):return aliases.get(a,a)==aliases.get(b,b)
plan={'scope':'Selected output-fed passive loads under valid 3.207..3.393V rail; all high-source voltages bounded by 3.393V.', 'resistance_tolerance_assumption':.01,'paths':['U3 output R6','U8 output R7 with dual EN pulldowns or active clamp','U_MONITOR_RX output R_MONITOR_RX_OFF','Future MCU R_SEQUENCE_OFF'], 'stop':'One netlist-checked calculation; no IC internal or dynamic current model.', 'limits':['Output-stage supply current beyond delivered load excluded','Future MCU is not integrated; its resistor budget is reserved separately','Each upper bound combined independently, not a reachable single state','No external overvoltage or negative-voltage fault']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
rows=[]
for driver,pin,resistor,value in [('U3','6','R6',220000),('U_MONITOR_RX','4','R_MONITOR_RX_OFF',220000)]:
 r=parts[resistor];assert same(parts[driver]['pins'][pin],r['pins']['1']) and r['pins']['2']=='GND'
 if 'value_ohm' in r:assert r['value_ohm']==value
 else:assert r['part'].startswith('220k')
 rows.append({'path':driver+' -> '+resistor,'supply':'LOGIC3V3','upper_A':3.393/(value*.99)})
r=parts['R7'];assert r['part'].startswith('4.7k') and same(parts['U8']['pins']['4'],r['pins']['1'])
rs=[]
for side in ['LEFT','RIGHT']:
 pd=parts[side+'_R_EN_PULLDOWN'];assert same(r['pins']['2'],pd['pins']['1']) and pd['pins']['2']=='GND';rs.append(pd['value_ohm']*.99)
parallel=1/sum(1/x for x in rs)
assert same(parts['U10']['pins']['1'],r['pins']['2'])
normal=3.393/(4700*.99+parallel);clamped=3.393/(4700*.99)
rows.append({'path':'U8 -> R7 -> EN pulldowns or U10 clamp','supply':'LOGIC3V3','normal_upper_A':normal,'upper_A':clamped,'counting':'R7 clamp upper replaces, does not add to, pulldown current'})
r=parts['R_SEQUENCE_OFF'];assert r['value_ohm']==10000 and r['pins']=={'1':'SEQUENCE_ENABLE_REQUEST','2':'GND'}
future=3.393/(10000*.99)
subtotal=sum(x['upper_A'] for x in rows);direct_data=json.loads(direct.read_text());assert direct_data['source_sha256']==hashlib.sha256(source.read_bytes()).hexdigest(), 'Direct load report does not match assembly';d=direct_data['rails']['LOGIC3V3']['conditional_resistor_subtotal_A']
result={'source_sha256':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in [source,direct]},'paths':rows,'output_fed_subtotal_A':subtotal,'future_MCU_enable_reservation_A':future,'logic_direct_plus_output_plus_reservation_A':d+subtotal+future,'complete_current_budget':False,'manufacturing_release':False}
(a.out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
