"""Record actual gate/source nets and unresolved qualification; no driver model invented."""
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
f=Path('schematics/power/servo_power_pololu_integration_candidate_v1/assembly.json');assembly=json.loads(f.read_text());parts={p['reference']:p for p in assembly['parts']};rows=[]
for side in ['LEFT','RIGHT']:
 u,q,r,c=[parts[side+s] for s in ['_U_POWER','_Q_REVERSE','_R_GATE','_C_GATE']]
 assert u['part']=='TPS259813LRPW' and q['part'].startswith('SiSS80DN')
 assert {q['pins'][str(n)] for n in [1,2,3]}=={u['pins']['6']}
 assert {q['pins'][str(n)] for n in [5,6,7,8]}=={side+'_SERVO_BUS'}
 assert r['pins']=={'1':u['pins']['7'],'2':q['pins']['4']}
 assert c['pins']=={'1':q['pins']['4'],'2':'GND'}
 rows.append({'side':side,'gate_net':q['pins']['4'],'source_net':q['pins']['1'],'drain_net':q['pins']['5'],'driver_net':u['pins']['7'],'VGS_expression':q['pins']['4']+' minus '+q['pins']['1'],'VDS_expression':q['pins']['5']+' minus '+q['pins']['1'],'gate_R_selected':r['part'] is not None and r.get('value_ohm') is not None,'gate_C_selected':c['part'] is not None and c.get('value_F') is not None})
report={'assembly_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'topology_checks_pass':True,'rows':rows,'review_scope':'TPS25981 RevD sections6.1/6.3/6.5/7.3.8/7.3.9 and Figure7-7/7-8; SiSS80DN RevB static/gate ratings','guaranteed_loaded_DVDT_minus_OUT_min_V':None,'guaranteed_loaded_DVDT_minus_OUT_max_V':None,'reason':'No quantitative external-driver loaded steady-state VGS limits identified in reviewed datasheet sections. Internal PG gate annotation and capacitor rating are not such limits.','external_gate_turnoff_bound_s':None,'rds_on_value_promoted_to_qualified':False,'lower_resistance_substitution_allowed_by_this_review':False,'manufacturing_release':False}
a.out.mkdir(parents=True,exist_ok=True);(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
