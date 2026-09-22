"""Inspect vendor fixture waveforms, not a loaded-board simulation."""
import argparse,hashlib,json,re,zipfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--archive',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
plan={'question':'Does vendor output_3p3 contain usable voltage/corner edge data for the MR-buffer link?', 'stop':'Inspect four fixture waveforms at three provided corners; no board-qualification claim.', 'comparison_window_V':[.8,2.0],'reference_input_limit_ns_per_V':10,'warning':'Fixture is 300 ohm with C_fixture=0; Cref=2pF is a reference parameter, not the external fixture capacitance.'}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
s=zipfile.ZipFile(a.archive).read('sn74hcs11.ibs').decode()
section=s.split('[Model]    output_3p3')[1].split('[Model]    output_5p5')[0]
rows=[]
for n,m in enumerate(re.finditer(r'\[(Rising|Falling) Waveform\]([^\[]*)',section)):
 text=m.group(2);pts=[]
 for line in text.splitlines():
  try:
   v=[float(x) for x in line.split()]
   if len(v)==4:pts.append(v)
  except ValueError:pass
 def cross(col,target):
  for u,v in zip(pts,pts[1:]):
   if min(u[col],v[col])<=target<=max(u[col],v[col]) and u[col]!=v[col]:return u[0]+(target-u[col])*(v[0]-u[0])/(v[col]-u[col])
  raise ValueError('No crossing')
 for col,corner in enumerate(['typ_3.3V_27C','slow_3.0V_150C','fast_3.6V_minus55C'],1):
  dt=abs(cross(col,2)-cross(col,.8))
  rows.append({'fixture_index':n,'edge':m.group(1),'corner':corner,'crossing_window_ns':dt*1e9,'average_ns_per_V':dt*1e9/1.2,'fixture_header':[x.strip() for x in text.splitlines() if '_fixture' in x]})
report={'archive_sha256':hashlib.sha256(a.archive.read_bytes()).hexdigest(),'model_revision':'2.0 2019-04-24','rows':rows,'largest_average_ns_per_V':max(x['average_ns_per_V'] for x in rows),'board_edge_qualified':False,'limitations':['Vendor simulation-derived model; not production guarantee','Average window slope does not bound every local slope','Package/trace/input load not simulated','Provided PVT temperatures extend beyond part operating range; not permission to operate there']}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='rows'}))
