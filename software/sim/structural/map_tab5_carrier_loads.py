"""Conditional load distribution, not a strength or preload qualification."""
import hashlib
import json
from pathlib import Path
import cadquery as cq
import numpy as np
from estimate_battery_translation_load import estimate_force

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'validation/tab5_carrier_load_map_v1'
OUT.mkdir(exist_ok=True)
plan = {
    'purpose': 'Identify axial, shear and moment demands before any local FE refinement',
    'support_positions_base_m': [[.042, y, z] for y in [-.058, .058] for z in [.088, .112]],
    'reference_base_m': [.042, 0, .100],
    'load_sharing_assumption': 'Rigid carrier and four equal isotropic point springs; not a conservative bound',
    'mass_assumptions': {'tab5_kg': .1184, 'tab5_center_m': [.058, 0, .088],
                         'carrier_density_kg_m3': 1270},
    'exclusions': ['Insert and Tab5 fastening hardware mass', 'Tab5 COM measurement',
                   'Rotational inertia couple', 'Preload and friction/contact separation',
                   'Updated robot dynamics, fall and emergency stop'],
    'criteria': ['Six independent unit wrenches reproduce force and moment within 1e-10',
                 'Retain simultaneous vectors and timestamps, not combined component extrema'],
    'stop': 'One algebraic map and two frozen EPIC4 traces; no strength acceptance or mesh sweep'
}
(OUT/'plan.json').write_text(json.dumps(plan, indent=2)+'\n')
positions = np.array(plan['support_positions_base_m'])
reference = np.array(plan['reference_base_m'])
def skew(r):
    x,y,z = r
    return np.array([[0,-z,y],[z,0,-x],[-y,x,0]])
A = np.vstack([np.tile(np.eye(3),(1,4)), np.hstack([skew(p-reference) for p in positions])])
# Scale moment rows to improve conditioning; exact full-rank constraints unchanged.
scale = np.diag([1,1,1,100,100,100])
B = np.linalg.pinv(scale@A)@scale
assert np.linalg.matrix_rank(A) == 6
error = float(np.max(np.abs(A@B-np.eye(6))))
assert error < 1e-10
carrier_path = ROOT/'validation/tab5_insert_candidate_v1/carrier_print.step'
carrier = cq.importers.importStep(str(carrier_path)).val()
# Use pre-install polymer as a dimensional comparison, not an as-built mass.
mass_carrier = carrier.Volume()*1e-9*1270
center_carrier = np.array(carrier.Center().toTuple())/1000
components = [('Tab5', .1184, np.array([.058,0,.088])),
              ('carrier_uniform_solid_PETG', mass_carrier, center_carrier)]
rows=[]
paths=[carrier_path]
for path in sorted((ROOT/'validation/prototype_epic4_v1').glob('actuator_fullbody_load_*/trace.npz')):
    paths.append(path)
    with np.load(path) as d:
        t=d['time'];q=d['qpos']
    force=np.zeros((len(t),3));moment=np.zeros_like(force)
    for _,mass,center in components:
        _,f=estimate_force(t,q,mass,center)
        force+=f
        moment+=np.cross(center-reference,f)
    wrench=np.column_stack([force,moment])
    loads=(wrench@B.T).reshape(-1,4,3)
    residual=float(np.max(np.abs(loads.reshape(-1,12)@A.T-wrench)))
    assert residual<1e-10
    valid=np.arange(2,len(t)-2)
    axial=np.abs(loads[:,:,1])
    shear=np.linalg.norm(loads[:,:,[0,2]],axis=2)
    selected=[]
    for label,array in [('axial_abs',axial),('shear_norm',shear)]:
        local,node=np.unravel_index(np.argmax(array[valid]),array[valid].shape)
        i=int(valid[local])
        selected.append({'criterion':label,'time_s':float(t[i]),'node':int(node),
                         'value_N':float(array[i,node]),'simultaneous_wrench_N_Nm':wrench[i].tolist(),
                         'all_four_node_force_N':loads[i].tolist()})
    np.savez_compressed(OUT/(path.parent.name+'.npz'), time_s=t,
                        applied_force_N=force,force_transfer_moment_Nm=moment,
                        node_force_N=loads,valid_indices=valid)
    rows.append({'source':str(path.relative_to(ROOT)),'equilibrium_residual':residual,'selected':selected})
static_force=sum((np.array([0,0,-9.81])*mass for _,mass,_ in components),start=np.zeros(3))
static_moment=sum((np.cross(center-reference,np.array([0,0,-9.81])*mass)
                   for _,mass,center in components),start=np.zeros(3))
result={'status':'conditional_force_transfer_not_design_upper_bound',
        'components':[{'name':name,'mass_kg':mass,'center_base_m':center.tolist()} for name,mass,center in components],
        'unit_wrench_equilibrium_error':error,'load_map_12_by_6':B.tolist(),
        'static_wrench_N_Nm':np.r_[static_force,static_moment].tolist(),
        'static_node_force_N':(B@np.r_[static_force,static_moment]).reshape(4,3).tolist(),
        'cases':rows,'manufacturing_release':False,'source_sha256':{
            str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
(OUT/'report.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ['load_map_12_by_6','source_sha256']},indent=2))
