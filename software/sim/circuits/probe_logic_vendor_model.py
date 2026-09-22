"""Reproduce vendor-model compatibility failure; never interpret exit status alone as pass."""
import argparse,hashlib,json,subprocess,urllib.request,zipfile,io
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True);out=a.out.resolve();root=Path.cwd();url='https://www.ti.com/lit/zip/sbvm571'
raw=urllib.request.urlopen(url,timeout=30).read();model=zipfile.ZipFile(io.BytesIO(raw)).read('TPS70933_TRANS.LIB');(out/'TPS70933_TRANS.LIB').write_bytes(model)
(out/'start.cir').write_bytes((root/'validation/logic_vendor_model_probe_v1/start.cir').read_bytes())
lib=root/'.tools/root/usr/lib/x86_64-linux-gnu/ngspice';(out/'.spiceinit').write_text('set ngbehavior=ps\n'+''.join(f'codemodel {lib/name}\n' for name in ['analog.cm','table.cm','xtradev.cm']))
with (out/'run.log').open('w') as log:
 try:
  result=subprocess.run([str(root/'.tools/root/usr/bin/ngspice'),'-b','start.cir'],cwd=out,stdout=log,stderr=subprocess.STDOUT,timeout=60);code=result.returncode
 except subprocess.TimeoutExpired:code=None
text=(out/'run.log').read_text(errors='replace');failed=code is None or any(s in text.lower() for s in ['aborted','timestep too small','simulation interrupted','error on line'])
report={'url':url,'zip_sha256':hashlib.sha256(raw).hexdigest(),'model_sha256':hashlib.sha256(model).hexdigest(),'process_returncode':code,'observed_model_error':failed,'electrical_qualification':False,'scope':'LDO compatibility probe only; ideal source, resistive load, no eFuse','model_complete_run_requires_waveform_validation_even_if_no_error':True}
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
