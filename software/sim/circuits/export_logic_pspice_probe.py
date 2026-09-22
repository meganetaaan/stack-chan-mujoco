"""Export nominal startup probe from integrated candidate, for licensed PSpice runtime."""
import hashlib,json
from pathlib import Path
src=Path('schematics/power/servo_power_logic_integration_candidate_v1/assembly.json');d=json.loads(src.read_text());parts={p['reference']:p for p in d['parts']};out=Path('validation/logic_pspice_probe_v1');out.mkdir(exist_ok=True)
lines=['Logic supply candidate nominal startup - NOT whole-board qualification','.LIB "TPS26601_TRANS.LIB"','.LIB "TPS70933_TRANS.LIB"','Vsource BATTERY_RAW 0 PWL(0 0 100u 12.6 10m 12.6)']
def net(n,fallback):return '0' if n=='GND' else (n or fallback)
x=parts['U_LOGIC_PROTECT'];pins=x['pins']
# TI model header order is distinct from physical package order.
order=['22','15','14','13','19','1','2','20','18','10','12','EP','23','24','8','9','17']
lines.append('Xprotect '+' '.join(net(pins[n],'PROTECT_OPEN_'+n) for n in order)+' TPS26601_TRANS')
x=parts['U_LOGIC_LDO'];order=['6','3','4','1','2'];lines.append('Xldo '+' '.join(net(x['pins'][n],'LDO_OPEN_'+n) for n in order)+' TPS70933_TRANS')
for p in d['parts']:
 ref=p['reference']
 if ref.startswith('R_LOGIC_'):
  lines.append(ref+' '+' '.join(net(n,'UNUSED') for n in p['pins'].values())+' '+str(p['value_ohm']))
 if ref.startswith('C_LOGIC_PROTECT_'):
  lines.append(ref+' '+' '.join(net(n,'UNUSED') for n in p['pins'].values())+' '+str(p['value_F']))
# Probe matches previous 27.975uF total, not a fitted board model.
lines+=['Cprobe LOGIC3V3 0 27.975u','Rprobe LOGIC3V3 0 165','.TRAN 1u 10m 0 1u','.PROBE V(BATTERY_RAW) V(LOGIC_PROTECTED_INPUT) V(LOGIC3V3) I(Vsource)','.END']
(out/'startup.cir').write_text('\n'.join(lines)+'\n')
r={'assembly_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'source':str(src),'executed':False,'qualified':False,'scope':'Nominal supply branch only, 165ohm load and lumped ideal capacitance; no actual logic or sequencer','model_pin_order_verified_against_header':True,'limitations':['Source ramp is an engineering probe, not battery contact model','27.975uF capacitance is previous conditional maximum; no ESR or temperature model','MCU and whole logic behavior replaced by resistor only for compatibility/startup probe','Encrypted eFuse requires supported licensed simulator','No worst-case current or timing guarantees from nominal model']}
(out/'manifest.json').write_text(json.dumps(r,indent=2)+'\n')
