"""Use already saved paired development inputs; no resampling, server or real model."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
import ast,hashlib,json,shutil,time
from pathlib import Path
import numpy as np
B=Path(__file__).resolve().parent;P=B/'blue_noise_model_pair_foldC_seed0_20261104_v1';O=P/'first_training_request_v2';N=B/'blue_pair_eval_v1'
OLD=B/'sampling_model_AB_foldC_seed0_20261103_v1/paired_development_eval_v1'
ARMS=['Euclidean_elimination','surface_graph'];PROJECT='/home/jovyan/adapointr_work/PoinTr';DATA=PROJECT+'/data/bcsp_blue_pair_dev_v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bind(p):p=Path(p);return dict(path=str(p.absolute()),bytes=p.stat().st_size,sha256=sha(p))
def dump(name,v):
    with (N/name).open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=True,indent=2,allow_nan=False)
def main():
    start=time.monotonic();assert not N.exists();N.mkdir()
    fold=json.loads((B/'consolidated_binding_v1/fold_binding.json').read_bytes())['folds']['C'];ids=fold['dev_case_ids'];sources=fold['dev_sources']
    assert len(ids)==105 and len(set(sources))==21 and not set(sources)&set(fold['train_sources'])
    oldreceipt=json.loads((P/'paired_dev_data_receipt.json').read_bytes());assert oldreceipt['status']=='PAIRED_105_DEVELOPMENT_INPUTS_PREPARED_NOT_EVALUATED' and oldreceipt['cases']==105
    refsfile=B/'development_eval_v1/reference_bank_v2/reference_manifest_v1.json';refs=json.loads(refsfile.read_bytes());assert refs['model_predictions_used'] is False
    refmap={r['case_id']:r for r in refs['cases'] if r['fold']=='C'};assert set(refmap)==set(ids)
    metadata={a:[json.loads(x) for x in (P/a/'dev_manifest_8192.jsonl').read_text(encoding='utf-8').splitlines()] for a in ARMS}
    assert all([r['case_id'] for r in rows]==ids for rows in metadata.values())
    rows=[];pairs=[];refrows=[];provenance=[]
    for j,cid in enumerate(ids):
        target=None
        for arm in ARMS:
            r=metadata[arm][j];source=P/arm/r['point_path'];assert sha(source)==r['sha256'] and r['comparison_stage']=='BCSP_BLUE_NOISE_AB_V1' and r['comparison_split']=='development'
            assert r['sampler_arm']==arm and r['sampling_seed']==0 and r['source_id'] in sources and r['n_input']==r['n_target']==8192
            with np.load(source,allow_pickle=False) as z:
                assert set(z.files)=={'partial','implant'}
                x=z['partial'];gt=z['implant'];assert x.shape==gt.shape==(8192,3) and x.dtype==gt.dtype==np.float32 and np.isfinite(x).all() and np.isfinite(gt).all()
                assert hashlib.sha256(gt.tobytes()).hexdigest()==r['target_array_sha256']
                if target is None:target=gt.copy()
                else:assert np.array_equal(target,gt)
            destination=N/'data'/arm/'points'/source.name;destination.parent.mkdir(parents=True,exist_ok=True)
            with destination.open('xb') as f:f.write(source.read_bytes())
            assert sha(destination)==r['sha256']
            rows.append(dict(run='C_'+arm,arm=arm,fold='C',n_input=8192,case_id=cid,source_id=r['source_id'],input=dict(bind(destination),path=DATA+'/'+arm+'/points/'+source.name),normalization=r['normalization'],target_array_sha256=r['target_array_sha256'],common_point_order_sha256=r['common_point_order_sha256']))
            provenance.append(bind(source))
        a,b=[metadata[arm][j] for arm in ARMS]
        assert all(a[k]==b[k] for k in ['case_id','source_id','target_array_sha256','normalization','common_point_order_sha256'])
        ref=refmap[cid];assert all(ref[k]==a[k] for k in ['source_id','target_array_sha256','normalization']) and bind(ref['path'])['sha256']==ref['sha256'] and Path(ref['path']).stat().st_size==ref['bytes']
        refrows.append(ref);pairs.append({k:a[k] for k in ['case_id','source_id','target_array_sha256','normalization','common_point_order_sha256']})
    runs=[]
    audits=[O/'post_Euclidean_training_freeze_audit_v1/audit_report_v1.json',O/'graph_request_v2/post_training_audit_v1/audit_report_v1.json']
    for arm,p in zip(ARMS,audits):
        audit=json.loads(p.read_bytes());assert audit['status']=='FORMAL_POST_TRAINING_FREEZE_AUDIT_PASS' and all(audit['checks'].values()) and audit['counts']['updates']==3900
        runs.append(dict(label='C_'+arm,arm=arm,fold='C',n_input=8192,checkpoint={k:audit['checkpoint'][k] for k in ['path','bytes','sha256']},freeze_audit=bind(p),train_sources=fold['train_sources'],dev_sources=sources,dev_case_ids=ids))
    rows.sort(key=lambda r:(ARMS.index(r['arm']),ids.index(r['case_id'])))
    dump('development_input_index_v1.json',dict(schema='bcsp-blue-noise-pair-development-index-v1',stage='BCSP_BLUE_NOISE_AB_V1',data_root=DATA,runs=runs,inputs=rows))
    dump('paired_development_data_receipt_v1.json',dict(status='PAIRED_105_CASES_210_INPUTS_VERIFIED',stage='BCSP_BLUE_NOISE_AB_V1',sources=21,cases=105,model_case_pairs=210,n_input=8192,n_target=8192,seed=0,point_geometry_resampled=False,GT_equal=True,common_input_permutation=True,model_predictions_used=False,raw_NRRD_read=False,pairs=pairs,source_records=provenance,parent_saved_point_receipt=bind(P/'paired_dev_data_receipt.json'),seconds=time.monotonic()-start))
    dump('reference_manifest_foldC_v1.json',dict(status='FROZEN_EXISTING_FOLD_C_105_REFERENCES',parent_manifest=bind(refsfile),cases=refrows,model_predictions_used=False,new_references_built=False))
    dump('comparison_protocol_v1.json',dict(stage='BCSP_BLUE_NOISE_AB_V1',train_sources=fold['train_sources'],development_sources=sources,development_case_ids=ids))
    old=OLD/'bcsp_sampling_pair_predict_v1.py';source=old.read_text(encoding='utf-8')
    source=source.replace('BCSP_SAMPLING_AB_V1','BCSP_BLUE_NOISE_AB_V1').replace('bcsp-sampling-pair-','bcsp-blue-noise-pair-').replace("'V1'","'Euclidean_elimination'").replace('Morton_area_stratified8k','surface_graph')
    source=source.replace('bcsp_sampling_ab_foldc_seed0_dev_v1','bcsp_blue_pair_dev_v1').replace('logs/cranial_bcsp_sampling_ab_v1','logs/cranial_bcsp_blue_noise_ab_v1').replace('SAMPLING_PAIR_210_FORWARD_COMPLETE','BLUE_NOISE_PAIR_210_FORWARD_COMPLETE')
    ast.parse(source)
    with (N/'bcsp_blue_pair_predict_v1.py').open('x',encoding='utf-8',newline='\n') as f:f.write(source)
    with (N/'bcsp_eval_metrics_v1.py').open('xb') as f:f.write((OLD/'bcsp_eval_metrics_v1.py').read_bytes())
    test=(OLD/'test_pair_predict_contract_v1.py').read_text(encoding='utf-8')
    test=test.replace('bcsp_sampling_pair_predict_v1','bcsp_blue_pair_predict_v1').replace('bcsp-sampling-pair-','bcsp-blue-noise-pair-').replace('BCSP_SAMPLING_AB_V1','BCSP_BLUE_NOISE_AB_V1').replace('Morton_area_stratified8k','surface_graph').replace('N.parents[1]/','N.parent/')
    ast.parse(test)
    with (N/'test_pair_predict_contract_v1.py').open('x',encoding='utf-8') as f:f.write(test)
    dump('implementation_derivation_v1.json',dict(parent=bind(old),candidate=bind(N/'bcsp_blue_pair_predict_v1.py'),changes=['exact Euclidean/surface_graph labels and schema','BCSP_BLUE_NOISE_AB_V1 final checkpoint marker','explicit new development data and output paths','distinct completion status'],unchanged=['inference loop and210 call count','strict numeric and provider contract','state/RNG invariance assertions','no GT decoding in prediction reader','native eval and8192 finite outputs','exclusive archive writer','one-way authorization','no optimizer/loss/BNCal'],metric_code_unchanged=bind(N/'bcsp_eval_metrics_v1.py')))
    print('SAVED_210_PAIRED_DEV_FILES_AND_MINIMAL_ENTRY_PREPARED_NO_MODEL_CALLS')
if __name__=='__main__':main()
