"""Bounded descriptive review of frozen score records. Stdlib only; no inference."""
import csv
import hashlib
import io
import json
import math
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCORES = ROOT / 'unified_scores_v1'
AUDIT = ROOT / 'post_scoring_freeze_audit_20261107_v1' / 'audit_report_v1.json'
DEST = ROOT / 'coarse_dense_regression_review_v1'
assert not DEST.exists(), 'single descriptive review destination already exists'
audit = json.loads(AUDIT.read_text(encoding='utf-8'))
assert audit['status'] == 'FORMAL_H2_THREE_ARM_POST_SCORING_FREEZE_AUDIT_PASS'


def fingerprint(p):
    b = p.read_bytes()
    return dict(path=str(p.resolve()), bytes=len(b), sha256=hashlib.sha256(b).hexdigest())


def verify_inputs():
    for expected in audit['output_manifest']:
        actual = fingerprint(Path(expected['path']))
        assert actual == expected, str(actual)


verify_inputs()
rows = [json.loads(s) for s in (SCORES / 'case_metrics.jsonl').read_text(encoding='utf-8').splitlines()]
models = [r for r in rows if r['arm'] in ['M0', 'H2_AUX', 'H2_COUPLE']]
assert len(models) == 630
index = {(r['fold'], r['case_id'], r['arm']): r for r in models}
assert len(index) == 630
risks = json.loads((SCORES / 'risk_transitions.json').read_text(encoding='utf-8'))
selected = {}
for fold in ['C', 'D']:
    for baseline in ['H2_AUX', 'M0']:
        table = risks[fold]['H2_COUPLE_minus_' + baseline]['labels']['severe_geometry']
        found = []
        for case in table['cases']:
            if case['new']:
                key = (fold, case['case_id'])
                selected.setdefault(key, []).append(baseline)
                found.append(key)
        assert len(found) == table['new']
assert len(selected) == 8

flat = []
for r in models:
    stage, pose, m = r['stage_geometry'], r['position_shape'], r['metrics']
    coarse, dense = stage['coarse'], stage['dense']
    shift = math.sqrt(sum(v*v for v in stage['mean_dense_minus_coarse_mm']))
    gt_radius = pose['GT8192_radius_gyration_mm']
    energy = stage['offset_centered_variance_mm2']
    cross = stage['cross_term_twice_covariance_mm2']
    residual = dense['prediction_radius_gyration_mm']**2 - coarse['radius_gyration_mm']**2 - energy - cross
    assert abs(residual) < 1e-7
    # No new scientific tolerance: algebra/serialization consistency only.
    assert abs(dense['centroid_offset_mm']-coarse['centroid_offset_mm']) <= shift + 1e-7
    assert r['risk_labels']['severe_geometry'] == (m['E_P95_mm'] > 20 or m['J_coverage_2.0mm'] == 0)
    v = dict(fold=r['fold'], case_id=r['case_id'], source_id=r['source_id'], arm=r['arm'],
             selected_new_severe_case=(r['fold'], r['case_id']) in selected,
             new_severe_against=';'.join(selected.get((r['fold'], r['case_id']), [])),
             severe=r['risk_labels']['severe_geometry'],
             E_P95_mm=m['E_P95_mm'], J_P95_mm=m['J_P95_mm'],
             E_Cover2=m['E_coverage_2.0mm'], J_Cover2=m['J_coverage_2.0mm'],
             outlier20_fraction=m['reverse_A2_outlier_20.0mm'],
             coarse_center_error_mm=coarse['centroid_offset_mm'], dense_center_error_mm=dense['centroid_offset_mm'],
             dense_minus_coarse_center_shift_mm=shift,
             coarse_radius_ratio=coarse['radius_gyration_ratio'], dense_radius_ratio=dense['radius_gyration_ratio'],
             coarse_compact=coarse['radius_gyration_ratio'] < .9,
             dense_compact=dense['radius_gyration_ratio'] < .9,
             coarse_position_tail=coarse['centroid_offset_mm'] > 20,
             dense_position_tail=dense['centroid_offset_mm'] > 20,
             radius_change_ratio=(dense['prediction_radius_gyration_mm']-coarse['radius_gyration_mm'])/gt_radius,
             offset_centered_variance_mm2=energy, twice_cross_covariance_mm2=cross,
             radius_squared_identity_residual_mm2=residual,
             coarse_tensor_saved=coarse['tensor_saved'])
    if 'H2' in stage:
        v.update({'H2_'+k: stage['H2'][k] for k in ['scale', 'raw_abs_log_radius_error', 'used_abs_log_radius_error', 'raw_centroid_offset_mm', 'used_centroid_offset_mm']})
    flat.append(v)

summary = {}
numeric = ['coarse_center_error_mm', 'dense_center_error_mm', 'dense_minus_coarse_center_shift_mm', 'coarse_radius_ratio', 'dense_radius_ratio', 'offset_centered_variance_mm2', 'twice_cross_covariance_mm2']
for fold in ['C', 'D']:
    summary[fold] = {}
    for arm in ['M0', 'H2_AUX', 'H2_COUPLE']:
        part = [v for v in flat if v['fold'] == fold and v['arm'] == arm]
        assert len(part) == 105
        summary[fold][arm] = dict(cases=105, sources=21,
            means={k: statistics.mean(v[k] for v in part) for k in numeric},
            medians={k: statistics.median(v[k] for v in part) for k in numeric},
            coarse_position_tail=sum(v['coarse_position_tail'] for v in part),
            dense_position_tail=sum(v['dense_position_tail'] for v in part),
            coarse_compact=sum(v['coarse_compact'] for v in part), dense_compact=sum(v['dense_compact'] for v in part),
            new_compact_after_dense=sum(not v['coarse_compact'] and v['dense_compact'] for v in part),
            rescued_compact_after_dense=sum(v['coarse_compact'] and not v['dense_compact'] for v in part),
            dense_radius_smaller=sum(v['radius_change_ratio'] < 0 for v in part))
focus = [v for v in flat if v['selected_new_severe_case']]
assert len(focus) == 24
couple = [v for v in focus if v['arm'] == 'H2_COUPLE']
counts = dict(unique_cases=8, C_cases=3, D_cases=5, sources=len({(v['fold'],v['source_id']) for v in couple}),
    new_against_AUX=sum('H2_AUX' in v['new_severe_against'] for v in couple),
    new_against_M0=sum('M0' in v['new_severe_against'] for v in couple),
    coarse_position_tail=sum(v['coarse_position_tail'] for v in couple),
    dense_position_tail=sum(v['dense_position_tail'] for v in couple),
    coarse_compact=sum(v['coarse_compact'] for v in couple),
    dense_compact=sum(v['dense_compact'] for v in couple),
    zero_J_cover=sum(v['J_Cover2'] == 0 for v in couple),
    coarse_tensor_saved=sum(v['coarse_tensor_saved'] for v in couple),
    dense_radius_smaller=sum(v['radius_change_ratio'] < 0 for v in couple))
assert counts['coarse_position_tail'] == 5 and counts['coarse_compact'] == 7
lines = ['# H2新增退化病例与coarse／dense阶段复盘 v1', '', '日期：2026-11-07。范围：既有冻结评分中的630行模型记录及210病例的配对风险记录。无服务器操作、forward、训练、点集重新评分、Oracle配准、参数扫描或正式gate。', '', '## 1. 研究问题与病例选取', '', '目标是判断已观察到的H2退化在coarse输出中是否已有可见位置／范围异常，以及dense相对位移是否进一步改变这些异常。本报告不把相关性解释为因果。', '', '全量背景使用C/D各105例、每例M0/AUX/COUPLE的记录。重点病例由冻结严重几何定义（E P95>20 mm或J Cover2=0）确定：COUPLE相对AUX新增6例，相对M0新增4例，重叠2例，合并8例、7个来源（C3例来自2来源，D5例来自5来源）。不追加最差病例筛选，不更改阈值。重点是事后失败分层，不能当作无偏泛化样本。', '', '全部8例保留3臂对照，共24行；同时提供630行全量阶段指标，避免把选定失败样本代表全体。', '', '## 2. 证据能回答什么', '', 'coarse是模型实际使用的256个中心；dense为8192个最终点。两者均在原始world-mm坐标、无配准。所有病例有同一次forward保存的质心、回转半径与位移汇总；重点8例中仅1例有保存的COUPLE coarse点张量，其余7例不能据此绘制实际coarse空间点形状或计算coarse接口距离。', '', '因此可定位“到coarse输出时已出现的位置／范围异常”，但不能确定异常更早起源于encoder、coarse坐标头、query特征或训练梯度，也不能从半径与质心认证局部切壁形状。未执行delta置零或供体置换，不能将两套训练权重的差异归因为单次缩放。', '', '```mermaid', 'flowchart LR', '  accTitle: 已有证据的阶段复盘', '  accDescr: 从冻结风险记录选出全部新增失败病例，比较实际coarse与dense统计；不执行模型或因果干预。', '  A[冻结风险与病例评分] --> B[8例新增严重退化]', '  B --> C[coarse位置与范围]', '  C --> D[dense位移与半径变化]', '  D --> E[最终覆盖与离群]', '```', '', '## 3. 全量阶段统计', '', '下表每折105病例均值；因每来源均为5缺损，此处与来源等权均值相等。紧缩计数仅沿用半径比<0.9的诊断定义，非临床阈值。', '', '| 折／臂 | coarse质心误差 mm | dense质心误差 mm | 质心位移模长 mm | coarse半径比 | dense半径比 | 紧缩病例 coarse→dense |', '|---|---:|---:|---:|---:|---:|---|']
for f, arms in summary.items():
    for a,v in arms.items():
        m=v['means']; lines.append(f"| {f}/{a} | {m['coarse_center_error_mm']:.3f} | {m['dense_center_error_mm']:.3f} | {m['dense_minus_coarse_center_shift_mm']:.3f} | {m['coarse_radius_ratio']:.3f} | {m['dense_radius_ratio']:.3f} | {v['coarse_compact']}→{v['dense_compact']} |")
lines += ['', 'COUPLE的平均dense质心误差两折均小于coarse，不能说dense在整体上制造了位置偏差。相对AUX，COUPLE在C折平均位置改善、D折接近，但接口表现仍不稳定。COUPLE的紧缩病例C折66→73、D折47→55；dense可能加重一部分范围不足，但不能据此称其为全部退化的唯一来源。', '', '## 4. 全部新增严重退化病例', '', '下表仅列COUPLE，完整三臂逐例表见 `selected_case_three_arm_stage_metrics_v1.csv`。半径比为相对GT的回转半径，不能替代形状覆盖。', '', '| 折／病例 | 相对谁新增 | E/J P95 mm | J Cover2 % | >20mm离群 % | 质心误差 coarse→dense mm | 半径比 coarse→dense |', '|---|---|---|---:|---:|---|---|']
for v in sorted(couple,key=lambda x:(x['fold'],x['case_id'])):
    lines.append(f"| {v['fold']}/{v['case_id']} | {v['new_severe_against']} | {v['E_P95_mm']:.2f}/{v['J_P95_mm']:.2f} | {100*v['J_Cover2']:.2f} | {100*v['outlier20_fraction']:.2f} | {v['coarse_center_error_mm']:.2f}→{v['dense_center_error_mm']:.2f} | {v['coarse_radius_ratio']:.3f}→{v['dense_radius_ratio']:.3f} |")
lines += ['', '### 4.1 大幅位置偏移在coarse已有证据', '', '8例中5例在coarse阶段质心误差已>20 mm，dense后仍>20 mm；dense不是这些大偏移首次可观察到的位置。', '', '- C/train__053__frontoorbital：COUPLE为96.17→96.88 mm，几乎未纠正；最终E P95=92.13 mm、J Cover2=0、远端离群100%。AUX质心为32.61→27.35 mm、E P95=11.68 mm，而M0本身也严重失败。它不是“所有基线都正常”的病例，但COUPLE较AUX显著回退。', '- C/train__025__parietotemporal及random_2：COUPLE coarse质心分别42.20、37.95 mm，dense仍40.05、30.85 mm。AUX更差，M0未达严重标记。因此这两例同时说明COUPLE缓解了AUX部分失败，却未恢复到M0水平；二者来自同一来源，不能当作两个独立患者证据。', '- D/train__079__frontoorbital及train__087__random_1：COUPLE coarse质心59.30、37.24 mm，dense后56.75、34.83 mm。前者M0也失败；后者相对AUX和M0均新增严重标记，且半径比0.942→0.926并不紧缩，说明单一半径诊断不能覆盖位置失败。', '', '### 4.2 另外3例不属于>20 mm质心偏移主导的同一种表型', '', '- D/train__004__random_2：COUPLE质心14.52→13.30 mm、半径比0.629→0.636；E P95=22.93 mm，但>20 mm离群比例为0。这与“预测没有广泛飞离骨块，却未覆盖足够GT范围”的表型相容。AUX半径比0.696→0.700、E P95=12.21 mm。不能用无远端离群推断覆盖正确。', '- D/train__060__bilateral：COUPLE质心14.70→14.59 mm，半径比0.640→0.643，E P95=21.19 mm、远端离群0。AUX质心接近而半径比更大（0.683→0.687），E P95=17.19 mm；M0已略过20 mm阈值。这里存在范围/空间分布问题，简单修正质心未必足够。', '- D/train__022__random_1：COUPLE质心19.23→14.21 mm得到改善，但J Cover2仍为0，半径比0.745→0.725，E P95=11.44 mm。这是接口未被覆盖的严重标记，不是E P95>20 mm导致；M0也有J Cover2=0。仅靠最终质心改善不能证明切壁吻合。', '', '这3例并非已被证明“纯形状错误”；仍可能包含方向、局部位置和缺损几何差异。现有汇总不足以分离这些因素，只能拒绝“一律由大幅整体平移解释”。', '', '## 5. dense相对位移：代数证据而非因果归因', '', '对每个dense点减去其所属coarse中心得到位移Δ，已保存的汇总满足：', '', '$$r_{dense}^2=r_{coarse}^2+\mathrm{Var}(\Delta)+2\,\mathrm{Cov}(q,\Delta).$$', '', '位移方差非负，而交叉项可能为负，因此位移幅度较大不代表覆盖会扩大。本次630行独立核对半径平方恒等式，以及质心误差变化不大于质心位移模长的三角不等式；只校验保存记录的代数一致性。', '', '重点8例的交叉项均为负，但仅3例dense回转半径小于coarse，其余5例略大。因此不能把“负交叉项”误写成“8例全部被dense收缩”。8例中7例在coarse已满足紧缩标记，dense后仍为7例；第8例是位置失败且半径比未紧缩。dense有局部加重作用的证据，但它未普遍制造这些重点病例的范围异常。', '', 'COUPLE实际缩放保持coarse质心不变；因此coarse大幅质心偏移不可能由这一次围绕自身中心的缩放直接平移产生。两训练臂的coarse位置差异仍可能来自辅助目标与重建梯度共同作用后的参数变化。没有干预不能分辨这些路径。', '', '## 6. 结论与下一阶段方向', '', '当前最可靠的结论是：**多数新增严重退化的可见位置／范围异常到coarse输出时已经存在，dense通常未充分纠正；并非全部失败都是整体位置错误，也并非统一由dense相对位移制造。**', '', '据此建议停止把单一全局半径修正作为当前主要改进路线，保留M0比较基线，收束当前H2版本；不扫描尺度、权重或增加训练。若提出下一项最小假设，应优先讨论“由输入局部几何约束的空间位置与各向异性范围如何同时进入生成路径”，并将接口覆盖列为独立验证目标。该方向尚未被本次观察证明有效，不能直接进入实现或训练。', '', '本轮已足够否定“只要把全局尺度拟合好就能可靠改善补全”的强解释。现阶段不必为收束阴性候选追加GPU干预。如果确有必要区分同一COUPLE模型对delta的瞬时依赖，可另行讨论原协议20次干预；这不是本轮完成的内容，也不是自动准入。', '', '现有记录尚不能证明：coarse各点的接口覆盖、内外板分配、具体远端离群空间方向、query特征是否充分利用输入。若下一步需要这些结论，应先审阅已有保存点集的可视化范围；不能把缺失证据写成已证实根因。', '', '## 7. 局限与可追溯性', '', '开发集重复使用、每折单seed和有限梯度非确定性限制因果与泛化结论。新增失败阈值会产生边界效应；完整连续指标和三臂数据随报告保存。未作显著性检验、患者独立性假设或临床安全认证。', '', '- `all_model_stage_metrics_v1.csv`：全部630行阶段指标。', '- `selected_case_three_arm_stage_metrics_v1.csv`：8病例×3臂，共24行。', '- `review_values_v1.json`：折/臂汇总、全部重点病例和选择规则。', '- `review_receipt_v1.json`：输入指纹、检查结果、执行边界。', '- `artifact_manifest_v1.json`：本次所有产物和脚本的SHA256。', '']
verify_inputs()
DEST.mkdir()


def write_json(name, obj):
    (DEST/name).write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n',encoding='utf-8')


def write_csv(name, records):
    fields = list(dict.fromkeys(k for r in records for k in r))
    s=io.StringIO(newline=''); writer=csv.DictWriter(s,fieldnames=fields)
    writer.writeheader();writer.writerows(records)
    (DEST/name).write_text(s.getvalue(),encoding='utf-8-sig',newline='')


write_csv('all_model_stage_metrics_v1.csv',flat)
write_csv('selected_case_three_arm_stage_metrics_v1.csv',focus)
write_json('review_values_v1.json',dict(status='FROZEN_RECORD_DESCRIPTIVE_REVIEW_COMPLETE', selection='union of COUPLE newly severe vs AUX and vs M0; fixed existing risk definitions',counts=counts,fold_arm_summary=summary,selected_three_arm_records=focus,formal_gate=False))
(DEST/'H2新增退化病例与coarse_dense阶段复盘_zh_v1.md').write_text('\n'.join(lines),encoding='utf-8')
verify_inputs()
write_json('review_receipt_v1.json',dict(status='READ_ONLY_INPUT_REVIEW_COMPLETE', counts=counts,
    checks=dict(formal_audit_PASS=True,all12_score_file_hashes_verified_before_and_after=True,model_rows630=True,unique_new_cases8=True,three_arm_focus_rows24=True,all630_radius_and_center_identities=True),
    inputs=[fingerprint(AUDIT),fingerprint(SCORES/'case_metrics.jsonl'),fingerprint(SCORES/'risk_transitions.json')],
    source_bytes_modified=False,model_imports=0,server_calls=0,forward=0,training=0,geometry_rescoring=0,oracle_registration=0,bootstrap=0,formal_gate=False))
paths=sorted(DEST.iterdir())+[Path(__file__).resolve()]
write_json('artifact_manifest_v1.json',[fingerprint(p) for p in paths])
for e in json.loads((DEST/'artifact_manifest_v1.json').read_text(encoding='utf-8')):
    assert fingerprint(Path(e['path'])) == e
assert len(list(csv.DictReader(io.StringIO((DEST/'all_model_stage_metrics_v1.csv').read_text(encoding='utf-8-sig'))))) == 630
assert len(list(csv.DictReader(io.StringIO((DEST/'selected_case_three_arm_stage_metrics_v1.csv').read_text(encoding='utf-8-sig'))))) == 24
print(json.dumps(dict(status='COMPLETE',counts=counts,output=str(DEST)),ensure_ascii=True))
