"""Replace the legacy single PG receiver; sequencer and main power stage remain external."""
import argparse,copy,csv,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
base=Path('schematics/power/manual_rearm_revI/assembly.json');receiver=Path('schematics/power/dual_pg_receiver_revB/connectivity.json')
r=copy.deepcopy(json.loads(base.read_text()));pg=json.loads(receiver.read_text())
removed={'U12','U13','R10','R11','R12','R13','C12','C13'}
assert removed <= {x['reference'] for x in r['parts']}
r['parts']=[x for x in r['parts'] if x['reference'] not in removed]+pg['parts']
assert len({x['reference'] for x in r['parts']})==len(r['parts'])
legacy={'MAIN_EFUSE_PG','PG_DIVIDED','PG_CONDITIONED_OD','PG_CONDITIONED'}
assert not any(net in legacy for x in r['parts'] for net in x['pins'].values())
for name in legacy:r['interfaces'].pop(name,None)
for side in ['LEFT','RIGHT']:
    r['interfaces'][side+'_PG_SOURCE']='Input from selected eFuse PG; source-side pullup, device compatibility not fully qualified'
    r['interfaces'][side+'_PG_CONDITIONED']='Output to unimplemented startup sequencer; not valid during unqualified power transitions'
r['interconnects']=pg['interconnects']
r['part_count']=len(r['parts']);r['pin_count']=sum(len(x['pins']) for x in r['parts'])
r['scope']='Manual rearm with two separate PG receivers; not complete two-leg power control'
r['source_sha256']={str(q):hashlib.sha256(q.read_bytes()).hexdigest() for q in [base,receiver]}
r['integration_limitations']=['Existing MAIN_EFUSE_EN driver is still single-channel; this revision only replaces PG reception','Source UV/OV monitors and startup sequencer not implemented','Hardware fault memory, power-transition behavior, pulse capture and clear timing incomplete','No KiCad ERC or electrical qualification inferred from connectivity checks']
r['manufacturing_release']=False;r['electrical_qualification']=False
(a.out/'assembly.json').write_text(json.dumps(r,indent=2)+'\n')
with (a.out/'pins.csv').open('w') as f:
    w=csv.writer(f,lineterminator='\n');w.writerow(['reference','part','pin','net'])
    for x in r['parts']:
        for pin,net in x['pins'].items():w.writerow([x['reference'],x['part'],pin,net or 'NC'])
(a.out/'integration_report.json').write_text(json.dumps({'removed_references':sorted(removed),'added_references':[x['reference'] for x in pg['parts']],'part_count':r['part_count'],'pin_count':r['pin_count'],'legacy_PG_nets_remaining':[],'hardware_validated':False},indent=2)+'\n')
print(r['part_count'],r['pin_count'])
