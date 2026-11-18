"""Descriptive analysis of the frozen G1/G2 coarse and dense predictions."""
import csv
import hashlib
import importlib.util
import io
import json
import tarfile
from collections import Counter
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
OUT = HERE.parent
SCORE = OUT / 'spcg_score_implementation_20261117_v1'
EPS = 1e-9


def load(path):
    return json.loads(Path(path).read_bytes())


def sha(blob):
    return hashlib.sha256(blob).hexdigest()


def exact(record):
    path = Path(record['path'])
    assert path.stat().st_size == record['bytes'], path
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(4194304), b''):
            digest.update(block)
    assert digest.hexdigest() == record['sha256'], path
    return path


def surface_stats(distances, weights):
    order = np.argsort(distances, kind='stable')
    cumulative = np.cumsum(weights[order], dtype=np.float64)
    return float(distances[order[np.searchsorted(cumulative,.95*cumulative[-1])]])


def case_metrics(coarse, dense, ref, tree, frozen):
    coarse_pose = frozen['stage_geometry']['coarse']
    score = frozen['metrics']
    result = {}
    target = np.array(frozen['position_shape']['GT8192_centroid_mm'])
    for stage, points, expected in [('coarse',coarse,coarse_pose['centroid_offset_mm']),
                                    ('dense',dense,score['centroid_offset_mm'])]:
        value = float(np.linalg.norm(points.mean(0)-target))
        assert np.isclose(value,expected,rtol=1e-11,atol=1e-10)
        result[stage+'_centroid_mm'] = value
    far_coarse = tree.query(coarse)[0] > 20
    far_dense = (tree.query(dense)[0] > 20).reshape(256,32)
    assert far_dense.mean() == score['reverse_A2_outlier_20.0mm']
    result.update(coarse_far_pct=100*far_coarse.mean(),dense_far_pct=100*far_dense.mean(),
                  dense_far_from_far_parent_pct=100*(far_dense & far_coarse[:,None]).mean(),
                  dense_far_from_near_parent_pct=100*(far_dense & ~far_coarse[:,None]).mean(),
                  dense_near_from_far_parent_pct=100*(~far_dense & far_coarse[:,None]).mean())
    d0 = cKDTree(coarse).query(ref['a_centers'])[0]
    d1 = cKDTree(dense).query(ref['a_centers'])[0]
    for region, mask in [('E',~ref['a_is_j']),('J',ref['a_is_j'])]:
        w = ref['a_weights'][mask]
        before, after = d0[mask]<=2,d1[mask]<=2
        for stage, dist, covered in [('coarse',d0,before),('dense',d1,after)]:
            result[f'{region}_{stage}_P95_mm'] = surface_stats(dist[mask],w)
            result[f'{region}_{stage}_coverage_pct'] = 100*float(np.average(covered,weights=w))
        assert np.isclose(result[f'{region}_dense_P95_mm'],score[f'{region}_P95_mm'],rtol=1e-11,atol=1e-10)
        assert np.isclose(result[f'{region}_dense_coverage_pct'],100*score[f'{region}_coverage_2.0mm'],atol=1e-10)
        for label, group in dict(retained=before&after,recovered=~before&after,lost=before&~after,missed_both=~before&~after).items():
            result[f'{region}_{label}_pct'] = 100*float(np.average(group,weights=w))
        assert np.isclose(sum(result[f'{region}_{k}_pct'] for k in ('retained','recovered','lost','missed_both')),100)
    return result


def dump_csv(name, rows):
    with (HERE/name).open('x',encoding='utf-8-sig',newline='') as stream:
        writer = csv.DictWriter(stream,fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def paired_summary(rows, keys):
    return {k: dict(mean=float(np.mean([r[k] for r in rows])),
                    median=float(np.median([r[k] for r in rows])),
                    positive=sum(int(r[k]>EPS) for r in rows), negative=sum(int(r[k]<-EPS) for r in rows),
                    tied=sum(int(abs(r[k])<=EPS) for r in rows)) for k in keys}


def main():
    request_path = SCORE/'SPCG_local_scoring_execution_request_v1.json'
    audit = load(OUT/'spcg_score_freeze_20261117_v1/audit_verification_v1.json')
    assert audit['status']=='FORMAL_SPCG_THREE_ARM_TWOFOLD_POST_SCORE_FREEZE_AUDIT_PASS'
    assert sha(request_path.read_bytes()) == audit['request_sha256']
    request = load(request_path)
    score_path = SCORE/'unified_scores_v1/case_metrics.jsonl'
    exact(dict(audit['inventory']['output'][score_path.name],path=str(score_path)))
    scores = {(r['fold'],r['case_id'],r['arm']):r for r in map(json.loads,score_path.read_bytes().splitlines()) if r['arm'] in ('G1','G2')}
    index = load(exact(request['score_case_index']))
    selected = [r for r in index['prediction_records'] if r['arm'] in ('G1','G2')]
    members = {r['member']:r for r in selected}
    assert len(selected)==len(members)==len(scores)==420
    pairs = {(r['fold'],r['case_id']) for r in selected}
    cases = {(r['fold'],r['case_id']):r for r in index['cases']}
    assert pairs==cases.keys()
    spec = importlib.util.spec_from_file_location('frozen_spcg_metric',exact(request['implementation']['metrics']))
    metric = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(metric)
    archive = request['archive_inputs']['SPCG']['archive']
    blobs = {}
    with tarfile.open(exact(archive),'r|gz') as tar:
        for member in tar:
            if member.name in members:
                expected = members[member.name]
                assert member.name not in blobs and member.isfile() and member.size==expected['bytes']
                blob = tar.extractfile(member).read()
                assert len(blob)==member.size and sha(blob)==expected['sha256']
                blobs[member.name]=blob
    assert blobs.keys()==members.keys()
    by_case = {(r['fold'],r['case_id'],r['arm']):r for r in selected}
    arm_rows, paired_rows, source_rows = [], [], []
    summaries = {}
    for fold in ('C','D'):
        fold_pairs = sorted(k for k in pairs if k[0]==fold)
        sources = Counter(cases[k]['source_id'] for k in fold_pairs)
        assert len(fold_pairs)==105 and len(sources)==21 and set(sources.values())=={5}
        for key in fold_pairs:
            case = cases[key]
            with np.load(exact(case['reference']),allow_pickle=False) as data:
                ref = {k:data[k] for k in data.files}
            a2, _, _ = metric.a2_reference(ref)
            tree = cKDTree(a2)
            metrics, risks = {}, {}
            for arm in ('G1','G2'):
                k = (*key,arm)
                with np.load(io.BytesIO(blobs[by_case[k]['member']]),allow_pickle=False) as data:
                    coarse, dense = data['coarse'], data['prediction']
                assert coarse.shape==(256,3) and dense.shape==(8192,3)
                assert all(a.dtype==np.float32 and np.isfinite(a).all() for a in (coarse,dense))
                risk = scores[k]['risk_labels']['severe_geometry']
                result = case_metrics(metric.world_points(coarse,case['normalization']),
                                      metric.world_points(dense,case['normalization']),ref,tree,scores[k])
                metrics[arm] = result
                risks[arm] = risk
                arm_rows.append(dict(fold=fold,case_id=key[1],source_id=case['source_id'],arm=arm,dense_severe=risk,**result))
            deltas = {k:metrics['G2'][k]-v for k,v in metrics['G1'].items()}
            paired_rows.append(dict(fold=fold,case_id=key[1],source_id=case['source_id'],
                                    new_dense_severe=risks['G2'] and not risks['G1'],
                                    rescued_dense_severe=risks['G1'] and not risks['G2'],**deltas))
        fold_rows = [r for r in paired_rows if r['fold']==fold]
        source_start = len(source_rows)
        for source in sorted(sources):
            rr = [r for r in fold_rows if r['source_id']==source]
            averaged = {k:float(np.mean([r[k] for r in rr])) for k in deltas}
            source_rows.append(dict(fold=fold,source_id=source,cases=len(rr),**averaged))
        affected = [r for r in fold_rows if r['E_dense_P95_mm']>EPS]
        new_severe = [r for r in fold_rows if r['new_dense_severe']]
        old = {(r['case_id'],r['arm']):r for r in arm_rows if r['fold']==fold}
        summaries[fold] = dict(
            n=105,sources=21,source_equal_deltas=paired_summary(source_rows[source_start:], list(deltas)),
            E_dense_P95_worse=len(affected),
            E_worse_at_both_stages=sum(r['E_coarse_P95_mm']>EPS for r in affected),
            J_dense_P95_worse=sum(r['J_dense_P95_mm']>EPS for r in fold_rows),
            J_worse_at_both_stages=sum(r['J_dense_P95_mm']>EPS and r['J_coarse_P95_mm']>EPS for r in fold_rows),
            worsened_subset_case_deltas=paired_summary(affected,list(deltas)),
            new_severe=[dict(case_id=r['case_id'],G1=old[r['case_id'],'G1'],G2=old[r['case_id'],'G2']) for r in new_severe],
            rescued_severe=sum(r['rescued_dense_severe'] for r in fold_rows))
    assert len(arm_rows)==420 and len(paired_rows)==210 and len(source_rows)==42
    assert not {r['source_id'] for r in source_rows if r['fold']=='C'} & {r['source_id'] for r in source_rows if r['fold']=='D'}
    dump_csv('case_arm_geometry.csv',arm_rows)
    dump_csv('paired_case_G2_minus_G1.csv',paired_rows)
    dump_csv('paired_source_G2_minus_G1.csv',source_rows)
    with (HERE/'summary_v1.json').open('x',encoding='utf-8') as stream:
        json.dump(dict(folds=summaries,cases=210,predictions=420,stages=840,source_pairs=42,
                       archive=archive,original_score_request_sha256=audit['request_sha256'],
                       new_forward=0,new_training=0,comparison_eps=EPS),stream,indent=2,allow_nan=False)
    print('Verified 420 predictions, 840 stages, 210 case pairs and 42 source pairs.')


if __name__=='__main__':
    main()
