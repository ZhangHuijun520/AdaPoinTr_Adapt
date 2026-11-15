"""Independent saved-array/metadata audit. NumPy CPU only, no model or GT."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
from pathlib import Path,PurePosixPath
import ast,hashlib,io,json,math,tarfile,time
import numpy as np
R=Path(__file__).resolve().parent.parent;F=R/'outputs/scq_rf_audit_20261114_v1';D=F/'downloads';O=D/'output';I=D/'installed'
B=R/'outputs/scq_rf_capture_implementation_20261114_v1/pending_request_v1'
QH='51ee9e42bc29c93002b71c8449b59ed14453aeb6d57cda242857e045cd536945';checks={};start=time.monotonic()
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def lines(p):return [json.loads(x) for x in p.read_text().splitlines()]
def check(name,value):checks[name]=bool(value);assert value,name
def emit(name,value):
    with (F/name).open('x',encoding='utf-8') as f:json.dump(value,f,indent=2,ensure_ascii=False,allow_nan=False)
def rng_valid(v):
    assert set(v)=={'CPU','CUDA','Python','numpy'}
    for key in ('CPU','CUDA'):assert len(v[key])==64 and all(c in '0123456789abcdef' for c in v[key])
    p=ast.literal_eval(v['Python']);assert p[0]==3 and len(p[1])==625 and 0<=p[1][-1]<=624
    s=v['numpy'];prefix=repr('MT19937');assert s.startswith(prefix) and len(bytes.fromhex(s[len(prefix):len(prefix)+4992]))==2496
    tail=ast.literal_eval(s[len(prefix)+4992:]);assert len(tail)==3 and 0<=tail[0]<=624 and tail[1] in (0,1) and math.isfinite(tail[2])
    return True
def descriptor(a,idx):
    M,F,z,Q=(a[k].astype(np.float64) for k in ('M','F','z','Q1'))
    nf=(F-F.mean(-1,keepdims=True))/np.sqrt(F.var(-1,keepdims=True)+1e-5)
    neighbors=nf[idx];d=M[idx]-Q[:,None,:];mu=d.mean(1)
    sigma=np.sqrt(((d-mu[:,None,:])**2).mean(1)+1e-6);rho=np.linalg.norm(d,axis=-1).mean(1,keepdims=True)
    return np.concatenate((np.broadcast_to(z,(256,1024)),neighbors.mean(1),neighbors.max(1),Q,mu,sigma,rho),axis=-1)

try:
    q=read(I/'SCQ_RF_ten_memory_execution_request_v1.json');mapping=read(B/'installation_mapping_v1.json');criteria=read(F/'local_array_audit_criteria_v1.json')
    check('exact_authorized_request_bytes',sha(I/'SCQ_RF_ten_memory_execution_request_v1.json')==sha(B/'payload/SCQ_RF_ten_memory_execution_request_v1.json')==QH)
    finished=read(F/'finished_result_v1.json');before=read(F/'inventory_before_result_v1.json');after=read(F/'inventory_after_result_v1.json')
    check('current_identity_exit0_no_worker_no_tmux',finished['status']=='EXIT0_TMUX_WORKER_ABSENT' and finished['hostname']==q['identity']['hostname'] and finished['uid']==1000 and (O/'exit_code.txt').read_text().strip()=='0')
    check('full_before_after_hash_and_content_fingerprint_stability_excluding_atime',before==after)
    output=before['output']['files'];installed=before['installed']['files'];names={row['output_filename'] for row in q['cases']}
    top={'forward_attempts.jsonl','memory_manifest.jsonl','neighbor_summaries.jsonl','capture_complete.json','resources.jsonl','completion.json','launch.log','worker.pid','exit_code.txt','development_predictions_v1.tar.gz','development_predictions_v1.tar.gz.sha256','development_predictions_v1.tar.gz.bytes','development_predictions_v1.tar.gz.contents.sha256'}
    check('exact23_output_files_and3_directories',set(output)==names|top and len(output)==23 and set(before['output']['directories'])=={'.','memory','tmp'})
    root=PurePosixPath(mapping['remote_root']);targets={str(PurePosixPath(x['target']).relative_to(root)):x for x in mapping['files']}
    controls={'control/authorization_v1.json','control/runtime_v1.json','control/launch_once_v1.sh','control/attempt_claim_v1.json'}
    check('exact17_installations_four_controls_three_directories',len(targets)==17 and set(installed)==set(targets)|controls and len(installed)==21 and set(before['installed']['directories'])=={'.','control','references'})
    for name,record in targets.items():
        assert installed[name]['bytes']==record['bytes'] and installed[name]['sha256']==record['sha256']
        assert sha(I/name)==record['sha256'] and (I/name).stat().st_size==record['bytes']
    check('all_installed_bytes_match_frozen_transport_and_local_readback',True)
    for name in ('authorization_v1.json','runtime_v1.json','launch_once_v1.sh'):
        assert (I/'control'/name).read_bytes()==(B/'authorized_execution_v1'/name).read_bytes()
    auth=read(I/'control/authorization_v1.json');runtime=read(I/'control/runtime_v1.json');claim=read(I/'control/attempt_claim_v1.json')
    check('explicit_authorization_and_one_way_runtime',auth['schema']=='scq-rf-memory-authorization-v1' and auth['request_sha256']==QH and auth['explicit_user_authorization'] is True and 'runtime_sha256' not in auth and runtime==dict(schema='scq-rf-memory-runtime-v1',request_sha256=QH,authorization_sha256=sha(I/'control/authorization_v1.json')))
    check('exclusive_single_attempt_claim',claim==dict(status='CLAIMED_BEFORE_TMUX',request_sha256=QH))
    check('launcher_and_original_entry_unchanged',sha(I/'bcsp_scq_rf_memory_capture_v1.py')=='678a6fffcba13a7b4dec354833fc8275bcd3081adffe5b4581673b977086e5c9' and sha(I/'control/launch_once_v1.sh')==sha(B/'authorized_execution_v1/launch_once_v1.sh'))
    done=read(O/'capture_complete.json');completion=read(O/'completion.json');manifest=lines(O/'memory_manifest.jsonl');attempts=lines(O/'forward_attempts.jsonl');summaries=lines(O/'neighbor_summaries.jsonl');rows=q['cases']
    check('completion_exact_counts_and_request_identity',done['status']=='TEN_MEMORY_CAPTURES_AWAITING_FORMAL_FREEZE' and completion['status']=='CAPTURE_ARCHIVED_AWAITING_FORMAL_FREEZE' and done['counts']==completion['counts']==q['counts'] and done['request_sha256']==completion['request_sha256']==QH)
    check('ten_claims_manifests_summaries_exact_order',len(rows)==len(attempts)==len(manifest)==len(summaries)==10 and [(x['run'],x['case_id']) for x in rows]==[(x['run'],x['case_id']) for x in manifest]==[(x['run'],x['case_id']) for x in summaries]==[(x['run'],x['case_id']) for x in attempts] and [x['forward_index'] for x in attempts]==list(range(1,11)))
    runs={x['label']:x for x in q['runs']}
    for row,m in zip(rows,manifest):
        assert m['input']==row['input'] and m['checkpoint']==runs[row['run']]['checkpoint'] and m['normalization']==row['normalization'] and m['name']==row['output_filename']
        assert all(m[k]==output[m['name']][k] for k in ('bytes','sha256')) and 'not rebuild_global_feature' in m['z_definition']
    check('all_ten_manifest_input_checkpoint_frame_and_capture_hashes',True)
    check('both_models_parameter_BN_and_RNG_unchanged',len(done['models'])==2 and [x['forwards'] for x in done['models']]==[7,3] and all(m['state_before']==m['state_after'] and m['RNG_before']==m['RNG_after'] and rng_valid(m['RNG_before']) for m in done['models']))
    previous=read(R/'outputs/scq_pred_freeze_20261114_v2/post_prediction_freeze_audit_result_v1.json');oldstates={x['run']:x['state_before'] for x in previous['models']}
    for m in done['models']:
        c=m['construction'];assert m['state_before']==oldstates[m['run']] and c['scq']['variant']=='S' and c['scq']['new_parameters']==693507 and c['scq']['total_parameters']==40596676
        assert c['parent']['inventory']['forbidden_registered_modules']==[] and c['parent']['artificial_fixture'] is False
    check('native_SCQ_LQI_construction_and_frozen_weight_state_identity',True)
    resources=lines(O/'resources.jsonl');expected=[];offset=0
    for label,num in [('S_C',7),('S_D',3)]:
        expected.append(('model_start:'+label,offset))
        for n in range(offset+1,offset+num+1):expected.extend([('before_forward',n-1),('after_forward',n)])
        offset+=num
    expected.append(('all_complete',10))
    check('exact23_resource_records_and_phase_order',len(resources)==23 and [(x['phase'],x['forwards']) for x in resources]==expected)
    L=q['limits']
    for event in resources:
        v=event['values'];actual=dict(RSS=v['RSS_bytes']<=L['RSS_bytes'],output=v['output_bytes']<=L['output_bytes'],device=v['device_MiB']<=L['device_MiB'],allocated=v['peak_allocated']<=L['torch_peak_bytes'],reserved=v['peak_reserved']<=L['torch_peak_bytes'],wall=v['elapsed_seconds']<=L['wall_seconds'],disk=v['free_disk_bytes']>=L['minimum_free_disk_bytes'])
        assert event['checks']==actual and all(actual.values()) and event['failed_checks']==[] and event['container_PID']==int((O/'worker.pid').read_text())
        assert all(math.isfinite(x) for x in v.values())
    check('all_resource_limits_independently_recomputed',sum(x['bytes'] for x in output.values())<=L['output_bytes'] and all(a['values']['elapsed_seconds']<=b['values']['elapsed_seconds'] for a,b in zip(resources,resources[1:])))
    assets=list(F.glob('fresh_asset_*_result_v1.json'));weights=list(F.glob('fresh_checkpoint_*_result_v1.json'));inputs=read(F/'fresh_inputs10.remote_result_v1.json')
    check('fresh67_assets_two_checkpoints_ten_inputs_hashes',len(assets)==17 and sum(read(p)['files'] for p in assets)==67 and len(weights)==2 and all(read(p)['status']=='EXACT_HASHES_PASS' for p in assets+weights) and inputs['files']==10 and inputs['array_reads']==0)
    an='development_predictions_v1.tar.gz';archive=D/an;ar=completion['archive'];members={x['name']:x for x in ar['members']}
    check('local_and_server_archive_hash_size_match',archive.stat().st_size==ar['bytes']==output[an]['bytes'] and sha(archive)==ar['sha256']==output[an]['sha256'])
    check('archive_hash_bytes_and_contents_sidecars',(O/(an+'.sha256')).read_text().split()==[ar['sha256'],an] and int((O/(an+'.bytes')).read_text())==ar['bytes'] and (O/(an+'.contents.sha256')).read_text()==''.join(x['sha256']+'  '+x['name']+'\n' for x in ar['members']))
    check('exact15_archived_members_match_output_hashes',len(members)==len(ar['members'])==15 and set(members)==names|{'forward_attempts.jsonl','memory_manifest.jsonl','neighbor_summaries.jsonl','capture_complete.json','resources.jsonl'} and all(all(x[k]==output[name][k] for k in ('bytes','sha256')) for name,x in members.items()) and read(F/'archive_result_v1.json')['members']==15)
    reference_root=I/'references';lookup={x['output_filename']:i for i,x in enumerate(rows)};array_results=[];seen=set();max_desc_error=0.;max_native_error=0.
    rt,at=criteria['descriptor_recompute']['rtol'],criteria['descriptor_recompute']['atol']
    with tarfile.open(archive,'r|gz') as tar:
        for member in tar:
            assert member.isfile() and member.name in members and member.name not in seen;seen.add(member.name)
            raw=tar.extractfile(member).read();assert len(raw)==members[member.name]['bytes'] and hashlib.sha256(raw).hexdigest()==members[member.name]['sha256']
            if member.name not in lookup:continue
            n=lookup[member.name];row=rows[n];m=manifest[n];g=summaries[n]
            with np.load(io.BytesIO(raw),allow_pickle=False) as z:a={k:z[k].copy() for k in z.files}
            assert set(a)==set(criteria['shapes'])
            for k,v in a.items():
                assert list(v.shape)==criteria['shapes'][k] and v.dtype==(np.int64 if k in ('N0','N1') else np.float32) and np.isfinite(v).all()
            assert np.array_equal(a['coarse'],a['Q1']) and np.allclose(a['Qraw']+a['delta0'],a['Q1'],rtol=2e-6,atol=2e-7)
            for key,Q in [('N0',a['Qraw']),('N1',a['Q1'])]:
                idx=a[key];assert np.all((idx>=0)&(idx<256)) and all(len(set(v.tolist()))==8 for v in idx)
                distances=np.linalg.norm(a['M'].astype(np.float64)[None,:,:]-Q.astype(np.float64)[:,None,:],axis=-1)
                selected=np.take_along_axis(distances,idx,axis=1).max(1);mask=np.ones((256,256),bool);np.put_along_axis(mask,idx,False,axis=1);excluded=np.where(mask,distances,np.inf).min(1)
                tol=64*np.finfo(np.float32).eps*np.maximum(1,np.maximum(selected,excluded));assert np.all(selected<=excluded+tol)
            for key,idx in [('h_static',a['N0']),('h_requery',a['N1'])]:
                h=descriptor(a,idx);err=float(np.max(np.abs(a[key].astype(np.float64)-h)));max_desc_error=max(max_desc_error,err)
                assert np.allclose(a[key],h,rtol=rt,atol=at),(row['case_id'],key,err)
                assert np.array_equal(a[key][:,:1024],np.broadcast_to(a['z'],(256,1024))) and np.array_equal(a[key][:,1792:1795],a['Q1'])
            overlap=(a['N0'][:,:,None]==a['N1'][:,None,:]).any(-1).mean(-1)
            assert g['neighbor_overlap_mean']==float(overlap.mean()) and g['neighbor_overlap_min']==float(overlap.min()) and g['changed_neighbor_queries']==int((overlap<1).sum())
            h0,h1=a['h_static'],a['h_requery'];computed=dict(h_max_abs_difference=float(np.max(np.abs(h1-h0))),fa_L2_mean=float(np.linalg.norm(h1[:,1024:1408]-h0[:,1024:1408],axis=-1).mean()),geometry_L2_mean=float(np.linalg.norm(h1[:,1795:]-h0[:,1795:],axis=-1).mean()),old_neighbor_mean_distance=float(h0[:,-1].mean()),new_neighbor_mean_distance=float(h1[:,-1].mean()))
            assert g['h_exactly_equal']==bool(np.array_equal(h0,h1)) and all(np.isclose(g[k],v,rtol=rt,atol=at) for k,v in computed.items())
            refpath=reference_root/('S_'+row['fold']+'__'+row['case_id']+'.npz');assert sha(refpath)==row['reference']['sha256']
            with np.load(refpath,allow_pickle=False) as z:
                assert set(z.files)=={'prediction','coarse','Qraw','delta'}
                errors={}
                for old,new in [('prediction','prediction'),('coarse','Q1'),('Qraw','Qraw'),('delta','delta0')]:
                    value=float(np.max(np.abs(z[old].astype(np.float64)-a[new].astype(np.float64))));max_native_error=max(max_native_error,value)
                    assert value<=1e-6 and value*row['normalization']['scale']<=.001
                    assert m['equivalence'][old]==dict(normalized_max_abs=value,world_max_abs_mm=value*row['normalization']['scale']);errors[old]=value
            array_results.append(dict(case_id=row['case_id'],run=row['run'],array_keys=len(a),native_max_abs=max(errors.values()),descriptor_verified=True,nearest_membership_verified=True))
    check('all15_local_archive_members_fresh_bytes_match',seen==set(members))
    check('all10_arrays_shapes_dtypes_finite_Q_arithmetic',len(array_results)==10)
    check('N0_N1_valid_unique_and_nearest_to_Qraw_Q1',all(x['nearest_membership_verified'] for x in array_results))
    check('independent_CPU64_Phi_at_Q1_and_exact_z_Q_slices',all(x['descriptor_verified'] for x in array_results))
    check('all10_native_references_and_logged_errors_recomputed',max_native_error<=1e-6)
    check('all10_neighbor_summaries_recomputed_from_arrays',True)
    check('collection_complete_no_failure_or_extra_execution',read(F/'collection_complete_v1.json')['status']=='READONLY_COLLECTION_COMPLETE' and not (F/'collection_failure_v1.json').exists() and 'failure.json' not in output)
    peaks={k:max(x['values'][k] for x in resources) for k in ('RSS_bytes','device_MiB','peak_allocated','peak_reserved','elapsed_seconds')};peaks['minimum_free_disk_bytes']=min(x['values']['free_disk_bytes'] for x in resources)
    audit=dict(status='FORMAL_SCQ_RF_POST_DIAGNOSTIC_FREEZE_AUDIT_PASS',date='2026-11-14',request_sha256=QH,checks=checks,checks_passed=len(checks),counts=q['counts'],output_files=23,installed_files=21,archive_members=15,cases=10,sources=10,models=[dict(run=x['run'],forwards=x['forwards'],state_sha256=x['state_before'],state_unchanged=True,RNG_unchanged=True) for x in done['models']],array_results=array_results,max_native_difference=max_native_error,max_descriptor_CPU64_vs_saved_FP32_difference=max_desc_error,resource_peaks=peaks,archive=dict(path=ar['path'],local_audit_copy=str(archive),bytes=ar['bytes'],sha256=ar['sha256']),seconds=time.monotonic()-start,operations=dict(server_writes=0,new_forward=0,model_load=0,checkpoint_deserialization=0,CUDA_tensor_operations=0,GT_arrays_read=0,new_accuracy_scoring=0),limitations=['Model and RNG equality verified from recorded fingerprints and bound source; no model restored to rehash current tensors.','Extra KNN count supported by execution/source and ten saved outputs, not low-level kernel tracing.','Sampled resource records, no hard isolation or PID ownership guarantee.','CPU64 descriptor audit uses predefined arithmetic tolerance only; not an efficacy threshold.','Local archive is an audit working copy, not a new long-term backup claim.'])
    emit('formal_post_diagnostic_freeze_audit_v1.json',audit)
    print(json.dumps(dict(status=audit['status'],checks=len(checks),max_native_difference=max_native_error,max_descriptor_recompute_error=max_desc_error,resource_peaks=peaks,seconds=audit['seconds'])))
except BaseException as exc:
    emit('audit_failure_v1.json',dict(status='AUDIT_FAILED_STOP_NO_ANALYSIS',checks=checks,error=repr(exc)))
    raise
