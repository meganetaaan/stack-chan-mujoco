"""Static necessity of tensile load transfer; not a preload/contact solution."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from scipy.optimize import linprog
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
load_path=Path('validation/yaw_shelf_compliance_v1/plan.json');seat_path=Path('validation/yaw_metal_seat_v4/report.json')
load=json.loads(load_path.read_text());seat=json.loads(seat_path.read_text())['rows'][0]
axes=np.asarray(seat['plate_support_axes']);centre=np.r_[axes.mean(axis=0),89.]
plan={'question':'Can normal compression alone transfer the archived force and bending moments from plate to shelf?',
 'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [load_path,seat_path]},
 'contact_outer_rectangle_xy_mm':[-37.5,11.6,9.5,42.5],
 'compression_sign':'Positive Z is plate pressing into underside of shelf at Z89.',
 'stop':'One archived resultant; reference-point shift, compression-only feasibility and minimum total tensile force lower bound. No parameter sweep.',
 'limits':['Rectangle overestimates actual contact region by filling holes and relief; feasibility would not prove real contact.','Point bolt axes, rigid static normal balance only; no preload, compliance, friction, shear or torsion capacity.','Lower bound on total tensile transfer is not bolt preload, per-bolt maximum, safety factor or allowable.','No strength or manufacturing release.']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
w=np.asarray(load['source_case']['selected_wrench_N_Nmm']);F=w[:3];M=w[3:]+np.cross(np.asarray(load['origin_mm'])-centre,F)
assert np.allclose(M+np.cross(centre-np.asarray(load['origin_mm']),F),w[3:])
# A unit +Z force at a point contributes [Fz, Mx, My] = [1, dy, -dx].
def normal_columns(points):
 r=np.asarray(points)-centre[:2]
 return np.vstack([np.ones(len(r)),r[:,1],-r[:,0]])
corners=np.array([[x,y] for x in [-37.5,11.6] for y in [9.5,42.5]])
C=normal_columns(corners);B=normal_columns(axes);target=np.array([F[2],M[0],M[1]])
compress=linprog(np.zeros(4),A_eq=C,b_eq=target,bounds=(0,None),method='highs')
if compress.status not in [0,2]:raise RuntimeError(compress.message)
combined=np.hstack([C,-B]);minimum=linprog(np.r_[np.zeros(4),np.ones(4)],A_eq=combined,b_eq=target,bounds=(0,None),method='highs');assert minimum.success
assert np.allclose(combined@minimum.x,target,atol=1e-7)
# Equal axial stiffness / rigid plate diagnostic; not actual fastener forces.
axial=B.T@np.linalg.solve(B@B.T,target);assert np.allclose(B@axial,target)
cop=centre[:2]+np.array([-M[1],M[0]])/F[2] if F[2]>0 else None
result={'reference_point_mm':centre.tolist(),'shifted_wrench_N_Nmm':np.r_[F,M].tolist(),
 'compression_only_possible_in_expanded_rectangle':bool(compress.success),'compression_solver_status':int(compress.status),
 'required_normal_centre_of_pressure_xy_mm':None if cop is None else cop.tolist(),
 'minimum_total_negative_Z_transfer_N':float(minimum.fun),
 'lower_bound_solution':{'corner_compression_N':minimum.x[:4].tolist(),'bolt_axis_tensile_transfer_N':minimum.x[4:].tolist()},
 'equal_axial_stiffness_diagnostic':{'axes_xy_mm':axes.tolist(),'signed_axial_N':axial.tolist()},
 'not_evaluated_wrench_components':['Fx','Fy','Mz'],'manufacturing_release':False}
(a.out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
