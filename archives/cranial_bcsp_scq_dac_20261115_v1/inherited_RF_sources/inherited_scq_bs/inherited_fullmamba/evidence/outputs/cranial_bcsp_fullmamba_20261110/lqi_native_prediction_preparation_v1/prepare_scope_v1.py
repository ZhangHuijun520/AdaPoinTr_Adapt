"""Local metadata preparation only; no tensor/model/payload or remote access."""
import copy
import hashlib
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent

def record(p):
    p = p.resolve()
    raw = p.read_bytes()
    return dict(path=str(p), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())

def read(p):
    return json.loads(p.read_text(encoding='utf-8'))

def write(name, value):
    with (HERE / name).open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')

original = BASE / 'Native_prediction_preparation_v1/F0_CD_Native_input_index_candidate_v1.json'
assert record(original)['sha256'] == '874f0c7b8e0a4dfc6d1c98682ba5302080b9e6853d69703c1035c708f1395e84'
index = copy.deepcopy(read(original))
index['schema'] = 'bcsp-lqi-native-development-index-candidate-v1'
index['status'] = 'FROZEN_METADATA_SCOPE_NOT_EXECUTABLE'
index['parent_F0_index'] = record(original)
audit_dirs = {
    'C': BASE / 'lqi_training_entry_v1/post_training_freeze_audit_v1',
    'D': BASE / 'lqi_FoldD_training_entry_v1/post_training_freeze_audit_v2',
}
suffix = {'C': '20261111_v1', 'D': '20261111_v2'}
audits = {}
for run in index['runs']:
    fold = run['fold']
    ap = audit_dirs[fold] / 'post_training_freeze_audit_result_v1.json'
    a = read(ap)
    assert a['status'] == 'FORMAL_LQI_FOLD'+fold+'_POST_TRAINING_FREEZE_AUDIT_PASS'
    assert a['checks_passed'] == len(a['checks']) == 42 and all(a['checks'].values())
    run.update(label=fold+'_LQI', variant='F0-LQI-v1')
    run['checkpoint'] = dict(path='/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/LQI_fold'+fold+'_seed0_train_'+suffix[fold]+'/ckpt-last.pth', bytes=a['checkpoint']['bytes'], sha256=a['checkpoint']['sha256'])
    request = (BASE / 'lqi_training_entry_v1/LQI_FoldC_training_execution_request_v1.json') if fold == 'C' else (BASE / 'lqi_FoldD_training_entry_v1/failed_startup_freeze_and_bridge_fix_v2/pending_transport_v2/LQI_FoldD_training_execution_request_v2.json')
    run['training_request'] = record(request)
    assert run['training_request']['sha256'] == a['request_sha256']
    run['training_audit'] = record(ap)
    pair = audit_dirs[fold] / ('F0_pairing_freeze_audit_result_v1.json' if fold == 'C' else 'F0D_LQIC_pairing_freeze_audit_result_v2.json')
    run['pairing_audit'] = record(pair)
    audits[fold] = record(ap)

parent = read(original)
for old, row in zip(parent['inputs'], index['inputs']):
    row.update(run=row['fold']+'_LQI', variant='F0-LQI-v1', cache_context=False, save_full_decoder_trace=False)
    row['prediction_filename'] = 'predictions/'+row['run']+'__'+row['case_id']+'.npz'
    changed = {'run','variant','prediction_filename','cache_context','save_full_decoder_trace'}
    assert {k:v for k,v in old.items() if k not in changed} == {k:v for k,v in row.items() if k not in changed}
for fold in ('C','D'):
    rows = [r for r in index['inputs'] if r['fold'] == fold]
    assert len(rows) == 105 and len({r['source_id'] for r in rows}) == 21
    assert set(Counter(r['source_id'] for r in rows).values()) == {5}
    assert set(Counter(r['defect_type'] for r in rows).values()) == {21}
assert len(index['inputs']) == 210
write('LQI_CD_Native_input_index_candidate_v1.json', index)

scope = dict(
    schema='bcsp-lqi-twofold-native-prediction-scope-v1',
    status='FROZEN_SCOPE_AWAITING_IMPLEMENTATION_NOT_EXECUTION_REQUEST',
    prepared_date='2026-11-11',
    authorization_boundary='No prediction/scoring/deployment or runtime/launcher/authorization materialization authorized by this scope.',
    current_resource_reference=dict(hostname='shu-common-25721452-notebook-zv9bqd-0', live_rechecked_this_round=False, require_bounded_identity_assets_resource_check_before_final_request=True),
    input_index=record(HERE / 'LQI_CD_Native_input_index_candidate_v1.json'),
    training_audits=audits,
    model_sources=[record(BASE / 'lqi_implementation_v1' / n) for n in ('bcsp_lqi_decoder_v1.py','bcsp_lqi_factory_v1.py')],
    original_entry=record(BASE / 'Native_prediction_implementation_v1/bcsp_f0_twofold_native_predict_v1.py'),
    inference=dict(folds=['C','D'], cases_per_fold=105, sources_per_fold=21, defect_types=['bilateral','frontoorbital','parietotemporal','random_1','random_2'], batch_size=1, input_points=8192, output_points=8192, coarse_points=256, forward_attempt_budget=210, successful_forwards_required=210, loss_calls=0, backward=0, optimizer_steps=0, BNCal=0, warmup=0, TTA=0, retries=0, model_mode='eval + inference_mode', real_GT_payload_access=False, input_arrays='partial only; target payload must not be read', normalization='unchanged defective_bbox; preserve center/scale from parent index', coordinate_frame='same normalized prediction frame as F0; world scoring uses frozen center/scale'),
    numeric=dict(dtype='FP32', TF32=False, deterministic_algorithms=True, pointnet2='existing native Python3.10 provider; fallback forbidden', chamfer='existing PyTorch cdist policy retained; no loss or Chamfer evaluation in this prediction scope', native_mamba=True, repeat_GPU_preflight=False),
    outputs=dict(prediction_files=210, per_prediction_arrays=dict(prediction=[8192,3],coarse=[256,3]), context_caches=0, full_decoder_traces=0, required=['inference_manifest.jsonl','forward_attempts.jsonl','geometry_summary.jsonl','per-model state/RNG before-after fingerprints','resource log','construction evidence','completion/exit code','archive plus SHA256/bytes/content manifest'], trace_semantics='No traces requested; any later LQI prefix_suffix trace means interleaved conditional query-position output, never F0 prefix/suffix conditioning.'),
    limits=dict(wall_seconds=7200,RSS_bytes=8589934592,torch_peak_bytes=21474836480,device_MiB=22528,output_bytes=1073741824,minimum_free_disk_bytes=4294967296),
    failure_policy='Persist first error and counts; stop immediately; no automatic retry/resume, forward substitution, case filtering, fallback, training or scoring.',
    later_scoring=dict(baseline='Reuse frozen F0 Native predictions, do not regenerate F0', pair_keys=['fold','case_id','source_id','input SHA256','normalization'], metrics_thresholds='unchanged frozen production definitions', metric_protocol_sha256='af938519125b25b6d22d862dd4967dabef3be6d97d38e60eb9995ee7e9ce9766', source_equal_paired_summary=True, prerequisite='Separate formal post-prediction freeze audit, download and local verification, then dedicated scoring entry compatibility/P3 and separately authorized CPU scoring request', no_efficacy_conclusion_yet=True),
    minimal_adapter_gaps=['LQI-specific request/index/model identity and exact trained-checkpoint/audit pins', 'Load exact LQI decoder/factory and bind their actual file reads, preserving parent encoder/factory', 'Validate LQI interleaving evidence, parameter count and common model contract; reject accidental F0 construction', 'Native-only all210 coarse+dense outputs; remove mandatory old20-context/10-trace count and donor-selection dependency without weakening case/input identity checks', 'CPU full authorize/load-route/read-policy/index/210-output/state-RNG/failure-path contract verification plus P3 before executable request'],
)
baseline_audit = BASE / 'Native_prediction_implementation_v1/resource_rebind_v2/post_prediction_freeze_audit_v1/post_prediction_freeze_audit_result_v1.json'
scope['frozen_F0_prediction_audit'] = record(baseline_audit)
assert scope['frozen_F0_prediction_audit']['sha256'] == '69a2438f42a40daeaf068ab77775a5679a30013167ba303a5da5dfa7287ae09e'
write('LQI_CD_210_Native_prediction_scope_v1.json', scope)
write('preparation_validation_receipt_v1.json', dict(status='LOCAL_METADATA_SCOPE_VALIDATED_NOT_EXECUTED', checks=dict(parent_index_hash=True,two_formal_training_audits_42_checks=True,request_hashes_match_audits=True,case_input_normalization_metadata_unchanged=True,twofold_105_each_21_sources_5_defects=True,no_payload_or_checkpoint_loaded=True), artifacts=[record(HERE / n) for n in ['LQI_CD_Native_input_index_candidate_v1.json','LQI_CD_210_Native_prediction_scope_v1.json']]))
print(json.dumps(record(HERE / 'LQI_CD_210_Native_prediction_scope_v1.json')))
