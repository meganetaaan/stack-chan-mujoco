"""Analytical cancellation and failing-load checks for load-cluster certificates."""
import argparse,json,subprocess,sys
from pathlib import Path
import numpy as np
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
inputs=a.out/'inputs';inputs.mkdir()
(inputs/'plan.json').write_text(json.dumps({'criteria':{'displacement_mm':.2,'stress_MPa':.2},'limitations':['analytical one-node fixture']}))
for i in range(6):
 u=np.zeros((1,3))
 if i<2:u[0,0]=1 if i==0 else -1
 stress=np.zeros((3,3,1,1))
 if i<2:stress[:,:,0,0]=np.diag([u[0,0],-u[0,0],0])
 np.savez_compressed(inputs/f'unit_{i}.npz',displacement_mm=u,stress_MPa=stress)
 (inputs/f'unit_{i}.json').write_text(json.dumps({'max_displacement_mm':float(np.linalg.norm(u)),
  'max_absolute_principal_MPa':float(abs(u[0,0])),'max_von_mises_MPa':float(abs(u[0,0])*np.sqrt(3))}))
cases={'cancel':np.array([[1.,1,0,0,0,0],[2.,2,0,0,0,0],[2.,2,0,0,0,0]]),
       'fail':np.array([[1.,0,0,0,0,0]])}
rows=[]
for name,w in cases.items():
 rows.append({'source':f'{name}/trace.npz','side':'left'})
 np.savez_compressed(inputs/(name+'_left_bounds.npz'),wrench_N_Nmm=w,time_s=np.arange(len(w)))
(inputs/'report.json').write_text(json.dumps({'rows':rows}))
script=Path(__file__).with_name('certify_yaw_load_clusters.py')
subprocess.run([sys.executable,str(script),'--bounds',str(inputs),'--out',str(a.out/'certificate')],check=True)
r=json.loads((a.out/'certificate/report.json').read_text())
assert r['total_samples']==4 and r['certified_samples']==3 and not r['passed']
cancel,fail=r['rows'];assert cancel['passed'] and cancel['response_upper'][0]==0
assert not fail['passed'] and fail['response_upper'][0]==1
np.testing.assert_allclose(fail['response_upper'],[1,1,np.sqrt(3)])
np.testing.assert_allclose(cancel['response_upper'],[0,0,0])
with np.load(a.out/'certificate/cancel_left.npz') as f:assert len(f['cluster_index'])==3 and np.all(f['cluster_index']>=0)
(a.out/'report.json').write_text(json.dumps({'analytical_check_passed':True,'scope':__doc__,
 'covers':['exact cancellation with initially failing triangle bound','duplicate loads in split','actual failing singleton','all-sample assignment']},indent=2)+'\n')
