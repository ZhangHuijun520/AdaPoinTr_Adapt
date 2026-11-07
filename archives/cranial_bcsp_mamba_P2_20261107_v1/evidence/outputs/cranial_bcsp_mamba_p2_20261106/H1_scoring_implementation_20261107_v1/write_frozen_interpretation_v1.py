"""Post-PASS descriptive reading of saved scores; no geometry or inference."""
from pathlib import Path
import json,hashlib,math,statistics
S=Path(__file__).resolve().parent;O=S/'unified_scores_v1';F=S/'post_scoring_freeze_audit_20261107_v1'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def bind(p):return dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
audit=read(F/'audit_report_v1.json');assert audit['status']=='FORMAL_POST_SCORING_FREEZE_AUDIT_PASS'
for b in audit['output_manifest']:assert bind(Path(b['path']))==b
p=read(O/'paired_comparison.json');risks=read(O/'risk_transitions.json');defects=read(O/'defect_comparison.json')
rows=[json.loads(x) for x in (O/'case_metrics.jsonl').read_text(encoding='utf-8').splitlines()]
summary={};lines=['# H1／M0 两折评分冻结审计与科研解读 v1','', '日期：2026-11-07。当前结论：**本次 H1 不支持继续投入 T-H1 训练；建议冻结为有限证伪结果，转向既有证据上的条件信息利用检查。** 本文是已授权的描述性解读，不运行 bootstrap、正式统计 gate 或新实验。','', '## 1. 正式只读冻结审计','',f"状态：`{audit['status']}`。21组检查全部通过；原评分退出码0，唯一一次执行，无超时、重试或丢弃病例。",'', '覆盖 C／D 各105例、各21来源，每来源5类缺损；420行模型评分＋420行共享控制＝840行病例评分，168行来源评分。12个输出文件清单、哈希、CSV／JSON顺序与数值一致；独立重算来源均值、配对差值、中位数、胜负计数、缺损分层及风险转移。630行 M0／共享控制与先前冻结的 P1 评分一致。','',f"只读核验 {audit['read_bytes']:,} 字节，用时 {audit['seconds']:.3f} 秒；文件内容相关属性前后稳定，排除 atime。未解码真实点集、重算几何距离、导入模型或访问服务器。几何距离的可靠性仍依赖已冻结评分实现及其验证；本审计证明保存值与归约的一致性。",'', '## 2. 比较口径','', '固定8k输入／8k输出、256 coarse，实体缺损与完整骨组织边界表示；H1是已有 coarse／fine 重建损失之外的固定质心／半径辅助项。每折各自比较已冻结 M0 与 M-H1，按每来源5类缺损平均，再对21来源等权平均。下表距离单位mm；覆盖率为百分比。H1−M0：距离负值、覆盖正值为改善。原始坐标预测直接评分，无GT配准。','', '每折只有一个训练seed，且开发集多次用于探索。本结果不代表跨训练随机性的显著性、不证明临床安全，也不用于选择最佳轮次或筛除失败病例。','', '## 3. 完整形状与接口结果','', '| 折 | 指标 | M0 | M-H1 | H1−M0 | 改善／退化来源 |','|---|---|---:|---:|---:|---:|']
metrics=['E_P95_mm','J_P95_mm','CD_L1_mm','E_coverage_2.0mm','J_coverage_2.0mm','reverse_A2_outlier_20.0mm','centroid_offset_mm']
for f in ['C','D']:
 s=p['comparison'][f]['metrics'];summary[f]=dict(metrics=s,risk_counts={},coarse={})
 for k in metrics:
  v=s[k];scale=100 if 'coverage' in k or 'outlier' in k else 1
  label=k+(' (%)' if scale==100 else '')
  lines.append(f"| {f} | {label} | {v['mean_M0']*scale:.4f} | {v['mean_M_H1']*scale:.4f} | {v['mean_delta_M_H1_minus_M0']*scale:+.4f} | {v['improved_sources']}／{v['worse_sources']} |")
lines+=['','C折E P95增加约26.5%，D折增加约9.6%；分别17/21和13/21来源退化，因而不能将均值回退解释为仅有一个异常病例。C折覆盖与离群也变差；D折覆盖略升、远端离群下降，但E／J P95与CD仍变差，说明“位置或尾部改善”与“完整表面覆盖改善”并不等价。','', '## 4. coarse 与 dense 的机制线索','', '以下只从已保存的阶段统计归约；绝对对数半径误差为 |log(r预测/rGT)|，越小越好，不把有符号平均半径比更接近1直接等同于每例改善。','', '| 折 | 阶段量 | M0 | M-H1 | 差值 |','|---|---|---:|---:|---:|']
for f in ['C','D']:
 for arm in ['M0','M_H1']:
  selected=[r for r in rows if r['fold']==f and r['arm']==arm]
  values={
   'coarse_centroid_mm':[r['stage_geometry']['coarse']['centroid_offset_mm'] for r in selected],
   'coarse_abs_log_radius':[abs(math.log(r['stage_geometry']['coarse']['radius_gyration_ratio'])) for r in selected],
   'dense_abs_log_radius':[abs(math.log(r['position_shape']['radius_gyration_ratio'])) for r in selected]}
  # Equal counts of five defects/source make this identical to source-equal averaging.
  summary[f]['coarse'][arm]={k:statistics.fmean(v) for k,v in values.items()}
 for k in summary[f]['coarse']['M0']:
  a=summary[f]['coarse']['M0'][k];b=summary[f]['coarse']['M_H1'][k];lines.append(f'| {f} | {k} | {a:.5f} | {b:.5f} | {b-a:+.5f} |')
lines+=['', '质心与径向二阶矩只是低阶分布描述；相同质心／半径可以对应不同形状、错误拓扑或漏覆盖。H1作用在coarse，但dense还受相对位移影响，因此不能由一个矩改善推出接口或未知表面恢复。这里没有梯度竞争、特征缺失或decoder因果归因的直接干预证据；不把一种机制解释写成已证实根因。','', '## 5. 风险与缺损分层','', '风险是预注册几何代理标签，可重叠，不是临床失效率：placement_tail为质心偏差>20mm；compact_distribution为半径比<0.9；severe_geometry为E P95>20mm或J Cover@2mm=0。','', '| 折 | 标签 | M0 | M-H1 | 新增 | 修复 |','|---|---|---:|---:|---:|---:|']
for f in ['C','D']:
 for k,z in risks[f]['labels'].items():
  summary[f]['risk_counts'][k]={key:z[key] for key in ['M0_count','M_H1_count','new','rescued']}
  lines.append(f"| {f} | {k} | {z['M0_count']} | {z['M_H1_count']} | {z['new']} | {z['rescued']} |")
lines+=['','C折严重几何病例4→5，新增3例、修复2例；D折10→7，仍新增2例、修复5例。D折净数下降掩盖了风险转移。两折共新增5例，故不满足原计划“新增严重几何退化为0”的继续投入要求。compact减少不能抵消E／J覆盖误差或新增严重病例。','', '| 折 | 缺损类型 | E P95差值mm | J P95差值mm |','|---|---|---:|---:|']
for f in ['C','D']:
 for d,v in defects[f].items():lines.append(f"| {f} | {d} | {v['mean_deltas']['E_P95_mm']:+.4f} | {v['mean_deltas']['J_P95_mm']:+.4f} |")
lines+=['', '新增严重几何病例（完整保留，不用于筛选训练／评价集合）：','']
for f in ['C','D']:
 ids=[r['case_id'] for r in risks[f]['labels']['severe_geometry']['cases'] if r['new']]
 lines.append('- '+f+'：'+ '、'.join(ids))
lines+=['', '## 6. 科研判断与下一步','', '1. 冻结当前H1定义、权重及两折负结果。当前证据否定的是“这个固定矩约束足以稳定改善本任务”的继续投入理由；不能推广为所有几何约束无效或Mamba不适用。','2. 不建议启动条件式T-H1两次训练，也不扫描H1权重、替换病例或放宽风险阈值挽救该候选。E P95两折回退，且新增严重退化已足以阻断原计划的资源继续条件，无需新增统计显著性计算。','3. 下一步建议仅制定／复核一个有界的D-only条件信息检查：比较既有coarse与固定简单几何／冻结特征读出，判断位置与范围信息是否存在但未被坐标头利用。读出训练和任何新增checkpoint instrumentation须另行冻结范围，不在本次执行。','4. 若证据支持，再定义唯一H2输入条件—coarse耦合假设，保留原表示、采样、数据、训练与评分合同；先确认信息路径和可证伪预测，再决定新训练。当前结果不能直接指定一种结构改动必然有效。','', '## 7. 可追溯材料','', '- 授权评分request：`'+audit['request_sha256']+'`。','- 正式审计：同目录 `audit_report_v1.json`（含12文件SHA256和全部读取清单）。','- 原始完整结果：上级 `unified_scores_v1/`，本解读不覆盖任何评分产物。','- 本解读没有重新运行评分、bootstrap、模型、BNCal、训练或正式gate。']
report=F/'H1_M0_两折评分冻结审计与科研解读_zh_v1.md'
with report.open('x',encoding='utf-8') as out:out.write('\n'.join(lines)+'\n')
with (F/'descriptive_interpretation_values_v1.json').open('x',encoding='utf-8') as out:json.dump(summary,out,indent=2,allow_nan=False)
manifest=dict(status='POST_SCORE_AUDIT_AND_INTERPRETATION_FROZEN',files=[bind(p) for p in [S/'build_independent_audit_v1.py',S/'audit_H1_M0_scores_v1.py',Path(__file__),F/'audit_report_v1.json',report,F/'descriptive_interpretation_values_v1.json']],no_new_experiment=True)
with (F/'delivery_manifest_v1.json').open('x',encoding='utf-8') as out:json.dump(manifest,out,indent=2)
print(json.dumps(dict(report=str(report),coarse={f:summary[f]['coarse'] for f in summary},delivery=bind(F/'delivery_manifest_v1.json')),ensure_ascii=False))
