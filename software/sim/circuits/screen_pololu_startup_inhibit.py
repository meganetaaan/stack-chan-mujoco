"""Nominal two-pullup ENA network; no undocumented threshold assumptions."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[3]
c=json.loads((ROOT/'schematics/power/pololu_startup_inhibit_candidate.json').read_text())
n=c['internal_network'];rint=1/(1/n['ENA_to_VIN_ohm']+1/(n['ENB_to_VIN_ohm']+n['ENA_to_ENB_ohm']))
pd=c['external_pulldown']['ohm'];rs=c['external_series']['ohm'];vin=12.6
rows=[]
for allow in [0,3.0,3.3,3.6]:
 v=(vin/rint+allow/rs)/(1/rint+1/pd+1/rs)
 rows.append({'allow_V':allow,'ENA_V':v,'driver_current_A':(allow-v)/rs})
r={'scope':'nominal DC network, not threshold or transient qualification','VIN_V':vin,
'ENA_with_control_open_V':vin*pd/(pd+rint),'cases':rows,
 'two_modules_shutdown_current_typ_A':2*(100e-6+2e-6*vin),
 'important':'Both internal pullups included through ENB link; shutdown current is typical only',
 'remaining':['ENA low threshold not quantified on module page','internal resistor tolerances','driver and power-off injection','ENA transient during VIN ramp','Tab5 and other loads still need independent inhibit'], 'manufacturing_release':False}
out=ROOT/'validation/pololu_startup_inhibit_v1';out.mkdir(exist_ok=True)
(out/'report.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps(r,indent=2))
