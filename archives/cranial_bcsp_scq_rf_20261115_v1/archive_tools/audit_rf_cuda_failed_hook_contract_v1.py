"""Independent stdlib-only failure freeze and exact-source hook contract review."""
from pathlib import Path
import ast
import hashlib
import json

R=Path(__file__).resolve().parent.parent
B=R/'outputs/scq_rf_cuda_preparation_20261114_v1'
F=B/'failed_freeze_hook_review_v1'
D=F/'downloads'
QH='85854f243d29000cc7a0ee87b03f4ce23974fc92d94d6fd479fd695e68c7ab32'
checks={}


def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rec(p):return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=sha(p))
def check(name,value):
    assert bool(value),name
    checks[name]=True
def emit(p,j):
    with p.open('x',encoding='utf-8') as f:json.dump(j,f,indent=2,ensure_ascii=False,allow_nan=False)


qpath=D/'installed/SCQ_RF_artificial_cuda_execution_request_v1.json';q=read(qpath)
check('authorized_request_exact_bytes',sha(qpath)==QH==sha(B/'pending_transport_v1/payload'/qpath.name))
check('current_identity_failed_exit_and_no_live_worker_tmux',read(F/'finished_result_v1.json')['status']=='FAILED_EXIT1_TMUX_AND_WORKER_ABSENT')
first,last=read(F/'inventory_before_result_v1.json'),read(F/'inventory_after_result_v1.json')
check('all_hashes_and_content_fingerprints_stable_excluding_atime',first==last)
files=first['files']
check('bounded29_files_within8MiB_60seconds',len(files)==29 and first['hashed_bytes']<=8388608 and read(F/'collection_complete_v1.json')['seconds']<=60)
check('exact_output6_installed16_upload4_related3',
      {k for k in files if k.startswith('output/')}=={'output/'+n for n in ('worker.pid','failure.json','launch.log','events.jsonl','resources.jsonl','exit_code.txt')}
      and sum(k.startswith('installed/') for k in files)==16 and sum(k.startswith('upload/') for k in files)==4 and sum(k.startswith('related/') for k in files)==3)
check('exact_output_cache_directories_and_install_control_directory',first['directories']['installed']==['.','control'] and first['directories']['output']==sorted(['.','cache','hf_cache','mplconfig','tmp','triton_cache']))
metadata=read(F/'metadata_result_v1.json')
for name,row in metadata['files'].items():
    p=D/name;assert len(p.read_bytes())==row['bytes']==files[name]['bytes'] and sha(p)==row['sha256']==files[name]['sha256']
check('all25_readback_files_match_fresh_server_hashes',len(metadata['files'])==25)
mapping=read(B/'pending_transport_v1/installation_mapping_v1.json')
for row in mapping['files']:
    local=B/'pending_transport_v1'/row['member'];fresh=D/'installed'/Path(row['target']).name
    assert fresh.stat().st_size==row['bytes'] and sha(fresh)==row['sha256']==sha(local)
check('twelve_installed_payloads_match_frozen_mapping',len(mapping['files'])==12)
delivery=read(B/'pending_delivery_v1.json');archive=Path(delivery['archive']['path'])
for suffix in ('','.sha256','.bytes','.contents.sha256'):
    p=Path(str(archive)+suffix);row=files['upload/'+p.name]
    assert row['bytes']==p.stat().st_size and row['sha256']==sha(p)
check('uploaded_archive_three_sidecars_match_local_frozen_bytes',True)
E=B/'authorized_execution_v1'
for name in ('authorization_v1.json','runtime_v1.json','launch_once_v1.sh'):
    assert (D/'installed/control'/name).read_bytes()==(E/name).read_bytes()
a=read(D/'installed/control/authorization_v1.json');rt=read(D/'installed/control/runtime_v1.json')
check('one_way_authorization_runtime_no_reverse_binding',set(a)=={'schema','request_sha256','explicit_user_authorization','user_authorization_text'} and a['request_sha256']==QH and a['explicit_user_authorization'] is True and rt==dict(schema='bcsp-scq-rf-cuda-runtime-v1',request_sha256=QH,authorization_sha256=sha(D/'installed/control/authorization_v1.json')))
check('controls_and_exclusive_single_claim_match_execution',read(D/'installed/control/attempt_claim_v1.json')==dict(status='CLAIMED_BEFORE_TMUX',request_sha256=QH))
expected_counts=dict(full_forward=1,full_backward=0,full_loss=0,decoder_forward=0,decoder_backward=0,optimizer_steps=0)
failure=read(D/'output/failure.json')
check('exact_failure_reason_exit1_and_counts1F0loss0B0step',failure==dict(status='FAILED_STOP_NO_RETRY',error="RuntimeError('actual Q2 consumer mismatch')",counts=expected_counts) and (D/'output/exit_code.txt').read_text().strip()=='1')
events=[json.loads(line) for line in (D/'output/events.jsonl').read_text().splitlines()]
check('exact_event_order_no_later_RF_or_loss_phase',len(events)==3 and [r['kind'] for r in events]==['NATIVE_OPTIMIZER_CLASSIFICATION_ONLY','ATTEMPT_BEFORE_CALL','PHASE_RESTORATION'] and events[0]['phase']==events[2]['phase']=='S_ref_eval1' and events[1]['operation']=='full_forward' and events[1]['counts']==expected_counts)
restoration=events[-1]
check('recorded_state_RNG_modes_BN_and_gradient_restoration',all(restoration[k] is True for k in ('state_restored','RNG_restored','modes_restored','BN_momenta_restored','gradients_cleared')))
check('actual_native_Sref_parameter_count_and_no_decay_rows',sum(__import__('math').prod(row['shape']) for row in events[0]['rows'])==40596676 and all(row['weight_decay']==0 for row in events[0]['rows'] if row['reason']=='explicit_no_weight_decay'))
resources=[json.loads(line) for line in (D/'output/resources.jsonl').read_text().splitlines()]
for row in resources:
    v=row['values'];L=q['limits']
    actual=dict(RSS=v['RSS_bytes']<=L['RSS_bytes'],output=v['output_bytes']<=L['output_bytes'],device=v['device_MiB']<=L['device_MiB'],allocated=v['peak_allocated']<=L['torch_peak_bytes'],reserved=v['peak_reserved']<=L['torch_peak_bytes'],wall=v['elapsed_seconds']<=L['wall_seconds'],disk=v['free_disk_bytes']>=L['minimum_free_disk_bytes'])
    assert row['checks']==actual and all(actual.values()) and row['failed_checks']==[] and row['forwards'] in (0,1)
check('all_recorded_resource_samples_recomputed_pass',len(resources)>0)
entry=D/'installed/bcsp_scq_rf_cuda_admission_v1.py';lqi=D/'related/1_bcsp_lqi_decoder_v1.py';mother=D/'related/2_AdaPoinTr.py';scq=D/'related/0_bcsp_scq_factory_v1.py'
check('three_actual_related_source_hashes_bound_to_request',sha(lqi)==q['implementation']['lqi_decoder']['sha256'] and sha(scq)==q['implementation']['scq_factory']['sha256'] and sha(mother)==next(r['sha256'] for r in q['reused_readonly_bindings'] if r['path']==q['model_root']+'/models/AdaPoinTr.py'))
entry_tree=ast.parse(entry.read_text(encoding='utf-8'));lqi_tree=ast.parse(lqi.read_text(encoding='utf-8'))
dec=next(n for n in lqi_tree.body if isinstance(n,ast.ClassDef) and n.name=='LQIDecoder')
fw=next(n for n in dec.body if isinstance(n,ast.FunctionDef) and n.name=='forward')
pe_calls=[n for n in ast.walk(fw) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='coordinate_pe']
check('actual_decoder_same_PE_module_called_query_then_Memory',len(pe_calls)==2 and [ast.unparse(n.args[0]) for n in pe_calls]==['q_pos','v_pos'])
phase=next(n for n in entry_tree.body if isinstance(n,ast.FunctionDef) and n.name=='phase_checks')
pe_writers=[n for n in ast.walk(phase) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='update' and any(k.arg=='PE' for k in n.keywords)]
check('entry_hook_overwrites_single_PE_key',len(pe_writers)==1 and 'PE=a[0].detach().clone()' in ast.unparse(pe_writers[0]))
test=D/'installed/test_rf_cuda_entry_cpu_v1.py';test_tree=ast.parse(test.read_text(encoding='utf-8'))
fake=next(n for n in ast.walk(test_tree) if isinstance(n,ast.ClassDef) and n.name=='Decoder')
fake_calls=[n for n in ast.walk(fake) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='coordinate_pe']
check('CPU_entry_fixture_covers_one_PE_call_only',len(fake_calls)==1 and ast.unparse(fake_calls[0].args[0])=='q_pos')
log=(D/'output/launch.log').read_text(encoding='utf-8')
check('saved_trace_fails_after_return_and_before_loss',"RuntimeError: actual Q2 consumer mismatch" in log and "phase_checks" in log and 'need(all(torch.equal(consumers[k],coarse)' in log)
findings=dict(status='HOOK_CONTRACT_DEFECT_CONFIRMED_BY_EXACT_SOURCE_NOT_NEW_FORWARD',
    chain=['LQIDecoder calls the same coordinate_pe on q_pos then v_pos unconditionally.',
           'The forward-pre-hook writes both inputs to consumers[PE] using dict.update.',
           'The second call overwrites the query snapshot with Memory coordinates v_pos.',
           'After model return, the entry compares that Memory snapshot with returned coarse/Q1 (Q2 slot). This is the wrong expected consumer role.',
           'The cheap CPU entry Decoder calls coordinate_pe only once, so its37 checks do not exercise overwrite.'],
    local_evidence=[dict(**rec(p),anchors=[dict(line=i,text=line.strip()) for i,line in enumerate(p.read_text(encoding='utf-8').splitlines(),1) if any(s in line for s in needles)]) for p,needles in [(entry,['consumers.update(PE=','actual Q2 consumer mismatch']),(lqi,['qp, mp = self.coordinate_pe']),(test,['def forward(self,q_pos):return self.coordinate_pe'])]],
    correct_contract='Record both calls in order and by role; query PE must match decoder q_pos/current coarse and Memory PE must match decoder v_pos. Preserve exact equality and call-count checks, and record per-consumer shapes/equality before combined assertions.',
    missing_runtime_evidence='No per-consumer tensor snapshots or equality vector were saved by the failed entry; cannot independently certify every consumer or actual numeric mismatch from artifacts. No re-forward allowed.',
    limitation='Confirms an observation/guard contract error sufficient to explain a false rejection, not proof of absence of all model defects or RF CUDA success.',
    RF_models_executed=False,source_edits=0,tests_run=0,new_forward=0)
emit(F/'hook_contract_findings_v1.json',findings)
summary=dict(status='FORMAL_RF_CUDA_FAILED_RUN_FREEZE_AUDIT_PASS_EXECUTION_REMAINS_FAILED',request_sha256=QH,checks=checks,count=len(checks),
             exact_file_count=len(files),unique_hashed_bytes=first['hashed_bytes'],remote_collection_seconds=read(F/'collection_complete_v1.json')['seconds'],
             actual_counts=expected_counts,exit_code=1,request_consumed=True,request_reuse_allowed=False,
             failure=rec(D/'output/failure.json'),hook_contract_findings=rec(F/'hook_contract_findings_v1.json'),
             evidence_manifest=[dict(name=k,**v) for k,v in files.items()],
             resources=dict(samples=len(resources),max_RSS_bytes=max(r['values']['RSS_bytes'] for r in resources),max_SMI_MiB=max(r['values']['device_MiB'] for r in resources),max_peak_allocated_bytes=max(r['values']['peak_allocated'] for r in resources),max_peak_reserved_bytes=max(r['values']['peak_reserved'] for r in resources)),
             restoration='Saved assertion records pass; no model reload or independent GPU reconstruction performed.',
             server_writes=0,new_forward=0,model_imports=0,tests_run=0,CUDA_admission_pass=False,scientific_efficacy='NOT_TESTED')
emit(F/'formal_failure_freeze_audit_v1.json',summary)
print(json.dumps(dict(status=summary['status'],checks=len(checks),files=len(files),bytes=first['hashed_bytes'],resources=summary['resources'],hook_contract=findings['status'])))
