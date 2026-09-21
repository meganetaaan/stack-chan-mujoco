"""Bounded local stiffness comparison; no printed-joint strength acceptance."""
import argparse,hashlib,json
from pathlib import Path
import cadquery as cq
import numpy as np
from elasticity import tetrahedralize,analyze,select_boundary
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--imprint',action='store_true');a=p.parse_args()
a.out.mkdir(parents=True,exist_ok=False)
sources={'closed':'validation/boot_low_head_candidate_v1/cad/left_boot_shell.step','side_entry':'validation/boot_nut_side_entry_v2/left_boot_shell.step'}
plan={'purpose':'Determine whether the side opening changes local seat compliance under the same nut-patch force',
 'sources':{n:{'path':v,'sha256':hashlib.sha256(Path(v).read_bytes()).hexdigest()} for n,v in sources.items()},
 'crop_mm':{'x':[-38,-30],'y':[-18.5,-10.5],'z':[-16,-12.8]},
 'contact_boundary_imprinted':a.imprint,'mesh_mm':[1,.7], 'force_N':1,'young_MPa':1120,'poisson':.35,
 'assumptions':['Normalized 1 N load, not actual preload or gait force','Unqualified isotropic PETG modulus used equally for both shapes',
 'Floor facets selected by centroid within centered 4 mm square; discretization area measured',
 'Cut boundaries free; bottom plane either fully clamped or bilateral normal support',
 'Normal support nodal reactions are diagnostic, not a solved unilateral contact problem'],
 'criteria':{'area_relative_error_max':.05,'equilibrium_error_N':1e-7,'compliance_mesh_relative_change_max':.05},
 'stopping_rule':'Run only two mesh sizes and two supports for both shapes; if area/compliance criteria fail, report unresolved and reconsider load patch or support, not automatic refinement',
 'strength_acceptance':False}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
def contact_mesh(step,out,size):
 import gmsh,meshio
 from skfem.io import from_meshio
 gmsh.initialize()
 try:
  gmsh.option.setNumber('General.Terminal',0)
  volumes=gmsh.model.occ.importShapes(str(step))
  rectangle=gmsh.model.occ.addRectangle(-36,-16.5,-14.6,4,4)
  disk=gmsh.model.occ.addDisk(-34,-14.5,-14.6,1.15,1.15)
  patch,_=gmsh.model.occ.cut([(2,rectangle)],[(2,disk)])
  gmsh.model.occ.fragment(volumes,patch)
  gmsh.model.occ.synchronize()
  gmsh.option.setNumber('Mesh.MeshSizeMin',size)
  gmsh.option.setNumber('Mesh.MeshSizeMax',size)
  gmsh.model.mesh.generate(3);gmsh.write(str(out))
 finally:gmsh.finalize()
 return from_meshio(meshio.read(out))
rows=[]
for variant,source in sources.items():
 shape=cq.importers.importStep(source).val().intersect(cq.Workplane('XY').box(8,8,3.2).val().translate((-34,-14.5,-14.4)))
 assert shape.isValid() and len(shape.Solids())==1
 step=a.out/(variant+'.step');cq.exporters.export(shape,str(step))
 for size in plan['mesh_mm']:
  mesh=(contact_mesh if a.imprint else tetrahedralize)(step,a.out/f'{variant}_{size}.msh',size)
  selector=lambda x:(abs(x[2]+14.6)<1e-6)&(abs(x[0]+34)<2)&(abs(x[1]+14.5)<2)
  ids=select_boundary(mesh,selector);tri=mesh.p[:,mesh.facets[:,ids]]
  area=float(np.linalg.norm(np.cross((tri[:,1]-tri[:,0]).T,(tri[:,2]-tri[:,0]).T),axis=1).sum()/2)
  for mode in ('clamped','normal_z'):
   r,d=analyze(mesh,lambda x:abs(x[2]+16)<1e-6,selector,[-34,-14.5,-14.6],[0,0,-1,0,0,0],1120,.35,support_mode=mode)
   react=d['reaction_N'];nodes=d['nodes_mm'];support=abs(nodes[:,2]+16)<1e-6
   total=react.sum(axis=0)+d['load_N'].sum(axis=0)
   r.update({'variant':variant,'mesh_mm':size,'loaded_area_mm2':area,
    'area_relative_error':abs(area/11.845243715627511-1),
    'unit_force_compliance_mm_per_N':2*r['strain_energy_Nmm'],
    'force_balance_error_N':float(np.linalg.norm(total)),
    'negative_support_nodal_reaction_sum_N':float(np.minimum(react[support,2],0).sum()),
    'negative_nodal_reaction_caution':'P2 equivalent nodal force signs do not by themselves prove tensile contact traction'})
   rows.append(r)
   print(json.dumps({k:r[k] for k in ('variant','mesh_mm','support_mode','loaded_area_mm2','unit_force_compliance_mm_per_N')}),flush=True)
comparisons=[]
for mode in ('clamped','normal_z'):
 by={v:[x for x in rows if x['variant']==v and x['support_mode']==mode] for v in sources}
 ratios={v:abs(xs[-1]['unit_force_compliance_mm_per_N']/xs[-2]['unit_force_compliance_mm_per_N']-1) for v,xs in by.items()}
 comparisons.append({'support_mode':mode,'compliance_mesh_relative_changes':ratios,
  'opening_to_closed_compliance_ratio_finer_mesh':by['side_entry'][-1]['unit_force_compliance_mm_per_N']/by['closed'][-1]['unit_force_compliance_mm_per_N'],
  'numerical_screen_pass':all(z<=.05 for z in ratios.values()) and all(x['area_relative_error']<=.05 and x['force_balance_error_N']<=1e-7 for xs in by.values() for x in xs)})
(a.out/'report.json').write_text(json.dumps({'rows':rows,'comparisons':comparisons,'effect_resolution_note':'Opening effect below observed mesh changes is not resolved in sign or precise magnitude','joint_strength_verified':False,'manufacturing_release':False},indent=2)+'\n')
