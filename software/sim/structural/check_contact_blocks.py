"""Verify unilateral face contact against a series-compliance block solution."""
import argparse,hashlib,json,os,subprocess,re
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--evaluate-only',action='store_true')
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=a.evaluate_only)
plan={'scope':__doc__,'units':'mm, N, MPa','area_mm2':100.,'height_each_mm':2.,
      'young_MPa':[1120.,68300.],'poisson':0.,'compression_mm':.01,'opening_mm':.01,
      'penalty_N_mm3':[1e4,1e6],'mesh_cells_per_side':[2,4],
      'criteria':{'relative_reaction_error':.01,'opened_force_N':1e-5,'relative_force_balance':1e-6,'relative_penalty_law_error':1e-5,'reclosure_relative_error':1e-5,'printed_gap_agreement_mm':1e-8},
      'analytical_force':'A * compression / (h1/E1 + h2/E2 + 1/K)',
      'sources':['https://www.dhondt.de/ccx_2.21.pdf'],
      'limitations':['synthetic flat blocks, not actual robot geometry','nu=0 and lateral constraints isolate normal compliance',
                     'no friction, screw preload, bending, plasticity or material qualification']}
if a.evaluate_only:
    assert json.loads((a.out/'plan.json').read_text())==plan,'Stored plan differs from evaluator'
else:
    (a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
exe=ROOT/'.tools/root/usr/bin/ccx'
env=os.environ.copy();env['LD_LIBRARY_PATH']=str(ROOT/'.tools/root/usr/lib/x86_64-linux-gnu');env['OMP_NUM_THREADS']='1'
for n in ([] if a.evaluate_only else plan['mesh_cells_per_side']):
 for penalty in plan['penalty_N_mm3']:
    folder=a.out/f'n{n}_k{int(penalty)}';folder.mkdir()
    nodes=[];elements=[];bottom=[];top=[];contact_lower=[];contact_upper=[]
    for block in range(2):
        ids={}
        for k in range(2):
         for j in range(n+1):
          for i in range(n+1):
            node=len(nodes)+1;ids[i,j,k]=node
            nodes.append((node,10*i/n,10*j/n,2*(block+k)))
            if block==0 and k==0:bottom.append(node)
            if block==1 and k==1:top.append(node)
        for j in range(n):
         for i in range(n):
            eid=len(elements)+1
            conn=[ids[i,j,0],ids[i+1,j,0],ids[i+1,j+1,0],ids[i,j+1,0],ids[i,j,1],ids[i+1,j,1],ids[i+1,j+1,1],ids[i,j+1,1]]
            elements.append((eid,*conn))
            (contact_lower if block==0 else contact_upper).append(eid)
    lines=['*HEADING','Contact compliance and release benchmark','*NODE,NSET=ALL']
    lines += [','.join(map(str,row)) for row in nodes]
    for name,es in [('LOWER',contact_lower),('UPPER',contact_upper)]:
        lines += [f'*ELEMENT,TYPE=C3D8,ELSET={name}']
        lines += [','.join(map(str,elements[e-1])) for e in es]
    for name,ns in [('BOTTOM',bottom),('TOP',top)]:
        lines.append(f'*NSET,NSET={name}')
        lines += [','.join(map(str,ns[i:i+12])) for i in range(0,len(ns),12)]
    for name,E in [('LOWER',1120),('UPPER',68300)]:
        lines += [f'*MATERIAL,NAME={name}', '*ELASTIC',f'{E},0',f'*SOLID SECTION,ELSET={name},MATERIAL={name}']
    lines += ['*SURFACE,NAME=MASTER,TYPE=ELEMENT','LOWER,S2',
              '*SURFACE,NAME=SLAVE,TYPE=ELEMENT','UPPER,S1',
              '*SURFACE INTERACTION,NAME=CONTACT','*SURFACE BEHAVIOR,PRESSURE-OVERCLOSURE=LINEAR',str(penalty),
              '*CONTACT PAIR,INTERACTION=CONTACT,TYPE=SURFACE TO SURFACE','SLAVE,MASTER',
              '*BOUNDARY','ALL,1,2,0','BOTTOM,3,3,0']
    for displacement in [-.01,.01,-.01]:
        lines += ['*STEP,NLGEOM,INC=100','*STATIC','.1,1,1e-6,.1','*BOUNDARY',f'TOP,3,3,{displacement}',
                  '*NODE PRINT,NSET=BOTTOM,TOTALS=ONLY','RF','*NODE PRINT,NSET=TOP,TOTALS=ONLY','RF',
                  '*NODE PRINT,NSET=ALL','U','*CONTACT PRINT,SLAVE=SLAVE,MASTER=MASTER','CF,CDIS,CSTR','*END STEP']
    (folder/'contact.inp').write_text('\n'.join(lines)+'\n')
    run=subprocess.run([str(exe),'-i','contact'],cwd=folder.resolve(),env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    (folder/'solver.log').write_text(run.stdout)
    (folder/'run.json').write_text(json.dumps({'returncode':run.returncode,'executable_sha256':hashlib.sha256(exe.read_bytes()).hexdigest()},indent=2)+'\n')
    print(folder.name,run.returncode,flush=True)
    if run.returncode or '*ERROR' in run.stdout or 'Job finished' not in run.stdout:raise RuntimeError('Contact benchmark solver failed; inspect solver.log')

def number(value):
    # Fortran's narrow exponential format omits E for three-digit exponents.
    return float(re.sub(r'^([+-]?(?:\d+\.?\d*|\.\d+))([+-]\d{3})$',r'\1e\2',value.replace('D','E')))

rows=[]
for n in plan['mesh_cells_per_side']:
 for penalty in plan['penalty_N_mm3']:
    folder=a.out/f'n{n}_k{int(penalty)}'
    content=(folder/'contact.dat').read_text()
    forces={}
    for name,time,values in re.findall(r'total force \(fx,fy,fz\) for set (BOTTOM|TOP) and time\s+(\S+)\s*\n\s*\n([^\n]+)',content):
        forces[name,float(time)]=np.array([number(x) for x in values.split()])
    displacements={}
    for time,values in re.findall(r'displacements \(vx,vy,vz\) for set ALL and time\s+(\S+)\s*\n\s*\n(.*?)(?=\n\s*\n)',content,re.S):
        displacements[float(time)]={int(v[0]):np.array(list(map(number,v[1:]))) for row in values.splitlines() if (v:=row.split())}
    expected=plan['area_mm2']*plan['compression_mm']/(sum(plan['height_each_mm']/E for E in plan['young_MPa'])+1/penalty)
    snapshots=[]
    m=(n+1)**2
    for time in [1.,2.,3.]:
        bottom=forces['BOTTOM',time];top=forces['TOP',time];u=displacements[time]
        gaps=np.array([u[2*m+i][2]-u[m+i][2] for i in range(1,m+1)])
        snapshots.append({'time':time,'bottom_reaction_N':bottom.tolist(),'top_reaction_N':top.tolist(),
                          'gap_min_mm':float(gaps.min()),'gap_max_mm':float(gaps.max()),
                          'penetration_mean_mm':float(-gaps.mean()),
                          'relative_balance':float(np.linalg.norm(bottom+top)/expected)})
    closed=snapshots[0];opened=snapshots[1];reclosed=snapshots[2]
    force=closed['bottom_reaction_N'][2]
    relative_error=abs(force-expected)/expected
    contact_gap=None
    for time,values in re.findall(r'relative contact displacement .*? time\s+(\S+)\s*\n\s*\n(.*?)(?=\n\s*\n)',content,re.S):
        if float(time)==1.:
            contact_gap=np.array([number(row.split()[2]) for row in values.splitlines() if row.strip()])
    assert contact_gap is not None and len(contact_gap)>0 and np.isfinite(contact_gap).all()
    direct_penetration=float(np.mean(abs(contact_gap)))
    printed_gap_error=abs(direct_penetration-closed['penetration_mean_mm'])
    penalty_error=abs(force/plan['area_mm2']-penalty*direct_penetration)/(force/plan['area_mm2'])
    reclose_error=abs(reclosed['bottom_reaction_N'][2]-force)/force
    gates={'compression_reaction':relative_error<=plan['criteria']['relative_reaction_error'],
           'opened_force':max(np.linalg.norm(opened[k]) for k in ['bottom_reaction_N','top_reaction_N'])<=plan['criteria']['opened_force_N'],
           'positive_open_gap':opened['gap_min_mm']>0,
           'force_balance':all(r['relative_balance']<=plan['criteria']['relative_force_balance'] for r in snapshots),
           'printed_gap_agreement':printed_gap_error<=plan['criteria']['printed_gap_agreement_mm'],
           'penalty_law':penalty_error<=plan['criteria']['relative_penalty_law_error'],
           'reclosure':reclose_error<=plan['criteria']['reclosure_relative_error']}
    gates={k:bool(v) for k,v in gates.items()}
    rows.append({'mesh':n,'penalty_N_mm3':penalty,'expected_compression_force_N':expected,
                 'relative_reaction_error':relative_error,'relative_penalty_law_error':penalty_error,
                 'contact_output_penetration_mm':direct_penetration,'printed_gap_disagreement_mm':printed_gap_error,
                 'reclosure_relative_error':reclose_error,'snapshots':snapshots,'gates':gates,'passed':all(gates.values())})
report={'scope':__doc__,'rows':rows,'passed':all(r['passed'] for r in rows),
        'gap_definition':'deformed upper bottom-surface z minus lower top-surface z; positive means separated',
        'undefined_open_contact_statistics':'Solver prints NaN contact centroids/normals when active contact area is zero; these are not used as physical reactions.',
        'robot_joint_verified':False}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'passed':report['passed'],'max_relative_reaction_error':max(r['relative_reaction_error'] for r in rows),'gates':[r['gates'] for r in rows]}))
