"""Post-analysis content review; no geometry re-execution, repairs or model use."""
import hashlib
import json
import re
from pathlib import Path
from PIL import Image

BASE=Path(__file__).resolve().parent
OUT=BASE/'mug_mesh_v1'

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):
            h.update(b)
    return h.hexdigest()

def verify(directory,manifest_name):
    seen=set()
    for line in (directory/manifest_name).read_text().splitlines():
        digest,name=line.split(None,1)
        assert Path(name).name==name and name not in seen
        assert sha(directory/name)==digest
        seen.add(name)
    return len(seen)

assert verify(OUT,'files.sha256')==9
previous_points=verify(BASE/'result_v2','analysis_files.sha256')
previous_raw=verify(BASE/'raw_pairing_v1','review_files.sha256')
results=json.loads((OUT/'results.json').read_text())
scope=json.loads((OUT/'scope.json').read_text())
assert len(scope['cases'])==len(results['cases'])==3
assert [r['source_id'] for r in results['cases']]==['A0136','A0137','A0138']
for plan,r in zip(scope['cases'],results['cases']):
    rec=plan['record']
    assert sha(Path(plan['stl']))==plan['stl_sha256_before']==r['source_stl_sha256_after']==rec['source_asset_sha256']
    assert sha(Path(plan['npz']))==plan['npz_sha256_before']==r['npz_sha256_after']==rec['derived_case_sha256']
    assert r['source_triangles']==r['retained_triangles']+r['removed_triangles']
    assert r['removed_triangles']==rec['geometry']['removed_triangles']
    assert r['retained_triangles']==rec['geometry']['remaining_triangles']
    assert r['retained_topology']['boundary_edges']==r['retained_boundary_inherited_from_source_edges']+r['retained_boundary_created_by_deletion_edges']+r['retained_boundary_from_source_nonmanifold_edges']
    assert r['retained_boundary_created_by_deletion_edges']>0 and r['new_cutwall_triangles_created']==0
    assert r['source_topology']['boundary_edges']>0 and r['source_topology']['nonmanifold_edges']>0
    assert r['cutwall_area_coverage'].startswith('UNDEFINED')
    assert 0<=r['retained_surface_centroid_area_coverage_at_1mm']<=r['retained_surface_centroid_area_coverage_at_2mm']<=1
    assert 0<=r['new_open_edge_midpoint_length_coverage']['1']<=r['new_open_edge_midpoint_length_coverage']['2']<=1
    assert sum(x['edges'] for x in r['new_open_edge_components']['details'])==r['retained_boundary_created_by_deletion_edges']
    with Image.open(OUT/(r['source_id']+'_mesh_sections.png')) as im:
        assert im.size==(1800,1190)
report=OUT/'mug_mesh_and_integrated_report_zh_v1.md'
for rel in re.findall(r'\]\(([^)]+)\)',report.read_text(encoding='utf-8')):
    assert (OUT/rel).is_file(),rel
receipt={'status':'VERIFIED_THREE_MUG_CASES_AND_PRIOR_SIX_CASE_EVIDENCE',
         'geometry_analysis_process_exit_code_observed':0,'geometry_runs':1,'geometry_reruns_by_this_verifier':0,
         'MUG_cases':3,'MUG_source_files_unchanged_by_hash':6,'MUG_original_result_entries_verified':9,
         'previous_point_analysis_entries_verified':previous_points,'previous_raw_pairing_entries_verified':previous_raw,
         'figures_decoded_and_size_verified':3,'figures_visually_reviewed':3,
         'frozen_geometry_count_match':'PASS','open_edge_accounting':'PASS','fixed_case_identity':'PASS',
         'source_hash_review':'PASS','sanity_checks':7,
         'analysis_script_sha256':sha(BASE/'analyze_mug_mesh_v1.py'),'verifier_sha256':sha(Path(__file__)),
         'report_sha256':sha(report),'server_operations':0,'source_writes':0,'model_and_gpu_operations':0,
         'limitations':['Not global cortical-layer semantic segmentation or complete cavity verification',
                        'No watertight-solid/self-intersection certificate or clinical validation',
                        'No new dataset, sampling change, training or proof of causal model failure']}
with (OUT/'verification_receipt_v1.json').open('x',encoding='utf-8') as f:
    json.dump(receipt,f,indent=2,ensure_ascii=False)
files=sorted(p for p in OUT.iterdir() if p.is_file() and p.name!='review_files.sha256')
with (OUT/'review_files.sha256').open('x') as f:
    for p in files:
        f.write(sha(p)+'  '+p.name+'\n')
print(json.dumps({'status':receipt['status'],'MUG_result_entries':9,'previous_point_entries':previous_points,
                  'previous_raw_entries':previous_raw,'new_review_entries':len(files),'source_hashes_matched':6},indent=2))
