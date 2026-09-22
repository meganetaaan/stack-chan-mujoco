"""Static SHDN interface checks before joining the auxiliary permission nets."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'validation/aux_start_connection_v1';OUT.mkdir(exist_ok=True)
source=ROOT/'schematics/power/protected_pack_system_candidate_v1/assembly.json';a=json.loads(source.read_text());p={x['reference']:x for x in a['parts']}
assert p['CTRL__U_AUX_GATE']['part']=='SN74LVC1G08DBVR'
assert p['CTRL__U_AUX_GATE']['pins']['4']=='LOGIC_START_ALLOW'
assert p['SYS__U_LOGIC_PROTECT']['pins']['17']=='PACK_RETURN'
assert p['SYS__U_LOGIC_PROTECT']['pins']['15']=='SYS__LOGIC_PROTECT_RTN'
assert p['SYS__R_LOGIC_SHDN_PD']['pins']['2']=='PACK_RETURN'
assert p['SYS__R_LOGIC_SHDN_SER']['pins']=={'1':'SYS__LOGIC_START_ALLOW','2':'SYS__LOGIC_SHDN'}
# Existing selected resistor values; total1% is a design tolerance budget, not part initial tolerance alone.
rs=1000.;rp=10000.;tol=.01
low_boundary=.4;pull_sink=low_boundary/(rp*(1+tol));worst_source=(10+10)*1e-6
# Conservative opposite leakage for high and source-direction leakage for low.
voh=2.4;vol=.4
rsh=rs*(1+tol);rpl=rp*(1-tol)
high=(voh/rsh-10e-6)/(1/rsh+1/rpl)
rsl=rs*(1-tol);rph=rp*(1+tol)
low=(vol/rsl+10e-6)/(1/rsl+1/rph)
r={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'decision':'Join LOGIC_START_ALLOW to SYS__LOGIC_START_ALLOW as a static-compatible candidate, not transient qualification','criteria_before_calculation':{'high_min_V':1.,'low_max_V':.4,'unpowered_driver_off_boundary_sink_exceeds_sources':True},'resistor_total_tolerance_assumption':tol,'calculations':{'high_SHDN_V_at_driver3V_table_bound':high,'low_SHDN_V_at_driver3V_table_bound':low,'pulldown_sink_A_at0_4V':pull_sink,'allocated_source_A_eFuse_plus_off_driver':worst_source,'CTRL_high_extra_branch_current_A_at3_6V':3.6/((rs+rp)*(1-tol))+10e-6},'checks':{'high_point':high>1,'low_point':low<.4,'driver_off_sink_capacity':pull_sink>worst_source,'SHDN_uses_system_ground':True,'RTN_not_shortened_to_GND':True},'leakage_assumption':'TPS266010uA condition is specified at0.4V; using magnitude10uA at other SHDN voltages is a comparison allocation, not a guaranteed bound', 'source_conditions':['TPS2660 RevG7.5 test default24V;9.3.5.7 SHDN low requires10uA sink at0.4V, enable>=1V','SN74LVC1G08 RevAA5.5: at3V/-16mA VOH>=2.4V;at3V/+16mA VOL<=0.4V;Ioff<=10uA atVCC0V','3V driver output bounds used as point check; full rail tolerance/temperature/startup are not thereby simulated'],'remaining':['Receiver input-voltage applicability across3S range and transient overshoot','CTRL ramp/brownout0<VCC<specified operation and reset/latch clearing','SHDN fault-latch reset and PCM restore sequencing','Back-power/leakage with stored energy and upstream reverse transients','Complete current budget and whole-power validation'],'full_operating_envelope_qualified':False,'manufacturing_release':False,'sources':['https://www.ti.com/lit/ds/symlink/tps2660.pdf','https://www.ti.com/lit/ds/symlink/sn74lvc1g08.pdf']}
assert all(r['checks'].values());(OUT/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r['calculations']))
