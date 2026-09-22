"""Tighten linear FE all-load bounds using load-space subdivision.

Each cluster is certified by the exact field at its center plus a rigorous
triangle-inequality bound on every recorded load's deviation from that center.
No interpolation between recorded times, contact or nonlinear behavior is proved.
"""
import argparse,hashlib,json
from pathlib import Path
import numpy as np


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bounds',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--reserve-fraction',type=float,default=0.,help='Tighten all response criteria by this fraction')
    a=p.parse_args()
    if not np.isfinite(a.reserve_fraction) or not 0<=a.reserve_fraction<1:p.error('reserve fraction must be in [0,1)')
    a.out.mkdir(parents=True,exist_ok=False)
    bounds_report=json.loads((a.bounds/'report.json').read_text())
    prior_plan=json.loads((a.bounds/'plan.json').read_text())
    limits=np.array([prior_plan['criteria']['displacement_mm'],prior_plan['criteria']['stress_MPa'],prior_plan['criteria']['stress_MPa']])
    original_limits=limits.copy()
    limits*=1-a.reserve_fraction
    unit_reports=[json.loads((a.bounds/f'unit_{i}.json').read_text()) for i in range(6)]
    coeff=np.array([[r['max_displacement_mm'],r['max_absolute_principal_MPa'],r['max_von_mises_MPa']] for r in unit_reports])
    units=[np.load(a.bounds/f'unit_{i}.npz') for i in range(6)]
    displacement=np.array([u['displacement_mm'] for u in units])
    stress=np.array([u['stress_MPa'] for u in units])
    for u in units:u.close()
    plan={'scope':__doc__,'original_limits':original_limits.tolist(),'reserve_fraction':a.reserve_fraction,'limits_displacement_principal_von_mises':limits.tolist(),
          'method':'midpoint of load bounding box; split largest weighted range; all records assigned to exactly one terminal cluster',
          'bounds_report_sha256':hashlib.sha256((a.bounds/'report.json').read_bytes()).hexdigest(),
          'unit_sha256':{f'unit_{i}.npz':hashlib.sha256((a.bounds/f'unit_{i}.npz').read_bytes()).hexdigest() for i in range(6)},
          'limitations':prior_plan['limitations']+['fixed FE mesh only; no time interpolation bound']}
    (a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    def center_metrics(center,need):
        actual=np.zeros(3)
        if need[0]:
            u=np.tensordot(center,displacement,axes=(0,0))
            actual[0]=np.linalg.norm(u,axis=1).max()
        if need[1:].any():
            s=np.tensordot(center,stress,axes=(0,0))
            eig=np.linalg.eigvalsh(np.moveaxis(s,(0,1),(-2,-1)))
            actual[1]=np.abs(eig).max()
            actual[2]=np.sqrt(((eig[...,0]-eig[...,1])**2+(eig[...,1]-eig[...,2])**2+(eig[...,2]-eig[...,0])**2)/2).max()
        return actual
    all_rows=[]
    for row in bounds_report['rows']:
        name=Path(row['source']).parent.name+'_'+row['side']
        with np.load(a.bounds/(name+'_bounds.npz')) as data:
            w=data['wrench_N_Nmm'];time=data['time_s']
        labels=np.full(len(w),-1,dtype=int);stack=[np.arange(len(w))];clusters=[];evaluations=0
        while stack:
            ids=stack.pop();v=w[ids]
            lo,hi=v.min(axis=0),v.max(axis=0);center=(lo+hi)/2
            simple=np.max(np.abs(v)@coeff,axis=0)
            need=simple>limits
            upper=simple.copy();actual=None
            if need.any():
                actual=center_metrics(center,need);evaluations+=1
                residual=np.max(np.abs(v-center)@coeff,axis=0)
                upper[need]=actual[need]+residual[need]
            if np.all(upper<=limits) or len(ids)==1:
                assert np.all(labels[ids]==-1)
                labels[ids]=len(clusters)
                clusters.append({'samples':len(ids),'center_wrench':center.tolist(),'lower_wrench':lo.tolist(),'upper_wrench':hi.tolist(),
                                 'response_upper':upper.tolist(),'passed':bool(np.all(upper<=limits)),
                                 'single_sample_time_s':float(time[ids[0]]) if len(ids)==1 else None})
                continue
            weights=np.max(coeff/limits,axis=1)
            dimension=int(((hi-lo)*weights).argmax())
            # Median split guarantees progress even with repeated load values.
            order=ids[np.argsort(v[:,dimension],kind='stable')];mid=len(order)//2
            stack.extend([order[:mid],order[mid:]])
        assert np.all(labels>=0) and sum(c['samples'] for c in clusters)==len(w)
        upper=np.max([c['response_upper'] for c in clusters],axis=0)
        result={'source':row['source'],'side':row['side'],'samples':len(w),'cluster_count':len(clusters),
                'center_evaluations':evaluations,'certified_samples':sum(c['samples'] for c in clusters if c['passed']),
                'response_upper':upper.tolist(),'passed':all(c['passed'] for c in clusters),'clusters':clusters}
        (a.out/(name+'.json')).write_text(json.dumps(result,indent=2)+'\n')
        np.savez_compressed(a.out/(name+'.npz'),cluster_index=labels,time_s=time)
        all_rows.append({k:v for k,v in result.items() if k!='clusters'})
        print(json.dumps(all_rows[-1]),flush=True)
    report={'scope':__doc__,'rows':all_rows,'total_samples':sum(r['samples'] for r in all_rows),
            'certified_samples':sum(r['certified_samples'] for r in all_rows),
            'response_upper':np.max([r['response_upper'] for r in all_rows],axis=0).tolist(),
            'passed':all(r['passed'] for r in all_rows),'production_verified':False}
    (a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ['scope','rows']}),flush=True)


if __name__=='__main__':main()
