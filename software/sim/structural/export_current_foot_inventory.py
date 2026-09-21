"""Assemble current split-sole comparison; retain density-parametric inertial data."""
import argparse, hashlib, itertools, json
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--out',type=Path,required=True)
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
rows=[];checks=[]
for side in ['left','right']:
    sources={
      'boot':f'validation/boot_low_head_candidate_v1/cad/{side}_boot_shell.step',
      'yoke':f'validation/sole_recessed_seat_v3/{side}_yoke.step',
      'holder':f'validation/sole_recessed_seat_v3/{side}_holder_envelope.step',
      'contact_layer':f'validation/sole_contact_split_v1/{side}_contact_layer.step',
      'washer':f'validation/sole_clamp_seat_v1/{side}_clamp_washer.step',
      'screw':f'validation/sole_external_nut_v1/{side}_screw.step',
      'nut':f'validation/sole_external_nut_v1/{side}_nut.step',
    }
    assembly=cq.Assembly(name=side+'_foot_comparison')
    parts={}
    for name,filename in sources.items():
        path=Path(filename);shape=cq.importers.importStep(str(path)).val()
        assert shape.isValid() and len(shape.Solids())==1
        parts[name]=shape;assembly.add(shape,name=name)
        rows.append({'side':side,'part':name,'source':filename,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
          'volume_mm3':shape.Volume(),'com_mm':shape.Center().toTuple(),
          'volume_inertia_about_com_mm5':cq.Shape.matrixOfInertia(shape),
          'density_g_cm3':None,'mass_kg':None,
          'material_status':'ABS/PETG candidate' if name in ['boot','yoke','holder'] else 'TPU or purchased sheet, undecided' if name=='contact_layer' else 'Metal part; material and actual part geometry need qualification'})
    for (n,s),(m,t) in itertools.combinations(parts.items(),2):
        checks.append({'side':side,'parts':[n,m],'overlap_mm3':s.intersect(t).Volume()})
    assembly.export(str(a.out/f'{side}_foot.step'))
report={'parts':rows,'pair_checks':checks,'manufacturing_release':False,
 'removed':'Old bypass spacer and monolithic TPU sole; do not include alongside replacements',
 'scope':'Seven-part comparison per foot, excludes servo/horn hardware and harness',
 'conversion':'For uniform density rho in g/cm3: mass_kg=volume_mm3*rho*1e-6; inertia_kg_m2=volume_inertia_mm5*rho*1e-12. COM is local CAD coordinates.',
 'model_updated':False}
(a.out/'inventory.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'parts':len(rows),'pair_checks':len(checks),'max_overlap_mm3':max(x['overlap_mm3'] for x in checks)}))
