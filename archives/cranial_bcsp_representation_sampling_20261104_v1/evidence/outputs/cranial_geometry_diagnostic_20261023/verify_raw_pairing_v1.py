"""Independent read-only content/hash review; does not rerun geometry analysis."""
import hashlib
import json
import re
from pathlib import Path
from PIL import Image

BASE=Path(__file__).resolve().parent
OUT=BASE/'raw_pairing_v1'

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):
            h.update(b)
    return h.hexdigest()

manifest={}
for line in (OUT/'files.sha256').read_text().splitlines():
    digest,name=line.split(None,1)
    assert Path(name).name==name and name not in manifest
    assert sha(OUT/name)==digest
    manifest[name]=digest
assert len(manifest)==15
results=json.loads((OUT/'results.json').read_text())
scope=json.loads((OUT/'scope.json').read_text())
assert len(results['cases'])==len(scope['cases'])==6
expected={('SkullFix',x) for x in ['002','003','004']}|{('SkullBreak','train__'+x+'__bilateral') for x in ['000','001','002']}
assert {(c['dataset'],c['case_id']) for c in results['cases']}==expected
source_files={}
for plan in scope['cases']:
    r=next(c for c in results['cases'] if c['dataset']==plan['dataset'] and c['case_id']==plan['case_id'])
    assert r['partition_exact'] and r['input_hashes_after_match']
    assert r['cut_interface_faces']>0 and r['sampled_cut_adjacent_voxel_centers']>0
    assert r['max_voxel_center_reprojection_error_index_units']<.001
    assert r['sparse_band_only_points']==0
    assert r['hashes_after']==plan['hashes_before']
    for p,digest in plan['hashes_before'].items():
        assert sha(Path(p))==digest
        source_files[p]=digest
    for key in ['defective_face_area_coverage_at_1mm','defective_face_area_coverage_at_2mm','cut_interface_area_coverage_all_input_at_1mm','cut_interface_area_coverage_all_input_at_2mm']:
        assert 0<=r[key]<=1
    with Image.open(OUT/(r['dataset']+'_'+r['case_id']+'_raw_sections.png')) as im:
        assert im.size==(1800,1160)
assert len(source_files)==24
report=(OUT/'raw_pairing_report_zh_v1.md').read_text(encoding='utf-8')
for rel in re.findall(r'\]\(([^)]+)\)',report):
    assert (OUT/rel).is_file(), rel
receipt={'status':'VERIFIED_SIX_CASE_RAW_PAIRING_RESULTS_WITH_EXPLICIT_LIMITATIONS',
         'original_manifest_entries':len(manifest),'cases':6,'source_files_readonly_rehashed':len(source_files),
         'original_inputs_unchanged':True,'figures_decoded_and_size_verified':6,'figures_visually_reviewed':6,
         'mask_partition_and_coordinate_checks':'PASS','source_readonly_hash_review':'PASS',
         'model_and_gpu_computations':0,'server_operations':0,'geometry_reruns':0,
         'sanity_checks':5,'observed_analysis_process_exit_code':0,
         'analysis_script_sha256':sha(BASE/'analyze_raw_pairs_v1.py'),
         'verification_script_sha256':sha(Path(__file__)),
         'report_sha256':sha(OUT/'raw_pairing_report_zh_v1.md'),
         'still_incomplete':['MUG500+ original STL topology and cut-wall analysis','Global anatomical inner/outer semantic coverage','Continuous mesh area/thickness/opening-width metrics']}
with (OUT/'verification_receipt_v1.json').open('x',encoding='utf-8') as f:
    json.dump(receipt,f,indent=2,ensure_ascii=False)
files=sorted(p for p in OUT.iterdir() if p.is_file() and p.name!='review_files.sha256')
with (OUT/'review_files.sha256').open('x') as f:
    for p in files:
        f.write(sha(p)+'  '+p.name+'\n')
print(json.dumps({'status':receipt['status'],'sources_verified':len(source_files),'result_files_verified':len(manifest),'final_review_manifest_entries':len(files)},indent=2))
