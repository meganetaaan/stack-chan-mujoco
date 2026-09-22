"""Place selected film-capacitor nominal envelope and provisional through-hole footprint."""
import argparse,json
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
base=Path('board/power/mechanical_outline_revA')
plan={'reference':'C_STOP_IN','part':'MKS2C042201K00JSSD','local_uv_mm':[40,12.5],'body_mm':[7.2,7.2,13],'body_standoff_mm':.5,'lead_pitch_mm':5,'lead_nominal_diameter_mm':.5,'proposed_drill_mm':.8,'proposed_pad_mm':1.6,'solder_side_lead_protrusion_mm':1.5,'criteria':['Body inside reserved component volume','No body/lead overlap with existing packaging','Lead holes do not intersect mounting keepouts'],'limits':['Manufacturer body nominal dimensions only','Standoff, drill, pad, and trimmed lead lengths are design proposals','No routing, solder fillet, tolerance stack or retention qualification']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
board=cq.importers.importStep(str(base/'board.step')).val()
body=cq.Solid.makeBox(13,7.2,7.2,cq.Vector(2.1,-3.6,107.9))
leads=[]
for y in (-2.5,2.5):
 board=board.cut(cq.Solid.makeCylinder(.4,1.6,cq.Vector(0,y,111.5),cq.Vector(1,0,0)))
 leads.append(cq.Solid.makeCylinder(.25,3.6,cq.Vector(-1.5,y,111.5),cq.Vector(1,0,0)))
shape=cq.Compound.makeCompound([body,*leads])
for name,s in [('board',board),('C_STOP_IN',shape)]:cq.exporters.export(s,str(a.out/(name+'.step')))
s=(base/'power_outline.kicad_pcb').read_text().rstrip();assert s.endswith(')');s=s[:-1]
s+='\n(net 1 "STOP_LDO_INPUT")\n(net 2 "GND")\n'
s+='(footprint "WIMA_MKS2_7.2x7.2_P5_candidate" (layer "F.Cu") (at 90 62.5) (attr through_hole)\n'
s+='(fp_text reference "C_STOP_IN" (at 0 -5) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))\n'
s+='(fp_text value "2.2uF 63V" (at 0 5) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))\n'
s+='(fp_rect (start -3.6 -3.6) (end 3.6 3.6) (stroke (width 0.15) (type default)) (fill none) (layer "F.SilkS"))\n'
for n,x,net in [(1,-2.5,'STOP_LDO_INPUT'),(2,2.5,'GND')]:s+=f'(pad "{n}" thru_hole circle (at {x} 0) (size 1.6 1.6) (drill 0.8) (layers "*.Cu" "*.Mask") (net {n} "{net}"))\n'
s+=')\n)\n';(a.out/'power_placement.kicad_pcb').write_text(s)
reserve=cq.importers.importStep('validation/power_board_reservation_v3/components.step').val()
assert abs(body.intersect(reserve).Volume()-body.Volume())<1e-6
rows=[]
for path in json.loads(Path('board/mechanical/prototype/power_packaging_revA/report.json').read_text())['sources_sha256']:
 obs=cq.importers.importStep(path).val();rows.append({'obstacle':path,'overlap_mm3':sum(shape.intersect(z).Volume() for z in obs.Solids()),'distance_mm':min(shape.distance(z) for z in obs.Solids())})
report={'checks':rows,'body_in_reservation':True,'nominal_clear':all(x['overlap_mm3']<1e-6 for x in rows),'capacitor_board_overlap_mm3':sum(z.intersect(board).Volume() for z in [body,*leads]),'placed_electrical_components':1,'total_candidate_electrical_components':98,'manufacturing_release':False}
assert report['capacitor_board_overlap_mm3']<1e-6
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print('nominal clear:',report['nominal_clear'])
