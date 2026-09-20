"""Reimport every prototype STEP/STL and measure the assembled R4 envelope."""
import json, sys
from pathlib import Path
import numpy as np
import cadquery as cq
import trimesh
ROOT=Path(__file__).resolve().parents[1]
parts=json.loads((ROOT/'models/components.json').read_text())['parts']
rows=[]
for p in parts:
    if p['role']!='custom': continue
    sp=ROOT/'cad/step'/f"{p['name']}.step"; mp=ROOT/'cad/stl_prototype'/f"{p['name']}.stl"
    sh=cq.importers.importStep(str(sp)).val(); m=trimesh.load_mesh(mp,process=True)
    error=abs(sh.Volume()-p['volume_mm3'])/p['volume_mm3']
    ok=sh.isValid() and len(sh.Solids())==1 and error<1e-7 and m.is_watertight and m.is_winding_consistent and abs(m.bounds[0,2])<.01
    rows.append(dict(name=p['name'],step_valid=sh.isValid(),step_solids=len(sh.Solids()),volume_relative_error=error,stl_watertight=bool(m.is_watertight),stl_winding_consistent=bool(m.is_winding_consistent),print_min_z_mm=float(m.bounds[0,2]),pass_=bool(ok)))
asm=cq.importers.importStep(str(ROOT/'cad/step/assembly.step')).val();b=asm.BoundingBox()
expected=sum(p['volume_mm3'] for p in parts); ae=abs(asm.Volume()-expected)/expected
rep={'status':'PASS' if all(p['pass_'] for p in rows) and asm.isValid() and len(asm.Solids())==len(parts) and ae<1e-7 else 'FAIL',
     'assembly_solids':len(asm.Solids()),'expected_solids':len(parts),'assembly_valid':asm.isValid(),'assembly_volume_relative_error':ae,'nominal_assembly_dimensions_mm':{'width':b.ylen,'depth':b.xlen,'height':b.zlen},'prototype_print_parts':rows,'manufacturing_release':False}
(ROOT/'reports/exports.json').write_text(json.dumps(rep,indent=2));print(rep['status'],rep['assembly_solids'],rep['nominal_assembly_dimensions_mm'])
if rep['status']!='PASS':sys.exit(1)
