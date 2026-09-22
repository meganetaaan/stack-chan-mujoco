"""Reproduce the manufacturer's public generic calculator, not article mass."""
import argparse,hashlib,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];p=argparse.ArgumentParser();p.add_argument('--calculator-js',type=Path,required=True);a=p.parse_args();raw=a.calculator_js.read_bytes();s=raw.decode()
# Verify the specific public table entries whose coefficients are used below.
assert '{ mm: 4, inch: 0.157, weight: 0.115 }' in s
assert '{ mm: 2.0, dm: 0.01 }' in s
assert 'weight: 7.87' in s
paths=[ROOT/'docs/prototype/mechanical/yaw_hex_nut/candidate.json',ROOT/'docs/prototype/mechanical/pololu_mount_fasteners/candidate.json',ROOT/'validation/current_torso_mass_v2/report.json']
yaw,power,ledger=[json.loads(x.read_text()) for x in paths]
assert yaw['article']==power['nut']['article']=='1088211'
assert yaw['across_flats_catalog_mm']==4 and yaw['height_max_catalog_mm']==1.6
names=[r['name'] for r in ledger['rows'] if r['mass_kg'] is None and (r['name'].startswith('yaw__') and r['name'].endswith('_nut') or r['name'].startswith('power__') and '_module_' in r['name'] and r['name'].endswith('_nut'))]
assert len(names)==16
# Metric UI reports kg per100pieces; source radius is in dm.
kg_per100=(.115/10)*1.6-.01**2*math.pi*1.6*.85*7.87
r={'article':'1088211','quantity':16,'part_names':names,'method':'Bossard generic hex nut Weight Calculator; steel, AF4mm, M2 nominal thread, height1.6mm','calculator_kg_per100':kg_per100,'comparison_mass_g_each':kg_per100*10,'comparison_total_g':kg_per100*10*len(names),'catalog_article_mass_g':None,'guaranteed_upper_mass_g':None,'promote_to_qualified_ledger':False,'input_scope':'Maximum catalog height used with nominal AF and generic steel factor; no claim that result is an upper bound','sources':{'calculator':'https://website-assets.bossard.com/Weight-Calculator/Weight-Calculator-en.html','public_module':'https://website-assets.bossard.com/Assets/js/data-weight-hexagon.js','UI_100piece_unit':'https://website-assets.bossard.com/Assets/js/weight-hexagonnuts.js','product_family':'https://www.bossard.com/ch-en/eshop/hex-nuts/hex-nuts-0-8d/p/109/'},'module_sha256':hashlib.sha256(raw).hexdigest(),'limits':['Generic calculator is initial estimate, not exact article data','Chamfer/thread/plating and material variations not qualified','No preload/proof-load or printed pocket strength implied','No CAD or complete robot inertia updated'],'source_sha256':{str(x.relative_to(ROOT)):hashlib.sha256(x.read_bytes()).hexdigest() for x in paths}}
out=ROOT/'validation/bossard_nut_mass_screen_v1';out.mkdir(exist_ok=True);(out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:r[k] for k in ['quantity','comparison_mass_g_each','comparison_total_g','catalog_article_mass_g']}))
