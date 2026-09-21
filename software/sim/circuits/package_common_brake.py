"""Package explicit candidate connectivity without inventing missing values."""
import csv,json,hashlib
from pathlib import Path
out=Path('schematics/power/common_brake_revA')
root=out.parent
cards={name:json.loads((root/f'{name}_candidate.json').read_text()) for name in ['brake_detector','brake_gate_driver','brake_mosfet']}
rows=[]
def add(ref,part,value,pins):
    for pin,net in pins.items():rows.append([ref,part,value,pin,net])
for suffix in ['A','B']:
    sense=f'SENSE_{suffix}';cmd=f'CMD_{suffix}';gate=f'GATE_{suffix}';drv=f'DRIVE_{suffix}';drain=f'DRAIN_{suffix}';source=f'SOURCE_{suffix}'
    add(f'UDET_{suffix}',cards['brake_detector']['part_number'],'',{'1':cmd,'2':'GND','3':sense,'4':'GND','5':'SERVO_BUS','6':f'NC_OUTB_{suffix}'})
    add(f'UDRV_{suffix}',cards['brake_gate_driver']['part_number'],'',{'1':'SERVO_BUS','2':'GND','3':cmd,'4':'GND','5':drv})
    add(f'Q_{suffix}',cards['brake_mosfet']['part_number'],'logical pins only',{'G':gate,'D':drain,'S':source})
    for ref,part,value,n1,n2 in [
        ('RTOP','TNPW0603127KBYEA','127k','SERVO_BUS',sense),
        ('RBOT','TNPW060310K0BYEA','10k',sense,'GND'),
        ('RPULL','TBD','10k candidate','SERVO_BUS',cmd),
        ('RGATE','TBD','TBD',drv,gate),
        ('RGS','TBD','TBD',gate,source),
        ('RBRAKE','Vishay AC10 order code TBD','5.1 ohm candidate','SERVO_BUS',drain),
        ('RSHUNT','TBD','0.1 ohm candidate',source,'GND'),
        ('CDET','TBD','TBD effective capacitance','SERVO_BUS','GND'),
        ('CDRV','TBD','TBD effective capacitance','SERVO_BUS','GND')]:
        add(f'{ref}_{suffix}',part,value,{'1':n1,'2':n2})
with (out/'connections.csv').open('w',newline='') as f:
    writer=csv.writer(f);writer.writerow(['reference','part_candidate','value','pin','net']);writer.writerows(rows)
report={'components':len({r[0] for r in rows}),'connections':len(rows),'manufacturing_release':False,'spice_model':False,'source_hashes':{str(root/f'{n}_candidate.json'):hashlib.sha256((root/f'{n}_candidate.json').read_bytes()).hexdigest() for n in cards}}
(out/'inventory.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
