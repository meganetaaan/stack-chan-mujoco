"""Screen unchanged archived torque/speed pairs at fixed lower servo voltages; no closed-loop performance claim."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
cp=Path('software/sim/actuator/catalog.json');jp=Path('board/mechanical/prototype/joints.json');catalog=json.loads(cp.read_text());joints=sorted(json.loads(jp.read_text()),key=lambda j:j['index'])
paths=[Path(f'validation/prototype_epic4_v1/actuator_fullbody_load_{side}_v1/trace.npz') for side in ['left','right']]
plan={'question':'Would a 3.7..4.2V direct-cell architecture preserve the archived torque/speed pairs within the existing endpoint model?',
 'voltages_V':[5.,4.2,3.7],'stop':'Two archived full-body turn traces at three fixed voltage points, no waveform tuning, no battery adoption or acceptance change.',
 'formula':'Use the same endpoint interpolation as drive.py: R=V/Istall, K=V/w0, eta=Tstall/(K Istall). Required current=tau/(eta K) for motoring, tau/(K/eta) for regeneration; bridge voltage=R I+K w.',
 'requirements_classification':'5V +/-5% remains the existing design target, not a user-required battery topology. Lower-voltage results are architecture diagnostics only.',
 'numeric_tolerance':1e-8,'source_sha256':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in [cp,jp,*paths]},
 'limits':['Same achieved archived torque/speed, not the requested or recomputed closed-loop trajectory','No battery cell, sag, loss, usable capacity, protection or Tab5 supply selected','Endpoint-fitted model, not guaranteed torque-speed curve or continuous rating','Latest mass, 10m walking and new closed-loop turning performance not evaluated','No brownout, switching or disconnected regeneration model']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');rows=[]
for path in paths:
 with np.load(path) as f:tau=f['torque_Nm'].copy();omega=f['angular_velocity_rad_s'].copy();t=f['time'].copy();baseline=f['motor_terminal_V'].copy()
 assert tau.shape==omega.shape==(len(t),len(joints))
 for voltage in plan['voltages_V']:
  detail=[];required=[]
  for i,j in enumerate(joints):
   spec=catalog['models'][j['motor'].removeprefix('ROBOTIS DYNAMIXEL ')]
   interp=lambda k:float(np.interp(voltage,spec['voltage_V'],spec[k]))
   stall=interp('stall_torque_Nm');current=interp('stall_current_A');speed=interp('no_load_speed_rpm')*np.pi/30
   R=voltage/current;K=voltage/speed;eta=stall/(K*current)
   kt=np.where(tau[:,i]*omega[:,i]>=0,eta*K,K/eta);I=tau[:,i]/kt;V=R*I+K*omega[:,i];required.append(V)
   badv=abs(V)>voltage+1e-8;badi=abs(I)>spec['analysis_current_limit_A']+1e-8
   k=int(np.argmax(abs(V)))
   detail.append({'joint':j['name'],'voltage_exceeded_samples':int(badv.sum()),'current_limit_exceeded_samples':int(badi.sum()),
     'max_abs_bridge_voltage_V':float(abs(V).max()),'max_abs_motor_current_A':float(abs(I).max()),'worst_voltage_time_s':float(t[k])})
  if voltage==5.:
   assert np.allclose(np.array(required).T,baseline,atol=1e-8,rtol=1e-8),'Baseline electrical reconstruction mismatch'
  rows.append({'source':str(path),'voltage_V':voltage,'samples':len(t),'joints':detail,
    'voltage_exceeded_joint_samples':sum(x['voltage_exceeded_samples'] for x in detail),
    'current_exceeded_joint_samples':sum(x['current_limit_exceeded_samples'] for x in detail)})
report={'rows':rows,'baseline_reconstruction_pass':True,'low_voltage_architecture_adopted':False,'manufacturing_release':False}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps([{k:v for k,v in row.items() if k!='joints'} for row in rows],indent=2))
