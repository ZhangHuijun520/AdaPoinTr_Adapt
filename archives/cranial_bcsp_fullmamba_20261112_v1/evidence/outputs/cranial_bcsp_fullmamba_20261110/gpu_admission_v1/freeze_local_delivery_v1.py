"""Local-only evidence freeze. Never connects, installs or launches anything."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import tarfile

B = Path(__file__).resolve().parent
ROOT = B.parents[2]
IMPL = B.parent/'implementation_v1'
P1 = ROOT/'outputs/cranial_bcsp_mamba_p1_20261104/minimal_implementation_v1'
OLD = ROOT/'outputs/cranial_bcsp_mamba_p2_20261106/H2_cuda_admission_v1/H2_artificial_cuda_execution_request_v1.json'
REMOTE = PurePosixPath('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_f0_cuda_20261110_v1')


def read(p):
    return json.loads(p.read_bytes())


def record(path, target=None):
    p = Path(path); b = p.read_bytes()
    return dict(path=str(target or p.resolve()), bytes=len(b), sha256=hashlib.sha256(b).hexdigest())


def emit(path, value):
    with path.open('x', encoding='ascii') as f:
        json.dump(value, f, indent=2, allow_nan=False)
        f.write('\n')


def main():
    result = read(B/'artificial_cpu_entry_batch_v1/result.json')
    assert result['status'] == 'ARTIFICIAL_CPU_ENTRY_BATCH_PASS' and result['check_count'] == 27
    static = read(B/'static_review_v1.json')
    for r in static['files']:
        assert record(r['path']) == r
    previous = read(IMPL/'implementation_P3_v1.json')
    for r in previous['new_code_files'] + previous['parent_files_reverified_unchanged']:
        now = record(r['path']); assert now['sha256'] == r['sha256'] and now['bytes'] == r['bytes']
    identity = read(B/'identity_approved_stdout_v1.bin')
    assert identity['hostname'] == 'shu-common-25721452-notebook-n8xph5-0' and identity['uid'] == 1000
    assert identity['free'] >= 4*1024**3
    for index in (0, 1):
        assert all(r['match'] for r in read(B/('assets_'+str(index)+'_stdout_v1.bin')))
    sources = read(B/'sources_stdout_v1.bin')
    assert all(r['match'] for r in sources['rows']) and sources['new_target_absent']
    utc = read(B/'UTC_stdout_v1.bin')
    gpu = [s.strip() for s in identity['gpu'].split(',')]
    assert len(gpu) == 5 and int(gpu[-1]) <= 256
    old = read(OLD)
    spec = importlib.util.spec_from_file_location('f0_freeze_entry', B/'bcsp_f0_cuda_admission_v1.py')
    entry = importlib.util.module_from_spec(spec); spec.loader.exec_module(entry)
    local_files = [B/'bcsp_f0_cuda_admission_v1.py', IMPL/'bcsp_f0_decoder_v1.py',
                   IMPL/'bcsp_f0_factory_v1.py', P1/'bcsp_mamba_encoder_v1.py',
                   P1/'bcsp_p1_model_factory_v1.py', P1/'bcsp_p1_training_runtime_v1.py']
    mapping = [dict(local=record(p), remote=record(p, REMOTE/p.name), overwrite=False) for p in local_files]
    implementation = {key: mapping[i]['remote'] for key, i in
                      [('encoder', 3), ('factory', 4), ('f0_decoder', 1), ('f0_factory', 2)]}
    evidence = [B/'static_review_v1.json', B/'artificial_cpu_entry_batch_v1/result.json',
                B/'identity_call_v1.json', B/'identity_stdout_v1.bin', B/'identity_stderr_v1.bin',
                B/'identity_approved_call_v1.json', B/'identity_approved_stdout_v1.bin',
                B/'identity_approved_stderr_v1.bin', B/'assets_0_stdout_v1.bin', B/'assets_0_stderr_v1.bin',
                B/'assets_1_stdout_v1.bin', B/'assets_1_stderr_v1.bin', B/'sources_stdout_v1.bin',
                B/'sources_stderr_v1.bin', B/'UTC_stdout_v1.bin', B/'UTC_stderr_v1.bin']
    p3 = dict(status='ENTRY_IMPLEMENTATION_CPU_P3_PASS_NATIVE_CUDA_NOT_EXECUTED', date='2026-11-10',
              entry_sources=[record(B/'bcsp_f0_cuda_admission_v1.py'), record(B/'test_f0_cuda_entry_cpu_v1.py')],
              artificial_CPU_checks=27, evidence=[record(p) for p in evidence],
              parent_implementation_P3=record(IMPL/'implementation_P3_v1.json'),
              exact_original_code_unchanged=True, inherited_assets_currently_verified=True,
              current_hostname=identity['hostname'], science=entry.SCIENCE,
              limitations=['CPU cheap loss and causal surrogate do not validate native CUDA or full Chamfer',
                          'Full checks restore parameters/BN/RNG; train BN updates are expected and recorded',
                          'Known dispatched attention ops are rejected; opaque extension internals are not inspected',
                          'RSS/device resource monitoring is sampled, not a hard dedicated cgroup limit',
                          'Parent asset/provider identity must be checked again before actual execution',
                          'Sandbox WSL call failed before server access; approved non-admin readonly calls succeeded'],
              server_writes=0, CUDA_forwards=0, optimizer_steps=0, execution_materialized=False)
    p3_path = B/'entry_P3_v1.json'; emit(p3_path, p3)
    mapping.append(dict(local=record(p3_path), remote=record(p3_path, REMOTE/p3_path.name), overwrite=False))
    I = dict(old['identity'])
    I.update(hostname=identity['hostname'], uid=identity['uid'], gpu_uuid=gpu[0], gpu_name=gpu[1],
             driver_version=gpu[2], nvidia_smi_memory_total_MiB=int(gpu[3]),
             python_realpath=identity['python'], python_version=sources['python_version'], torch_cuda_version='11.8')
    env = dict(old['environment']); env['CUDA_VISIBLE_DEVICES'] = I['gpu_uuid']
    output = '/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/F0_artificial_cuda_20261110_v1'
    controls = REMOTE/'control'
    q = dict(schema='bcsp-f0-synthetic-cuda-v1', status='AWAITING_EXPLICIT_USER_AUTHORIZATION',
        execution_authorized=False, date='2026-11-10', identity=I,
        project='/home/jovyan/adapointr_work/PoinTr', environment=env,
        model_root=old['model_root'], dependencies=old['dependencies'],
        helper=old['helper'], parent_helper=old['parent_entry'],
        preflight_scope=old['preflight_scope'], static_config=old['static_config'],
        timezone_implementation=old['implementation']['timezone'], timezone_resource=utc,
        implementation=implementation, training_runtime=mapping[5]['remote'],
        entry=mapping[0]['remote'], P3=mapping[6]['remote'],
        science=entry.SCIENCE, tolerances=entry.TOLERANCE,
        limits=dict(old['limits'], wall_seconds=1800),
        output=output, install_root=str(REMOTE), installation_bindings=[r['remote'] for r in mapping],
        readiness=dict(identity_verified=True, inherited_assets_verified=True, new_install_root_observed_absent=True,
                       readonly_evidence_P3=mapping[6]['remote'], reverify_immediately_before_launch=True),
        fixture=dict(full='NumPy default_rng seeds20261110/20261112 uniform[-.5,.5], FP32(8,8192,3); B1 uses first row',
                     decoder='CPU torch.Generator seed20261111: q/memory (2,256,384), q/mpos (2,256,3); randn*.2, copied toCUDA',
                     order=['original_1', 'original_2', 'feature_null', 'full_prefix_null', 'early_prefix_64', 'second_case_changed'],
                     full_prefix_null='zero every layer conditional input first256 tokens including PE, local graph unchanged',
                     early_prefix='add linspace(-.1,.1,384) to first64 sorted Memory prefix tokens; final3 and Query unchanged',
                     observation='first layer conditional SSM suffix before graph/merge, no anatomical correspondence claim',
                     batch_isolation='change only second sample q/memory/qpos/mpos by+.137; first sample output must match tolerance'),
        numeric=dict(FP32=True, TF32=False, strict_deterministic=True, finite_gradient_nondeterminism_accepted=True,
                     gradient_policy='all present finite; nonzero module norm for all22mixers, PE, coarse head/reduce_map; no bitwise gradient equality',
                     response='maxabs above max(1e-7,10*original-repeat maxabs noise); not tuned after native observation'),
        launch_contract=dict(tmux_session='bcsp_f0_cuda_20261110_v1',
            request_path=str(REMOTE/'F0_artificial_cuda_execution_request_v1.json'),
            authorization_path=str(controls/'authorization_v1.json'), runtime_path=str(controls/'runtime_v1.json'),
            launcher_path=str(controls/'launch_once_v1.sh'), launch_attempt_path=str(controls/'launch_attempt_v1.json'),
            log=output+'/launch.log', PID=output+'/worker.pid', exit_code=output+'/exit_code.txt',
            materialization_order='authorization -> itsSHA256 -> runtime(one-way) -> launcher',
            render_function='entry.render_launcher, bound entry bytes', parent_before_redirection=True,
            PowerShell_explicit_exit_LASTEXITCODE=True, transport='original bytes/Base64, never text decode-reencode',
            exclusive_single_attempt=True, automatic_retry=False, timeout_kill_after_seconds=10),
        resource_policy=dict(RSS='8GiB monitored, no dedicated hard cgroup guarantee', torch_peak='20GiB allocated/reserved',
            physical_GPU_stop_MiB=22528, initial_GPU_max_MiB=256, monitoring_poll_seconds=2,
            nvidia_smi_timeout_seconds=10, nvidia_smi_no_retry=True, PID='diagnostic only; no procfs ownership assertion',
            wall_budget_reason='bounded1800s for four full real-loss F/B including B8 plus six local calls; not a speed claim'),
        required_outputs=['worker.pid','events.jsonl','resources.jsonl','construction.json','optimizer_group_records.json',
                          'completion.json OR failure.json/monitor_failure.json','payload_manifest.json on success','launch.log','exit_code.txt'],
        forbidden=['Execution before separate fullSHA authorization', 'optimizer construction/step or model training',
                   'real data/checkpoint reads or BNCal/development evaluation', 'download/build/install/upgrade of dependencies',
                   'extra warmup/forward/backward, retry or resume', 'changing source/fixture/loss/provider/limits/tolerance',
                   'automatic training admission before formal post-CUDA freeze audit'],
        provenance=dict(local_implementation_P3=record(IMPL/'implementation_P3_v1.json'),
                        formal_plan=previous['parent_files_reverified_unchanged'][-1],
                        CPU_entry_result=record(B/'artificial_cpu_entry_batch_v1/result.json')))
    request_path = B/'F0_artificial_cuda_execution_request_v1.json'; emit(request_path, q)
    mapping.append(dict(local=record(request_path), remote=record(request_path, REMOTE/request_path.name), overwrite=False))
    emit(B/'frozen_transport_installation_mapping_v1.json', dict(status='FROZEN_NOT_UPLOADED_NOT_INSTALLED',
         request_sha256=record(request_path)['sha256'], files=mapping,
         policy='Recheck current identity, upload SHA, all eight targets and safe parents; exclusive no-overwrite writes; stop on anomaly'))
    # Render only in memory with artificial hashes: not an authorized launcher or runtime file.
    rendered = entry.render_launcher(q, 'a'*64, 'b'*64, 'c'*64)
    assert '\\' not in rendered.replace('\\n', '') and str(PurePosixPath(output).parent) in rendered
    assert rendered.index('mkdir -p') < rendered.index(' >')
    emit(B/'final_contract_review_v1.json', dict(status='PASS_PREPARATION_ONLY',
         request=record(request_path), installation_files=len(mapping), real_GPU_calls=0,
         controls_materialized=False, rendered_in_memory_with_artificial_hashes=True,
         code_and_evidence_rehashed=True, artificial_CPU_checks=27))
    archive = B/'bcsp_f0_artificial_cuda_pending_20261110_v1.tar.gz'
    with archive.open('xb') as stream:
        with tarfile.open(fileobj=stream, mode='w:gz') as tar:
            for row in mapping:
                tar.add(row['local']['path'], arcname=Path(row['local']['path']).name, recursive=False)
    with tarfile.open(archive, 'r:gz') as tar:
        members = tar.getmembers(); assert len(members) == 8 and all(m.isfile() for m in members)
        byname = {Path(row['local']['path']).name: row['local'] for row in mapping}
        for member in members:
            b = tar.extractfile(member).read(); r = byname[member.name]
            assert len(b) == r['bytes'] and hashlib.sha256(b).hexdigest() == r['sha256']
    for suffix, text in [('.sha256', record(archive)['sha256']+'  '+archive.name+'\n'),
                         ('.bytes', str(archive.stat().st_size)+'\n'),
                         ('.contents.sha256', ''.join(row['remote']['sha256']+'  '+Path(row['local']['path']).name+'\n' for row in mapping))]:
        with Path(str(archive)+suffix).open('x', encoding='ascii') as f:
            f.write(text)
    emit(B/'delivery_receipt_v1.json', dict(status='READY_FOR_UPLOAD_AND_SEPARATE_AUTHORIZATION_NOT_EXECUTED',
         request=record(request_path), archive=record(archive), files=8,
         sidecars=[record(Path(str(archive)+s)) for s in ('.sha256','.bytes','.contents.sha256')],
         server_writes=0, GPU_calls=0, CPU_checks=27))
    print(json.dumps(dict(status='PREPARATION_COMPLETE_NOT_EXECUTED', request=record(request_path), archive=record(archive),files=8)))


if __name__ == '__main__':
    main()
