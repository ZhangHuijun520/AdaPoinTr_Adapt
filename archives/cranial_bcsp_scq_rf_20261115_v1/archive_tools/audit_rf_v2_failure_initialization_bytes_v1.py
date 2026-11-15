"""Stdlib-only failure freeze and binary-contract review. Never generates random values."""
from pathlib import Path
import ast,hashlib,json,math,struct

R=Path(__file__).resolve().parent.parent
B=R/'outputs/scq_rf_cuda_preparation_20261114_v2'
F=B/'failed_freeze_initialization_review_v1';D=F/'downloads'
M=R/'outputs/scq_rf_implementation_20261114_v1'
QH='09de6045f2ecc760558039c2c25724e94eae078b52f744aef6e25574575e1bcf'
checks={}


def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rec(p):return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=sha(p))
def check(n,v):
    assert bool(v),n
    checks[n]=True
def emit(p,j):
    with p.open('x',encoding='utf-8') as f:json.dump(j,f,indent=2,ensure_ascii=False,allow_nan=False)


qpath=D/'installed/SCQ_RF_artificial_cuda_execution_request_v2.json';q=read(qpath)
check('exact_authorized_v2_request',sha(qpath)==QH==sha(B/'pending_transport_v2/payload'/qpath.name))
check('current_identity_failed_exit1_no_live_worker_or_tmux',read(F/'finished_result_v1.json')['status']=='FAILED_EXIT1_TMUX_AND_WORKER_ABSENT')
first,last=read(F/'inventory_before_result_v1.json'),read(F/'inventory_after_result_v1.json')
check('two_readings_all_content_hashes_and_fingerprints_stable',first==last)
files=first['files']
check('bounded26_files_8MiB_60seconds',len(files)==26 and first['hashed_bytes']<=8388608 and read(F/'collection_complete_v1.json')['seconds']<=60)
check('exact_output6_install11_related5_upload4',
      {n for n in files if n.startswith('output/')}=={'output/'+n for n in ('failure.json','exit_code.txt','worker.pid','launch.log','events.jsonl','resources.jsonl')}
      and sum(n.startswith('installed/') for n in files)==11 and sum(n.startswith('related/') for n in files)==5 and sum(n.startswith('upload/') for n in files)==4)
check('expected_output_cache_and_install_directories',first['directories']['output']==sorted(['.','cache','hf_cache','mplconfig','tmp','triton_cache']) and first['directories']['installed']==['.','control'])
metadata=read(F/'metadata_result_v1.json')
for name,row in metadata['files'].items():
    p=D/name;assert p.stat().st_size==row['bytes']==files[name]['bytes'] and sha(p)==row['sha256']==files[name]['sha256']
check('all22_readback_files_match_fresh_hashes',len(metadata['files'])==22)
mapping=read(B/'pending_transport_v2/installation_mapping_v2.json')
for row in mapping['files']:
    local=B/'pending_transport_v2'/row['member'];fresh=D/'installed'/Path(row['target']).name
    assert sha(fresh)==row['sha256']==sha(local) and fresh.stat().st_size==row['bytes']
check('seven_installed_files_match_frozen_transport',len(mapping['files'])==7)
delivery=read(B/'pending_delivery_v2.json');archive=Path(delivery['archive']['path'])
for suffix in ('','.sha256','.bytes','.contents.sha256'):
    p=Path(str(archive)+suffix);r=files['upload/'+p.name];assert sha(p)==r['sha256'] and p.stat().st_size==r['bytes']
check('upload_archive_three_sidecars_unchanged',True)
E=B/'authorized_execution_v2'
for name in ('authorization_v2.json','runtime_v2.json','launch_once_v2.sh'):
    assert (D/'installed/control'/name).read_bytes()==(E/name).read_bytes()
a=read(D/'installed/control/authorization_v2.json');rt=read(D/'installed/control/runtime_v2.json')
check('single_claim_and_one_way_control_bindings',set(a)=={'schema','request_sha256','explicit_user_authorization','user_authorization_text'} and a['request_sha256']==QH and a['explicit_user_authorization'] is True and rt==dict(schema='bcsp-scq-rf-cuda-runtime-v1',request_sha256=QH,authorization_sha256=sha(D/'installed/control/authorization_v2.json')) and read(D/'installed/control/attempt_claim_v2.json')==dict(status='CLAIMED_BEFORE_TMUX',request_sha256=QH))
counts=dict(full_forward=1,full_backward=0,full_loss=0,decoder_forward=0,decoder_backward=0,optimizer_steps=0)
failure=read(D/'output/failure.json')
check('first_error_counts_and_exit1',failure==dict(status='FAILED_STOP_NO_RETRY',error="ValueError('RF fixed private-seed values')",counts=counts) and (D/'output/exit_code.txt').read_text().strip()=='1')
events=[json.loads(line) for line in (D/'output/events.jsonl').read_text().splitlines()]
check('exact_five_event_order_Sref_only',len(events)==5 and [r.get('kind') for r in events]==['NATIVE_OPTIMIZER_CLASSIFICATION_ONLY','ATTEMPT_BEFORE_CALL','COORDINATE_CONSUMERS_BEFORE_ASSERTIONS',None,'PHASE_RESTORATION'] and events[1]['counts']==counts and all(r.get('phase','S_ref_eval1')=='S_ref_eval1' for r in events))
consumer=events[2]
check('Sref_dual_PE_role_checks_all_six_exactly_equal',consumer['call_counts']==dict(query=1,decoder=1,Memory=1,PE=2,rebuild=1,relative=1) and consumer['exact_call_contract'] is True and len(consumer['comparisons'])==6 and all(r['exact_equal'] and r['finite'] and r['max_abs']==0 for r in consumer['comparisons']))
phase=events[3];restored=events[4]
check('Sref_phase_completed_no_loss_and_recorded_full_restore',phase['loss'] is None and phase['gradients'] is None and phase['parameters_unchanged'] is True and phase['actual_Q2_consumers'] is True and phase['RNG_before']==phase['RNG_after'] and all(restored[k] is True for k in ('state_restored','RNG_restored','modes_restored','BN_momenta_restored','gradients_cleared')))
resources=[json.loads(line) for line in (D/'output/resources.jsonl').read_text().splitlines()]
for row in resources:
    v=row['values'];L=q['limits']
    actual=dict(RSS=v['RSS_bytes']<=L['RSS_bytes'],output=v['output_bytes']<=L['output_bytes'],device=v['device_MiB']<=L['device_MiB'],allocated=v['peak_allocated']<=L['torch_peak_bytes'],reserved=v['peak_reserved']<=L['torch_peak_bytes'],wall=v['elapsed_seconds']<=L['wall_seconds'],disk=v['free_disk_bytes']>=L['minimum_free_disk_bytes'])
    assert row['checks']==actual and all(actual.values()) and row['failed_checks']==[]
check('all_recorded_resource_thresholds_independently_recomputed',len(resources)>0)
binary=D/'related/2_rf_initialization_v1.bin';manifest_path=D/'related/3_rf_initialization_manifest_v1.json'
manifest=read(manifest_path);raw=binary.read_bytes()
check('actual_RF_binary_path_size_hash_match_request_and_local_original',files['related/2_rf_initialization_v1.bin']['path']==q['rf_initialization']['path'] and len(raw)==q['rf_initialization']['bytes']==924684 and sha(binary)==q['rf_initialization']['sha256']==sha(M/'initialization_v1.bin')=='a4024fbdb49feb41c609ae1171f04c2cb14ab794fc3663855d81395c6a1ea79e')
check('initialization_manifest_matches_frozen_provenance',manifest_path.read_bytes()==(M/'initialization_manifest_v1.json').read_bytes() and manifest['sha256']==sha(binary) and manifest['byte_order']=='little' and manifest['seed']==2026111402)
offset=0;chunks=[]
for row in manifest['layout']:
    count=math.prod(row['shape']);chunk=raw[offset:offset+count*4];offset+=count*4
    assert len(chunk)==count*4 and hashlib.sha256(chunk).hexdigest()==row['sha256']
    values=[v[0] for v in struct.iter_unpack('<f',chunk)]
    assert all(math.isfinite(v) for v in values)
    if row['name'].startswith('V2.'):assert chunk==bytes(len(chunk))
    chunks.append(dict(name=row['name'],shape=row['shape'],elements=count,bytes=len(chunk),sha256=row['sha256'],all_finite=True,nonzero_elements=sum(v!=0 for v in values),minimum=min(values),maximum=max(values)))
check('all_four_frozen_tensor_blocks_exact_hash_finite_and_zero_output',len(chunks)==4 and offset==len(raw) and sum(r['elements'] for r in chunks)==231171)
residual=D/'related/0_bcsp_scq_rf_residual_v1.py';factory=D/'related/1_bcsp_scq_rf_factory_v1.py'
check('actual_residual_and_factory_exact_request_and_local_source_hashes',sha(residual)==q['implementation']['rf_residual']['sha256']==sha(M/'bcsp_scq_rf_residual_v1.py') and sha(factory)==q['implementation']['rf_factory']['sha256']==sha(M/'bcsp_scq_rf_factory_v1.py'))
tree=ast.parse(residual.read_text(encoding='utf-8'));loader=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='load_initialization')
text=ast.unparse(loader)
check('source_order_bytes_hash_layout_finite_zero_before_seed_regeneration',text.index('RF initialization size')<text.index('RF initialization SHA256')<text.index('RF initialization finite')<text.index('RF zero output')<text.index('expected = initialization_values()')<text.index('RF fixed private-seed values'))
check('constructor_failure_before_RF_state_load_or_forward',"self.load_state_dict(load_initialization(initialization), strict=True)" in residual.read_text(encoding='utf-8') and "model, evidence = install(model, variant, rf_initialization)" in factory.read_text(encoding='utf-8'))
log=(D/'output/launch.log').read_text(encoding='utf-8')
check('log_preserves_first_error_separate_from_shutdown_KeyError',"Original exception was:" in log and "ValueError: RF fixed private-seed values" in log and "KeyError: PosixPath(" in log)
local_cpu=read(M/'cpu_batch_v2/result_v2.json')
check('recorded_generation_CPU_and_execution_version_contract_differ',manifest['torch_version']==local_cpu['torch']=='2.5.1' and q['identity']['torch_version']=='2.4.1+cu118')
findings=dict(status='FROZEN_INITIALIZATION_BYTES_VALID_RUNTIME_REGENERATION_EXACT_ASSERTION_REJECTED',
    binary=rec(binary),actual_server_path=q['rf_initialization']['path'],manifest=rec(manifest_path),blocks=chunks,
    source=rec(residual),recorded_generation_torch=manifest['torch_version'],execution_entry_version_contract=q['identity']['torch_version'],
    facts=['Actual server initialization bytes exactly match the frozen local original and request.',
           'All4 tensor chunk hashes match;231171 FP32 values are finite;V2 weight and bias are bitwise zero.',
           'First error occurs after byte/hash/finite/zero checks at regeneration-and-torch.equal assertion during RF model construction.',
           'S-ref completed its forward and corrected consumer-role checks; neither RF arm entered forward.'],
    interpretation='The loader adds a runtime random-number regeneration requirement beyond authoritative frozen bytes. It rejects an otherwise byte-valid initialization under the current execution environment.',
    unresolved='No regenerated arrays or per-tensor comparison statistics were saved. The affected tensor, magnitude, dtype/device of regenerated values and specific cause (version/platform/default settings/CPU implementation path) cannot be identified without an additional separately scoped computation. This audit did not regenerate anything.',
    shutdown_secondary='Log KeyError occurs during traceback formatting after exact-read file descriptors have been closed; first error remains preserved in failure.json. No code change here.',
    recommendation='Retain the frozen binary as authoritative: preserve exact size/SHA256/layout/FP32/finite/zero-output checks; use seed as provenance rather than regenerating and demanding cross-environment bit equality. Only implement after separate authorization, with targeted artificial loader tests and new P3/request. Do not regenerate/replace frozen initialization or retry v2.',
    seed_generation_calls=0,torch_imports=0,model_imports=0,tests_run=0,new_forward=0)
emit(F/'initialization_byte_contract_findings_v1.json',findings)
summary=dict(status='FORMAL_RF_V2_FAILURE_FREEZE_AUDIT_PASS_CUDA_REMAINS_FAILED',checks=checks,count=len(checks),request_sha256=QH,
    file_count=len(files),unique_hashed_bytes=first['hashed_bytes'],collection_seconds=read(F/'collection_complete_v1.json')['seconds'],
    evidence_manifest=[dict(name=k,**v) for k,v in files.items()],actual_counts=counts,request_consumed=True,reuse_allowed=False,exit_code=1,
    initialization_contract=rec(F/'initialization_byte_contract_findings_v1.json'),
    recorded_resource_peaks=dict(RSS_bytes=max(r['values']['RSS_bytes'] for r in resources),SMI_MiB=max(r['values']['device_MiB'] for r in resources),allocated_bytes=max(r['values']['peak_allocated'] for r in resources),reserved_bytes=max(r['values']['peak_reserved'] for r in resources)),
    restoration_evidence='Saved phase/state/RNG checks only; no independent model reload',server_writes=0,random_regeneration=0,new_forward=0,torch_imports=0,model_imports=0,CUDA_admission=False)
emit(F/'formal_failure_freeze_audit_v1.json',summary)
print(json.dumps(dict(status=summary['status'],checks=len(checks),files=len(files),bytes=first['hashed_bytes'],binary_sha256=sha(binary),peaks=summary['recorded_resource_peaks'])))
