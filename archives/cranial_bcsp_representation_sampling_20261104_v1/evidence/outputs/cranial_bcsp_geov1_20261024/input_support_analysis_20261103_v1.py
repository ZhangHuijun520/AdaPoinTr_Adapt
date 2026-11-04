# -*- coding: utf-8 -*-
"""Analyze saved SkullFix input support; no raw decode, sampling, model or GPU."""
import csv,hashlib,json,sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
B=Path(__file__).resolve().parent
SRC=B/'skullfix_surface_points_20261103_v1'
OUT=B/'input_support_analysis_20261103_v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):
    with p.open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False)
def main():
    manifest=json.loads((SRC/'artifact_manifest.json').read_text(encoding='utf-8'))
    records=[json.loads(s) for s in (SRC/'manifest_8192.jsonl').read_text(encoding='utf-8').splitlines()]
    assert len(records)==90
    consumed={};rows=[]
    for rec in records:
        rel=f"cases/{rec['case_id']}.json";p=SRC/rel
        assert sha(p)==manifest['files'][rel]['sha256'];consumed[str(p)]=sha(p)
        row=json.loads(p.read_text(encoding='utf-8'));d,g=row['D'],row['G']
        pp=SRC/rec['point_path'];dp=SRC/rec['diagnostic_provenance_path']
        assert sha(pp)==rec['sha256'] and sha(dp)==rec['diagnostic_provenance_sha256']
        consumed[str(pp)]=sha(pp);consumed[str(dp)]=sha(dp)
        with np.load(pp,allow_pickle=False) as z,np.load(dp,allow_pickle=False) as v:
            points=z['partial'].astype(float)*v['normalization_scale']+v['normalization_center']
            isj=v['D_sample_is_J'];assert isj.sum()==d['sample_J_points']
            jp=points[isj]
            nnj=cKDTree(jp).query(jp,k=2)[0][:,1]
            nna=cKDTree(points).query(jp,k=2)[0][:,1]
        fraction=d['J_area_mm2']/d['total_area_mm2'];expected=8192*fraction
        # Counterfactual expectations, not a newly generated point set or performance estimate.
        exp_no_fov=8192*d['J_area_mm2']/(d['total_area_mm2']-d['FOV_area_mm2'])
        rows.append({'case_id':rec['case_id'],'split':rec['split'],
            'J_area_fraction':fraction,'J_points_observed':d['sample_J_points'],
            'J_points_area_uniform_expectation':expected,
            'observed_over_expected':d['sample_J_points']/expected,
            'binomial_standardized_count_residual':(d['sample_J_points']-expected)/np.sqrt(expected*(1-fraction)),
            'D_area_mm2':d['total_area_mm2'],'G_area_mm2':g['total_area_mm2'],
            'D_point_density_per_mm2':8192/d['total_area_mm2'],'G_point_density_per_mm2':8192/g['total_area_mm2'],
            'G_over_D_density_ratio':d['total_area_mm2']/g['total_area_mm2'],
            'D_J_cover2':d['J_metric']['cover_2mm'],'D_all_cover2':d['all_boundary_metric']['cover_2mm'],
            'G_J_cover2':g['J_metric']['cover_2mm'],
            'D_J_only_cover2':d['J_provenance_only_metric']['cover_2mm'],
            'D_J_p95_mm':d['J_metric']['p95_mm'],
            'J_sample_nearest_J_median_mm':float(np.median(nnj)),
            'J_sample_nearest_any_D_median_mm':float(np.median(nna)),
            'FOV_area_fraction':d['FOV_area_fraction'],
            'expected_J_points_if_only_FOV_excluded':exp_no_fov,
            'expected_J_points_gain_if_only_FOV_excluded':exp_no_fov-expected})
    OUT.mkdir(exist_ok=False)
    def stats(key):
        a=np.array([r[key] for r in rows]);return {k:float(v) for k,v in [('mean',a.mean()),('median',np.median(a)),('min',a.min()),('max',a.max())]}
    aggregate={k:stats(k) for k in rows[0] if k not in ['case_id','split']}
    aggregate['observed_J_points_total']=sum(r['J_points_observed'] for r in rows)
    aggregate['expected_J_points_total']=sum(r['J_points_area_uniform_expectation'] for r in rows)
    aggregate['count_residual_abs_gt_2_cases']=[r['case_id'] for r in rows if abs(r['binomial_standardized_count_residual'])>2]
    dump(OUT/'results.json',{'case_count':90,'aggregation':'case-equal means; no hypothesis significance tests','aggregate':aggregate,'cases':rows})
    with (OUT/'case_support.csv').open('x',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    dump(OUT/'scope_and_verification.json',{'status':'COMPLETED_READ_ONLY_EXISTING_POINT_ANALYSIS','cases':90,'train':80,'validation':10,
        'raw_payload_reads':0,'new_point_sets':0,'model_GPU_training_calls':0,
        'diagnostic_J_labels_used_for_evaluation_only':True,'source_artifact_manifest_sha256':sha(SRC/'artifact_manifest.json'),
        'source_point_manifest_sha256':sha(SRC/'manifest_8192.jsonl'),'script_sha256':sha(Path(__file__)),
        'consumed_files_sha256':consumed,'source_files_unchanged':all(sha(Path(p))==h for p,h in consumed.items())})
    print(json.dumps(aggregate,ensure_ascii=True))
if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');main()
