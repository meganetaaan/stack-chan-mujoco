"""PETG solid estimate for current rigid foot parts; not complete ankle-body inertia."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
p.add_argument('--inventory',type=Path,default=Path('board/mechanical/prototype/foot_candidate/revB/inventory.json'))
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
ip=a.inventory
mp=Path('board/mechanical/prototype/rc_battery_tray_revB/material_candidate.json')
inv=json.loads(ip.read_text());mat=json.loads(mp.read_text());rho=mat['typical_density_g_cm3']
rows=[];groups=[]
for side in ['left','right']:
    selected=[]
    for x in inv['parts']:
        if x['side']!=side or x['part'] not in {'boot','yoke','holder'}:continue
        mass=x['volume_mm3']*rho*1e-6;com=np.array(x['com_mm'])*1e-3
        inertia=np.array(x['volume_inertia_about_com_mm5'])*rho*1e-12
        row={'side':side,'part':x['part'],'mass_kg':mass,'com_m':com.tolist(),'inertia_at_com_kg_m2':inertia.tolist()}
        rows.append(row);selected.append(row)
    assert len(selected)==3
    total=sum(x['mass_kg'] for x in selected)
    center=sum((x['mass_kg']*np.array(x['com_m']) for x in selected),np.zeros(3))/total
    combined=np.zeros((3,3))
    for x in selected:
        delta=np.array(x['com_m'])-center
        combined+=np.array(x['inertia_at_com_kg_m2'])+x['mass_kg']*(np.dot(delta,delta)*np.eye(3)-np.outer(delta,delta))
    eig=np.linalg.eigvalsh(combined)
    assert min(eig)>0 and max(eig)<=sum(eig)-max(eig)+1e-12
    groups.append({'side':side,'mass_kg':total,'com_m':center.tolist(),'inertia_at_com_kg_m2':combined.tolist(),'principal_inertias_kg_m2':eig.tolist()})
r={'material_comparison':mat['product'],'density_g_cm3':rho,'parts':rows,'rigid_subassemblies':groups,'source_sha256':{str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in [ip,mp]},'complete_foot_inertia':False,'model_updated':False,'manufacturing_release':False,'excludes':['Contact layer density and material','Metal washer screw and nut','Servo horn fasteners and harness','Printed voids and process variation'],'coordinate_frame':'Local foot CAD coordinates; verify MJCF frame transform before insertion'}
(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print([(x['side'],x['mass_kg'],x['com_m']) for x in groups])
