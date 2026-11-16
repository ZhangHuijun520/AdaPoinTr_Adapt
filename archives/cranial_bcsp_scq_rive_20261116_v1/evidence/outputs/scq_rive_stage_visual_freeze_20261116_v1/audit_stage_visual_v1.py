from pathlib import Path
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
import json, hashlib, csv, io, math, tarfile, struct, zlib, time
import numpy as np

W = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
D = W / 'outputs/scq_rive_stage_visual_20261116_v1'
S = W / 'outputs/scq_rive_score_implementation_20261116_v1'
start = time.monotonic()
checks = {}
tracked = {}

def digest(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(1048576), b''):
            h.update(b)
    return h.hexdigest()

def snap(p):
    assert p.is_file() and not p.is_symlink(), str(p)
    st = p.stat()
    return dict(bytes=st.st_size, sha256=digest(p), mtime_ns=st.st_mtime_ns)

def track(p, expected=None):
    p = Path(p)
    v = snap(p)
    if expected:
        assert v['bytes'] == expected['bytes'] and v['sha256'] == expected['sha256'], str(p)
    tracked[str(p)] = v
    return p

def read(p):
    return json.loads(track(p).read_bytes())

def ok(k, cond):
    assert cond, k
    checks[k] = True

def close(a, b, atol=1e-9):
    return bool(np.allclose(a, b, rtol=1e-10, atol=atol))

manifest = read(D / 'artifact_manifest_v1.json')
actual = {p.relative_to(D).as_posix() for p in D.rglob('*') if p.is_file()}
expected = {x['path'] for x in manifest['files']}
ok('exact22_diagnostic_files_no_extra', actual == expected | {'artifact_manifest_v1.json'} and len(actual) == 22)
ok('exact_single_figures_directory', {p.relative_to(D).as_posix() for p in D.rglob('*') if p.is_dir()} == {'figures'})
for x in manifest['files']:
    p = D / x['path']
    assert p.resolve().is_relative_to(D.resolve())
    track(p, x)
ok('all21_manifest_entries_size_SHA256', True)
ok('manifest_total_bytes', sum(x['bytes'] for x in manifest['files']) == manifest['total_bytes'])

scope = read(D / 'fixed_visual_scope_v1.json')
r = read(D / 'stage_diagnostic_result_v1.json')
q = read(S / 'local_scoring_execution_request_v1.json')
scoreaudit = json.loads(track(scope['source_audit']['path'], scope['source_audit']).read_bytes())
ok('upstream_formal_score_audit_pass', scoreaudit['status'] == 'FORMAL_RIVE_TWO_ARM_POST_SCORE_FREEZE_AUDIT_PASS' and all(scoreaudit['checks'].values()))
for name, e in scoreaudit['inventory']['output'].items():
    track(S / 'unified_scores_v1' / name, e)
ok('all12_frozen_scoring_outputs_unchanged', True)
idx = json.loads(track(q['score_case_index']['path'], q['score_case_index']).read_bytes())
track(q['implementation']['metrics']['path'], q['implementation']['metrics'])
archive = track(q['archive_inputs']['SCQ_RIVE']['archive']['path'], q['archive_inputs']['SCQ_RIVE']['archive'])
risk = json.loads((S / 'unified_scores_v1/risk_transitions.json').read_bytes())
scored = [json.loads(x) for x in (S / 'unified_scores_v1/case_metrics.jsonl').read_text(encoding='utf-8').splitlines()]
sl = {(x['fold'], x['case_id'], x['arm']): x for x in scored}
new = {(f, x['case_id']) for f in ['C', 'D'] for x in risk[f]['RF-Requery_minus_RF-Static']['labels']['severe_geometry']['cases'] if x['new']}
got = {(x['fold'], x['case_id']) for x in scope['cases'] if x['role'] == 'new_severe'}
ok('all9_new_severe_exactly_from_frozen_risk', got == new and len(new) == 9)
controls = []
for f in ['C', 'D']:
    candidates = []
    for fold, cid, arm in sl:
        if fold == f and arm == 'RF-Requery':
            b, c = sl[f, cid, 'RF-Static']['metrics'], sl[f, cid, arm]['metrics']
            delta = c['E_P95_mm'] - b['E_P95_mm']
            if delta < 0 and not bool(c['severe_geometry']):
                candidates.append((delta, cid))
    delta, cid = min(candidates)
    item = [x for x in scope['cases'] if x['fold'] == f and x['role'] == 'fixed_improved_control']
    assert len(item) == 1 and item[0]['case_id'] == cid and close(item[0]['selection_delta_E_P95_mm'], delta)
    controls.append(dict(fold=f, case_id=cid, delta_E_P95_mm=delta))
ok('two_controls_independently_reselected_frozen_rule', True)
ok('11_unique_cases_and_result_scope_exact', len(scope['cases']) == 11 and len({(x['fold'],x['case_id']) for x in scope['cases']}) == 11 and r['cases'] == scope['cases'])
ok('two_arms_four_stages', scope['arms'] == ['RF-Static','RF-Requery'] and scope['stages'] == ['Q0','Q1','Q2','dense'])
roles = {(x['fold'],x['case_id']):x['role'] for x in scope['cases']}
records = r['records']
rl = {(x['fold'],x['case_id'],x['arm'],x['stage']):x for x in records}
expected_keys = {(f,c,a,s) for f,c in roles for a in scope['arms'] for s in scope['stages']}
ok('88_unique_complete_stage_records', len(records) == len(rl) == 88 and set(rl) == expected_keys)
for x in records:
    assert x['role'] == roles[x['fold'],x['case_id']]
    assert x['points'] == (8192 if x['stage'] == 'dense' else 256)
    for k,v in x.items():
        if isinstance(v, (float,int)):
            assert math.isfinite(v)
    assert all(0 <= x[k] <= 1 for k in ['E_cover2','J_cover2','reverse_outlier20'])
    assert all(x[k] >= 0 for k in ['centroid_offset_mm','radius_ratio','E_P95_mm','J_P95_mm','reverse_A2_P95_mm','CD_L1_mm'])
ok('stage_roles_counts_finiteness_metric_domains', True)

def compare_csv(name, rows):
    with (D / name).open(encoding='utf-8', newline='') as f:
        rr = list(csv.DictReader(f))
    flat = [{k:v for k,v in x.items() if k != 'centroid'} for x in rows]
    assert len(rr) == len(flat)
    for a,b in zip(rr,flat):
        assert set(a) == set(b)
        for k,v in b.items():
            assert close(float(a[k]), v, 1e-12) if isinstance(v,(int,float)) else a[k] == v
compare_csv('stage_metrics_v1.csv', records)
compare_csv('stage_transition_changes_v1.csv', r['transitions'])
ok('both_CSVs_exact_JSON_record_consistency', True)
ib = {(x['fold'],x['case_id'],x['arm']):x for x in idx['prediction_records']}
ic = {(x['fold'],x['case_id']):x for x in idx['cases']}
ok('22_exact_frozen_prediction_bindings', len(r['bindings']) == 22 and len({(x['fold'],x['case_id'],x['arm']) for x in r['bindings']}) == 22 and all(x == ib[x['fold'],x['case_id'],x['arm']] for x in r['bindings']))
gtmeans = {}
with tarfile.open(archive, 'r:gz') as tar:
    members = tar.getmembers()
    assert len({x.name for x in members}) == len(members)
    for f,c in roles:
        ci = ic[f,c]
        track(ci['reference']['path'], ci['reference'])
        pf = track(ci['point_file']['path'], ci['point_file'])
        with np.load(pf, allow_pickle=False) as z:
            # No NN scoring: only verify original coordinate/centroid/radius algebra.
            gt = z['implant'].astype(np.float64)*ci['normalization']['scale']+np.asarray(ci['normalization']['center'])
        gm = gt.mean(0); gr = np.sqrt(np.mean(np.sum((gt-gm)**2,axis=1))); gtmeans[f,c] = gm
        for arm in scope['arms']:
            b = ib[f,c,arm]; member = tar.getmember(b['member']); assert member.isfile()
            blob = tar.extractfile(member).read()
            assert len(blob) == b['bytes'] and hashlib.sha256(blob).hexdigest() == b['sha256']
            with np.load(io.BytesIO(blob), allow_pickle=False) as z:
                arrays = {k:z[k].copy() for k in z.files}
            assert np.allclose(arrays['Q0']+arrays['delta0'],arrays['Q1'],rtol=2e-5,atol=2e-6)
            assert np.allclose(arrays['Q1']+arrays['delta1'],arrays['Q2'],rtol=2e-5,atol=2e-6)
            for s,k in [('Q0','Q0'),('Q1','Q1'),('Q2','Q2'),('dense','prediction')]:
                a = arrays[k].reshape(-1,3).astype(np.float64)*ci['normalization']['scale']+np.asarray(ci['normalization']['center'])
                v = rl[f,c,arm,s]; mu=a.mean(0); radius=np.sqrt(np.mean(np.sum((a-mu)**2,axis=1)))
                assert len(a) == v['points'] and np.isfinite(a).all()
                assert close(mu,v['centroid']) and close(np.linalg.norm(mu-gm),v['centroid_offset_mm']) and close(radius/gr,v['radius_ratio'])
ok('22_archive_members_size_hash_and_stage_residual_equations', True)
ok('22_reference_point_bindings_and88_world_centroid_radius_checks', True)
mapping = [('E_P95_mm','E_P95_mm'),('J_P95_mm','J_P95_mm'),('E_cover2','E_coverage_2.0mm'),('J_cover2','J_coverage_2.0mm'),('CD_L1_mm','CD_L1_mm'),('reverse_outlier20','reverse_A2_outlier_20.0mm'),('centroid_offset_mm','centroid_offset_mm')]
for f,c in roles:
    for arm in scope['arms']:
        for a,b in mapping:
            assert close(rl[f,c,arm,'dense'][a], sl[f,c,arm]['metrics'][b],1e-10)
ok('154_dense_metric_values_equal_frozen_scoring', True)
tk=set()
for t in r['transitions']:
    f,c,arm = t['fold'],t['case_id'],t['arm']; sa,sb = t['transition'].split('->'); a,b=rl[f,c,arm,sa],rl[f,c,arm,sb]
    key=(f,c,arm,sa,sb);assert key not in tk;tk.add(key)
    assert t['role'] == roles[f,c]
    for k,v in t.items():
        if k.startswith('delta_'): assert close(v,b[k[6:]]-a[k[6:]])
    e=np.asarray(a['centroid'])-gtmeans[f,c];d=np.asarray(b['centroid'])-a['centroid']
    assert close(t['direction_term_2e_dot_delta_mm2'],2*float(e@d))
    assert close(t['step_squared_norm_mm2'],float(d@d))
    assert close(t['centroid_squared_change_mm2'],b['centroid_offset_mm']**2-a['centroid_offset_mm']**2)
    assert close(t['centroid_squared_change_mm2'],2*float(e@d)+float(d@d),1e-8)
ok('66_unique_complete_transitions_and_rederived_algebra', len(tk) == 66 and tk == {(f,c,a,s,t) for f,c in roles for a in scope['arms'] for s,t in zip(scope['stages'][:-1],scope['stages'][1:])})
counts={k:sum(rl[f,c,'RF-Requery','Q2'][k]>rl[f,c,'RF-Requery','Q1'][k] for f,c in new) for k in ['centroid_offset_mm','E_P95_mm','J_P95_mm']}
ok('report_7_3_5_transition_counts', list(counts.values()) == [7,3,5])
ok('all9_Q0_centroid_over40_and_above_Static', all(rl[f,c,'RF-Requery','Q0']['centroid_offset_mm']>40 and rl[f,c,'RF-Requery','Q0']['centroid_offset_mm']>rl[f,c,'RF-Static','Q0']['centroid_offset_mm'] for f,c in new))
ok('all9_dense_E_below_Q2', all(rl[f,c,'RF-Requery','dense']['E_P95_mm']<rl[f,c,'RF-Requery','Q2']['E_P95_mm'] for f,c in new))
report=(D/'RIVE_固定病例分阶段几何诊断报告_zh_v1.md').read_text(encoding='utf-8')
table=[l for l in report.splitlines() if l.startswith('| C／') or l.startswith('| D／')]
assert len(table)==11
for line,item in zip(table,scope['cases']):
    xs=[rl[item['fold'],item['case_id'],'RF-Requery',s] for s in scope['stages']]
    assert f"{item['fold']}／{item['case_id']}" in line
    for k in ['centroid_offset_mm','E_P95_mm']:assert ' → '.join(f'{x[k]:.3f}' for x in xs) in line
    assert f"{xs[-1]['J_P95_mm']:.3f}" in line and f"{100*xs[-1]['J_cover2']:.1f}%" in line
ok('report_all11_numeric_table_rows_match_full_precision_results', True)
ok('report_selection_causality_pointcount_limitations_disclosed', all(s in report for s in ['不能用于估计平均收益或失败率','256点','8192点','无法证明','未配准','临床安全']))

pngs=[]
for p in sorted(D.rglob('*.png')):
    blob=p.read_bytes();assert blob[:8]==b'\x89PNG\r\n\x1a\n';off=8;types=[]
    while off<len(blob):
        n=struct.unpack('>I',blob[off:off+4])[0];typ=blob[off+4:off+8];data=blob[off+8:off+8+n];crc=struct.unpack('>I',blob[off+8+n:off+12+n])[0]
        assert zlib.crc32(typ+data)&0xffffffff==crc;types.append(typ);off+=12+n
    assert off==len(blob) and types[0]==b'IHDR' and types[-1]==b'IEND' and b'IDAT' in types
    width,height=struct.unpack('>II',blob[16:24]);pngs.append(dict(path=p.relative_to(D).as_posix(),width=width,height=height))
ok('12_PNG_full_chunk_CRC_integrity',len(pngs)==12)
html=(D/'index.html').read_text(encoding='utf-8')
ok('11_panel_metadata_HTML_references_exact', len(r['panels'])==11 and all(p['fold']==c['fold'] and p['case_id']==c['case_id'] and p['role']==c['role'] and html.count('src="'+p['image']+'"')==1 and (D/p['image']).is_file() for p,c in zip(r['panels'],scope['cases'])))
source=(D/'run_fixed_stage_visual_v1.py').read_text(encoding='utf-8');summary=(D/'render_summary_v1.py').read_text(encoding='utf-8')
ok('plot_source_shared_bounds_equal_scale_colors_full_metric_contract',all(x in source for x in ["combined=np.concatenate([gt,*clouds.values()])","ax.set_aspect('equal')","vmin=0,vmax=40","x[::step,u]","stats(x,ref,gt,a2)","key[0]+'__'+key[1]+'.png'"]))
ok('summary_plot_reads_frozen_result_no_model', all(x in summary for x in ["stage_diagnostic_result_v1.json","centroid_offset_mm","E_P95_mm","RF-Static","RF-Requery"]))
ok('zero_forward_training_checkpoint_server_operations', all(v==0 for v in r['operations'].values()) and r['operations']==scope['operations'])
after={p:snap(Path(p)) for p in tracked}
ok('all_original_inputs_outputs_hash_size_mtime_unchanged_before_after', after==tracked)
result=dict(status='FORMAL_RIVE_STAGE_VISUAL_POST_DIAGNOSTIC_FREEZE_AUDIT_PASS',checks=checks,check_count=len(checks),counts=dict(cases=11,prediction_members=22,stage_rows=88,transitions=66,case_panels=11,summary_images=1),descriptive_increases=counts,controls=controls,images=pngs,inventory=tracked,seconds=time.monotonic()-start,operations=dict(forward=0,training=0,checkpoint_loads=0,server_calls=0,nearest_distance_rescoring=0),limitations=['No nearest-neighbor distance rescoring; E/J and CD consistency verified against frozen scoring and existing diagnostic records.','PNG integrity and renderer/source bindings are verified; no claim of automatic pixel-to-point semantic proof.','No new scientific efficacy or causal claim.'])
(OUT/'audit_verification_v1.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:result[k] for k in ['status','check_count','counts','seconds']},ensure_ascii=False))
