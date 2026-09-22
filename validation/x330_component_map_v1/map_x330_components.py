"""Identify STEP assembly components and map nominal surfaces to ankle frame."""
import argparse,hashlib,json
from pathlib import Path
import cadquery as cq
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.XCAFDoc import XCAFDoc_DocumentTool
from OCP.TDF import TDF_LabelSequence,TDF_Label
from OCP.TDataStd import TDataStd_Name
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--step',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
D=TDocStd_Document(TCollection_ExtendedString('doc'));R=STEPCAFControl_Reader();R.SetNameMode(True)
R.ReadFile(str(a.step))
if not R.Transfer(D):raise RuntimeError('STEP transfer failed')
S=XCAFDoc_DocumentTool.ShapeTool_s(D.Main());roots=TDF_LabelSequence();S.GetFreeShapes(roots)
if roots.Length()!=1:raise ValueError('Expected single assembly')
components=TDF_LabelSequence();S.GetComponents_s(roots.Value(1),components);rows=[]
for i in range(1,components.Length()+1):
 instance=components.Value(i);ref=TDF_Label()
 if not S.GetReferredShape_s(instance,ref):ref=instance
 n=TDataStd_Name()
 if not ref.FindAttribute(TDataStd_Name.GetID_s(),n):raise ValueError('Unnamed component')
 name=n.Get().ToExtString();shape=cq.Shape.cast(S.GetShape_s(instance));b=shape.BoundingBox()
 rows.append(dict(index=i-1,product_name=name,solid_count=len(shape.Solids()),volume_mm3=shape.Volume(),bounds_mm={k:getattr(b,k) for k in ('xmin','xmax','ymin','ymax','zmin','zmax')},
                  mapped_x_bounds_mm=[b.zmin-3.5,b.zmax-3.5]))
report=dict(source_sha256=hashlib.sha256(a.step.read_bytes()).hexdigest(),components=rows,
            proposed_mapping={'formula_mm':['x=source_z-3.5','y=-source_x','z=-source_y'],'reference':'Front case plane source Z=3.5 mapped to simplified motor front plane X=0; coaxial alignment assumes source X=Y=0','status':'nominal geometric registration; not approved installed transform'},
            limits=['CAD component names do not establish screw selection or purchased BOM.',
                    'Source assemblies may include shell representations as well as solids; do not sum volume to infer mass.',
                    'CAD is nominal, no tolerance or thread engagement inferred.'])
a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps([r for r in rows if 'HORN' in r['product_name'] or 'CASE_' in r['product_name']],indent=2))
