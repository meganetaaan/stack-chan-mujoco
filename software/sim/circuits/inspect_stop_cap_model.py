"""Inspect a user-downloaded manufacturer archive without redistributing model data."""
import argparse,hashlib,json,shutil,zipfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--archive',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
with zipfile.ZipFile(a.archive) as z:
 names=[n for n in z.namelist() if n.endswith('/GRM31CR71H475KA12_H.mod')]
 if len(names)!=1:raise ValueError('Expected one exact candidate model')
 data=z.read(names[0]);s=data.decode()
 encrypted='.PROT ddl1' in s and '.UNPROT' in s
 r={'archive_sha256':hashlib.sha256(a.archive.read_bytes()).hexdigest(),'member':names[0],
 'model_sha256':hashlib.sha256(data).hexdigest(),'hspice_encrypted':encrypted,
 'declared_frequency_Hz':[100,6e9],'declared_temperature_C':[-55,125],
 'declared_dc_bias_V':[0,50],'small_signal_only':True,
 'header_conditions_verified':all(x in s for x in ('100Hz - 6GHz','-55 degC - 125 degC','0V - 50V','Small Signal Operation')),
 'hspice_executable':shutil.which('hspice'),'simulation_executed':False,
 'qualification_proven':False,'model_data_redistributed':False}
 if not r['header_conditions_verified']:raise ValueError('Manufacturer header changed; review conditions')
 a.out.mkdir(parents=True,exist_ok=False);(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n')
 print('Model located and applicability inspected; simulation not executed')
