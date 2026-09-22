"""Static wired clamp budget with explicit independent supply and response limits."""
import argparse,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
plan={'question':'Can an independently powered supervisor override EN through a current-limiting series resistor?', 'acceptance':['Clamp current <=1mA under declared driver-high injection','EN <=0.4V while clamp asserted, below 0.59V shutdown threshold','Normal EN >=1.23V while clamp released'], 'assumptions':['5V eFuse input powers clamp supervisor and remains in its valid supply range','Driver-high injection limited to 3.393V; not a model of unspecified brownout output','4.7k series and 39k pulldown total +/-1% budget','Supervisor output asserted and settled; propagation transient excluded'], 'stop':'One static interval calculation; do not assert brownout or recovery qualification'}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
smin,smax=4700*.99,4700*1.01
rmin=39000*.99
leak=.3e-6+.1e-6
vhigh=(3.207-.1-smax*leak)*rmin/(rmin+smax)
iclamp=3.393/smin+.1e-6
r={'normal_EN_lower_V':vhigh,'normal_EN_margin_V':vhigh-1.23,'buffer_normal_load_upper_A':3.393/(smin+rmin)+leak,'clamp_sink_conservative_A':iclamp,'clamp_sink_spec_A':.001,'clamped_EN_upper_V':.4,'shutdown_low_margin_V':.59-.4,'full_brownout_qualification':False,'pending':['Supervisor input supply range and fault independence','Response delay and rail-slew coordination','Input/output behavior outside rated supplies','New manual action after supervisor recovery; clamp release alone must not re-enable','Independent stop and output-stage fault coverage']}
assert vhigh>1.23 and iclamp<.001 and r['buffer_normal_load_upper_A']<100e-6
(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
