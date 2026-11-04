"""Verify downloaded results and derive descriptive summaries; no data payload reads."""
import hashlib
import json
import posixpath
import statistics
from pathlib import Path

BASE = Path(__file__).resolve().parent
RESULT = BASE / 'result_v2'
EXPECTED_ARCHIVE_SHA256 = '684e09bee3311059fc99157b2fbe2fb238b3827c80145e258fdc3f5f5c24e6e8'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

assert sha(BASE / 'geometry_result_v2.tar.gz') == EXPECTED_ARCHIVE_SHA256
checked = []
for line in (RESULT / 'analysis_files.sha256').read_text().splitlines():
    digest, name = line.split(None, 1)
    assert Path(name).name == name
    assert sha(RESULT / name) == digest
    checked.append(name)
r = json.loads((RESULT / 'results.json').read_text())
s = json.loads((RESULT / 'selected_scope.json').read_text())
assert (RESULT / 'exit_code.txt').read_text().strip() == '0'
assert len(r['cases']) == 9
assert all(c['sha256_before'] == c['sha256_after'] for c in r['cases'])
assert len(list(RESULT.glob('*point_slabs.png'))) == 9
summary = {}
for d in ['SkullFix','SkullBreak','MUG500plus']:
    cases = [c for c in r['cases'] if c['dataset'] == d]
    summary[d] = {
        'cases': [c['case_id'] for c in cases],
        'case_n': len(cases),
        'input_points_per_case': [c['partial_n'] for c in cases],
        'target_points_per_case': [c['implant_n'] for c in cases],
        'median_of_case_global_nn_medians_mm': statistics.median(c['global_unique_nn_mm']['median'] for c in cases),
        'support_2mm_n_min_max': [min(c['contact_support_2mm_n'] for c in cases),max(c['contact_support_2mm_n'] for c in cases)],
        'support_2mm_fraction_median': statistics.median(c['contact_support_2mm_fraction'] for c in cases),
        'median_of_case_within_rim_nn_medians_mm': statistics.median(c['rim_within_band_unique_nn_mm']['median'] for c in cases),
        'median_of_case_unsigned_normal_angle_medians_deg': statistics.median(c['unsigned_neighbor_normal_angle_deg']['median'] for c in cases),
        'all_partial_points_unique': all(c['partial_duplicate_fraction'] == 0 for c in cases),
        'stored_rim_agreement': [c['reference_rim_mask_agrees_at_2mm'] for c in cases]
    }
missing = []
for item in s['cases']:
    rec = item['record']
    if item['dataset'] == 'MUG500plus':
        missing.append({'dataset': item['dataset'], 'case_id': rec['case_id'],
                        'path_recorded': posixpath.normpath(item['root'] + '/' + rec['source_asset_path']),
                        'sha256_expected': rec['source_asset_sha256'],
                        'suggested_local_relative_path': 'MUG500plus/' + rec['source_asset_path'].split('/')[-1],
                        'needed_for': 'Original mesh sections, topology and exact centroid-mask deletion study'})
    else:
        root = 'D:/dataset/SkullFix/extracted/training_set' if item['dataset'] == 'SkullFix' else 'D:/dataset/SkullBreak/raw'
        for role, rel in rec['raw'].items():
            missing.append({'dataset': item['dataset'], 'case_id': rec['case_id'], 'role': role,
                            'path_recorded': root + '/' + rel,
                            'sha256_expected': None,
                            'mask_fingerprint_sha256_expected': rec.get('complete_mask_sha256') if role == 'complete' else None,
                            'hash_note': 'NRRD file hash unavailable; mask fingerprint, when present, hashes int32 shape plus binary array content, not the compressed NRRD file.',
                            'suggested_local_relative_path': item['dataset'] + '/' + rel,
                            'needed_for': 'Raw boundary voxel count, physical surface coverage and true cut-wall reference'})
receipt = {'status': 'LOCAL_DOWNLOAD_AND_CONTENT_VERIFIED_PARTIAL_SCIENCE_COMPLETE',
           'receipt_version': 3,
           'supersedes': 'v1/v2: correct POSIX display and distinguish binary-mask fingerprints from NRRD file SHA256. No analysis rerun or metric change.',
           'archive_sha256': EXPECTED_ARCHIVE_SHA256, 'archive_bytes': (BASE/'geometry_result_v2.tar.gz').stat().st_size,
           'verified_manifest_entries': len(checked), 'point_cloud_cases':9, 'raw_masks_read':0,'raw_stls_read':0,
           'input_hashes_before_after_match':True, 'summary':summary, 'elapsed_seconds_remote':r['elapsed_seconds'],
           'missing_raw_assets':missing,
           'limitations':['These are stored NPZ variants at SkullFixPC/SkullBreakPC, not all out8192 variants or runtime FPS inputs.',
                          'Target point counts differ: 4096 versus 8192. Not a density-controlled cross-dataset experiment.',
                          'No anatomical classification or raw-surface coverage is established.']}
with (BASE/'local_verification_and_summary_v3.json').open('x',encoding='utf-8') as f:
    json.dump(receipt,f,indent=2,ensure_ascii=False,allow_nan=False)
print(json.dumps({'verified_entries':len(checked),'summary':summary,'elapsed_seconds':r['elapsed_seconds'],
                  'missing_raw_files':len(missing),'MUG_STL_bindings':[x for x in missing if x['dataset']=='MUG500plus']},ensure_ascii=False,indent=2))
