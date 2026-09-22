"""Nominal side-fastener stack with explicit contact pads and real-part candidates."""
import hashlib,json,math
from pathlib import Path
import cadquery as cq
ROOT=Path(__file__).resolve().parents[3];out=ROOT/'validation/tab5_carrier_hardware_v2';out.mkdir(exist_ok=True)
plan={'screw':'NBK SLH-M3-10','nut':'Accu HPN-M3-A2','quantity_each':4,'screw_dimensions_mm':{'length':10,'head_diameter':5.5,'head_height':2,'socket_AF':2},'nut_dimensions_mm':{'AF_max':5.5,'height_max':2.4},'pad_radius_mm':3.5,'pad_abs_y_mm':[61,62.2],'criteria':['Valid single carrier','Pad contacts fixed shell without overlap','Hardware no volume interference with print parts'],'limits':['Nominal envelopes no threads/chamfers','No assembly torque or preload qualified','No screw/head tolerances applied'],'stop':'One nominal stack, report overall width increase explicitly'}
(out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
p=ROOT/'validation/tab5_carrier_side_mount_v2';files=[p/'carrier.step',p/'fixed_shell.step'];carrier=cq.importers.importStep(str(files[0])).val();fixed=cq.importers.importStep(str(files[1])).val();hw={};pads=[]
for sign in [-1,1]:
 for z in [88,112]:
  def cyl(r,h,y):return cq.Solid.makeCylinder(r,h,cq.Vector(42,sign*y,z),cq.Vector(0,sign,0))
  pad=cyl(3.5,1.2,61).cut(cyl(1.7,1.2,61));pads.append(pad);carrier=carrier.fuse(pad)
  bolt=cyl(1.5,10,54).fuse(cyl(2.75,2,64))
  plane=cq.Plane(origin=(42,sign*55.4,z),xDir=(1,0,0),normal=(0,sign,0))
  nut=cq.Workplane(plane).polygon(6,5.5/math.cos(math.pi/6)).extrude(2.4).val().cut(cyl(1.5,2.4,55.4))
  hw[f'{sign}_{z}_screw']=bolt;hw[f'{sign}_{z}_nut']=nut
carrier=carrier.clean();checks=[]
for n,s in hw.items():
 for m,t in [('carrier',carrier),('fixed_shell',fixed)]:
  checks.append({'hardware':n,'part':m,'overlap_mm3':s.intersect(t).Volume()})
result={'carrier_valid':carrier.isValid(),'carrier_solids':len(carrier.Solids()),'pad_to_shell_gap_mm':[s.distance(fixed) for s in pads],'carrier_fixed_overlap_mm3':carrier.intersect(fixed).Volume(),'hardware_checks':checks,'nut_inner_face_abs_y_mm':55.4,'screw_tip_abs_y_mm':54,'nominal_tip_protrusion_mm':1.4,'width_with_heads_mm':132,'previous_width_mm':128,'width_increase_mm':4,'width_increase_percent':3.125,'candidate_hardware_mass_g':4*(.7+.38),'source_sha256':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},'manufacturing_release':False}
for n,s in {'carrier':carrier,'fixed_shell':fixed,**hw}.items():cq.exporters.export(s,str(out/(n+'.step')))
(out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
