"""Candidate domain crossing; no full-system integration or timing qualification."""
import csv,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'schematics/power/pack_main_allow_interface_candidate_v1';OUT.mkdir(exist_ok=True)
paths=[ROOT/'schematics/power/pack_control_ramp_candidate_v1/assembly.json',ROOT/'schematics/power/system_power_integration_candidate_v1/assembly.json']
ctrl,sys=[json.loads(p.read_text()) for p in paths]
c={p['reference']:p for p in ctrl['parts']};s={p['reference']:p for p in sys['parts']}
assert c['CTRL__U_MAIN_GATE']['pins']['4']=='MAIN_START_ALLOW'
assert s['SYS__U3']['pins']['4']=='SYS__SEQUENCE_ENABLE_REQUEST'
assert s['SYS__U3']['pins']['3']=='SYS__ENABLE_PERMISSION' and s['SYS__U3']['pins']['5']=='SYS__RESET_N'
assert s['SYS__R_SEQUENCE_OFF']['pins']=={'1':'SYS__SEQUENCE_ENABLE_REQUEST','2':'PACK_RETURN'}
parts=[{'reference':'IF_MAIN__U_BUFFER','part':'74LVC1G17GV','pins':{'1':None,'2':'MAIN_START_ALLOW','3':'PACK_RETURN','4':'SYS__SEQUENCE_ENABLE_REQUEST','5':'SYS__LOGIC3V3'},'role':'Receiver-powered tolerant-input buffer'}, {'reference':'IF_MAIN__R_INPUT_PD','part':'TNPW060310K0BEEA','value_ohm':10000,'pins':{'1':'MAIN_START_ALLOW','2':'PACK_RETURN'},'placement':'At buffer input, receiver end of link','total_tolerance_assumption':.01}, {'reference':'IF_MAIN__C_HF','part':'GRM31C5C1H104JA01L','value_F':1e-7,'pins':{'1':'SYS__LOGIC3V3','2':'PACK_RETURN'},'placement':'At buffer supply'}]
result={'status':'domain_crossing_candidate_not_integrated','parts':parts,'required_existing_parts':['CTRL__U_MAIN_GATE','SYS__U3','SYS__R_SEQUENCE_OFF'],'connection_checks_pass':True,'check_scope':'Source/sink pin names and preservation of independent permission/reset inputs; not electrical proof','rejected_direct_wire':{'case':'CTRL3V3=3.3V, SYS__LOGIC3V3=0V, MAIN_START_ALLOW high','reason':'SN74HCS11 recommended input range0..VCC; input clamp exists aboveVCC+0.5V; no claim of damage current without impedance model'},'sources':[{'url':'https://www.ti.com/lit/ds/symlink/sn74hcs11.pdf','revision':'SCLS790B March2026','sections':['4','5.1','5.3']},{'url':'https://assets.nexperia.com/documents/data-sheet/74LVC1G17.pdf','revision':'16.1 September2024','sections':['6','9','10']}],'engineering_choices':['10k input pulldown, total1% assumed','Reuse existing output-side10k pulldown; do not duplicate','MAIN_START_ALLOW occupies sequence request input only; keep manual permission and reset AND conditions'],'remaining':['Receiver brownout0<VCC<1.65V behavior and reset hold timing','High/low margins across both rail tolerances and gate loads','Input driver unpowered leakage and pulldown timing','Add input pulldown load and buffer consumption to rail budgets','Physical manual request/Tab5 handshake/UV detector not connected','Whole-system power paths and LOGIC_START_ALLOW crossing remain separate work'],'electrically_operational':False,'manufacturing_release':False,'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
(OUT/'assembly.json').write_text(json.dumps(result,indent=2)+'\n')
with (OUT/'bom.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['reference','part','quantity']);w.writerows((p['reference'],p['part'],1) for p in parts)
with (OUT/'connections.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['reference','pin','net']);w.writerows((p['reference'],pin,net) for p in parts for pin,net in p['pins'].items())
print('3 candidate parts; existing source/sink and independent inhibit inputs checked; not integrated or qualified')
