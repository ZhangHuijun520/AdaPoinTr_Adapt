"""Local P3/request/transport freeze only. No server mutation or execution."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import tarfile

B = Path(__file__).resolve().parent
ROOT = B.parents[2]
GPU = B.parent/'lqi_gpu_admission_v1'
AUDIT = GPU/'post_CUDA_freeze_audit_v1'
REMOTE = PurePosixPath('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_lqi_foldD_training_20261111_v1')
OUT = '/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/LQI_foldD_seed0_train_20261111_v1'


def read(p):
    return json.loads(p.read_bytes())


def record(p,target=None):
    b = p.read_bytes()
    return dict(path=str(target or p.resolve()),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())


def emit(name,value):
    with (B/name).open('x',encoding='ascii') as f:
        json.dump(value,f,indent=2,allow_nan=False); f.write('\n')


def main():
    cpu = read(B/'artificial_cpu_batch_v2/result_v1.json')
    assert cpu['status'] == 'ARTIFICIAL_LQI_FOLDD_TRAINING_ENTRY_CPU_PASS' and cpu['check_count'] == 29 and cpu['optimizer_steps'] == cpu['CUDA_calls'] == 0
    static = read(B/'static_review_v1.json')
    entry = B/'bcsp_lqi_foldD_training_entry_v1.py'
    assert record(entry) == static['sources'][0]
    spec = importlib.util.spec_from_file_location('f0_training_freeze',entry)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    old = read(B/'frozen_M0_FoldD_reference_request_v1.json')
    C = B.parent/'lqi_training_entry_v1'
    cq = read(C/'LQI_FoldC_training_execution_request_v1.json')
    cuda = read(GPU/'pending_transport_v1/payload/LQI_artificial_cuda_execution_request_v1.json')
    admission = read(C/'native_LQI_admission_receipt_v1.json')
    assert record(C/'native_LQI_admission_receipt_v1.json')['sha256'] == module.ADMISSION_SHA
    assert record(GPU/'pending_transport_v1/payload/LQI_artificial_cuda_execution_request_v1.json')['sha256'] == module.CUDA_REQUEST_SHA
    observed = read(B/'stat_readiness_stdout_v1.bin'); meta = read(B/'metadata_readonly_stdout_v1.bin')
    assert len(observed['files']) == 315 and observed['new_targets_absent'] and observed['tmux_absent']
    assert observed['hostname'] == cuda['identity']['hostname'] and observed['uid'] == cuda['identity']['uid']
    assert observed['free_disk_bytes'] >= module.RESOURCES['minimum_free_disk_bytes']
    g = [s.strip() for s in observed['gpu'].split(',')]; I = cuda['identity']
    assert g[:4] == [I['gpu_uuid'],I['gpu_name'],I['driver_version'],str(I['nvidia_smi_memory_total_MiB'])] and int(g[4]) <= 256
    assert meta['status'] == 'TRAINING_METADATA_AND_REUSED_HELPERS_HASH_PASS' and len(meta['files']) == 9
    mirror = {}
    # These are byte-exact existing metadata files. They are not real point payloads.
    metadata_local = [ROOT/'outputs/cranial_bcsp_geov1_20261024/first_run_freeze_foldC_8192_v1/static_training_config_v1.json',
        ROOT/'outputs/cranial_bcsp_mamba_p1_20261104/FoldD_pair_preparation_20261106_v1/shared_order_foldD_seed0_v1.json',
        ROOT/'outputs/cranial_bcsp_geov1_20261024/foldD_8192_training_v1/qualified_data_qc_foldD_8192_v1.json',
        ROOT/'outputs/cranial_bcsp_geov1_20261024/real_data_qc_verification_v1.json',
        ROOT/'outputs/cranial_bcsp_geov1_20261024/real_data_qc_v1/manifest_8192.jsonl',
        ROOT/'outputs/cranial_bcsp_geov1_20261024/real_data_qc_v1/manifest_16384.jsonl',
        ROOT/'outputs/cranial_bcsp_geov1_20261024/consolidated_binding_v1/fold_binding.json',
        ROOT/'outputs/cranial_bcsp_geov1_20261024/resource_rebind_implementation_v1/monitor_diagnostic_v3/research_priority_monitor_v4/new_container_training_v1/bcsp_training_contract_01dt08_v3.py',
        ROOT/'outputs/cranial_bcsp_mamba_p1_20261104/training_entry_v1/bcsp_p1_training_entry_v1.py']
    for r,p in zip(meta['files'],metadata_local):
        actual = record(p)
        assert (actual['bytes'],actual['sha256']) == (r['bytes'],r['sha256']),str(p)
        mirror[r['path']] = p
    mapping = []
    def transport(local,name=None):
        remote = record(local,REMOTE/(name or local.name))
        mapping.append(dict(local=record(local),remote=remote,overwrite=False))
        mirror[remote['path']] = local
        return remote
    entry_record = transport(entry)
    bridge = cq['implementation']['bridge']
    proof = {}
    for key,p in [('receipt',C/'native_LQI_admission_receipt_v1.json'),('audit',AUDIT/'formal_post_CUDA_freeze_audit_result_v1.json'),
                  ('construction',AUDIT/'downloads/output/construction.json'),('completion',AUDIT/'downloads/output/completion.json'),
                  ('request',GPU/'pending_transport_v1/payload/LQI_artificial_cuda_execution_request_v1.json')]:
        proof[key] = transport(p)
    FC = C/'post_training_freeze_audit_v1'
    prior_C = {}
    for key,local,name in [('audit',FC/'post_training_freeze_audit_result_v1.json',None),
        ('request',FC/'downloaded/installed/LQI_FoldC_training_execution_request_v1.json',None),
        ('construction',FC/'downloaded/output/model_construction.json',None),
        ('initialization',FC/'downloaded/output/initialization.json',None),('order',FC/'downloaded/output/order_plan.json',None),
        ('completion',FC/'downloaded/output/completion.json','FoldC_completion.json')]:
        prior_C[key] = transport(local,name)
    D_reference = transport(B/'frozen_M0_FoldD_reference_request_v1.json')
    impl = dict(cuda['implementation'])
    impl.update(entry=entry_record,bridge=bridge,runtime=cq['implementation']['runtime'],contract=cq['implementation']['contract'],
                budget_parent=cq['implementation']['budget_parent'],preflight_helper=cuda['helper'],timezone=cuda['timezone_implementation'])
    for k,h in module.PINS.items():
        assert impl[k]['sha256'] == h,k
    readiness = dict(status='LQI_FOLDD_METADATA_RESOURCE_READINESS_PASS',date='2026-11-10',identity=I,
                    metadata=meta['files'],train_files_stat=observed['files'],train_case_count=315,
                    payload_arrays_read=0,payload_bytes_rehashed_this_preparation=False,
                    bytes_hashes_from_frozen_QC_only=True,preexecution315payload_sha256_check_required=True,
                    new_paths_absent=True,tmux_absent=True,free_disk_bytes=observed['free_disk_bytes'],physical_gpu_observed=observed['gpu'],
                    recheck_identity_assets_and_resources_before_execution=True)
    emit('FoldD_readiness_receipt_v1.json',readiness)
    ready_record = transport(B/'FoldD_readiness_receipt_v1.json')
    pair = dict(status='FROZEN_LQI_CD_TRAINING_CONTRACT_NOT_AUTHORIZATION',seed=0,arm_order=['C','D'],counts=module.COUNTS,
                drop_events_per_run=300,total_updates_two_runs=7800,resources=module.RESOURCES,
                static_config=old['static_config'],FoldC_QC=cq['QC'],FoldC_order_plan=cq['order_plan'],FoldD_QC=old['QC'],FoldD_order_plan=old['order_plan'],FoldC_audit_sha256=module.FOLDC_AUDIT_SHA,
                native_admission_sha256=module.ADMISSION_SHA,scientific_configuration_unchanged=True,
                initialize_from='scratch via M0 common constructor; private encoder20261104/decoder20261110 seeds',
                previous_T0_M0_reference='reuse frozen predictions and existing matching fold order; no retraining/warmstart',
                repeat_GPU_preflight=False,foldD_requires_separate_request=True,FoldC_completed_and_formally_frozen=True)
    emit('LQI_CD_training_contract_v1.json',pair)
    pair_record = transport(B/'LQI_CD_training_contract_v1.json')
    model_pins = read(B.parent/'implementation_v1/implementation_P3_v1.json')
    for r in model_pins['new_code_files']+model_pins['parent_files_reverified_unchanged']:
        now = record(Path(r['path'])); assert (now['bytes'],now['sha256']) == (r['bytes'],r['sha256'])
    p3 = dict(status='LQI_TRAINING_ENTRY_CPU_P3_PASS',date='2026-11-10',entry_sha256=entry_record['sha256'],
             native_admission_sha256=module.ADMISSION_SHA,CPU_checks_passed=29,
             entry=record(entry),test=record(B/'test_lqi_foldD_training_entry_cpu_v2.py'),
             CPU_result=record(B/'artificial_cpu_batch_v2/result_v1.json'),static_review=record(B/'static_review_v1.json'),
             FoldC_audit_sha256=module.FOLDC_AUDIT_SHA,FoldD_reference_sha256=module.FOLDD_REFERENCE_SHA,
             original_model_loss_runtime_and_FoldC_entry_unchanged=True,one_new_production_entry=True,
             diff=record(B/'FoldC_to_FoldD_entry_diff_v1.patch'),
             coverage=['actual complete authorize path with pinned native/Cfold/historicalD proofs and real metadata only',
                       'F0 surrogate factory8k batch8 artificialF/B and bridge/runtime spies,0optimizerstep',
                       'wrong C audit/init, wrong D reference/order, noauth, hash/count/path guards'],
             limits=['no real point payload arrays; real metadata identities are not synthetic point tensors',
                     'CPU front/loss/mixers/runtime spies validate control and signature, not3900step training',
                     'native CUDA admission reused, no new preflight',
                     '315 real train files stat-only; full payload SHA recheck deferred to explicit execution'],
             server_writes=0,GPU_calls=0,optimizer_steps=0,training_request_execution_authorized=False)
    emit('training_entry_P3_v1.json',p3)
    p3_record = transport(B/'training_entry_P3_v1.json')
    control = REMOTE/'control'
    q = dict(schema='bcsp-lqi-training-request-v1',status='AWAITING_EXPLICIT_USER_AUTHORIZATION',stage='CRANIAL_BCSP_FULLMAMBA',
        run_id='LQI_foldD_seed0_train_20261111_v1',variant='F0-LQI-v1',fold='D',seed=0,n_input=8192,n_output=8192,
        static_config=old['static_config'],QC=old['QC'],order_plan=old['order_plan'],identity=I,data_root=old['data_root'],
        model_root=cuda['model_root'],implementation=impl,preflight_scope=cuda['preflight_scope'],dependencies=cuda['dependencies'],
        environment=cuda['environment'],output=OUT,launch_attempt=str(control/'launch_attempt_v1.json'),
        launch_contract=dict(tmux_session='bcsp_lqi_foldD_train_20261111_v1',request_path=str(REMOTE/'LQI_FoldD_training_execution_request_v1.json'),
            authorization_path=str(control/'authorization_v1.json'),runtime_path=str(control/'runtime_v1.json'),launcher_path=str(control/'launch_once_v1.sh'),
            log=OUT+'/launch.log',PID=OUT+'/worker.pid',exit_code=OUT+'/exit_code.txt',
            materialization_order='authorization -> SHA -> one-way runtime -> launcher -> exclusive claim -> unique tmux',
            render_function='bound entry.render_launcher',parent_before_redirection=True,PowerShell_explicit_exit_LASTEXITCODE=True,
            original_file_byte_transport=True,automatic_retry=False,resume=False,PID_policy='DIAGNOSTIC_ONLY_NO_OWNERSHIP_GUARANTEE'),
        admission=proof,readiness=ready_record,pair_contract=pair_record,P3=p3_record,FoldC_pairing=prior_C,FoldD_reference=D_reference,
        not_authorized=['Execution before separate full requestSHA authorization','overwrite installation/results',
                        'checkpoint warmstart/resume/retry','BNCal/development evaluation/FoldC rerun',
                        'AMP, loss/model/sampling/count/resource changes','download/build/upgrade or repeat GPU preflight',
                        'confirmation20/unopened cases/data outside fixed315train allowlist'])
    # Read-only semantic review of the final proof chain/metadata, without synthetic or real execution authorization materialization.
    old_exact = module.exact
    def mirrored_exact(r):
        return old_exact(dict(r,path=str(mirror[r['path']].resolve()))) if r['path'] in mirror else old_exact(r)
    module.exact = mirrored_exact
    assert q['fold'] == 'D' and q['variant'] == 'F0-LQI-v1' and q['seed'] == 0
    _, expected_factory = module.validate_admission(q)
    module.validate_FoldC_and_reference(q,expected_factory)
    spec = importlib.util.spec_from_file_location('local_F0_metadata_review',metadata_local[-2]); metadata = importlib.util.module_from_spec(spec);spec.loader.exec_module(metadata)
    original_exact = metadata.exact
    metadata.exact = lambda r: original_exact(dict(r,path=str(mirror[r['path']].resolve())))
    selected,fold = metadata.verify_qualified_receipt(json.loads(mirror[q['QC']['qualified_receipt']['path']].read_bytes()),
        q['QC']['verification'],q['QC']['manifests'],q['QC']['fold_binding'],'D',8192)
    plan = metadata.validate_order(json.loads(mirror[q['order_plan']['path']].read_bytes()),fold['train_case_ids'])
    assert {r['case_id'] for r in selected} == {r['case_id'] for r in observed['files']}
    assert metadata.validate_static(json.loads(mirror[q['static_config']['path']].read_bytes()))['resources'] == module.RESOURCES
    launcher = module.render_launcher(q,'a'*64,'b'*64,'c'*64)
    assert '\\' not in launcher.replace('\\n','') and max(map(len,launcher.splitlines())) <= 2048
    emit('LQI_FoldD_training_execution_request_v1.json',q)
    request_record = transport(B/'LQI_FoldD_training_execution_request_v1.json')
    emit('final_request_review_v1.json',dict(status='FINAL_PENDING_REQUEST_REVIEW_PASS_NOT_EXECUTED',request=request_record,
         native_admission_sha256=module.ADMISSION_SHA,QC_order_counts_validated=True,case_count=315,source_count=63,
         updates=3900,CPU_checks=29,controls_materialized=False,GPU_calls=0,training_started=False))
    emit('frozen_transport_installation_mapping_v1.json',dict(status='FROZEN_NOT_UPLOADED_NOT_DEPLOYED',request_sha256=request_record['sha256'],
         files=mapping,policy='revalidate archive/identity/all targets and safe parents; exclusive no-overwrite install',
         unchanged_implementations_reused=impl))
    archive = B/'bcsp_lqi_FoldD_training_pending_20261111_v1.tar.gz'
    with archive.open('xb') as stream:
        with tarfile.open(fileobj=stream,mode='w:gz') as tar:
            for row in mapping:
                tar.add(row['local']['path'],arcname=PurePosixPath(row['remote']['path']).name,recursive=False)
    with tarfile.open(archive,'r:gz') as tar:
        assert len(tar.getmembers()) == len(mapping) == 17
        for row in mapping:
            data = tar.extractfile(PurePosixPath(row['remote']['path']).name).read()
            assert len(data) == row['remote']['bytes'] and hashlib.sha256(data).hexdigest() == row['remote']['sha256']
    for suffix,text in [('.sha256',record(archive)['sha256']+'  '+archive.name+'\n'),('.bytes',str(archive.stat().st_size)+'\n'),
                        ('.contents.sha256',''.join(r['remote']['sha256']+'  '+PurePosixPath(r['remote']['path']).name+'\n' for r in mapping))]:
        with Path(str(archive)+suffix).open('x',encoding='ascii') as f:
            f.write(text)
    emit('delivery_receipt_v1.json',dict(status='PENDING_REQUEST_AND17FILE_TRANSPORT_COMPLETE_NOT_EXECUTED',
         request=request_record,archive=record(archive),sidecars=[record(Path(str(archive)+s)) for s in ['.sha256','.bytes','.contents.sha256']],
         file_count=17,CPU_checks=29,server_writes=0,GPU_calls=0,training_started=False))
    print(json.dumps(dict(status=q['status'],request=request_record,archive=record(archive),CPU_checks=29,files=17),indent=2))


if __name__ == '__main__':
    main()
