"""Bounded NumPy FPS geometry surrogate plus source metadata bindings; no model."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
os.environ['OMP_NUM_THREADS']='1'
import json, time, hashlib, importlib.util, gc
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
ROOT=Path(__file__).resolve().parents[2]
BASE=Path(__file__).parent
OUT=BASE/'consolidated_binding_v1'
def load_module(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
raw=load_module('raw',ROOT/'outputs/cranial_geometry_diagnostic_20261023/analyze_raw_pairs_v1.py')
lock=load_module('lock',ROOT/'outputs/cranial_scqr_v12_qa_github_publish_20261019/tools/lock_skullbreak_mamba_v12_development_protocol.py')
def save(name,v):
    with (OUT/name).open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False)
def fps(p,n):
    # Deterministic first point 0, float64, first-index tie: not CUDA equivalence.
    d=np.full(len(p),np.inf);idx=np.empty(n,int);far=0
    for i in range(n):
        idx[i]=far;d=np.minimum(d,np.sum((p-p[far])**2,axis=1));far=int(np.argmax(d))
    return idx
def metric(j,w,p):
    ds=cKDTree(p).query(j,workers=1)[0];ix=np.argsort(ds);cum=np.cumsum(w[ix]);return {'J_cover_1mm':float(np.average(ds<=1,weights=w)),'J_cover_2mm':float(np.average(ds<=2,weights=w)),'J_p95_mm':float(ds[ix[np.searchsorted(cum,.95*cum[-1])]])}
def main():
    OUT.mkdir(exist_ok=False);start=time.monotonic()
    toy=np.array([[0.,0,0],[1,0,0],[3,0,0]]);assert list(fps(toy,2))==[0,2]
    manifest=Path('E:/dataset/SkullBreakPC/manifest.jsonl');records,msha=lock.read_manifest(manifest)
    by=lock.validate_strict_train(lock.strict_train_records(records));confirmation,folds=lock.make_assignments(by)
    mapping={}
    for fold in 'CD':
        dev={s for s,f in folds.items() if f==fold};train=set(folds)-dev
        ids=lock.case_ids_for_skulls(by,train);text='\n'.join(ids)+'\n'
        req=json.loads((ROOT/f'server_uploads/v12_qa1_b0_fold{fold.lower()}_training_20261008/v12_qa1_b0_fold{fold.lower()}_seed0_training_execution_authorization_request_v1.json').read_text(encoding='utf8')) if fold=='D' else None
        ah=hashlib.sha256(text.encode()).hexdigest()
        if req:assert ah==req['data_scope']['train_allowlist_sha256'],'historical fold mismatch'
        mapping[fold]={'train_sources':sorted(train),'dev_sources':sorted(dev),'train_case_ids':ids,'dev_case_ids':lock.case_ids_for_skulls(by,dev),'train_allowlist_sha256':ah,'historical_D_allowlist_verified':fold=='D','train_cases':len(ids),'dev_cases':len(dev)*5,'traversals_proposed':100,'batch':8,'drop_last':True,'updates_proposed':100*(len(ids)//8),'case_exposures_proposed':100*(len(ids)//8)*8}
    save('fold_binding.json',{'status':'METADATA_BOUND_DERIVED_PAYLOAD_NOT_GENERATED','manifest_sha256':msha,'protocol_salt':lock.PROTOCOL_SALT,'confirmation_count_excluded':len(confirmation),'folds':mapping,'cross_fold_note':'C/D dev sources disjoint; train sets overlap as in CV; not two independent datasets'})
    scope=json.loads((ROOT/'outputs/cranial_geometry_diagnostic_20261023/raw_pairing_v1/scope.json').read_text())
    rows=[];hashes=[]
    for c in scope['cases']:
        assert time.monotonic()-start<900
        cid=c['dataset']+'_'+c['case_id'];print('START',cid,flush=True)
        dp=Path(c['raw_paths']['defective']);gp=Path(c['raw_paths']['implant'])
        before={str(p):raw.sha(p) for p in (dp,gp)}
        for p,h in before.items():assert h==c['hashes_before'][p]
        D,A,o=raw.read_mask(dp);G,B,b=raw.read_mask(gp);assert np.array_equal(A,B) and np.array_equal(o,b)
        refs=[];ws=[]
        for axis in range(3):
            area=np.linalg.norm(np.cross(A[(axis+1)%3],A[(axis+2)%3]))
            for sign in (-1,1):
                q,tag=raw.faces(D,G,axis,sign);q=q[tag].astype(float);q[:,axis]+=.5*sign;refs.append(q@A+o);ws.append(np.full(len(q),area))
        J=np.concatenate(refs);w=np.concatenate(ws);del D,G;gc.collect()
        for n in (8192,16384):
            path=BASE/'cpu_result_v1'/f'{cid}_D_V1_{n}.npz';before[str(path)]=raw.sha(path)
            with np.load(path,allow_pickle=False) as z:p=z['xyz'].copy()
            i=fps(p,512);cent=p[i];k=fps(cent,256);proxy=cent[k]
            neighbors=cKDTree(p).query(cent,k=16,workers=1)[1];support=np.unique(neighbors)
            near=cKDTree(J).query(p,workers=1)[0]<=1.
            for stage,points in [('input',p),('center512',cent),('proxy256',proxy),('first_layer_direct_neighborhood_union',p[support])]:
                rows.append({'case':cid,'n':n,'stage':stage,'points':len(points),'interface_near_raw_points':int(near.sum()),'interface_near_in_direct_union':int(near[support].sum()),**metric(J,w,points)})
            np.savez_compressed(OUT/f'{cid}_{n}_fps_indices.npz',first=i,second=k,raw_proxy_indices=i[k])
        for p,h in before.items():assert raw.sha(Path(p))==h
        hashes.append({'case':cid,'sources_unchanged':True,'hashes':before});save(cid+'_rows.json',rows[-8:]);print('DONE',cid,flush=True)
    save('proxy_metrics.json',rows);save('input_hashes.json',hashes)
    save('completion.json',{'status':'COMPLETED','cases':6,'input_sampling_seeds':1,'seconds':time.monotonic()-start,'model_calls':0,'GPU_calls':0,'source_writes':0,'caveats':['float64 CPU FPS first-index tie; not CUDA equivalence','direct-neighborhood union is support geometry, not learned feature retention','no 2-hop expansion, no training data generation','metadata fold reconstruction does not open confirmation payload']})
if __name__=='__main__':main()
