"""Evaluate solver completion and artificial anchor reactions of a pressure probe."""
import argparse,json,re
from pathlib import Path
import numpy as np
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True);a=p.parse_args()
plan=json.loads((a.run/'plan.json').read_text());run=json.loads((a.run/'run.json').read_text())
text=(a.run/'contact.dat').read_text()
def number(s):return float(re.sub(r'^([+-]?(?:\d+\.?\d*|\.\d+))([+-]\d{3})$',r'\1e\2',s.replace('D','E')))
rows=[]
for time,body in re.findall(r'(?<!total )forces \(fx,fy,fz\) for set ANCHORS and time\s+(\S+)\s*\n\s*\n(.*?)(?=\n\s*\n)',text,re.S):
 forces={int(v[0]):np.array([number(x) for x in v[1:]]) for line in body.splitlines() if (v:=line.split())}
 total=sum(forces.values(),np.zeros(3)); moment=np.zeros(3)
 for anchors in plan['anchors'].values():
  for anchor in anchors:moment+=np.cross(anchor['xyz'],forces[anchor['node']])
 scale=4*plan['force_per_corner_N']*number(time)
 rows.append({'time':number(time),'total_anchor_force_N':total.tolist(),'anchor_moment_Nmm':moment.tolist(),
  'largest_anchor_force_N':float(max(np.linalg.norm(f) for f in forces.values())),
  'relative_total_anchor_force':float(np.linalg.norm(total)/scale)})
complete=bool(rows and abs(rows[-1]['time']-1)<1e-7 and run['solver_finished'])
gates={'solver_completion':complete,'anchor_force':bool(complete and all(r['relative_total_anchor_force']<=plan['criteria']['relative_total_anchor_force_max'] for r in rows))}
report={'scope':__doc__,'increments':rows,'gates':gates,'passed':all(gates.values()),
 'joint_strength_verified':False,'actual_screw_preload_verified':False,
 'limitations':plan['limitations']+['small total anchor force alone does not rule out a self-equilibrated restraint effect; individual reactions and moments retained for review']}
# FRD nodal stresses are extrapolated/averaged diagnostics, not a convergence proof.
fields={}; active=None; time=None
for line in (a.run/'contact.frd').read_text().splitlines():
 if line.startswith('  100CL'): time=number(line.split()[2])
 elif line.startswith(' -4'):
  name=line.split()[1];active=(time,name) if name in ['DISP','STRESS'] else None
  if active:fields[active]={}
 elif line.startswith(' -3'):active=None
 elif active and line.startswith(' -1'):
  node=int(line[3:13]); values=[number(line[i:i+12]) for i in range(13,len(line),12) if line[i:i+12].strip()]
  fields[active][node]=values
if complete:
 counts=json.loads((Path(__file__).resolve().parents[3]/'validation/rear_contact_assembly_mesh_development_v1/ccx_v1/report.json').read_text())['parts']
 lower=1;diagnostics=[]
 for part in counts[:2]:
  ids=list(range(lower,lower+part['nodes']));lower+=part['nodes']
  u=np.array([fields[1.,'DISP'][n] for n in ids]);s=np.array([fields[1.,'STRESS'][n] for n in ids])
  assert u.shape==(len(ids),3) and s.shape==(len(ids),6)
  tensors=np.zeros((len(ids),3,3))
  tensors[:,0,0]=s[:,0];tensors[:,1,1]=s[:,1];tensors[:,2,2]=s[:,2]
  tensors[:,0,1]=tensors[:,1,0]=s[:,3];tensors[:,1,2]=tensors[:,2,1]=s[:,4];tensors[:,2,0]=tensors[:,0,2]=s[:,5]
  principal=np.max(np.abs(np.linalg.eigvalsh(tensors)),axis=1)
  vm=np.sqrt(.5*((s[:,0]-s[:,1])**2+(s[:,1]-s[:,2])**2+(s[:,2]-s[:,0])**2)+3*np.sum(s[:,3:]**2,axis=1))
  diagnostics.append({'part':part['part'],'maximum_nodal_displacement_mm':float(np.linalg.norm(u,axis=1).max()),
   'maximum_absolute_nodal_principal_MPa':float(principal.max()),'maximum_nodal_von_mises_MPa':float(vm.max()),
   'principal_peak_node':ids[int(np.argmax(principal))]})
 report['nodal_diagnostics']=diagnostics
 report['stress_interpretation']='Extrapolated nodal values on one linear tetrahedral mesh; not strength acceptance.'
(a.run/'evaluation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
