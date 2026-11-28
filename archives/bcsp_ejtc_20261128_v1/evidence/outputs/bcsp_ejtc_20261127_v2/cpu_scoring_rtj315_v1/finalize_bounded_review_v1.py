from pathlib import Path
import hashlib,json
d=Path(__file__).resolve().parent;e=d/'bounded_failure_review_v1';r=json.loads((e/'bounded_review_evidence_v1.json').read_bytes());p=next(e.glob('*.md'))
text=p.read_text(encoding='utf-8')
addition='''
## 本次可辨识的结果

1. **新增严重病例093-parietotemporal在coarse端点已出现明显失败，dense有所收回但未修复覆盖。** J 的256个粗点中135个（52.734%）距A2参考面超过20 mm，R/T均为0；J粗质心相对目标偏差32.10 mm，T为22.89 mm。这不是“256个粗点全部远离目标”。dense远端比例降至9.265%，但E Cover@2仅1.458%、J Cover@2仅0.229%，密E P95为20.710 mm。759个远端子点中733个属于远端父点组，26个来自近端父点组。远端比例下降不能等同正确骨块恢复。首次失败可定位为“不晚于已保存coarse端点”，不能继续追溯到S、首次生成头或LQI内部。

2. **粗far20保护门的全折增量主要受来源093驱动。** 来源093对全折J−T粗far20贡献+0.502 pp，而全折净增仅+0.391 pp，说明其他来源净有抵消。描述性去掉093后为−0.117 pp。来源095、037也有退化，不能称仅一例有问题；此留一结果只用于归因，不允许删来源后重判。

3. **自由表面Cover@2退化不是093一个来源能够解释。** 去掉093后仍为−0.734 pp，仍低于原−0.50 pp保护下限。004、068、101来源分别下降5.459、6.167、4.584 pp。004-bilateral没有粗/密远端点，J切壁覆盖比T提高16.867 pp，自由表面覆盖却下降15.544 pp；这是明确的区域覆盖交换表现，不能归结为远端离群。101-bilateral也没有远端点，自由表面覆盖仍下降8.722 pp；现有端点指标不足以区分表面细节、局部放置与形状分布的具体机制。

4. **037-random_1的远端退化主要沿已远离参考面的父组传递。** J相对T的远端子点增加414个，近父远子计数均为83，远父远子从281增至695。因此本例不是主要由近端父点的新远端子点解释。068-random_1则二者均增加：远父远子47→246，近父远子40→61。父组归属是观测关联，不能作为训练梯度的因果证明。

5. **整体结论保持原FAIL_STOP。** 切壁覆盖的总体收益与两类可分离的风险共存：粗结构的少量高影响失败，以及更分散的自由表面覆盖损失。现有证据不支持通过调门槛、删除093或追加一个局部修正来宣布方案成功；也不支持从这些病例推断Mamba本身或256个粗点数必然不适合。

本次有界复核到此停止，不追加内部采集、可调参数扫描或训练。下一步可形成EJTC结题报告与归档，并依既定计划返回稳定OASG+LQI基座的论文验证工作。
'''
# Preserve the first generated report and write a finalized separate version.
final=e/'EJTC_D1_bounded_failure_review_zh_v2.md';final.write_text(text+addition,encoding='utf-8')
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
receipt=dict(status='BOUNDED_REVIEW_FINALIZED',selected_sources=6,reviewed_case_pairs=30,deep_review_cases=6,new_forward_calls=0,new_distance_scores=0,training=0,original_FAIL_STOP_unchanged=True,report=dict(path=str(final),sha256=h(final)),evidence=dict(path=str(e/'bounded_review_evidence_v1.json'),sha256=h(e/'bounded_review_evidence_v1.json')),formal_separate_diagnostic_freeze_audit=False)
with (e/'bounded_review_receipt_v1.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,ensure_ascii=False,indent=2)
print(json.dumps(receipt,ensure_ascii=False))
