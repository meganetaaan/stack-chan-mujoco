"""Pin-level and conditional stress screen, not a reverse transient simulation."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];p=ROOT/'schematics/power/battery_inlet_candidate.json'
raw=p.read_bytes();d=json.loads(raw);parts={x['reference']:x for x in d['parts']}
u=parts['INLET__U_REVERSE']['pins'];q=parts['INLET__Q_REVERSE']['pins']
assert u=={'1':'INLET_VCAP','2':'CELL_B_MINUS','3':'CELL_POS_FUSED_RAW','4':'CELL_POS_FUSED','5':'INLET_GATE','6':'CELL_POS_FUSED_RAW'}
assert all(q[str(i)]==u['6'] for i in [1,2,3])
assert all(q[str(i)]==u['4'] for i in [5,6,7,8]) and q['4']==u['5']
assert q['exposed_drain_pad']==u['4']
rows=[{'current_A':i,'assumed_Rds_ohm':.0033,'conduction_drop_V':i*.0033,'conduction_loss_W':i*i*.0033} for i in [5,8.6,10]]
r={'source_sha256':hashlib.sha256(raw).hexdigest(),'pin_mapping_checks_pass':True,
 'loss_conditions':'FET fully enhanced at VGS4.5V,25C datasheet maxRds3.3mohm at28A; illustrative currents, not hot system bounds or regulated-mode loss',
 'conditional_loss_rows':rows,
 'steady_reverse_comparison':{'input_V':-12.6,'precharged_output_V':12.6,'MOSFET_VDS_V':25.2,'MOSFET_rating_V':60,'controller_cathode_minus_anode_V':25.2,'transient_margin_proven':False},
 'gate_rating_comparison':{'controller_recommended_minimum_FET_VGS_rating_V':15,'FET_absolute_VGS_rating_V':20,'transient_clamp_proven':False},
 'states':[{'name':'normal forward','path':'body diode initially, controller-driven channel afterwards','qualified':False},
 {'name':'EN low or controller not started','path':'forward body diode remains; not a load disconnect','qualified_as_disconnect':False},
 {'name':'input reversed/output precharged','path':'controller must remove gate charge; steady body diode blocks reverse; transient current unproven','qualified':False},
 {'name':'main input removed with cell taps connected','path':'possible alternative supply through sense network; must audit separately','qualified':False}],
 'manufacturing_release':False}
out=ROOT/'validation/inlet_ideal_diode_v1';out.mkdir(exist_ok=True)
(out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print('pin mapping passed; transient and full protection unqualified')
