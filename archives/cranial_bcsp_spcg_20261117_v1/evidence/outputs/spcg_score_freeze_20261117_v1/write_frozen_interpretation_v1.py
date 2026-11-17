"""Explain audited scores only; no new score, resampling, selection or gate."""
from pathlib import Path
import json,hashlib
D=Path(__file__).resolve().parent
a=json.loads((D/'audit_verification_v1.json').read_bytes());s=json.loads((D/'frozen_research_summary_v1.json').read_bytes())
assert a['status']=='FORMAL_SPCG_THREE_ARM_TWOFOLD_POST_SCORE_FREEZE_AUDIT_PASS' and all(a['checks'].values())
lines=['# SPCG G0／G1／G2：正式评分后冻结审计与结果解读','',
'日期：2026-11-17。状态：正式只读冻结审计通过；以下解读只依据已冻结评分。未计算正式投资 gate，未追加模型调用或训练。','',
'## 1. 审计结论','',
'27项检查全部通过。评分进程退出码0，未超时，用时约30分37秒；错误日志为空。16个输出文件和7个执行凭据的完整清单、大小、SHA256及内容相关属性已记录，审计前后稳定。','',
'实际完成210个开发病例、630行模型评分、420行共享控制，共1050行病例评分；生成210行来源×角色汇总。每折21个独立来源，每来源5种缺损，五种缺损等权后再对来源等权。模型630行不代表630个独立患者。','',
'重新核验了归档及三个校验文件、210份参考与210份点集、评分实现/指标/P3/协议绑定。420行共享控制与旧冻结控制逐行完全相等。三份CSV与JSON内容逐字节一致。风险、缺损分层、病例差值、来源差值和排序与病例行一致。','',
'每折保存的2000×21抽样矩阵、来源字典序、种子与SHA均通过复核；使用独立的PCG64重建检查矩阵，逐比较、逐指标从冻结来源差值重新核验均值和线性百分位区间。该过程用于审计已有统计，不新增统计方案。未重新计算任何点距离、运行forward或访问服务器。','',
'审计不等于独立重跑全部点距离指标；运行时RSS由原进程断言控制，本次没有新增连续RSS日志。证据见 `audit_verification_v1.json`。','',
'## 2. 比较含义与限制','',
'G0保留原LQI全局coarse头；G1使用全部256个Memory的全局摘要和SPCG共享坐标头；G2使用探针附近8个Memory的局部摘要及相同结构/初态的头。主比较G2−G1，实用参考G2−G0，解释比较G1−G0。G1/G2之间不仅邻域位置不同，也有聚合基数与平均平滑差异；不能把所有差值唯一归因于局部空间性。','',
'C折三臂在同一训练设备上；D折G1/G2同设备，但G0_D在旧设备上，故D折对G0的比较只能作跨设备参考。统一预测设备不消除训练设备混杂。G0与新头还存在槽位参数化与少量参数量差异，不是单一局部机制消融。','',
'下列均值均为来源等权的病例指标均值，并非把全体点合并后求一个P95。E、J为既定分区；覆盖率是离散几何支持，不是临床接触间隙、水密性或安全认证。','',
'## 3. 主要绝对结果','',
'E/J P95与CD-L1单位mm，越低越好；J Cover@2mm越高越好。严重几何标签为 E_P95>20mm 或 J Cover@2mm=0，计数单位为病例（每臂每折105例）。','',
'|折|模型|E P95|J P95|CD-L1|J Cover@2mm|严重病例|质心偏差mm|回转半径比|',
'|---|---|---:|---:|---:|---:|---:|---:|---:|']
for f in ['C','D']:
 for arm in ['G0','G1','G2']:
  v=s['folds'][f]['arms'][arm];m=v['metrics'];lines.append(f"|{f}|{arm}|{m['E_P95_mm']:.4f}|{m['J_P95_mm']:.4f}|{m['CD_L1_mm']:.4f}|{100*m['J_coverage_2.0mm']:.2f}%|{v['risks']['severe_geometry']}|{m['centroid_offset_mm']:.4f}|{m['radius_gyration_ratio']:.4f}|")
lines+=['','## 4. 核心配对比较：G2−G1','',
'差值为候选减参考。误差负值有利，覆盖率正值有利。95%区间为每折21个来源的固定2000次配对bootstrap百分位区间；它不估计训练种子波动，也不校正开发集反复探索或多重比较。','',
'|折|指标|均值差|95%来源bootstrap区间|改善／回退来源|','|---|---|---:|---|---|']
for f in ['C','D']:
 for k,label in [('E_P95_mm','E P95/mm'),('J_P95_mm','J P95/mm'),('CD_L1_mm','CD-L1/mm'),('J_coverage_2.0mm','J Cover@2mm/百分点')]:
  v=s['folds'][f]['comparisons']['G2_minus_G1']['metrics'][k];scale=100 if 'coverage' in k else 1;lo,hi=v['bootstrap']['CI95'];lines.append(f"|{f}|{label}|{v['mean_delta_b_minus_a']*scale:+.4f}|[{lo*scale:+.4f}, {hi*scale:+.4f}]|{v['improved_sources']}／{v['worse_sources']}|")
lines+=['',
'**解释：本轮没有支持G2局部8邻域方案优于G1全局摘要。** C折主指标平均回退1.5270mm，12/21来源回退，但区间跨0，不能说已确定存在总体劣势或两者等效；D折平均回退1.8720mm，18/21来源回退，区间[0.9379,2.8983]mm全为正。D折J P95和CD-L1也同时回退，且对应区间全为正；这是同设备的G1/G2对照，不能用G0_D迁移解释掉。','',
'C折G2的J Cover@2mm比G1提高7.0196个百分点，17/21来源改善，区间[2.6035,12.1417]个百分点；但J P95更差、严重病例更多。一个模型可以在更多参考点附近提供局部支持，同时遗漏另一部分表面或产生长尾误差，覆盖均值改善与P95恶化并不矛盾。D折该覆盖提升仅0.3750个百分点，区间跨0，未形成跨折稳定的接口覆盖信号。','',
'## 5. 相对G0的结果','',
'|折|比较|E P95均值差mm|95%来源bootstrap区间|J Cover@2mm差/百分点|',
'|---|---|---:|---|---:|']
for f in ['C','D']:
 for key in ['G2_minus_G0','G1_minus_G0']:
  c=s['folds'][f]['comparisons'][key];v=c['metrics']['E_P95_mm'];lo,hi=v['bootstrap']['CI95'];lines.append(f"|{f}|{key}|{v['mean_delta_b_minus_a']:+.4f}|[{lo:+.4f}, {hi:+.4f}]|{100*c['metrics']['J_coverage_2.0mm']['mean_delta_b_minus_a']:+.4f}|")
lines+=['',
'G2对G0的E P95两折均约回退1.44mm；C折15/21来源回退、D折18/21来源回退。C折区间跨0；D折虽区间为正，但该比较混有训练设备变化，不能给出严格单一架构因果结论。','',
'G1对G0的E P95变化很小：C折−0.0902mm、D折−0.4294mm，区间均跨0。J Cover@2mm却分别下降4.6062和2.7814个百分点，对应区间均低于0（D仍有设备混杂）。因此，G1也不能据此升级为已证实优于G0的正式新基线。应保留三臂，不挑一个次指标宣布胜出。','',
'## 6. 严重退化与挽回','',
'不能只看净严重病例数。下面是同一病例相对参考新进入严重标签／被挽回的数量。','',
'|折|候选−参考|参考严重|候选严重|新增严重|挽回|','|---|---|---:|---:|---:|---:|']
for f in ['C','D']:
 for key in ['G2_minus_G1','G2_minus_G0','G1_minus_G0']:
  v=s['folds'][f]['comparisons'][key]['severe'];lines.append(f"|{f}|{key}|{v['baseline_count']}|{v['candidate_count']}|{v['new']}|{v['rescued']}|")
lines+=['',
'G2对G1：C折新增9例、挽回4例；D折新增7例、挽回0例。两折合计16例新增、4例挽回只是描述性计数，不替代分折比较。G2不是仅在少数已严重病例中改变分数，而是引入了新的严重失败。','',
'G2的回转半径比在两折都更接近1，紧缩标签病例也减少（C：81→59；D：68→38，相对G1）；然而E/J与严重退化没有随之改善。整体尺度矩接近GT不等于骨块表面形状或接口吻合。C折G2平均质心偏差下降，D折反而上升，也不支持一个跨折一致的“定位已修好”结论。','',
'## 7. 当前能说什么、不能说什么','',
'本轮可说：固定公式、固定训练预算与seed0下，局部8-Memory替换全局聚合没有产生稳定的补全精度收益；D折的主要连续误差与新增严重病例均给出不利证据。C折局部覆盖的改善具有代价，不能据此忽略尾部与失效病例。','',
'本轮不能说：所有空间条件、Mamba或局部建模都无效；也不能把原因唯一定位为探针落点、局部特征贫乏、坐标头坍缩或dense放大。当前Native归档只有coarse/dense，未保存实际probe/邻域摘要、索引及计划中的有限Memory观察。这些记录为 NOT_COLLECTED，不能从最终预测倒推出实际邻域，也不能以事后猜测补足机制证据。','',
'两折源自相同训练开发方案且只有seed0，来源bootstrap并非独立重复训练。训练存在已披露的有限梯度非确定性；当前区间不能外推到新种子、外部数据或临床患者。原协议投资gate本次未执行，本报告不冒充正式gate回执。','',
'## 8. 下一步建议','',
'暂不追加训练、扩大邻域或扫描探针/权重，也不宣布G1/G2获胜。先按既定计划，复用已有coarse/dense及评分，对至多3个G2−G1新增严重病例与2个固定明显改善对照做限定几何展示：新增病例按ΔE降序、并列case_id；改善对照每折选ΔE最小且G2不严重者。此项仍需单独授权，本次没有选例、作图或运行forward。','',
'展示重点是同病例G0/G1/G2的coarse与dense相对GT位置、整体覆盖、远端离群和E/J分区误差，区分coarse已有偏差与dense后续放大；只能报告共现/分阶段误差，不将coarse点集与dense点集不同点数的分数直接解释为因果增益。','',
'若这些有限图不能提供足够新信息，应正式收束当前SPCG候选，整理负结果及可靠性代价。任何恢复Memory采集、同权重反事实、第二seed或新公式都应另立最小问题与执行范围，不自动扩大本轮。','',
'## 9. 核心文件','',
'- `audit_verification_v1.json`：27项检查、16+7文件完整SHA256清单及冻结边界。',
'- `frozen_research_summary_v1.json`：三臂两折均值、六个比较、区间与风险转移。',
'- 原评分目录：`outputs/spcg_score_implementation_20261117_v1/unified_scores_v1`；原文件均未修改。','']
target=D/'正式评分后冻结审计与G0_G1_G2结果解读_zh_v1.md'
with target.open('x',encoding='utf-8') as f:f.write('\n'.join(lines))
manifest=[]
for p in sorted(D.iterdir()):
 if p.is_file():manifest.append(dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
with (D/'delivery_manifest_v1.json').open('x',encoding='utf-8') as f:json.dump(dict(status='AUDIT_PASS_INTERPRETATION_FROZEN',files=manifest,no_new_forward=True,no_new_training=True,no_formal_gate=True),f,ensure_ascii=False,indent=2)
print(json.dumps(dict(status='INTERPRETATION_WRITTEN',report=str(target),new_forward=0,real_point_metric_recalculations=0),ensure_ascii=False))
