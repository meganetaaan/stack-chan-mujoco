"""Check CAD/mesh imports and an ngspice transient against an analytic RC solution."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import numpy as np
import cadquery as cq
import gmsh

ROOT = Path(__file__).resolve().parents[3]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    cube = cq.Workplane('XY').box(2, 2, 2).val()
    assert cube.isValid() and abs(cube.Volume()-8) < 1e-10
    cq.exporters.export(cube, str(out/'cube.step'))
    gmsh.initialize()
    try:
        gmsh.option.setNumber('General.Terminal', 0)
        gmsh.model.occ.importShapes(str(out/'cube.step'))
        gmsh.model.occ.synchronize()
        gmsh.option.setNumber('Mesh.MeshSizeMax', .5)
        gmsh.model.mesh.generate(3)
        _, tags, _ = gmsh.model.mesh.getElements(3)
        count = sum(len(t) for t in tags)
        assert count > 0
        gmsh.write(str(out/'cube.msh'))
    finally:
        gmsh.finalize()
    netlist = '''RC transient benchmark; 1 kohm, 1 uF, 5 V step
Vstep in 0 PULSE(0 5 0 1n 1n 10m 20m)
R1 in out 1k
C1 out 0 1u IC=0
.control
set wr_singlescale
set wr_vecnames
tran 1u 3m uic
wrdata rc.dat v(out)
quit
.endc
.end
'''
    (out/'rc.cir').write_text(netlist)
    binary = ROOT/'.tools/root/usr/bin/ngspice'
    result = subprocess.run([str(binary), '-b', 'rc.cir'], cwd=out, text=True, capture_output=True)
    (out/'ngspice.log').write_text(result.stdout+result.stderr)
    result.check_returncode()
    data = np.loadtxt(out/'rc.dat', skiprows=1)
    expected = 5*(1-np.exp(-data[:,0]/.001))
    error = float(abs(data[:,1]-expected).max())
    assert error < 1e-4, error
    report = {'passed':True, 'cadquery_version':cq.__version__, 'gmsh_version':gmsh.__version__,
              'cube_volume_mm3':float(cube.Volume()), 'tetrahedra':count,
              'rc_max_error_V':error,
              'scope':'Toolchain and known RC response only; not robot strength or power acceptance.'}
    (out/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
