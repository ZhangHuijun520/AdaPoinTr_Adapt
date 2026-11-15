"""Stdlib-only post-training audit. No torch import, checkpoint load or forward."""
from collections import Counter
import hashlib
import json
import math
from pathlib import Path, PurePosixPath

D = Path(__file__).resolve().parent
B = D.parent
ROOT = D.parents[3]
O = D/'downloaded/output'
I = D/'downloaded/installed'
QH = 'ea45165142676c16b0c18e5616494ee78e1231970590ce4b314bf4c479bcd8b0'
CHECKS = {}


def read(p):
    return json.loads(p.read_bytes())


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def record(p):
    return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=sha(p))


def check(name, value):
    CHECKS[name] = bool(value)
    if not value:
        raise AssertionError(name)


def lines(p):
    return [json.loads(s) for s in p.read_text(encoding='utf-8').splitlines()]


def canonical(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def emit(name,value):
    with (D/name).open('x',encoding='ascii') as f:
        json.dump(value,f,indent=2,allow_nan=False);f.write('\n')


def main():
    before = read(D/'inventory_before_stdout.bin'); after = read(D/'inventory_after_stdout.bin')
    check('current_hostname_UID',before['hostname'] == after['hostname'] == 'shu-common-25721452-notebook-n8xph5-0' and before['uid'] == after['uid'] == 1000)
    check('worker_and_tmux_not_live',all(not a['tmux_present'] and not a['worker_PID_exists'] for a in (before,after)))
    check('40files_stable_hash_content_fingerprints_no_atime',before['rows'] == after['rows'] and len(before['rows']) == 40)
    check('exact_tmp_control_directories_only',before['dirs'] == after['dirs'] == [dict(role=0,name='tmp'),dict(role=1,name='control')])
    check('bounded2GiB_inventory_no_checkpoint_deserialize',before['bytes'] <= 2*1024**3 and not before['checkpoint_deserialized'] and not after['checkpoint_deserialized'])
    collection = read(D/'collection_receipt_v1.json')
    check('39noncheckpoint_files_download_hash_match',len(collection['files']) == 39 and all(Path(r['local']).stat().st_size == r['bytes'] and sha(Path(r['local'])) == r['sha256'] for r in collection['files']))
    check('checkpoint_not_downloaded',not (O/'ckpt-last.pth').exists())
    rows = {(r['role'],r['name']):r for r in before['rows']}
    expected = {'F0_geometry.jsonl','ckpt-last.pth','completion.json','exit_code.txt','exposure.json','initialization.json','launch.log',
                'metrics.jsonl','model_construction.json','optimizer_actual_defaults.json','optimizer_parameter_groups.json','order_plan.json',
                'payload_manifest.json','resources.jsonl','run_identity.json','worker.pid'}
    check('exact16output_files_no_failure',set(n for role,n in rows if role == 0) == expected)
    checkpoint = rows[(0,'ckpt-last.pth')]
    check('exit_code0',(O/'exit_code.txt').read_text().strip() == '0')
    qfile = I/'F0_FoldD_training_execution_request_v1.json'; q = read(qfile)
    check('exact_authorized_request',sha(qfile) == sha(B/qfile.name) == QH and q['fold'] == 'D' and q['variant'] == 'F0-P-v2')
    mapping = read(B/'frozen_transport_installation_mapping_v1.json')['files']
    check('18installed_files_frozen_mapping',{n for role,n in rows if role == 1 and '/' not in n} == {Path(r['remote']['path']).name for r in mapping}
          and all(sha(I/Path(r['remote']['path']).name) == r['remote']['sha256'] for r in mapping))
    controls = {'authorization_v1.json','runtime_v1.json','launch_once_v1.sh','launch_attempt_v1.json','readiness_and_installation_receipt_v1.json','startup_receipt_v1.json'}
    check('exact6controls',{n[8:] for role,n in rows if role == 1 and n.startswith('control/')} == controls)
    C = I/'control'; auth = read(C/'authorization_v1.json'); runtime = read(C/'runtime_v1.json')
    check('explicit_authorization_no_reverse_binding',set(auth) == {'schema','request_sha256','explicit_user_authorization','user_authorization_text'}
          and auth['schema'] == 'bcsp-f0-training-authorization-v1' and auth['request_sha256'] == QH and auth['explicit_user_authorization'] is True)
    check('one_way_runtime',runtime == dict(schema='bcsp-f0-training-runtime-v1',request_sha256=QH,authorization_sha256=sha(C/'authorization_v1.json')))
    check('single_attempt_claim',read(C/'launch_attempt_v1.json') == dict(status='CLAIMED_BEFORE_TMUX',request_sha256=QH))
    env = dict(__name__='read_only_launcher_review',__file__=str(I/'bcsp_f0_foldD_training_entry_v1.py'))
    exec(compile((I/'bcsp_f0_foldD_training_entry_v1.py').read_bytes(),'<bound_renderer_only>','exec'),env)
    launch = env['render_launcher'](q,QH,sha(C/'authorization_v1.json'),sha(C/'runtime_v1.json'))
    check('exact_launcher_rendered_bytes',(C/'launch_once_v1.sh').read_bytes() == launch.encode())
    rehash = read(D/'rehash_assets_stdout_v1.bin')
    check('77fixed_nonpayload_assets_rehashed',rehash['status'] == 'POST_RUN_PINNED_ASSETS_REHASH_PASS' and rehash['records'] == 77)
    completed = read(O/'completion.json'); initialization = read(O/'initialization.json')
    exact_counts = dict(forward=3900,backward=3900,clip=3900,step=3900,lr_scheduler=100,bn_scheduler=100)
    check('completion_3900updates100traversals31200exposures',completed['counts'] == exact_counts and completed['optimizer_updates'] == 3900
          and completed['traversals'] == 100 and completed['case_exposures'] == 31200)
    check('checkpoint_fresh_SHA_matches_completion',checkpoint['sha256'] == completed['checkpoint_sha256'] and checkpoint['bytes'] > 0)
    check('BNCal_evaluation_resume_false',completed['bncal_executed'] is False and completed['evaluation_executed'] is False and completed['resume'] is False)
    manifest = read(O/'payload_manifest.json')['files']
    check('12payload_manifest_records_exact',len(manifest) == 12 and {r['name'] for r in manifest} == expected-{'payload_manifest.json','exit_code.txt','worker.pid','launch.log'}
          and all(rows[(0,r['name'])]['sha256'] == r['sha256'] and rows[(0,r['name'])]['bytes'] == r['bytes'] for r in manifest))
    frozen_order = ROOT/'outputs/cranial_bcsp_mamba_p1_20261104/FoldD_pair_preparation_20261106_v1/shared_order_foldD_seed0_v1.json'
    plan = read(O/'order_plan.json')
    check('same_raw_frozen_FoldD_order',sha(O/'order_plan.json') == sha(frozen_order) == q['order_plan']['sha256'])
    order_sha = canonical(plan)
    check('canonical_order_initialization_completion',order_sha == initialization['order_sha256'] == completed['order_sha256'])
    metadata_root = ROOT/'outputs/cranial_bcsp_geov1_20261024'
    mf = metadata_root/'real_data_qc_v1/manifest_8192.jsonl'; fb = metadata_root/'consolidated_binding_v1/fold_binding.json'
    check('frozen_manifest_fold_metadata',sha(mf) == q['QC']['manifests']['8192']['sha256'] and sha(fb) == q['QC']['fold_binding']['sha256'])
    source_by_id = {r['case_id']:r['source_id'] for r in lines(mf)}; fold = read(fb)['folds']['D']
    check('315cases63sources21dev_disjoint',plan['case_ids'] == fold['train_case_ids'] and len(set(plan['case_ids'])) == 315
          and len(fold['train_sources']) == 63 and len(fold['dev_sources']) == 21 and not set(fold['train_sources']) & set(fold['dev_sources']))
    metrics = lines(O/'metrics.jsonl'); geometry = lines(O/'F0_geometry.jsonl')
    check('3900metrics_and3900geometry',len(metrics) == len(geometry) == 3900)
    case_counts = Counter(); source_counts = Counter(); drops = Counter()
    for epoch, spec in enumerate(plan['epochs']):
        assert spec['epoch'] == epoch and len(spec['batches']) == 39 and len(spec['dropped']) == 3
        flat = sum(spec['batches'],[]) + spec['dropped']
        assert len(flat) == len(set(flat)) == 315 and set(flat) == set(plan['case_ids'])
        drops.update(spec['dropped'])
    for index,(row,geo) in enumerate(zip(metrics,geometry)):
        epoch,batch = divmod(index,39); step = index+1; ids = plan['epochs'][epoch]['batches'][batch]
        assert (row['step'],row['epoch'],row['batch']) == (step,epoch,batch)
        assert row['case_ids'] == ids and row['source_ids'] == [source_by_id[c] for c in ids]
        assert all(source_by_id[c] in fold['train_sources'] for c in ids) and row['optimizer_step_committed'] is True
        assert all(math.isfinite(row[k]) for k in ['loss_sparse','loss_dense','loss_denoise','loss_reconstruction','loss','grad_norm_before_clip'])
        assert row['loss_sparse'] == row['loss_denoise'] == 0 and row['loss_dense'] == row['loss_reconstruction'] == row['loss']
        assert row['clip_max_norm'] == 10 and row['grad_norm_before_clip'] >= 0
        lr = .0001*max(.9**(epoch/21),.02); momentum = max(.9*.5**(epoch/21),.01)
        assert len(row['LR']) == 2 and all(math.isclose(v,lr,rel_tol=1e-12) for v in row['LR'])
        assert math.isclose(row['BN_momentum'],momentum,rel_tol=1e-12)
        assert (geo['step'],geo['epoch'],geo['batch']) == (step,epoch,batch) and geo['case_ids'] == ids
        assert geo['coordinate_frame'] == 'D-only normalized, not world mm' and set(geo['geometry']) == {'coarse','dense'}
        for part in geo['geometry'].values():
            assert set(part) == {'centroid','radius','minimum','maximum'} and all(len(part[k]) == 8 for k in part)
            for center,radius,lo,hi in zip(part['centroid'],part['radius'],part['minimum'],part['maximum']):
                assert len(center) == len(lo) == len(hi) == 3
                assert all(math.isfinite(v) for v in center+lo+hi+[radius]) and radius >= 0
                tol = 1e-5*(1+max(map(abs,center+lo+hi)))
                assert all(a <= b and a-tol <= c <= b+tol for a,b,c in zip(lo,hi,center))
        case_counts.update(ids); source_counts.update(row['source_ids'])
    check('all_actual_batches_sources_LR_BN_clip_loss_verified',True)
    check('all_geometry_rows_finite_shapes_step_case_aligned',True)
    exposure = read(O/'exposure.json')
    check('exposure_recomputed_not_completion_only',dict(case_counts) == exposure['case'] and dict(source_counts) == exposure['source']
          and dict(drops) == exposure['dropped_case'] and exposure['order_sha256'] == order_sha)
    check('31200exposures300drops100percase',sum(case_counts.values()) == sum(source_counts.values()) == 31200 and sum(drops.values()) == 300
          and all(case_counts[c]+drops[c] == 100 for c in plan['case_ids']))
    install = read(C/'readiness_and_installation_receipt_v1.json')
    payload_hashes = [r for r in install['read_manifest'] if r['path'].endswith('.npz')]
    manifest_by_id = {r['case_id']:r for r in lines(mf)}
    expected_payloads = {(str(PurePosixPath(q['data_root'])/manifest_by_id[c]['point_path']),manifest_by_id[c]['sha256']) for c in plan['case_ids']}
    check('315preexecution_train_hashes_bound_no_dev_payload',len(payload_hashes) == 315
          and {(r['path'],r['sha256']) for r in payload_hashes} == expected_payloads and install['payload_arrays_read'] == 0)
    model = read(O/'model_construction.json'); original_model = read(I/'construction.json')
    check('exact_factory_initialization_matches_native_admission',model['factory'] == original_model['factory']
          and model['factory']['artificial_fixture'] is False and model['factory']['common_initialization_preserved'])
    gpu_events_file = B.parent/'gpu_admission_v1/post_CUDA_freeze_audit_v1/downloaded/output/events.jsonl'
    gpu_audit = read(I/'post_CUDA_freeze_audit_result_v2.json')
    audited_events = next(r for r in gpu_audit['artifacts'] if r['role'] == 0 and r['name'] == 'events.jsonl')
    check('GPU_reference_events_hash_authentic',sha(gpu_events_file) == audited_events['sha256'])
    eval_state = next(e['state_sha256'] for e in lines(gpu_events_file) if e.get('phase') == 'eval_1')
    check('complete_initial_state_fingerprint_matches_GPU_admission',initialization['persistent_state_sha256'] == eval_state and initialization['seed'] == 0)
    identity = read(O/'run_identity.json')
    check('F0_stage_D_seed0_numeric_disclosure',identity['stage'] == q['stage'] and identity['variant'] == 'F0-P-v2' and identity['fold'] == 'D'
          and identity['seed'] == 0 and identity['SSM_gradient_non_bitwise_reproducibility_disclosed']
          and identity['native_admission_sha256'] == q['admission']['receipt']['sha256'])
    groups = read(O/'optimizer_parameter_groups.json'); defaults = read(O/'optimizer_actual_defaults.json')
    check('411_unique_parameter_records',len(groups) == len({r['name'] for r in groups}) == 411)
    computed = dict(total=0,encoder=0,decoder=0,other=0)
    for r in groups:
        count = math.prod(r['shape']); computed['total'] += count
        part = 'encoder' if r['name'].startswith('base_model.encoder.') else 'decoder' if r['name'].startswith('base_model.decoder.') else 'other'
        computed[part] += count
        desired = 0 if r['name'].endswith(('.A_log','.D','.bias')) or len(r['shape']) == 1 else .0005
        assert r['weight_decay'] == desired
    check('actual_parameter_counts_and_effective_weight_decay',computed == model['parameters'] and computed['total'] == 39903169)
    check('22Alog_22D_no_decay',all(len([r for r in groups if r['name'].endswith(suffix) and r['weight_decay'] == 0]) == 22 for suffix in ['.A_log','.D']))
    check('AdamW_defaults_without_confusing_default_decay',defaults['lr'] == .0001 and defaults['betas'] == [.9,.999] and defaults['eps'] == 1e-8
          and not defaults['amsgrad'] and not defaults['maximize'] and defaults['foreach'] is None and defaults['fused'] is None)
    resource = lines(O/'resources.jsonl'); limits = read(B/'F0_FoldD_training_execution_request_v1.json')['pair_contract']
    L = read(I/'F0_CD_training_contract_v1.json')['resources']; previous = -1
    check('3902resource_record_count',len(resource) == 3902)
    for index,r in enumerate(resource):
        assert r['limits'] == L and math.isfinite(r['elapsed_seconds']) and previous <= r['elapsed_seconds'] <= L['wall_seconds']
        previous = r['elapsed_seconds']
        expected_phase,step = ('after_step',index+1) if index < 3900 else ('before_final' if index == 3900 else 'after_final',3900)
        assert r['phase'] == expected_phase and r['committed_step'] == step
        expected_checks = dict(allocated_within_limit=r['peak_allocated'] <= L['torch_peak_bytes'],
                              reserved_within_limit=r['peak_reserved'] <= L['torch_peak_bytes'],device_within_limit=r['device_MiB'] <= L['device_MiB'])
        assert r['checks'] == expected_checks and all(expected_checks.values()) and r['resource_guard_passed'] and r['failed_checks'] == []
        assert r['RSS'] <= L['RSS_bytes'] and r['output_bytes'] <= L['output_bytes']
        assert r['PID_policy'] == 'DIAGNOSTIC_ONLY_NO_OWNERSHIP_GUARANTEE'
    check('all3902_resource_values_phases_recomputed',True)
    check('final_output_bytes_within_budget',sum(r['bytes'] for r in before['rows'] if r['role'] == 0) <= L['output_bytes'])
    peaks = {k:max(r[k] for r in resource) for k in ['RSS','peak_allocated','peak_reserved','device_MiB','elapsed_seconds']}
    FC = B.parent/'training_entry_v1/post_training_freeze_audit_v1'
    ca_file = FC/'post_training_freeze_audit_result_v1.json'; ca = read(ca_file)
    check('FoldC_formal_audit_exact_bound_anchor',sha(ca_file) == q['FoldC_pairing']['audit']['sha256'] == sha(I/'post_training_freeze_audit_result_v1.json')
          and ca['status'] == 'FORMAL_F0_FOLDC_POST_TRAINING_FREEZE_AUDIT_PASS' and all(ca['checks'].values())
          and ca['checks_passed'] == len(ca['checks']))
    for key,ref in q['FoldC_pairing'].items():
        local = I/PurePosixPath(ref['path']).name
        assert local.stat().st_size == ref['bytes'] and sha(local) == ref['sha256']
    check('all_six_FoldC_pairing_copies_hash_match',True)
    fresh_C = read(D/'counterpart_stdout_v1.bin')
    ca_rows = {r['name']:r for r in ca['artifacts'] if r['role'] == 0}
    check('live_FoldC_checkpoint_and_six_metadata_still_frozen',fresh_C['status'] == 'FROZEN_FOLDC_COUNTERPART_REHASH_PASS'
          and len(fresh_C['files']) == 7 and not fresh_C['checkpoint_deserialized']
          and all((r['bytes'],r['sha256']) == (ca_rows[PurePosixPath(r['path']).name]['bytes'],ca_rows[PurePosixPath(r['path']).name]['sha256']) for r in fresh_C['files']))
    ci = read(FC/'downloaded/output/initialization.json'); cm = read(FC/'downloaded/output/model_construction.json')
    cq = read(FC/'downloaded/installed/F0_FoldC_training_execution_request_v1.json'); cc = read(FC/'downloaded/output/completion.json')
    check('C_D_same_complete_initial_parameters_and_state',initialization['parameter_sha256'] == ci['parameter_sha256']
          and initialization['persistent_state_sha256'] == ci['persistent_state_sha256'] and initialization['seed'] == ci['seed'] == 0)
    check('C_D_same_actual_factory_and_parameter_counts',model == cm)
    for n in ['optimizer_actual_defaults.json','optimizer_parameter_groups.json']:
        ref = next(r for r in fresh_C['files'] if PurePosixPath(r['path']).name == n)
        assert sha(FC/'downloaded/output'/n) == ref['sha256'] and read(O/n) == read(FC/'downloaded/output'/n)
    check('C_D_same_actual_optimizer_defaults_and_groups',True)
    common_fields = ['variant','seed','n_input','n_output','static_config','identity','model_root','preflight_scope','dependencies','environment']
    check('C_D_same_scientific_numeric_and_device_contract',all(q[k] == cq[k] for k in common_fields))
    check('C_D_same_unmodified_model_and_runtime_implementations',all(q['implementation'][k] == cq['implementation'][k]
          for k in q['implementation'] if k not in ('entry','bridge'))
          and q['implementation']['bridge']['sha256'] == cq['implementation']['bridge']['sha256'])
    reference = read(I/'frozen_M0_FoldD_reference_request_v1.json')
    check('D_uses_exact_frozen_M0_D_QC_data_and_order',sha(I/'frozen_M0_FoldD_reference_request_v1.json') == q['FoldD_reference']['sha256']
          and all(q[k] == reference[k] for k in ['static_config','QC','order_plan','data_root','model_root','preflight_scope']))
    check('fold_specific_orders_each_match_own_reference_not_required_equal',q['fold'] == 'D' and cq['fold'] == 'C'
          and q['order_plan']['sha256'] != cq['order_plan']['sha256']
          and sha(FC/'downloaded/output/order_plan.json') == cq['order_plan']['sha256'])
    check('both_folds3900_completed_no_BNCal_eval_resume',cc['counts'] == completed['counts'] == exact_counts
          and ca['counts'] == dict(updates=3900,traversals=100,case_exposures=31200,drop_events=300,metric_records=3900,geometry_records=3900,resource_records=3902)
          and all(cc[k] is False and completed[k] is False for k in ['bncal_executed','evaluation_executed','resume']))
    pairing = dict(status='FORMAL_F0_CD_TRAINING_PAIR_CONTRACT_PASS',FoldC_audit=record(ca_file),
        FoldC_checkpoint=ca['checkpoint'],FoldD_checkpoint=checkpoint,
        common_parameter_sha256=initialization['parameter_sha256'],common_initial_state_sha256=initialization['persistent_state_sha256'],
        FoldC_order=cq['order_plan']['sha256'],FoldD_order=q['order_plan']['sha256'],
        updates_per_fold=3900,total_updates=7800,forward_or_weight_load_performed=False,
        note='same scratch model/optimizer contract; different prespecified folds and respective M0 orders, not independent seed repeats')
    audit = dict(status='FORMAL_F0_FOLDD_POST_TRAINING_FREEZE_AUDIT_PASS',date='2026-11-11',request_sha256=QH,
                 checks=CHECKS,checks_passed=len(CHECKS),checkpoint=checkpoint,initialization=initialization,
                 initialization_matches_GPU_admission=True,actual_order_canonical_sha256=order_sha,
                 counts=dict(updates=3900,traversals=100,case_exposures=31200,drop_events=300,metric_records=3900,geometry_records=3900,resource_records=3902),
                 parameters=computed,peaks=peaks,completion=completed,artifacts=before['rows'],C_D_pairing=pairing,
                 operations=dict(server_writes=0,new_forward=0,new_backward=0,checkpoint_deserialized=False,checkpoint_downloaded=False,
                                 training_restarted=False,BNCal=False,evaluation=False),
                 limitations=['Raw checkpoint bytes hashed twice; no internal tensor/optimizer deserialization',
                              'RNG/state equality refers to initial replay, not trained-gradient bitwise repeatability',
                              'Known attention-free module/source admission inherited; no new full-training opaque-kernel inspection',
                              'RSS/SMI are sampled; PID ownership is not asserted; minimum disk enforced by pinned local guard without per-row free-disk telemetry',
                              'No development accuracy or scientific benefit conclusion from training loss'])
    emit('post_training_freeze_audit_result_v1.json',audit)
    emit('C_D_pairing_freeze_receipt_v1.json',pairing)
    print(json.dumps(dict(status=audit['status'],checks=len(CHECKS),checkpoint=checkpoint,counts=audit['counts'],peaks=peaks),indent=2))


if __name__ == '__main__':
    try:
        main()
    except BaseException as exc:
        emit('audit_failure_v1.json',dict(status='AUDIT_FAILED_STOP_NO_RETRY',checks=CHECKS,error=repr(exc)))
        raise
