"""Independent stdlib-only freeze audit of captured files. No imports of model/CUDA."""
import hashlib
import json
import math
from pathlib import Path

D = Path(__file__).resolve().parent
B = D.parent
OUT = D/'downloaded/output'
INST = D/'downloaded/installed'
QH = 'a9fbc819da73415008ac5643f5b6cea9ab1b3818029129e6f93e2e67bcc23efc'
CHECKS = {}


def read(p):
    return json.loads(p.read_bytes())


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def record(p):
    return dict(path=str(p.resolve()), bytes=p.stat().st_size, sha256=digest(p))


def check(name, condition):
    CHECKS[name] = bool(condition)
    if not condition:
        raise AssertionError(name)


def write(name, value):
    with (D/name).open('x', encoding='ascii') as f:
        json.dump(value, f, indent=2, allow_nan=False); f.write('\n')


def lines(p):
    return [json.loads(s) for s in p.read_text(encoding='utf-8').splitlines()]


def main():
    before = read(D/'inventory_before_stdout.bin'); after = read(D/'inventory_after_stdout.bin')
    check('same_current_hostname_uid', before['hostname'] == after['hostname'] == 'shu-common-25721452-notebook-n8xph5-0'
          and before['uid'] == after['uid'] == 1000)
    check('tmux_and_worker_absent_before_and_after', all(not x['tmux_present'] and not x['worker_PID_exists'] for x in (before, after)))
    check('stable23file_content_fingerprints_excluding_atime', before['rows'] == after['rows'] and len(before['rows']) == 23)
    check('stable_exact_directories', before['dirs'] == after['dirs'] and before['dirs'] ==
          [dict(role=0, name=n) for n in ['cache','hf_cache','mplconfig','tmp','triton_cache']] + [dict(role=1, name='control')])
    collection = read(D/'collection_receipt_v1.json')
    check('collection_23_exact_hashes', collection['status'] == 'ALL23_EXACT_ARTIFACTS_DOWNLOADED_AND_HASH_MATCH'
          and len(collection['files']) == 23 and all(Path(r['local']).stat().st_size == r['bytes'] and
          digest(Path(r['local'])) == r['sha256'] for r in collection['files']))
    check('bounded_collection_16MiB_128files', before['bytes'] == sum(r['bytes'] for r in before['rows']) <= 16*1024**2)
    qfile = INST/'F0_artificial_cuda_execution_request_v1.json'; q = read(qfile)
    check('authorized_request_identity', digest(qfile) == QH == digest(B/qfile.name))
    mapping = read(B/'frozen_transport_installation_mapping_v1.json')['files']
    root_files = {r['name'] for r in before['rows'] if r['role'] == 1 and '/' not in r['name']}
    check('eight_installed_files_exact_frozen_mapping', root_files == {Path(r['remote']['path']).name for r in mapping}
          and all(digest(INST/Path(r['remote']['path']).name) == r['remote']['sha256'] and
                  (INST/Path(r['remote']['path']).name).stat().st_size == r['remote']['bytes'] for r in mapping))
    expected_output = {'completion.json','construction.json','events.jsonl','exit_code.txt','launch.log',
                       'optimizer_group_records.json','payload_manifest.json','resources.jsonl','worker.pid'}
    check('nine_exact_output_files_no_failures', {r['name'] for r in before['rows'] if r['role'] == 0} == expected_output)
    expected_control = {'authorization_v1.json','runtime_v1.json','launch_once_v1.sh','launch_attempt_v1.json',
                        'readiness_and_installation_receipt_v1.json','startup_receipt_v1.json'}
    check('six_exact_controls', {r['name'][8:] for r in before['rows'] if r['role'] == 1 and r['name'].startswith('control/')} == expected_control)
    manifest = read(OUT/'payload_manifest.json')
    check('original_manifest_five_payload_hashes', {r['name'] for r in manifest} == expected_output-
          {'payload_manifest.json','launch.log','worker.pid','exit_code.txt'} and len(manifest) == 5
          and all(digest(OUT/r['name']) == r['sha256'] and (OUT/r['name']).stat().st_size == r['bytes'] for r in manifest))
    ctrl = INST/'control'; auth = read(ctrl/'authorization_v1.json'); runtime = read(ctrl/'runtime_v1.json')
    check('explicit_authorization_no_reverse_cycle', set(auth) == {'schema','request_sha256','explicit_user_authorization','user_authorization_text'}
          and auth['schema'] == 'bcsp-f0-cuda-authorization-v1' and auth['request_sha256'] == QH
          and auth['explicit_user_authorization'] is True and QH in auth['user_authorization_text'])
    check('one_way_runtime_authorization_hash', runtime == dict(schema='bcsp-f0-cuda-runtime-v1', request_sha256=QH,
                                                              authorization_sha256=digest(ctrl/'authorization_v1.json')))
    # Re-render from exact inert entry bytes, without importing torch or entering main().
    env = dict(__name__='local_readonly_renderer', __file__=str(INST/'bcsp_f0_cuda_admission_v1.py'))
    exec(compile((INST/'bcsp_f0_cuda_admission_v1.py').read_bytes(), '<bound_renderer_only>', 'exec'), env)
    env['authorize'](q, QH, auth, digest(ctrl/'authorization_v1.json'), runtime)
    launcher = env['render_launcher'](q, QH, digest(ctrl/'authorization_v1.json'), digest(ctrl/'runtime_v1.json'))
    check('launcher_exact_frozen_renderer', (ctrl/'launch_once_v1.sh').read_bytes() == launcher.encode('utf-8'))
    claim = read(ctrl/'launch_attempt_v1.json'); startup = read(ctrl/'startup_receipt_v1.json')
    check('unique_claim_bound_to_materialized_controls', claim == dict(status='CLAIMED_BEFORE_UNIQUE_TMUX', request_sha256=QH,
          authorization_sha256=digest(ctrl/'authorization_v1.json'), runtime_sha256=digest(ctrl/'runtime_v1.json'),
          launcher_sha256=digest(ctrl/'launch_once_v1.sh')) and startup['tmux_returncode'] == 0
          and startup['session'] == q['launch_contract']['tmux_session'])
    install = read(ctrl/'readiness_and_installation_receipt_v1.json')
    rehash = read(D/'rehash_assets_stdout_v1.bin')
    check('post_run51_pinned_assets_rehashed', rehash['status'] == 'POST_RUN_PINNED_ASSETS_REHASH_PASS'
          and rehash['records'] == len(install['read_manifest']) == 51 and rehash['bytes'] <= 2*1024**3)
    required = [q[k] for k in ['helper','parent_helper','preflight_scope','static_config','timezone_implementation']] + q['dependencies']
    def key(r):
        return (r['path'],r['bytes'],r['sha256'])
    check('reused_manifest_covers_frozen_direct_dependencies', set(map(key, required)) <= set(map(key, install['read_manifest']))
          and install['status'] == 'EIGHT_EXCLUSIVE_INSTALL_HASHES_PASS' and install['overwritten_files'] == 0)
    check('exit_code_zero', (OUT/'exit_code.txt').read_text().strip() == '0')
    completion = read(OUT/'completion.json')
    expected = dict(full_forward=4,full_backward=4,full_loss=4,decoder_forward=6,decoder_backward=1,optimizer_steps=0)
    check('completion_exact_4fullFB_6decoderF_1B_0step', completion['status'] == 'F0_NATIVE_CUDA_COMPLETE_PENDING_FORMAL_FREEZE_AUDIT'
          and completion['request_sha256'] == QH and completion['counts'] == expected)
    check('no_real_payload_checkpoint_optimizer_training_BNCal', completion['real_data_reads'] == completion['checkpoint_loads'] == 0
          and completion['optimizer_constructed'] is False and completion['training_admission'] is False and completion['BNCal'] is False)
    events = lines(OUT/'events.jsonl'); resources = lines(OUT/'resources.jsonl')
    attempts = [e for e in events if e.get('kind') == 'ATTEMPT_BEFORE_CALL']
    current = {k:0 for k in expected}
    for e in attempts:
        current[e['operation']] += 1
        check('attempt_'+str(sum(current.values()))+'_counters', e['counts'] == current)
    check('19attempts_exact_final_counts', len(attempts) == 19 and current == expected)
    phases = [e for e in events if 'phase' in e]
    check('four_full_phase_batch_order', [(e['phase'],e['batch']) for e in phases] ==
          [('eval_1',1),('eval_2',1),('train_1',8),('train_2',8)] and len(events) == 26)
    prefixes = ['base_model.coarse_pred.','base_model.decoder.coordinate_pe.','reduce_map.']
    prefixes += ['base_model.encoder.blocks.blocks.'+str(i)+'.attn.mixer.' for i in range(6)]
    prefixes += ['base_model.decoder.blocks.'+str(i)+'.'+s+'.' for i in range(8) for s in ['self_ssm','cond_ssm']]
    for e in phases:
        norms = e['gradients']['parameter_norms']; reported = e['gradients']['module_norm_sums']
        sums = {p:sum(v for n,v in norms.items() if n.startswith(p)) for p in prefixes}
        check(e['phase']+'_25module_gradients_finite_nonzero', set(reported) == set(prefixes)
              and all(math.isfinite(v) and v >= 0 for v in norms.values())
              and all(v > 0 and math.isclose(v, reported[p], rel_tol=1e-12) for p,v in sums.items()))
        check(e['phase']+'_weights_and_RNG', e['parameters_unchanged'] and e['RNG_before'] == e['RNG_after']
              and set(e['RNG_before']) == {'CPU','CUDA','Python','numpy'}
              and all(isinstance(v,str) and len(v) == 64 for v in e['RNG_before'].values()))
        check(e['phase']+'_finite_loss', math.isfinite(e['loss']))
    check('eval_state_fingerprints_identical', phases[0]['state_sha256'] == phases[1]['state_sha256']
          and not phases[0]['BN_changed'] and not phases[1]['BN_changed'])
    bn = ['increase_dim.1.running_mean','increase_dim.1.running_var','increase_dim.1.num_batches_tracked']
    check('train_only_expected_BN_buffers', phases[2]['BN_changed'] == phases[3]['BN_changed'] == bn)
    check('same_start_RNG_all_four_checks', all(e['RNG_before'] == phases[0]['RNG_before'] for e in phases))
    check('repeat_output_loss_tolerance', all(v['close'] and math.isfinite(v['max_abs']) for e in (phases[1],phases[3]) for v in e['repeat'].values()))
    restoration = [e for e in events if e.get('kind') == 'FULL_RESTORATION']
    check('full_state_RNG_mode_restored', len(restoration) == 1 and all(restoration[0][k] for k in ['state_restored','RNG_restored','modes_restored']))
    mechanism = next(e for e in events if e.get('kind') == 'PREFIX_MECHANISM')
    threshold = max(q['tolerances']['response_floor'], q['tolerances']['noise_multiplier']*mechanism['noise'])
    check('prefix_response_noise_threshold_unchanged', mechanism['response_threshold'] == threshold
          and set(mechanism['effects']) == {'feature_null','full_prefix_null','early64'}
          and all(math.isfinite(v) and v > threshold for v in mechanism['effects'].values()))
    check('first_layer_before_graph_preserved_conv_boundary', mechanism['first_layer_conditional_suffix_before_graph']
          and mechanism['boundary_last_prefix_tokens_unchanged'] == 3)
    check('decoder_repeat_and_case_isolation', mechanism['repeat']['close'] and mechanism['batch_first']['close'])
    prefix_back = next(e for e in events if e.get('kind') == 'PREFIX_BACKWARD')
    check('prefix_memory_conditional_PE_finite_gradients', math.isfinite(prefix_back['memory_grad_norm']) and prefix_back['memory_grad_norm'] > 0
          and all(math.isfinite(v) and v > 0 for v in prefix_back['gradients']['module_norm_sums'].values()))
    calls = completion['native_SSM_calls']
    check('native22mixers_288calls_per_module', len(calls) == 22 and sum(calls.values()) == 288
          and all(v == (8 if '.encoder.' in n else 20 if '.self_ssm' in n else 10) for n,v in calls.items()))
    construction = read(OUT/'construction.json'); f = construction['factory']; parent = f['parent']
    check('native_M0parent_F0_16decoder_mixers_sharedPE', f['artificial_fixture'] is False and parent['artificial_fixture'] is False
          and parent['variant'] == 'M0' and parent['replaced_global_branches'] == 6 and f['new_mamba_mixers'] == 16
          and f['shared_coordinate_pe_parameters'] == 1152 and f['decoder_seed'] == 20261110
          and f['common_initialization_preserved'] and parent['common_state_unchanged'] and f['shared_decoder_tensors'] == 104)
    check('native_seven_origin_files_pinned', len(construction['native_origins']) == 7
          and set(construction['native_origins']) <= {r['path'] for r in q['dependencies']})
    groups = read(OUT/'optimizer_group_records.json')
    check('411_unique_parameter_groups_no_optimizer', len(groups) == len({r['name'] for r in groups}) == 411
          and all(r['weight_decay'] in (0,.0005) for r in groups))
    check('22_Alog_D_no_decay', all(len([r for r in groups if r['name'].endswith(suffix) and r['weight_decay'] == 0]) == 22
          for suffix in ('.A_log','.D')))
    check('no_registered_attention_known_dispatch_guard_completed', not completion['attention_registered']['forbidden_registered_modules']
          and not f['inventory']['forbidden_registered_modules'] and completion['dispatch_observations'] == {})
    check('opaque_dynamic_limit_retained_not_falsified', completion['attention_registered']['dynamic_kernel_audit_pending'] is True
          and 'opaque' in completion['dynamic_audit_limit'].lower())
    limits = q['limits']; previous_t = -1
    for row in resources:
        v = row['values']
        assert all(math.isfinite(x) for x in v.values())
        assert v['elapsed_seconds'] >= previous_t; previous_t = v['elapsed_seconds']
        recomputed = dict(RSS=v['RSS_bytes'] <= limits['RSS_bytes'], output=v['output_bytes'] <= limits['output_bytes'],
            device=v['device_MiB'] <= limits['device_MiB'], allocated=v['peak_allocated'] <= limits['torch_peak_bytes'],
            reserved=v['peak_reserved'] <= limits['torch_peak_bytes'], wall=v['elapsed_seconds'] <= limits['wall_seconds'],
            disk=v['free_disk_bytes'] >= limits['minimum_free_disk_bytes'])
        assert row['checks'] == recomputed and all(recomputed.values()) and row['failed_checks'] == []
    check('all51resource_rows_independently_recomputed', len(resources) == 51 and resources[0]['phase'] == 'before_construction'
          and resources[-1]['phase'] == 'complete')
    expected_resource = ['before_construction']
    for phase in ['eval_1','eval_2','train_1','train_2']:
        expected_resource += [phase+':before',phase+':before_backward',phase+':restored']
    expected_resource += ['decoder:'+p for p in q['fixture']['order']] + ['complete']
    check('resource_phase_coverage_complete', [r['phase'] for r in resources if r['phase'] != 'MONITOR'] == expected_resource)
    peaks = {key:max(r['values'][key] for r in resources) for key in
             ['RSS_bytes','device_MiB','peak_allocated','peak_reserved','elapsed_seconds']}
    audit = dict(status='POST_CUDA_FREEZE_AUDIT_PASS', date='2026-11-10', request_sha256=QH,
                 checks=CHECKS, checks_passed=len(CHECKS), artifacts=before['rows'], counts=expected,
                 resource_rows=len(resources), peaks=peaks, prefix_mechanism=mechanism,
                 completion=record(OUT/'completion.json'), evidence_files=[record(D/n) for n in
                 ['inventory_before_stdout.bin','inventory_after_stdout.bin','collection_receipt_v1.json','rehash_assets_stdout_v1.bin']],
                 scope_limits=['Synthetic native CUDA execution only; no anatomy/performance conclusion',
                     'Known dispatched attention guards and bound module source; opaque extension internals not inspected',
                     'dynamic_kernel_audit_pending is preserved in original generic inventory; no comprehensive kernel audit claimed',
                     'RNG/state/gradient audit compares logged fingerprints/norms and pinned asserting source; no tensor replay',
                     'Resource peaks are sampled or Torch allocator counters, not dedicated hard cgroup guarantees'],
                 operations=dict(server_writes=0, CUDA_calls=0, real_data_reads=0, checkpoint_loads=0,
                                 tests_rerun=0, training_started=False))
    write('post_CUDA_freeze_audit_result_v1.json', audit)
    write('native_admission_receipt_v1.json', dict(status='F0_NATIVE_CUDA_ADMISSION_PASS', request_sha256=QH,
          audit=record(D/'post_CUDA_freeze_audit_result_v1.json'),
          implementation=q['implementation'], entry=q['entry'], backend='native Mamba2.3.1/PointNet2 + cdist Chamfer',
          scope=expected, training_authorized=False, must_bind_receipt_hash_in_future_training_request=True,
          caveats=audit['scope_limits']))
    print(json.dumps(dict(status=audit['status'], checks=len(CHECKS), counts=expected, peaks=peaks,
                         prefix_effects=mechanism['effects']), indent=2))


if __name__ == '__main__':
    try:
        main()
    except BaseException as exc:
        write('audit_failure_v1.json', dict(status='AUDIT_FAILED_STOP_NO_RETRY', checks=CHECKS, error=repr(exc)))
        raise
