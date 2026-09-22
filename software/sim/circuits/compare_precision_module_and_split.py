"""Compare physical supply changes without relaxing servo terminal targets."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
paths={'load':'validation/model_dc_envelope_v2/report.json','wire':'validation/pololu_wiring_budget_v1/plan.json'}
d={k:json.loads((ROOT/v).read_text()) for k,v in paths.items()}
axis={x['model']:x['dc_draw_upper_A'] for x in d['load']['rows']}
xl,xc=axis['XL330-M288-T'],axis['XC330-M288-T'];assert 3*(xl+xc)==4.917
bleed=2*5.25/(360*.95)
rho=d['wire']['wire_comparison']['nominal_DCR_ohm_per_1000ft_at20C']/304.8
r_contact=d['wire']['contacts_each_branch_loop']*d['wire']['EH_contact_ohm_each']
# Datasheet table1 nominal output using169ohm is5.005V. Footnote2 includes suitable RSET.
voltage=5.005;lower=voltage*.985;upper=voltage*1.015
rows=[]
for part,i in axis.items():
 total=3*(xl+xc)+bleed;feeder=total*2*.05*rho
 rows.append({'option':'PTH08T240W plus one TPS25948 per leg','axis':part,'source_min_V':lower,'source_max_V':upper,'shared_A':total,'protection_drop_V':total*.020,'contacts_drop_V':i*r_contact,'50mm_feeder_drop_V':feeder,'remaining_V':lower-4.75-total*.020-i*r_contact-feeder})
for name,group in [('2XL_1XC',2*xl+xc),('1XL_2XC',xl+2*xc)]:
 # Each independent protected bus retains two discharge resistors; not one per bus.
 shared=group+bleed;all_groups=3*(xl+xc)+2*bleed;feeder=all_groups*2*.05*rho
 rows.append({'option':'Existing Pololu plus two TPS25948 per leg','group':name,'source_min_V':4.85,'shared_A':shared,'protection_drop_V':shared*.020,'worst_XC_contacts_drop_V':xc*r_contact,'50mm_common_feeder_drop_V':feeder,'remaining_V':4.85-4.75-shared*.020-xc*r_contact-feeder})
report={'source_sha256':{v:hashlib.sha256((ROOT/v).read_bytes()).hexdigest() for v in paths.values()},
 'preexisting_targets_V':[4.75,5.25],'target_changed':False,'PTH_set_resistor_ohm':169,'PTH_total_accuracy_fraction':.015,'RSET_tolerance_added_again':False,
 'RSET_basis':'TI table1 169ohm ->5.005V; footnote2 says limits met with1%100ppm/C or better. Do not double count this tolerance.',
 'rows':rows,'decision':'Prioritize precision-module candidate for further component/thermal/inhibit design; split protection is backup and has smaller unallocated drop margin.',
 'new_module_candidate':{'part_family':'PTH08T240W','quantity':2,'ordering_suffix':None,'normal_input_for5V_min_V':7,'input_max_V':14,'input_note':'9..12.6V battery comparison fits DC range; hotplug/overshoot below14V not yet proved','RSET_ohm':169,'minimum_output_capacitance_F_at5V':330e-6,'required_input_electrolytic_F':220e-6,'input_cap_min_ripple_A':.5,'inhibit':'Open enables, pull low disables; internal pullup, no external pullup. Need low-leakage open-drain driver, current push-pull ENA network cannot be reused.','sense':'Local before protective disconnect; do not remote-sense beyond switch without stability/open-sense/fault analysis'},
 'sources':[{'url':'https://www.ti.com/lit/gpn/pth08t240w','revision':'SLTS264J June2009','sections':['Electrical characteristics footnotes2/4/5/6','Table1 RSET']},{'url':'https://www.ti.com/lit/ds/symlink/tps25948.pdf','revision':'D April2026','section':'6.5 RON20mohm at3A'}],
 'remaining':['Exact orderable module/suffix and current supply status','Capacitor types, tolerances, ESR, ripple, and5V transient stability; no TurboTrans chart extrapolation','Inhibit fail-low/partial power behavior and pin mapping','Input transient protection versus14V operating ceiling','Thermal derating at actual enclosure conditions;10A at25C is not hot-box proof','Carrier CAD, height/clearance, harness and full mass update','eFuse RON at actual current, overcurrent and voltage thresholds and regeneration'],
 'limits':['DC selection screen only; residual must fund OEM branch wire,PCB,solder,hot-wire increase and dynamic droop','20mohm eFuse table at3A is applied to larger per-leg current only as comparison; split currents stay below3A','50mm feeder is assumed routing length and nominal20C DCR','Doubling protected buses requires independent discharge, capacitors and fault monitoring; no automatic division of unknown bus capacitance'],
 'integrated_into_current_CAD_or_circuit':False,'manufacturing_release':False}
assert all(r['remaining_V']>0 for r in rows)
assert upper<5.25
out=ROOT/'validation/precision_module_comparison_v1';out.mkdir(exist_ok=True)
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'rows':rows,'selected_for_next_design':'PTH08T240W candidate, not released'}))
