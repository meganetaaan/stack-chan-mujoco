"""Give the unimplemented sequence-enable request a physical default Low."""
import argparse,hashlib,json
from pathlib import Path
from assembly_net_aliases import net_aliases
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--out',type=Path,required=True)
a=p.parse_args()
base=Path('schematics/power/servo_power_rearm_integration_revH/assembly.json')
r=json.loads(base.read_text())
def endpoints(assembly, net):
 aliases=net_aliases(assembly)
 return [{'reference':x['reference'],'pin':k,'part':x['part']} for x in assembly['parts'] for k,v in x['pins'].items() if v and v!='NC' and aliases[v]==aliases[net]]
before=endpoints(r,'SEQUENCE_ENABLE_REQUEST')
assert [(x['reference'],x['pin']) for x in before]==[('U3','4')]
r['parts'].append({'reference':'R_SEQUENCE_OFF','part':None,'value_ohm':10000,
 'pins':{'1':'SEQUENCE_ENABLE_REQUEST','2':'GND'},
 'placement':'At U3 pin4; after any future sequencer interconnect; not at remote driver'})
after=endpoints(r,'SEQUENCE_ENABLE_REQUEST')
r['scope']=__doc__
r['part_count']=len(r['parts']);r['pin_count']=sum(len(x['pins']) for x in r['parts'])
r['interfaces']['SEQUENCE_ENABLE_REQUEST']='U3 pin4 with local 10 kohm pulldown; sequencer driver absent; future source must meet loading and partial-power constraints'
r['interfaces']['MAIN_EFUSE_EN']='Common EN to both TPS259813L; source monitor circuits exist, but their inhibition/qualification and sequencer remain unfinished'
r['integration_limitations']+=['Sequence-enable input now has local pulldown; no sequencer behavior is supplied by this resistor']
r['source_sha256']={str(base):hashlib.sha256(base.read_bytes()).hexdigest(),__file__:hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
r['manufacturing_release']=False;r['electrical_qualification']=False
report={'classification':'connectivity_fault_correction_and_resistor_budget',
 'failure_before':'U3 pin4 SEQUENCE_ENABLE_REQUEST has only one endpoint: floating CMOS input, no physical driver or bias',
 'before':before,'after':after,
 'source':'https://www.ti.com/lit/ds/symlink/sn74hcs11.pdf','revision':'SCLS790B March 2026 pp5,11',
 'datasheet_input_leakage_max_A':1e-6,
 'assumptions':['10 kohm total +/-1 percent; exact resistor unselected',
  'Datasheet leakage at VCC=6 V and VI=rail/ground applied as a comparison budget',
  'No future driver leakage or board contamination included',
  '3.6 V maximum used only for prospective driver load budget'],
 'bounds':{'leakage_only_input_V':1e-6*10100,
  'prospective_high_driver_load_A':3.6/9900+1e-6,
  'resistor_power_at_3V6_W':3.6**2/9900},
 'bias_connection_verified':len(after)==2,
 'sequencer_implemented':False,'power_on_inhibit_proven':False,
 'pending':['Exact resistor and tolerance allocation',
  'Driver High voltage and current under added load',
  'Input-low threshold across actual rail and power transitions',
  'Sequencer implementation and fault memory; resistor does not replace either'],
 'part_count':r['part_count'],'pin_count':r['pin_count'],'manufacturing_release':False}
a.out.mkdir(parents=True,exist_ok=False)
(a.out/'assembly.json').write_text(json.dumps(r,indent=2)+'\n')
(a.out/'integration_report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
