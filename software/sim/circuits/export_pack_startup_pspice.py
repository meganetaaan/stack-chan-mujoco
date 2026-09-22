"""Export current input branch for supported PSpice; does not execute models."""
import argparse,hashlib,json,re,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
p=argparse.ArgumentParser();p.add_argument('--efuse-zip',type=Path,required=True);p.add_argument('--ldo-zip',type=Path,required=True);p.add_argument('--include-main-interface-load',action='store_true');p.add_argument('--include-current-interfaces',action='store_true');args=p.parse_args()
assert not (args.include_current_interfaces and args.include_main_interface_load), 'Choose one load revision'
OUT=ROOT/('validation/pack_startup_pspice_v3' if args.include_current_interfaces else 'validation/pack_startup_pspice_v2' if args.include_main_interface_load else 'validation/pack_startup_pspice_v1');OUT.mkdir(exist_ok=True)
source=ROOT/'schematics/power/pack_control_ramp_candidate_v1/assembly.json'
budget_path=ROOT/('validation/controller_probe_load_v1/report.json' if args.include_current_interfaces else 'validation/main_allow_interface_screen_v1/report.json' if args.include_main_interface_load else 'validation/pack_controller_budget_v1/report.json')
budget=json.loads(budget_path.read_text())
if args.include_main_interface_load or args.include_current_interfaces:
 for name,expected in budget['source_sha256'].items():
  assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==expected, f'Stale interface load screen: {name}'
 rows=budget['rows'] if args.include_current_interfaces else budget['updated_partial_controller_budgets']
else:rows=budget['rows']
row=next(r for r in rows if r['MCU_MHz']==64)
load=row['partial_screen_sum_A'];resistance=3.3/load
a=json.loads(source.read_text());parts={p['reference']:p for p in a['parts']}
models=[]
for archive,member,url in [(args.efuse_zip,'TPS26600_TRANS.LIB','https://www.ti.com/lit/zip/slvmbr3b'),(args.ldo_zip,'TPS70933_TRANS.LIB','https://www.ti.com/lit/zip/sbvm571')]:
 raw=zipfile.ZipFile(archive).read(member);text=raw.decode(errors='replace')
 joined=re.sub(r'\r?\n\+\s*',' ',text)
 header=re.search(r'(?im)^\.subckt '+member[:-4]+r'\s+([^\r\n]+)',joined).group(1).split()
 models.append({'url':url,'member':member,'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'model_sha256':hashlib.sha256(raw).hexdigest(),'pins':header,'encrypted':'**$ENCRYPTED_LIB' in text})
assert models[0]['pins']==['FLT_N','RTN','SHDN_N','MODE','ILIM','NC_0','NC_1','dVdT','IMON','UVLO','OVP','PAD','OUT_0','OUT_1','IN_0','IN_1','GND'],models[0]['pins']
assert models[1]['pins']==['IN','GND','EN','OUT','NC']
def net(n,fallback):return '0' if n=='PACK_RETURN' else (n or fallback)
value_by_part={'TNPW060340K2BEEA':40200,'TNPW060310K0BEEA':10000,'TNPW0603124KBEEA':124000,'TNPW0603118KBEEA':118000,'TNPW0805402KBEEA':402000,'GRM31C5C1H104JA01L':1e-7}
for voltage in [9,12.6]:
 lines=['Pack controller nominal compatibility/startup probe; NOT full load qualification', '.LIB "TPS26600_TRANS.LIB"','.LIB "TPS70933_TRANS.LIB"',f'Vsource PACK_FUSED_REVERSE_PROTECTED 0 PWL(0 0 100u {voltage} 50m {voltage})']
 for ref,order,model in [('U_CTRL_INPUT_LIMIT',['22','15','14','13','19','1','2','20','18','10','12','EP','23','24','8','9','17'],'TPS26600_TRANS'),('CTRL__U_LDO',['1','2','3','5','4'],'TPS70933_TRANS')]:
  pins=parts[ref]['pins'];lines.append('X'+ref+' '+' '.join(net(pins[k],ref+'_OPEN_'+k) for k in order)+' '+model)
 for ref,part in parts.items():
  if ref.startswith(('R_CTRL_INPUT_','C_CTRL_INPUT_')) or ref in ['CTRL__C_LDO_IN','CTRL__C_LDO_OUT','CTRL__C_HOST_BULK','CTRL__C_HOST_HF','CTRL__C_HOST_SUP','CTRL__C_WD','CTRL__C_RESET_BUFFER','CTRL__C_PERMIT_LATCH','CTRL__C_MAIN_GATE','CTRL__C_AUX_GATE']:
   value=part.get('value_F',value_by_part.get(part['part']))
   assert value is not None,ref
   prefix='R' if 'R_CTRL_INPUT_' in ref else 'C'
   lines.append(prefix+ref+' '+' '.join(net(n,'unused') for n in part['pins'].values())+' '+str(value))
 if args.include_current_interfaces:
  base_cap_refs={ref for ref,part in parts.items() if set(part['pins'].values())=={'CTRL3V3','PACK_RETURN'} and part.get('value_F') is not None}
  for ref,value in budget['CTRL3V3_nominal_capacitors_F'].items():
   if ref not in base_cap_refs:lines.append('C'+ref+' CTRL3V3 0 '+str(value))
 lines += [f'Rload CTRL3V3 0 {resistance:.12g}','.TRAN 1u 50m 0 1u','.PROBE V(PACK_FUSED_REVERSE_PROTECTED) V(CONTROL_INPUT_PROTECTED) V(CTRL3V3) I(Vsource)','.END']
 (OUT/f'startup_{voltage:g}V.cir').write_text('\n'.join(lines)+'\n')
report={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'models':models,'executed':False,'qualification':False,'probe_load_ohm':resistance,'load_scope':'Partial budget at3.3V represented by resistor, not full MCU current model','budget_path':str(budget_path.relative_to(ROOT)),'partial_load_A_at3_3V':load,'main_interface_load_included':args.include_main_interface_load or args.include_current_interfaces,'current_interface_partial_loads_included':args.include_current_interfaces,'main_interface_receiver_supply_included':False,'budget_sha256':hashlib.sha256(budget_path.read_bytes()).hexdigest(),'source_ramp_s':.0001,'target_time_s':.05,'max_step_s':1e-6,'limits':['Nominal model only; no temperature or tolerance qualification','LDO model omits input-dependent quiescent/ground current','eFuse thermal timing is simplified, not actual temperature integration','No MCU state/reset/enable sequencing','No upstream PCM, fuse, reverse protection or contact model'],'model_files_redistributed':False}
(OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'exported':2,'executed':False,'model_pins_verified':True}))
