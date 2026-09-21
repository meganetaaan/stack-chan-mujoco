"""Instantiate two separate PG receiver candidates from reviewed single-channel data."""
import argparse, csv, hashlib, json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
src=Path('schematics/power/manual_rearm_revI/assembly.json')
assembly=json.loads(src.read_text());byref={x['reference']:x for x in assembly['parts']}
rpath=Path('schematics/power/manual_rearm_resistors_revI.json');res={x['reference']:x for x in json.loads(rpath.read_text())['resistors']}
cpath=Path('schematics/power/manual_rearm_capacitors.json');cap=json.loads(cpath.read_text())
parts=[]
links=[]
for side in ['LEFT','RIGHT']:
    links.append({'name':side+'_PG_TRACE','from':side+'_PG_SOURCE','to':side+'_EFUSE_PG','type':'PCB trace, not a resistor','placement':'Pullup R10 at eFuse source end; R11/R12 at receiver end'})
    rename={'MAIN_EFUSE_PG':side+'_EFUSE_PG','PG_DIVIDED':side+'_PG_DIVIDED','PG_CONDITIONED_OD':side+'_PG_CONDITIONED_OD','PG_CONDITIONED':side+'_PG_CONDITIONED'}
    for ref in ['U12','U13','R10','R11','R12','R13','C12','C13']:
        item=json.loads(json.dumps(byref[ref]));item['reference']=side+'_'+ref
        item['pins']={pin:rename.get(net,net) for pin,net in item['pins'].items()}
        if ref=='R10':
            item['pins']['2']=side+'_PG_SOURCE'
            item['placement']='At eFuse PG pin, before monitored trace'
        if ref in res:item['part']=res[ref]['part_number']
        if ref.startswith('C'):item['part']=cap['part_number']
        item['origin_reference']=ref;parts.append(item)
left={net for x in parts if x['reference'].startswith('LEFT') for net in x['pins'].values() if net}
right={net for x in parts if x['reference'].startswith('RIGHT') for net in x['pins'].values() if net}
assert left & right == {'GND','LOGIC3V3'}
assert len({x['reference'] for x in parts})==len(parts)
report={'interconnects':links,'parts':parts,'shared_nets':sorted(left & right),'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [src,rpath,cpath]},'manufacturing_release':False,'electrical_qualification':False,'scope':'Two PG receiver subcircuits only; replaces single receiver when integrated, not an addition to it','remaining':['Monitor power-transition validity','PG source pin compatibility for selected eFuse','Open-wire and stuck-high faults','Logic supply budget after duplication','Sequencer and independent source UV/OV monitors']}
(a.out/'connectivity.json').write_text(json.dumps(report,indent=2)+'\n')
with (a.out/'pins.csv').open('w') as f:
    w=csv.writer(f);w.writerow(['reference','part','pin','net'])
    for x in parts:
        for pin,net in x['pins'].items():w.writerow([x['reference'],x['part'],pin,net or 'NC'])
print(json.dumps({'parts':len(parts),'pins':sum(len(x['pins']) for x in parts),'shared_nets':report['shared_nets']}))
