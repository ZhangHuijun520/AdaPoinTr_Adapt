"""Formal stdlib-only audit of completed RF CUDA artifacts; no model or torch import."""
from pathlib import Path
import ast,hashlib,json,math,struct

R=Path(__file__).resolve().parent.parent
B=R/'outputs/scq_rf_initialization_loader_20261114_v2'
F=B/'post_CUDA_freeze_audit_v3';D=F/'downloads'
QH='8a3d0173fa3cec9e737e384c9af99f37e996c79ef3e60bb5e99b14dc275f2cac'
checks={}


def read(p):return json.loads(p.read_bytes())
def rec(p):return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def check(name,value):
    assert bool(value),name
    checks[name]=True
def emit(p,j):
    with p.open('x',encoding='utf-8') as f:json.dump(j,f,indent=2,ensure_ascii=False,allow_nan=False)


qp=D/'installed/SCQ_RF_artificial_cuda_execution_request_v3.json';q=read(qp)
check('authorized_request_exact_unchanged_bytes',rec(qp)['sha256']==QH==rec(B/'pending_transport_v3/payload'/qp.name)['sha256'])
check('current_identity_exit0_tmux_worker_absent',read(F/'finished_result_v1.json')['status']=='EXIT0_TMUX_AND_WORKER_ABSENT')
before,after=read(F/'inventory_before_result_v1.json'),read(F/'inventory_after_result_v1.json')
check('two_readings_content_hashes_and_fingerprints_stable_excluding_atime',before==after)
files=before['files'];collection=read(F/'collection_complete_v1.json')
check('bounded32_files8MiB60seconds',len(files)==32 and before['hashed_bytes']<=8388608 and collection['seconds']<=60)
output_names={'completion.json','construction.json','events.jsonl','resources.jsonl','payload_manifest.json','launch.log','worker.pid','exit_code.txt'}
check('exact_output8_installed12_related8_upload4_file_sets',{n for n in files if n.startswith('output/')}=={'output/'+n for n in output_names} and sum(n.startswith('installed/') for n in files)==12 and sum(n.startswith('related/') for n in files)==8 and sum(n.startswith('upload/') for n in files)==4)
check('exact_install_control_and_output_cache_directories',before['directories']['installed']==['.','control'] and before['directories']['output']==sorted(['.','tmp','cache','mplconfig','triton_cache','hf_cache']))
metadata=read(F/'metadata_result_v1.json')
for name,row in metadata['files'].items():
    p=D/name;assert rec(p)['sha256']==row['sha256']==files[name]['sha256'] and p.stat().st_size==row['bytes']==files[name]['bytes']
check('all28_readback_bytes_match_fresh_remote_hashes',len(metadata['files'])==28)
mapping=read(B/'pending_transport_v3/installation_mapping_v3.json')
for row in mapping['files']:
    p=D/'installed'/Path(row['target']).name;assert rec(p)['sha256']==row['sha256']==rec(B/'pending_transport_v3'/row['member'])['sha256'] and p.stat().st_size==row['bytes']
check('eight_installed_payloads_match_frozen_mapping',len(mapping['files'])==8)
delivery=read(B/'pending_delivery_v3.json');archive=Path(delivery['archive']['path'])
for suffix in ('','.sha256','.bytes','.contents.sha256'):
    p=Path(str(archive)+suffix);r=files['upload/'+p.name];assert rec(p)['sha256']==r['sha256'] and p.stat().st_size==r['bytes']
check('archive_and_three_sidecars_match_frozen_upload',True)
E=B/'authorized_execution_v3'
for name in ('authorization_v3.json','runtime_v3.json','launch_once_v3.sh'):
    assert (D/'installed/control'/name).read_bytes()==(E/name).read_bytes()
a=read(D/'installed/control/authorization_v3.json');rt=read(D/'installed/control/runtime_v3.json')
check('authorization_one_way_runtime_and_exclusive_claim',set(a)=={'schema','request_sha256','explicit_user_authorization','user_authorization_text'} and a['request_sha256']==QH and a['explicit_user_authorization'] is True and rt==dict(schema='bcsp-scq-rf-cuda-runtime-v1',request_sha256=QH,authorization_sha256=rec(D/'installed/control/authorization_v3.json')['sha256']) and read(D/'installed/control/attempt_claim_v3.json')==dict(status='CLAIMED_BEFORE_TMUX',request_sha256=QH))
check('exit_code_exact0', (D/'output/exit_code.txt').read_text().strip()=='0')
comp=read(D/'output/completion.json');construction=read(D/'output/construction.json');manifest=read(D/'output/payload_manifest.json')
events=[json.loads(line) for line in (D/'output/events.jsonl').read_text().splitlines()]
resources=[json.loads(line) for line in (D/'output/resources.jsonl').read_text().splitlines()]
counts=dict(full_forward=5,full_backward=4,full_loss=4,decoder_forward=0,decoder_backward=0,optimizer_steps=0)
check('completion_exact5F4loss4B0step_native_initial_equivalence',comp['status']=='RF_NATIVE_CUDA_COMPLETE_PENDING_FORMAL_FREEZE' and comp['request_sha256']==QH and comp['counts']==counts and comp['initial_common_state_equal'] is True and comp['initial_RF_Sref_equivalence'] is True)
check('no_real_data_checkpoint_optimizer_BNCal_training',comp['real_data_reads']==comp['checkpoint_loads']==0 and comp['optimizer_constructed'] is False and comp['BNCal'] is False and comp['training_admission'] is False)
for row in manifest:assert files['output/'+row['name']]['bytes']==row['bytes'] and files['output/'+row['name']]['sha256']==row['sha256']
check('payload_manifest_four_members_exact_fresh_hashes',len(manifest)==4 and {r['name'] for r in manifest}=={'completion.json','construction.json','events.jsonl','resources.jsonl'})
entry=D/'related/0_bcsp_scq_rf_cuda_admission_v2.py';factory=D/'related/1_bcsp_scq_rf_factory_v1.py'
refs=[q['entry'],q['implementation']['rf_factory'],q['rf_initialization'],q['initialization'],q['implementation']['scq_residual'],q['implementation']['scq_factory'],q['implementation']['lqi_decoder'],q['parent_helper']]
for i,r in enumerate(refs):
    p=D/'related'/(str(i)+'_'+Path(r['path']).name);assert rec(p)['sha256']==r['sha256'] and p.stat().st_size==r['bytes'] and files['related/'+p.name]['path']==r['path']
check('eight_reused_source_and_initialization_bindings_exact',True)
rf_init=D/'related/2_rf_initialization_v1.bin';scq_init=D/'related/3_initialization_v1.bin'
M=R/'outputs/scq_rf_implementation_20261114_v1';S=R/'outputs/cranial_bcsp_scq_implementation_20261113_v1'
initializations=[]
for path,manpath,original in [(rf_init,M/'initialization_manifest_v1.json',M/'initialization_v1.bin'),(scq_init,S/'initialization_manifest_v1.json',S/'initialization_v1.bin')]:
    m=read(manpath);raw=path.read_bytes();assert rec(path)['sha256']==m['sha256']==rec(original)['sha256'] and len(raw)==m['bytes']
    pos=0
    for row in m['layout']:
        length=math.prod(row['shape'])*4;b=raw[pos:pos+length];pos+=length
        assert hashlib.sha256(b).hexdigest()==row['sha256'] and all(math.isfinite(v[0]) for v in struct.iter_unpack('<f',b))
        if row['name'].startswith(('V2.','W2.')):assert b==bytes(len(b))
    assert pos==len(raw)
    initializations.append(dict(server_path=files['related/'+path.name]['path'],bytes=len(raw),sha256=m['sha256'],all_block_hashes_finite_zero_heads=True))
check('both_frozen_initializations_exact_chunk_hashes_finite_zero_heads',len(initializations)==2)
check('corrected_loader_source_and_P3_bind_current_version',rec(D/'installed/bcsp_scq_rf_residual_v2.py')['sha256']==q['implementation']['rf_residual']['sha256'] and rec(D/'installed/implementation_P3_v3.json')['sha256']==q['implementation_P3']['sha256'] and read(D/'installed/implementation_P3_v3.json')['loader_CPU_checks']==36)
# Extract only the side-effect-free string-prefix function, never import entry/torch/models.
et=ast.parse(entry.read_text(encoding='utf-8'));fn=next(n for n in et.body if isinstance(n,ast.FunctionDef) and n.name=='gradient_prefixes')
env={};exec(compile(ast.Module([fn],[]),'pure_prefix_list_only','exec'),env);prefixes=env['gradient_prefixes']();assert len(prefixes)==35
expected_running={k:0 for k in counts};cursor=0;summaries=[]
for i,phase in enumerate(q['phases']):
    label,variant,batch,training=phase
    chunk=events[cursor:cursor+(5 if variant=='S-ref' else 8)];cursor+=len(chunk)
    kinds=['NATIVE_OPTIMIZER_CLASSIFICATION_ONLY','ATTEMPT_BEFORE_CALL','COORDINATE_CONSUMERS_BEFORE_ASSERTIONS',None,'PHASE_RESTORATION'] if variant=='S-ref' else ['NATIVE_OPTIMIZER_CLASSIFICATION_ONLY','ATTEMPT_BEFORE_CALL','COORDINATE_CONSUMERS_BEFORE_ASSERTIONS','ATTEMPT_BEFORE_CALL','ATTEMPT_BEFORE_CALL','HEAD_GRADIENTS_BEFORE_ASSERTIONS',None,'PHASE_RESTORATION']
    assert [r.get('kind') for r in chunk]==kinds
    assert all(r.get('phase',label)==label for r in chunk)
    for row in chunk:
        if row.get('kind')=='ATTEMPT_BEFORE_CALL':
            expected_running[row['operation']]+=1
            assert row['counts']==expected_running
    groups=chunk[0]['rows'];total=sum(math.prod(row['shape']) for row in groups)
    assert total==(40596676 if variant=='S-ref' else 40827847) and len({r['name'] for r in groups})==len(groups)
    assert all(r['weight_decay']==0 for r in groups if r['reason']=='explicit_no_weight_decay')
    for r in groups:
        if r['name'].startswith('base_model.rf.'):assert r['weight_decay']==(0. if r['name'].endswith('.bias') else .0005)
    row,restore=chunk[-2:];assert row==comp['phases'][i]
    assert (row['phase'],row['variant'],row['batch'])==(label,variant,batch) and row['parameters_unchanged'] is True
    assert all(restore[k] is True for k in ('state_restored','RNG_restored','modes_restored','BN_momenta_restored','gradients_cleared'))
    changes=row['BN_changed'];assert bool(changes)==training and all(n.endswith(('running_mean','running_var','num_batches_tracked')) for n in changes)
    if not training:assert row['RNG_before']==row['RNG_after']
    for key in ('RNG_before','RNG_after'):
        assert set(row[key])=={'CPU','CUDA','Python','numpy'}
        assert all(len(row[key][k])==64 and all(c in '0123456789abcdef' for c in row[key][k]) for k in ('CPU','CUDA'))
    c=chunk[2];assert row['coordinate_consumers']==c and c['exact_call_contract'] is True
    assert c['call_counts']==c['expected_call_counts']==dict(query=1,decoder=1,Memory=1,PE=2,rebuild=1,relative=1)
    assert c['relative_shape']==[batch,256,32,3]
    assert [r['role'] for r in c['comparisons']]==['query_MLP','decoder_query','PE_query_first','PE_Memory_second','FC_rebuild','dense_center']
    for r in c['comparisons']:
        assert r['present'] and r['finite'] and r['exact_equal'] and r['max_abs']==0 and r['dtype']=='torch.float32' and r['device']=='cuda:0'
        assert r['actual_shape']==r['expected_shape']==([batch,8192,3] if r['role']=='dense_center' else [batch,256,3])
    if variant=='S-ref':
        assert row['loss'] is None and row['gradients'] is None and row['head_gradients'] is None
    else:
        assert math.isfinite(row['loss']) and row['loss']>=0
        norms=row['gradients']['parameter_norms'];totals=row['gradients']['module_norm_sums']
        assert set(totals)==set(prefixes) and all(math.isfinite(v) and v>=0 for v in norms.values())
        for prefix in prefixes:
            measured=sum(v for n,v in norms.items() if n.startswith(prefix));assert measured>0 and math.isclose(measured,totals[prefix],rel_tol=1e-12,abs_tol=1e-12)
        heads=chunk[5];assert row['head_gradients']==heads['heads']
        assert heads['Q2']['present'] and heads['Q2']['finite'] and heads['Q2']['norm']>0 and math.isfinite(heads['Q2']['norm'])
        for head,hidden,last in [('scq','W1','W2'),('rf','V1','V2')]:
            values=row['head_gradients'][head];assert set(values)=={hidden+'.weight',hidden+'.bias',last+'.weight',last+'.bias'}
            assert all(v['present'] and v['finite'] and math.isfinite(v['norm']) for v in values.values())
            assert values[hidden+'.weight']['norm']==values[hidden+'.bias']['norm']==0
            assert values[last+'.weight']['norm']>0 and values[last+'.bias']['norm']>0
            for name,v in values.items():assert math.isclose(v['norm'],norms['base_model.'+head+'.'+name],rel_tol=1e-12,abs_tol=1e-12)
        if not training:assert len(row['initial_equivalence'])==2 and all(r['close'] is True and math.isfinite(r['max_abs']) and r['max_abs']>=0 for r in row['initial_equivalence'])
    summaries.append(dict(phase=label,variant=variant,batch=batch,loss=row['loss'],all_six_Q2_comparisons_max_abs0=True,gradient_prefixes=0 if variant=='S-ref' else 35,head_gradients=row['head_gradients'],initial_equivalence=row['initial_equivalence'],BN_changed_count=len(changes),restoration=restore))
check('exact37_events_five_phases_13_pre_call_claims',cursor==len(events)==37 and expected_running==counts)
check('all_five_native_parameter_groupings_correct',True)
check('all_six_consumers_five_phases_exact_count_and_values',True)
check('four_backwards35_shared_gradient_groups_recomputed_positive_finite',True)
check('both_heads_initial_zero_hidden_effective_output_and_Q2_gradients',True)
check('all_recorded_state_RNG_modes_BN_restore_and_eval_fingerprints',True)
native={'base_model.encoder.blocks.blocks.'+str(i)+'.attn.mixer':10 for i in range(6)}
native.update({'base_model.decoder.blocks.'+str(i)+'.'+s:(5 if s=='cond_ssm' else 10) for i in range(8) for s in ('self_ssm','cond_ssm')})
check('actual22_native_modules180_calls',comp['native_SSM_calls']==native and len(native)==22 and sum(native.values())==180)
assert len(construction['models'])==5
for row,phase in zip(construction['models'],q['phases']):
    assert row['phase']==phase[0] and row['variant']==phase[1]
    assert row['parameters']==(40596676 if phase[1]=='S-ref' else 40827847) and row['new_parameters']==(0 if phase[1]=='S-ref' else 231171)
    assert row['logical_capacity']>q['limits']['torch_peak_bytes']
check('five_native_builds_shared_original_SCQ_state_equal',len({r['shared_initial_state_SHA256'] for r in construction['models']})==1)
check('seven_native_dependency_origins_bound',len(construction['native_origins'])==7 and set(construction['native_origins'])<={r['path'] for r in q['dependencies']})
for row in resources:
    v=row['values'];L=q['limits'];assert all(math.isfinite(x) and x>=0 for x in v.values())
    actual=dict(RSS=v['RSS_bytes']<=L['RSS_bytes'],output=v['output_bytes']<=L['output_bytes'],device=v['device_MiB']<=L['device_MiB'],allocated=v['peak_allocated']<=L['torch_peak_bytes'],reserved=v['peak_reserved']<=L['torch_peak_bytes'],wall=v['elapsed_seconds']<=L['wall_seconds'],disk=v['free_disk_bytes']>=L['minimum_free_disk_bytes'])
    assert row['checks']==actual and all(actual.values()) and row['failed_checks']==[] and 0<=row['forwards']<=5
assert resources[0]['phase']=='before_construction' and resources[-1]['phase']=='complete' and resources[-1]['forwards']==5
for phase in q['phases']:assert sum(r['phase']==phase[0]+':restored' for r in resources)==1
check('all_recorded_resource_limits_independently_recomputed',len(resources)>0)
peaks=dict(samples=len(resources),max_RSS_bytes=max(r['values']['RSS_bytes'] for r in resources),max_SMI_MiB=max(r['values']['device_MiB'] for r in resources),max_allocated_bytes=max(r['values']['peak_allocated'] for r in resources),max_reserved_bytes=max(r['values']['peak_reserved'] for r in resources),minimum_free_disk_bytes=min(r['values']['free_disk_bytes'] for r in resources),monitored_elapsed_seconds=resources[-1]['values']['elapsed_seconds'])
result=dict(status='FORMAL_RF_POST_CUDA_FREEZE_AUDIT_PASS',request_sha256=QH,checks=checks,count=len(checks),exit_code=0,counts=counts,
    native_SSM_modules=22,native_SSM_calls=180,phases=summaries,initializations=initializations,resources=peaks,
    fresh_file_count=len(files),unique_hashed_bytes=before['hashed_bytes'],collection_seconds=collection['seconds'],
    evidence_manifest=[dict(name=k,**v) for k,v in files.items()],
    evidence_limits=['State/RNG restoration verified from bound runtime assertions, event/completion consistency and saved fingerprints; no independent model reload after exit.',
                     'Torch per-phase recorded peaks plus sampled SMI/RSS; not a hard cgroup or continuous physical GPU peak guarantee.',
                     'KNN and model Native call counts bound to hooks/journals, not a kernel trace.',
                     'Artificial zero-update check proves this frozen CUDA path can run; not RF efficacy, reliability, or training authorization.'],
    server_writes=0,new_forward=0,model_imports=0,torch_imports=0,random_regeneration=0,training_authorized=False,training_request_created=False)
emit(F/'freeze_verification_v3.json',result)
print(json.dumps(dict(status=result['status'],checks=len(checks),files=len(files),bytes=before['hashed_bytes'],counts=counts,resources=peaks)))
