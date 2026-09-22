"""Identify individual fixed parts at the closest sampled yaw poses; audit allowance arithmetic."""
import argparse
import hashlib
import json
from pathlib import Path
import cadquery as cq
import numpy as np

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--candidate',type=Path,required=True)
p.add_argument('--motion',type=Path,required=True)
a=p.parse_args()
invpath=a.candidate/'inventory.json';assembly=a.candidate/'yaw_support_candidate.step'
parts=json.loads(invpath.read_text())['parts'];solids=cq.importers.importStep(str(assembly)).val().Solids()
assert len(parts)==len(solids)
for part,solid in zip(parts,solids):
    assert abs(part['volume_mm3']-solid.Volume())<1e-5
planpath=a.motion/'plan.json';reportpath=a.motion/'report.json'
plan=json.loads(planpath.read_text());report=json.loads(reportpath.read_text())
assert plan['include_cradle'] and plan['angle_scope']=='model joint limits'
rows=[]
for result in report['results']:
    assert result['cad_sha256'][str(assembly)]==hashlib.sha256(assembly.read_bytes()).hexdigest()
    side=result['side'];sign=1 if side=='left' else -1
    movingdir=Path('software/sim/mujoco/assets')
    coupler=cq.importers.importStep(str(movingdir/'r9_fast_turn_v1/cad'/f'{side}_yaw_coupler.step')).val()
    cradle=cq.importers.importStep(str(movingdir/'r8_yaw_offset_flange_v1/cad'/f'{side}_fixed_roll_cradle.step')).val().translate((0,sign*4,0))
    pivot=(-5,sign*26,62)
    moving=cq.Compound.makeCompound([coupler,cradle]).rotate(pivot,(-5,sign*26,63),float(np.rad2deg(result['minimum_angle_rad'])))
    distances=sorted([{'part':part['name'],'distance_mm':float(solid.distance(moving))} for part,solid in zip(parts,solids)],key=lambda r:r['distance_mm'])
    assert abs(distances[0]['distance_mm']-result['minimum_sampled_distance_mm'])<1e-6
    criteria=plan['criteria']
    allowance=result['minimum_sampled_distance_mm']-result['sampling_miss_bound_mm']-2*criteria['tolerance_per_part_mm']-criteria['residual_clearance_min_mm']
    rows.append({'side':side,'sample_angle_rad':result['minimum_angle_rad'],'nearest_five':distances[:5],
                 'total_deformation_budget_at_required_clearance_mm':allowance,
                 'currently_allocated_total_deformation_mm':2*criteria['assumed_deflection_per_part_mm'],
                 'additional_budget_over_existing_allocation_mm':allowance-2*criteria['assumed_deflection_per_part_mm']})
out={'source_sha256':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in [invpath,assembly,planpath,reportpath]},'rows':rows,
     'limits':['Nearest part identified at sampled worst pose only; other parts may be nearest at other angles.',
               'Budget is available combined relative motion, not proven actual deformation.',
               'Support FE absolute displacement does not give moving assembly or shroud relative displacement.',
               'Yaw coupler plus roll cradle only; no complete articulated legs, cables, servos or tool access.'],
     'criteria_changed':False,'manufacturing_release':False}
(a.motion/'neighbours.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
