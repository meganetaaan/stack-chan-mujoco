"""G030 clear-request drive and default assertion under a declared DC budget."""
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
ptr=Path('schematics/power/servo_power_rearm_current.json');ap=Path(json.loads(ptr.read_text())['assembly']);cp=Path('schematics/power/sequence_controller_candidate/g030_controller.json');sp=Path('schematics/power/sequence_clear_sink_candidate.json');parts={x['reference']:x for x in json.loads(ap.read_text())['parts']};controller=json.loads(cp.read_text());sink=json.loads(sp.read_text())
assert parts['U14']['part']=='74AUP1G06GW' and parts['U14']['pins']['2']=='SEQUENCE_CLEAR_REQUEST'
assert parts['R14']['part'].startswith('100k') and parts['R14']['pins']=={'1':'LOGIC3V3','2':'SEQUENCE_CLEAR_REQUEST'}
assert controller['pins']['16']['selected_gpio']=='PA11' and controller['pins']['16']['signal']=='SEQUENCE_CLEAR_REQUEST'
plan={'question':'Can G030 PA11 drive U14 and leave clear asserted when GPIO is high impedance at a valid common rail?',
 'scope':'Static valid common LOGIC3V3 only; not reset/startup behavior or unpowered pin qualification.',
 'assumptions':['LOGIC3V3 3.207..3.393 V','Entire MCU product leakage 10 uA + 44*70 nA allocated to this node conservatively','AUP input leakage 0.5 uA at -40..85 C','Resistor total tolerance +/-1%; no board leakage included'],
 'sources':{'MCU':'https://www.st.com/resource/en/datasheet/stm32g030f6.pdf DS12991 Rev6 pp61,64','sink':'https://assets.nexperia.com/documents/data-sheet/74AUP1G06.pdf Rev12 pp5,6'},
 'criteria':['Default request >=2.0 V','Driven High >=2.0 V, driven Low <=0.9 V','Drive load <=6 mA at VDD>=2.7 V'],
 'stop':'Existing 100k versus one 10k replacement proposal; no resistor sweep or transistor simulation.'}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
low,high=3.207,3.393;leak=10e-6+44*70e-9+.5e-6;rows=[]
for resistance in [100000,10000]:
 default=low-leak*resistance*1.01;load=high/(resistance*.99)+.5e-6
 rows.append({'pullup_ohm':resistance,'default_request_lower_V':default,'default_high_pass':default>=2,'driven_low_V_max':.4,'driven_high_V_min':low-.4,'worst_low_sink_current_A':load,'drive_current_pass':load<=.006,'high_margin_V':low-.4-2,'low_margin_V':.9-.4})
proposal={'status':'conditional_connection_proposal_not_integrated','controller':'STM32G030F6P6','package_pin':16,'gpio':'PA11','net':'SEQUENCE_CLEAR_REQUEST','receiver':{'reference':'U14','pin':2,'part':'74AUP1G06GW'},'replace_R14':{'part':'TNPW060310K0BYEA','value_ohm':10000,'total_tolerance_budget':.01,'pins':parts['R14']['pins']},'conditions':['Internal pulls disabled, valid common supply','Preload GPIO output data High before selecting output mode; reset tri-state treated separately','Actual reset/power, input edge rate, board leakage and total supply budget still need verification'],'manufacturing_release':False}
(a.out/'connection_proposal.json').write_text(json.dumps(proposal,indent=2)+'\n')
result={'source_sha256':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in [ptr,ap,cp,sp]},'rows':rows,'interpretation':'100k cannot demonstrate default assertion with the declared leakage budget. 10k passes this static comparison only. No claim of measured failure or safe power transitions.','manufacturing_release':False}
(a.out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(rows,indent=2))
