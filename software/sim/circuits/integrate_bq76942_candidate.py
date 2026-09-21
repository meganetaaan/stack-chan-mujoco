"""Compose selected candidate fragments; unresolved pins remain explicit."""
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
power=ROOT/'schematics/power'
sources=['bq76942_candidate.json','bq76942_series_filter_candidate.json','bq76942_pack_fet_candidate.json','bq76942_reg0_limiter_candidate.json','bq_local_host_candidate.json']
a,c,q,limiter,host=[json.loads((power/s).read_text()) for s in sources]
parts=[]
def add(ref,part,pins,**extra):
 parts.append({'reference':ref,'part':part,'pins':{str(k):v for k,v in pins.items()},**extra})
bq_pins={str(p['pin']):p['sense_net'] for p in a['cell_input_map']['pins']}
bq_pins.update({'17':'CELL_B_MINUS','43':'BQ76942_DSG_43','45':'BQ76942_CHG_45','41':'BQ_LD','42':'BQ_PACK','47':'BQ_BAT_HOLD','24':'BQ_REG18','46':'BQ_CP1','18':'BQ_SRP','20':'BQ_SRN'})
bq_pins.update({'21':'BQ_TS_CELL','23':'BQ_TS_FET','30':'BQ_BOTHOFF_N','29':'CELL_B_MINUS','33':'CELL_B_MINUS','25':'BQ_ALERT_N','26':'BQ_SCL','27':'BQ_SDA'})
for pin in a['cell_input_map']['NC_pins_left_open']:bq_pins[str(pin)]=None
# Unused optional functions, per datasheet Table16-3; not silicon NC.
unused_open=[28,31,32,34,38]
for pin in unused_open:bq_pins[str(pin)]=None
bq_pins.update({'35':'BQ_CTRL3V3','36':'BQ_REGIN','37':'BQ_BREG'})
unresolved=[i for i in range(1,49) if str(i) not in bq_pins]
add('U_CELL_PROTECT',a['part'],bq_pins,unresolved_pins=unresolved,intentionally_unused_open_pins=unused_open,REG0_REG1_required=True,REG2_disabled_required=True)
for ref,pins in q['pin_connections'].items():add(ref,q['part'],pins)
g=q['gate_network_candidate']
for x in g['connections']:
 suffix=x['FET'][2:]
 add('R_GATE_'+suffix,g['series_resistor']['part'],dict(enumerate(x['series_resistor'],1)))
 add('R_GS_'+suffix,g['gate_source_resistor']['part'],dict(enumerate(x['bleed_resistor'],1)))
 add('D_GS_'+suffix,g['zener']['type'],x['zener_pins'],ordering_suffix_pending=True)
for i,b in enumerate(a['cell_input_filter_candidate']['branches']):
 add(f'R_CELL_{i}',a['cell_input_filter_candidate']['resistor']['part'],dict(enumerate(b['resistor'],1)))
for f in c['filters']:
 for x in f['capacitors']:add(x['reference'],c['capacitor_part'],dict(enumerate(x['nets'],1)))
# Separate sense resistors preserve the distinct PACK and LD functions.
add('R_LD','TNPW060310K0BEEA',{1:'PACK_POS_PROTECTED',2:'BQ_LD'})
add('R_PACK','TNPW060310K0BEEA',{1:'PACK_POS_PROTECTED',2:'BQ_PACK'})
add('R_BAT','TNPW1206100RBEEA',{1:'CELL_POS_FUSED',2:'BQ_BAT_DIODE_A'})
add('D_BAT','BAS116',{1:'BQ_BAT_DIODE_A',2:None,3:'BQ_BAT_HOLD'},ordering_suffix_pending=True)
add('C_BAT','C1206C105K3RACTU',{1:'BQ_BAT_HOLD',2:'CELL_B_MINUS'},effective_capacitance_qualified=False)
for i in range(3):
 add(f'C_REG18_{i}','C1206C105K3RACTU',{1:'BQ_REG18',2:'CELL_B_MINUS'},effective_capacitance_qualified=False)
add('C_CP1','C1206C105K3RACTU',{1:'BQ_CP1',2:'BQ_BAT_HOLD'},effective_capacitance_qualified=False)
# Manufacturer functional labels, not invented footprint pad numbers.
# E terminals are separate Kelvin traces; do not merge them into current nets.
add('R_SHUNT','WSK25125L000FEA',{'I1':'CELL_B_MINUS','I2':'PACK_RETURN','E1':'SHUNT_CELL_SENSE','E2':'SHUNT_PACK_SENSE'},
    pin_label_source='Vishay 30108 Rev 11-Dec-2023 p3',footprint_pad_mapping_qualified=False,
    resistance_ohm=0.005,tolerance_fraction=0.01,component_tcr_ppm_per_K=35,
    rated_power_W_at_70C=1.0,kelvin_routing_required=True,thermal_qualified=False)
add('R_SRP','TNPW0603100RBEEA',{1:'SHUNT_CELL_SENSE',2:'BQ_SRP'})
add('R_SRN','TNPW0603100RBEEA',{1:'SHUNT_PACK_SENSE',2:'BQ_SRN'})
add('C_CURRENT','C1206C104J3GACAUTO',{1:'BQ_SRP',2:'BQ_SRN'})
for ref,net,location in [('TH_CELL','BQ_TS_CELL','battery exterior'),('TH_FET','BQ_TS_FET','main protection FET region')]:
 add(ref,'103AT-2',{1:net,2:'CELL_B_MINUS'},location_candidate=location,
     mounting_qualified=False,protection_threshold_qualified=False)
# Active-low BOTHOFF: local pulldown holds inhibit if the external allow wire opens.
# The source must be a qualified CELL_B_MINUS-referenced control domain.
add('R_ALLOW_SER','TNPW06031K00BEEA',{1:'BQ_ALLOW_BMINUS',2:'BQ_BOTHOFF_N'})
add('R_ALLOW_PD','TNPW060310K0BEEA',{1:'BQ_BOTHOFF_N',2:'CELL_B_MINUS'})
# Dedicated preregulator feed; do not share the BAT hold-up diode.
for item in limiter['parts']:parts.append(item)
add('D_REG0','BAT46W-7-F',{'A':'BQ_REG0_LIMITED','K':'BQ_REG0_PRE_R'},footprint_pad_mapping_qualified=False)
for i in range(2):
 add(f'R_REG0_{i}',limiter['feed_resistors']['part'],{1:'BQ_REG0_PRE_R',2:'BQ_REG0_COLLECTOR'})
add('C_REG0','C1206C105K3RACTU',{1:'BQ_REG0_COLLECTOR',2:'CELL_B_MINUS'},effective_capacitance_qualified=False)
add('Q_REG0','FCX495TA',{'B':'BQ_BREG','C':'BQ_REG0_COLLECTOR','E':'BQ_REGIN'},footprint_pad_mapping_qualified=False,thermal_qualified=False)
add('C_REGIN','C0603C223K4RACTU',{1:'BQ_REGIN',2:'CELL_B_MINUS'},effective_capacitance_qualified=False)
add('C_REG1','C1206C105K3RACTU',{1:'BQ_CTRL3V3',2:'CELL_B_MINUS'},effective_capacitance_qualified=False)
for name in ['SCL','SDA']:
 add('R_BQ_'+name,'TNPW06032K21BEEA',{1:'BQ_CTRL3V3',2:'BQ_'+name})
add('R_BQ_ALERT','TNPW060310K0BEEA',{1:'BQ_CTRL3V3',2:'BQ_ALERT_N'})
parts.extend(host['parts'])
assert len(parts)==86 and len({p['reference'] for p in parts})==86
# Check that the obsolete 8-capacitor parallel-only filter was not also imported.
assert sum(p['part']==c['capacitor_part'] and p['reference'].startswith('C_F') for p in parts)==24
out=power/'battery_protection_integration_candidate_v1';out.mkdir(exist_ok=True)
assembly={'status':'partial_connection_candidate','parts':parts,'part_count':len(parts),'unresolved_BQ76942_pins':unresolved,'source_sha256':{s:hashlib.sha256((power/s).read_bytes()).hexdigest() for s in sources},'external_ports':['CELL_B_MINUS','CELL1_TAP','CELL2_TAP','CELL3_TAP','CELL_POS_FUSED','PACK_POS_PROTECTED','PACK_RETURN','BQ_ALLOW_BMINUS','BQ_CTRL3V3','BQ_SCL','BQ_SDA','BQ_ALERT_N','BQ_AUX_START_REQUEST','BQ_HOST_HEARTBEAT','BQ_HOST_NRST','BQ_HOST_SWDIO','BQ_HOST_SWCLK'],'local_host_candidate':host,'missing_stages':['cell tap and main connectors','battery fuse and reverse protection','current threshold, shunt thermal/pulse and sense-routing qualification','BAT and REG0 input faults; REG18/CP1/REGIN/REG1 effective capacitance, headroom, load and startup','PACK/LD transient and reverse-polarity qualification','local host and reset supervisor connected; firmware, independent watchdog and domain-crossing driver unimplemented; dynamic reset unqualified','thermistor attachment, harness, fault response and temperature protection settings','system integration candidate exists; whole-system electrical qualification incomplete'],'temperature_configuration_candidate':{'TS1':{'address':'0x92FD','value':'0x07','role':'cell temperature'},'TS3':{'address':'0x92FF','value':'0x0F','role':'FET temperature'},'source':'TI SLUUBY1B tables 13-9/13-11 and memory map','applied_to_hardware':False,'full_protection_configuration':False},'startup_inhibit_candidate':{'DFETOFF_config':{'address':'0x92FB','value':'0xC2','active_level':'low','function':'BOTHOFF'},'CFETOFF_config':{'address':'0x92FA','value':'0x00'},'RST_SHUT':'unused tied to VSS; not emergency stop','effective_before_configuration':False,'external_allow_driver_qualified':False,'control_reference':'CELL_B_MINUS'},'control_supply_candidate':{'part':'BQ7694202PFBR','source':'REG0 plus factory-enabled REG1','domain_reference':'CELL_B_MINUS','factory_REG0_Config':'0x01','factory_REG12_Config':'0x0D','I2C_CRC_required':True,'REG1_output_spec_V':[3.0,3.6],'REG1_output_spec_conditions':'REGIN >=4.1V, load 0..45mA; datasheet section7.12','MCU_load_budget_qualified':False,'cold_start_qualified':False,'shutdown_cuts_control_supply':True},'communications_candidate':{'clock_Hz':100000,'I2C_CRC_required':True,'pullup_ohm':2210,'bus_capacitance_allocation_F':100e-12,'allocation_origin':'engineering PCB budget, not measured','ALERT_config':{'address':'0x92FC','value':'0x82','function':'active-low open-drain'},'domain_reference':'CELL_B_MINUS','host_interface_qualified':False},'electrically_operational':False,'manufacturing_release':False}
(out/'assembly.json').write_text(json.dumps(assembly,indent=2)+'\n')
with (out/'bom.csv').open('w') as f:
 w=csv.writer(f,lineterminator='\n');w.writerow(['part_or_type','quantity','references'])
 for part,n in sorted(Counter(p['part'] for p in parts).items()):w.writerow([part,n,' '.join(p['reference'] for p in parts if p['part']==part)])
with (out/'connections.csv').open('w') as f:
 w=csv.writer(f,lineterminator='\n');w.writerow(['reference','pin','net','status'])
 for p in parts:
  for pin,net in p['pins'].items():w.writerow([p['reference'],pin,net,('UNUSED_OPEN' if int(pin) in p.get('intentionally_unused_open_pins',[]) else 'NC') if net is None else 'candidate_connected'])
  for pin in p.get('unresolved_pins',[]):w.writerow([p['reference'],pin,'','UNRESOLVED'])
print(f'{len(parts)} parts; {len(unresolved)} BQ pins unresolved; not operational')
