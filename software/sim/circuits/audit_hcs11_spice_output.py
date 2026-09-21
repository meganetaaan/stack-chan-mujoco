"""Check the vendor behavioral output stage against datasheet transition-time conditions."""
import argparse,hashlib,json,math,re,zipfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--archive',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
plan={'question':'Can SCLM296 output resistance be used as a quantitative edge-rate model?', 'stop':'Compare all three tabulated voltage points at datasheet CL=50pF; do not retune vendor parameters.', 'criterion':'Reproduce the datasheet 10-90% transition test at least within published maxima before using for interface acceptance.'}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
s=zipfile.ZipFile(a.archive).read('SN74HCS11.cir').decode()
section=s.split('.SUBCKT LOGIC_PP_OUTPUT_HC_3i_AND_PP_ST_SN74HCS11')[1].split('.ENDS')[0]
up=section.split('EROH')[1].split('EROL')[0];down=section.split('EROL')[1].split('E1')[0]
def table(t):return {float(v):float(r) for v,r in re.findall(r'\+\(([^,]+),([^\)]+)\)',t)}
rows=[]
for v,typ,maximum in [(2,9,17),(4.5,5,8),(6,4,7)]:
 for edge,t in [('rising',table(up)),('falling',table(down))]:
  resistance=t[v]+.01
  transition=math.log(9)*resistance*50e-12*1e9
  rows.append({'supply_V':v,'edge':edge,'output_resistance_ohm':resistance,'derived_transition_ns':transition,'datasheet_typical_ns':typ,'datasheet_maximum_ns':maximum,'within_datasheet_maximum':transition<=maximum})
report={'archive_sha256':hashlib.sha256(a.archive.read_bytes()).hexdigest(),'method':'Exact first-order RC solution of vendor resistive output plus 0.01ohm enabled switch and external 50pF; internal output source switches ideally. Propagation delay does not change 10-90% edge time.','rows':rows,'suitable_for_edge_acceptance':all(r['within_datasheet_maximum'] for r in rows),'limits':['Output-stage analytic audit, not full PSpice execution','Generic vendor model states typical 25C behavior only','Input clamp/current/power behavior not audited']}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
