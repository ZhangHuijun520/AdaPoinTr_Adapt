"""Describe already audited saved scores; no geometry scoring or model execution."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'unified_scores_v1'
DEST = ROOT / 'post_scoring_freeze_audit_20261107_v1'
AUDIT = DEST / 'audit_report_v1.json'
audit = json.loads(AUDIT.read_text(encoding='utf-8'))
assert audit['status'] == 'FORMAL_H2_THREE_ARM_POST_SCORING_FREEZE_AUDIT_PASS'
paired = json.loads((OUT / 'paired_comparison.json').read_text(encoding='utf-8'))
risk = json.loads((OUT / 'risk_transitions.json').read_text(encoding='utf-8'))
rows = [json.loads(s) for s in (OUT / 'case_metrics.jsonl').read_text(encoding='utf-8').splitlines()]
keys = ['E_P95_mm', 'J_P95_mm', 'CD_L1_mm', 'E_coverage_2.0mm', 'J_coverage_2.0mm', 'reverse_A2_outlier_20.0mm', 'centroid_offset_mm']
derived = {'status': 'DESCRIPTIVE_INTERPRETATION_OF_FROZEN_SCORES', 'audit_sha256': hashlib.sha256(AUDIT.read_bytes()).hexdigest(), 'fold_arm_means': {}, 'frontoorbital': {}, 'H2_offline_radius': {}, 'formal_gate': False, 'new_forward': 0, 'geometry_rescoring': False}
lines = ['# H2／M0 两折统一评分：正式冻结审计与科研结果解读 v1', '', '日期：2026-11-07。仅解读既有冻结评分；本报告不运行模型、重算几何距离、执行统计显著性检验或正式 gate。', '', '## 一、审计结论与证据范围', '', '正式只读评分后冻结审计通过，21项检查全部满足。执行退出码为0，无超时、自动重试或续跑。核验210个病例、42个来源（每折21来源，每来源5种缺损）、630行模型评分及420行共享控制，共1050行病例评分、210行来源评分、6组折内配对汇总和630行病例差值。', '', '独立重算保存指标的来源均值、三组配对差值、缺损类型汇总、风险转移及CSV/JSON一致性；630行M0和共享控制与既有P1冻结评分一致。重新核验请求、实现、P3、人工CPU证据、输入归档与产物哈希；审计读取并计算指纹569,510,238字节。未解码点集、重算最近邻距离或导入模型。', '', '评分request SHA256：`' + audit['request_sha256'] + '`。正式审计JSON SHA256：`' + derived['audit_sha256'] + '`。各产物完整哈希见同目录 `audit_report_v1.json` 的 `output_manifest`；全部读取对象见 `all_read_file_manifest`。', '', '## 二、比较设计与指标口径', '', 'M0为既有Mamba基线；H2-AUX只增加尺度残差辅助学习；H2-COUPLE在同类辅助学习外，将预测尺度以有界、保持coarse质心的方式送入生成路径。主比较为COUPLE−AUX，另列COUPLE−M0和AUX−M0。8k输入／8k输出、同折初始化和批次顺序、3900步合同保持冻结。', '', '表中为先在每来源内平均5种缺损，再在每折21个来源间等权平均。E为未知原始表面，J为共享切壁接口；P95和CD单位mm，越低越好；Cover@2mm越高越好，远端离群比例越低越好。P95列是病例P95的来源等权均值，不能解释为所有点合并后的总体P95。', '', '## 三、原始模型性能', '', '| 折 | 模型 | E P95 mm | J P95 mm | CD-L1 mm | E Cover2 % | J Cover2 % | >20mm离群 % | 质心偏差 mm |', '|---|---|---:|---:|---:|---:|---:|---:|---:|']
for fold in ['C', 'D']:
    derived['fold_arm_means'][fold] = {}
    derived['frontoorbital'][fold] = {}
    derived['H2_offline_radius'][fold] = {}
    for arm in ['M0', 'H2_AUX', 'H2_COUPLE']:
        subset = [r for r in rows if r['fold'] == fold and r['arm'] == arm]
        assert len(subset) == 105
        means = {k: sum(r['metrics'][k] for r in subset) / len(subset) for k in keys}
        derived['fold_arm_means'][fold][arm] = means
        values = [means[k] * (100 if 'coverage' in k or 'outlier' in k else 1) for k in keys]
        lines.append('| ' + fold + ' | ' + arm + ' | ' + ' | '.join(f'{v:.3f}' for v in values) + ' |')
        front = [r for r in subset if 'frontoorbital' in r['case_id']]
        assert len(front) == 21
        derived['frontoorbital'][fold][arm] = {k: sum(r['metrics'][k] for r in front) / len(front) for k in keys}
        if arm != 'M0':
            h = [r['stage_geometry']['H2'] for r in subset]
            derived['H2_offline_radius'][fold][arm] = {k: sum(r[k] for r in h) / len(h) for k in ['scale', 'raw_abs_log_radius_error', 'used_abs_log_radius_error', 'abs_delta_target_error']}
            derived['H2_offline_radius'][fold][arm]['scale_range'] = [min(r['scale'] for r in h), max(r['scale'] for r in h)]
lines += ['', '## 四、主比较：COUPLE相对AUX', '', '| 折 | ΔE P95 mm | E改善／退化来源 | ΔJ P95 mm | ΔCD mm | ΔE Cover2 百分点 | ΔJ Cover2 百分点 |', '|---|---:|---|---:|---:|---:|---:|']
for f in ['C', 'D']:
    m = paired['comparison'][f]['H2_COUPLE_minus_H2_AUX']['metrics']
    d = lambda k: m[k]['mean_delta_b_minus_a']
    lines.append(f"| {f} | {d('E_P95_mm'):.3f} | {m['E_P95_mm']['improved_sources']}／{m['E_P95_mm']['worse_sources']} | {d('J_P95_mm'):.3f} | {d('CD_L1_mm'):.3f} | {100*d('E_coverage_2.0mm'):.3f} | {100*d('J_coverage_2.0mm'):.3f} |")
lines += ['', 'C折有部分总体收益，但D折E/J P95反向变化，两折J Cover2均下降。因此“尺度耦合稳定改善未知表面与接口”的假设未获得支持。两折CD均下降，并不能抵消接口覆盖和尾部误差的退化。', '', 'COUPLE对M0：C折E/J P95分别增加1.700/2.241 mm，E/J Cover2下降4.648/7.053个百分点；D折E/J P95增加0.055/0.438 mm，J Cover2下降1.906个百分点。AUX相对M0也呈折间不一致：C折明显退化，D折部分表面/接口指标改善。现有结果不足以用H2替代M0。', '', '## 五、病例级风险：净计数不能掩盖新增失败', '', '严重几何标记沿用冻结定义：E P95>20 mm或J Cover2=0；这是诊断阈值，不是临床安全认证。', '', '| 折 | 比较 | 严重病例 基线→候选 | 新增 | 挽回 |', '|---|---|---|---:|---:|']
for f in ['C', 'D']:
    for name in ['H2_COUPLE_minus_H2_AUX', 'H2_COUPLE_minus_M0', 'H2_AUX_minus_M0']:
        v = risk[f][name]['labels']['severe_geometry']
        lines.append(f"| {f} | {name} | {v['baseline_count']}→{v['candidate_count']} | {v['new']} | {v['rescued']} |")
lines += ['', 'COUPLE相对AUX在C折严重病例减少，但仍新增1例；D折新增5例、挽回2例，严重病例6→9。相对M0，两折各新增2例严重病例；C折总数不变、D折总数略减，均不能表述为没有新增风险。COUPLE相对AUX的紧缩分布标记（dense回转半径比<0.9）C折58→73、D折45→55；尺度头扩大coarse并不保证dense分布免于紧缩。不同风险标签可重叠，不应相加当作独立病例数。', '', '## 六、预先关注的frontoorbital类型', '', '| 折 | 模型 | E P95 mm | J P95 mm | 质心偏差 mm |', '|---|---|---:|---:|---:|']
for f in ['C', 'D']:
    for a, v in derived['frontoorbital'][f].items():
        lines.append(f"| {f} | {a} | {v['E_P95_mm']:.3f} | {v['J_P95_mm']:.3f} | {v['centroid_offset_mm']:.3f} |")
lines += ['', 'frontoorbital的E/J P95在两折COUPLE均高于AUX和M0。C折质心偏差也更大；D折虽较AUX减小，仍高于M0。不能用整体CD的改善宣称该困难类型获益。', '', '## 七、尺度读出的机制含义与边界', '', '| 折 | 模型 | raw绝对log半径误差 | used绝对log半径误差 | 平均scale | scale范围 |', '|---|---|---:|---:|---:|---|']
for f in ['C', 'D']:
    for a, v in derived['H2_offline_radius'][f].items():
        lo, hi = v['scale_range']
        lines.append(f"| {f} | {a} | {v['raw_abs_log_radius_error']:.4f} | {v['used_abs_log_radius_error']:.4f} | {v['scale']:.4f} | {lo:.4f}–{hi:.4f} |")
lines += ['', 'COUPLE内部raw→used半径误差确实下降，但其used误差与AUX raw误差接近（C折0.1585对0.1595，D折0.1317对0.1245），且COUPLE训练后的raw半径误差更大。这与“生成路径可能适应耦合变换、抵消部分尺度校正”的解释相容，但不能仅凭这些观察确定因果。更不能将GT参与离线计算的半径残差作为推理输入。', '', 'COUPLE围绕自身coarse质心缩放，不能直接纠正质心位置、各向异性形状、拓扑或接口对应；dense还受相对位移影响。故当前结果仅证明低阶尺度可被改变，没有证明完整骨块及接口得到可靠改善。已保存Native证据不等同于delta置零或供体置换干预；原协议额外20次forward未执行，本次不自动启动。', '', '## 八、结论、局限和下一步', '', '建议将本版本H2作为未获支持的候选收束：保留M0作为比较基线，不根据两折开发结果继续扫描辅助权重、尺度范围或病例。这里是描述性科研判断，不是额外执行正式gate。', '', '若下一步需要解释机制，优先限定复盘已保存的coarse/dense与严重新增病例，区分位置、尺度、覆盖和远端离群；只有明确剩余因果问题后，才考虑原协议已定义、仍需单独授权的20次条件干预。没有必要直接追加训练。后续新的结构假设应明确针对位置/形状/接口哪一环节，不能继续以半径拟合改善代替目标改善。', '', '本结果局限：每折单seed，有限Mamba梯度非确定性已接受并披露；开发来源被重复使用；每来源5个缺损并非5个独立患者；没有bootstrap、p值或训练随机性估计，没有独立外部/临床验证。不能据此声称对所有颅骨补全任务无效，也不能宣称Mamba特异性机制或临床安全。', '', '## 九、可追溯文件', '', '- 正式审计：`audit_report_v1.json`。', '- 派生数值：`descriptive_interpretation_values_v1.json`（仅从冻结病例/配对记录聚合）。', '- 原始冻结评分：上一级 `unified_scores_v1/`，未修改。', '- 本报告和审计辅助文件指纹：`audit_and_interpretation_manifest_v1.json`。', '']
targets = {DEST / 'descriptive_interpretation_values_v1.json': json.dumps(derived, ensure_ascii=False, indent=2) + '\n', DEST / 'H2_M0两折评分后冻结审计与科研解读_zh_v1.md': '\n'.join(lines)}
assert all(not p.exists() for p in targets)
for p, content in targets.items():
    p.write_text(content, encoding='utf-8')
paths = [AUDIT, *targets, ROOT/'audit_H2_three_arm_scores_v1.py', ROOT/'independent_score_audit_body_v1.txt', ROOT/'build_independent_score_audit_v1.py', Path(__file__).resolve()]
manifest = [{'path': str(p), 'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths]
mp = DEST / 'audit_and_interpretation_manifest_v1.json'
assert not mp.exists()
mp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'report': str(list(targets)[1]), 'audit_status': audit['status'], 'manifest': str(mp)}, ensure_ascii=False))
