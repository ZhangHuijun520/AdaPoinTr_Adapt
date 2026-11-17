# -*- coding: utf-8 -*-
"""Describe selected existing-array diagnostics; no forward or parameter change."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[2];O=R/'outputs/spcg_coarse_dense_visualization_20261117_v1'
v=json.loads((O/'fixed_case_geometry_metrics_v1.json').read_bytes());c=json.loads((O/'completion_v1.json').read_bytes());assert c['status']=='FIVE_FIXED_CASE_COARSE_DENSE_GEOMETRY_VISUALIZATION_COMPLETE'
lines=['# SPCG：5例固定退化与改善病例的 coarse／dense 几何诊断','',
'日期：2026-11-17。本次只复用已有数组：5例×3模型，共15份预测、30个coarse/dense点集。没有新forward、训练、checkpoint加载、配准或调参。','',
'## 1. 病例范围与展示合同','',
'依据既定规则：G2相对G1新增严重病例，按病例ΔE从大到小、并列case_id取前3；改善对照每折取G2不严重且ΔE最小的1例。选例在读取选中预测数组之前写入 frozen_case_scope_v1.json。本次选例是事后解释，不是新的独立确认样本。','',
'|折|病例|用途|dense ΔE：G2−G1/mm|','|---|---|---|---:|']
for case in v['cases']:lines.append(f"|{case['fold']}|{case['case_id']}|{'新增严重' if case['selection']=='posthoc_new_severe' else '改善对照，非正常保证'}|{case['delta_E_G2_minus_G1_mm']:+.4f}|")
lines+=['',
'每例生成4张图：XY、XZ、YZ全局投影，以及XY局部放大，共20张。每张图按G0/G1/G2分行，coarse256/dense8192分列。相同病例全部模型/阶段共用等比例world-mm全局坐标范围，包含输入、GT及全部预测离群点。没有模型间配准或删除离群点。','',
'局部框为GT8192包围盒外扩10mm，仅用于显示，不能当作可部署的输入定位器。局部图会裁剪显示范围，同时报告落在3D框外的预测点数；全局图保留所有点。颜色是预测点到A2离散参考的最近距离，40mm以上颜色饱和，但统计不截断。灰色为输入，青色GT，紫色为J参考面中心；投影重合不能证明三维接触。','',
'## 2. G2主要阶段数值','',
'质心偏差与E P95单位mm；反向离群比例为预测→A2距离>20mm。E/J支持按既定A1面积权重计算。','',
'|病例|coarse质心偏差|dense质心偏差|coarse E95|dense E95|coarse→dense质心移动|dense反向离群|',
'|---|---:|---:|---:|---:|---:|---:|']
for case in v['cases']:
 m=case['metrics']['G2'];a,b=m['coarse'],m['dense'];lines.append(f"|{case['case_id']}|{a['centroid_offset_mm']:.3f}|{b['centroid_offset_mm']:.3f}|{a['support']['E']['p95_mm']:.3f}|{b['support']['E']['p95_mm']:.3f}|{m['dense_minus_coarse']['centroid_shift_mm']:.3f}|{100*b['to_A2_gt20_fraction']:.2f}%|")
lines+=['',
'## 3. 三个新增严重病例','',
'### C / train__051__random_1','',
'G2 coarse质心偏差97.552mm，dense为97.699mm；反向>20mm比例由98.83%变为99.37%，J Cover@2mm两阶段均为0。全局三视图显示预测落在错误空间区域，局部细节不能解释如此大的失配。coarse到dense质心只移动2.030mm，子点相对本模型coarse中心的RMS为7.709mm。对应G1 dense质心偏差6.433mm、E95=9.559mm。大偏移在可观察coarse节点已经存在，dense主要延续它。','',
'### C / train__072__random_1','',
'G2 coarse质心偏差89.779mm，dense为90.631mm；两个阶段的预测点全部距A2超过20mm，J Cover@2mm均为0。coarse半径比0.9994几乎等于1，位置仍然完全不对，直接说明尺度矩正确不能替代位置与表面覆盖。dense质心仅移动1.956mm，不能挽回近90mm级偏移。此例G0也严重（dense质心62.185mm、E95=41.778mm），所以“新增严重”是相对G1而言，不能称为只有G2失败。','',
'### D / train__008__random_2','',
'G2 coarse/dense质心偏差为23.879/22.314mm，半径比0.5924/0.5808，E95为46.650/35.557mm，J95为55.192/44.535mm。两个阶段反向>20mm离群比例均为0，但图中预测集中在目标的一部分区域，远端目标没有得到覆盖。这是范围收缩、分布偏置与目标漏覆盖，不能把“没有远端离群”解释成形状正确。相对G1的E95回退30.244mm也不是由dense从一个正确coarse突然偏离而出现。','',
'**这3例的共同观察：主要失配已在保存的coarse节点出现，dense没有纠正。** dense的E/J支持距离有所下降，不能直接称为生成机制修复：点数从256增至8192，本来就会影响离散覆盖。这里没有证据表明这3例主要属于“正确coarse经dense变成大偏移”的模式。也不能由这3个事后极端病例推断整个210例队列都相同。','',
'## 4. 两个改善对照','',
'### C / train__012__parietotemporal','',
'G1在coarse阶段已偏位83.851mm，dense为84.418mm，所有点距目标A2超过20mm。G2 coarse偏差13.333mm、dense12.501mm，dense E95由G1的71.642降为4.590mm，J95由75.721降为7.643mm。收益也已经出现在coarse层，dense进一步提供密集覆盖。它说明当前局部方案能够在个别病例恢复位置和形状支持，但与退化病例一起看，表现具有明显病例依赖，不能宣布稳定定位问题已解决。','',
'### D / train__046__parietotemporal','',
'G2相对G1的dense E95由14.258降到4.575mm，J95由16.690降到4.522mm，J Cover@2mm由5.92%提高到54.82%。然而G2 dense质心仍偏26.672mm，半径比1.383，反向>20mm离群达32.42%；coarse已有40.23%离群。它是“目标支持改善但预测仍明显多余/偏位”的对照，不是正常病例。G0的反向离群仅2.55%、质心13.806mm，因此按E指标选出的改善样本也不能被包装成整体几何最优。','',
'## 5. 归因边界','',
'1. 本次支持将关注点前移到coarse空间生成的可靠性，而非首先归咎于dense残差放大。但保存的coarse是现有可观察节点，不证明错误在计算图中首次产生的位置。','2. 本次所有模型使用同一冻结病例和D-only归一化/反归一化合同，读取的文件/成员哈希均一致。三臂同病例结果明显不同，不支持把统一坐标变换错误作为唯一解释；这并不代替所有上游轴向/空间合同的独立证明。','3. coarse与dense点数不同。质心位移、范围与离群比例可描述阶段变化；E/J覆盖变化含点预算影响，不是同预算因果消融。','4. dense按现有每coarse32子点布局检查相对位移；同一槽位在不同模型之间没有保证一致的解剖含义，不能跨模型逐槽硬配对。','5. 未保存实际Memory、probe/索引与局部摘要，本次不能把失败唯一归因于探针位置、近邻选择或特征质量，也未执行同权重反事实。','6. D折G1/G2同设备，G0_D跨设备仅供参考；5例是按结果选出的解释样本，不代表总体失败率。','',
'## 6. 交付与下一步','',
'已保存20张PNG、总览、可离线打开的index.html、逐病例/模型/阶段指标、选例范围、源文件及15份预测成员的SHA绑定和产物清单。所选dense的E/J、质心和反向离群指标已与正式冻结评分核对一致；原评分、预测和备份未修改。','',
'建议下一步先对本次图表、选例和数值做正式只读诊断后冻结审计，再与已冻结全队列评分综合决定收束当前SPCG候选。不要直接据此添加dense补偿、扫描邻域大小或追加训练；本次没有授权或执行这些操作。运行时一致性核验不代替另行正式冻结审计。','',
'## 7. 三臂两阶段完整简表','',
'每病例每模型均列出，避免只报告G2或最显著一张投影。','',
'|病例|模型|coarse质心/mm|dense质心/mm|coarse E95/mm|dense E95/mm|dense J95/mm|dense J2/%|dense离群20/%|',
'|---|---|---:|---:|---:|---:|---:|---:|---:|']
for case in v['cases']:
 for arm in ['G0','G1','G2']:
  m=case['metrics'][arm];a,b=m['coarse'],m['dense'];lines.append(f"|{case['case_id']}|{arm}|{a['centroid_offset_mm']:.3f}|{b['centroid_offset_mm']:.3f}|{a['support']['E']['p95_mm']:.3f}|{b['support']['E']['p95_mm']:.3f}|{b['support']['J']['p95_mm']:.3f}|{100*b['support']['J']['coverage']['2.0']:.2f}|{100*b['to_A2_gt20_fraction']:.2f}|")
lines+=['','## 8. 图表入口','']
for case in v['cases']:
 lines.append('### '+case['case_id']);lines.append('')
 for name in case['figures']:lines.append(f'[{name}]({name})')
 lines.append('')
report=O/'固定五例_coarse_dense几何诊断报告_zh_v1.md'
with report.open('x',encoding='utf-8') as f:f.write('\n'.join(lines))
# Read-only render checks, not a formal post-diagnostic freeze audit.
from PIL import Image
manifest=json.loads((O/'artifact_manifest_v1.json').read_bytes())
for r in manifest['files']:
 p=Path(r['path']);assert p.stat().st_size==r['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256']
for case in v['cases']:
 for n in case['figures']:
  with Image.open(O/n) as im:assert im.size==(1860,1860);im.verify()
quality=dict(status='RENDER_AND_DELIVERY_CHECK_PASS_NOT_FORMAL_FREEZE_AUDIT',fixed_cases=5,main_figures=20,dimensions=[1860,1860],visually_inspected_examples=['train__051__random_1_XY_global.png','train__008__random_2_XZ_global.png','train__046__parietotemporal_XZ_global.png'],notes=['All global views use shared world-mm equal-axis bounds; no clipping of model points.','Color cap40mm is display only.','ROI clipping is disclosed; global panels retained.'],report=dict(path=str(report),bytes=report.stat().st_size,sha256=hashlib.sha256(report.read_bytes()).hexdigest()))
with (O/'delivery_quality_check_v1.json').open('x',encoding='utf-8') as f:json.dump(quality,f,ensure_ascii=False,indent=2)
files=[dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(O.iterdir()) if p.is_file()]
with (O/'final_delivery_manifest_v1.json').open('x',encoding='utf-8') as f:json.dump(dict(files=files,status='FIXED_VISUALIZATION_COMPLETE_AWAITING_FORMAL_FREEZE'),f,ensure_ascii=False,indent=2)
print(json.dumps(dict(status='REPORT_AND_RENDER_CHECK_COMPLETE',report=str(report),forward_calls=0),ensure_ascii=False))
