"""Audit initial contact geometry of the current rear connection CAD candidate."""
import argparse,hashlib,json,itertools,math
from pathlib import Path
import cadquery as cq
ROOT=Path(__file__).resolve().parents[3]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
config_path=ROOT/'board/mechanical/engineering/rear_connection_candidate.json';config=json.loads(config_path.read_text())
paths={k:ROOT/v['path'] for k,v in config['assets'].items()}
for k,f in paths.items():assert hashlib.sha256(f.read_bytes()).hexdigest()==config['assets'][k]['sha256']
source=paths['body'].parent
rear=ROOT/'validation/rear_joint_assembly_development_v1/rear_joint_socket_double_v1'
for i in range(4):
 for kind in ['bolt','nut','inner_washer']:paths[f'{kind}_{i}']=source/f'corner_{i}_{kind}.step'
 paths[f'rear_washer_{i}']=rear/f'corner_{i}_rear_washer.step'
plan={'scope':__doc__,'criteria':{'unintended_overlap_mm3':.01,'contact_distance_mm':1e-6,'minimum_contact_area_mm2':1.},
      'source_sha256':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [config_path,*paths.values()]},
      'contact_law_target':'unilateral compression; actual friction, preload and joint compliance to be specified',
      'thread_model':'bolt major-diameter envelope overlaps nut minor-diameter envelope; not a physical thread contact mesh',
      'limitations':['initial nominal geometry only','no deformation/preload/material solve','CAD faces are not yet mapped to FE contact elements','no manufacturing tolerance or roughness contact state']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
parts={k:cq.importers.importStep(str(f)).val() for k,f in paths.items()}
expected=[('body','rear_plate',-62.2,'body_plate')]
for i in range(4):
 expected.extend([(f'bolt_{i}',f'rear_washer_{i}',-64.7,f'head_washer_{i}'),
                  (f'rear_washer_{i}','rear_plate',-64.2,f'washer_plate_{i}'),
                  ('body',f'inner_washer_{i}',-56.2,f'body_washer_{i}'),
                  (f'inner_washer_{i}',f'nut_{i}',-55.7,f'washer_nut_{i}')])
def faces_at_x(s,x):
 return [(i,f) for i,f in enumerate(s.Faces()) if f.geomType()=='PLANE' and abs(f.BoundingBox().xmin-x)<1e-6 and abs(f.BoundingBox().xmax-x)<1e-6]
contacts=[]
for left,right,x,name in expected:
    patches=[];pairs=[]
    for i,fa in faces_at_x(parts[left],x):
      for j,fb in faces_at_x(parts[right],x):
        common=fa.intersect(fb)
        if common.Area()>1e-8:
            dot=fa.normalAt().dot(fb.normalAt())
            assert dot<-.999999,(name,dot)
            patches.extend(common.Faces());pairs.append({'left_face_index':i,'right_face_index':j,'area_mm2':float(common.Area()),'normal_dot':float(dot)})
    area=sum(f.Area() for f in patches)
    if patches:cq.exporters.export(cq.Compound.makeCompound(patches),str(a.out/(name+'.step')))
    distance=float(parts[left].distance(parts[right]))
    contacts.append({'name':name,'parts':[left,right],'plane_x_mm':x,'area_mm2':area,'distance_mm':distance,'face_pairs':pairs,'passed':bool(area>=1 and distance<=1e-6)})
interfaces=[];unexpected=[];threads=[]
for (ka,sa),(kb,sb) in itertools.combinations(parts.items(),2):
    distance=float(sa.distance(sb));volume=float(sa.intersect(sb).Volume()) if distance<1e-6 else 0.
    row={'parts':[ka,kb],'distance_mm':distance,'overlap_mm3':volume};interfaces.append(row)
    intentional=any({ka,kb}=={f'bolt_{i}',f'nut_{i}'} for i in range(4))
    if volume>.01:(threads if intentional else unexpected).append(row)
report={'scope':__doc__,'contacts':contacts,'interfaces':interfaces,'intentional_thread_envelope_overlaps':threads,'unintended_overlaps':unexpected,
        'gates':{'all_expected_contacts':all(r['passed'] for r in contacts),'no_unintended_overlap':not unexpected,'four_thread_placeholders_identified':len(threads)==4},
        'contact_load_path_verified':False,'preload_verified':False,'note':'Replace thread-envelope overlap with an explicit calibrated connector or resolved thread model before solving.'}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'gates':report['gates'],'contacts':[{k:r[k] for k in ['name','area_mm2','distance_mm']} for r in contacts],'thread_overlaps':threads}))
