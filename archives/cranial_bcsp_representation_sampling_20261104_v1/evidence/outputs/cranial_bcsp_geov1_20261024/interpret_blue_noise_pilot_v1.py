"""Explicit fine-cutwall tradeoff from saved scores only; no resampling."""
import os
from pathlib import Path
B=Path(__file__).resolve().parent;O=B/'blue_noise_pilot_20261103_v1'
os.environ['MPLBACKEND']='Agg';os.environ['MPLCONFIGDIR']=str(O/'mpl_cache')
import csv,json,hashlib
import numpy as np
import matplotlib.pyplot as plt

rows=list(csv.DictReader((O/'paired_case_region_summary.csv').open(encoding='utf-8-sig')))
j=[r for r in rows if r['region']=='J' and r['distance']=='same_surface']
fig,axs=plt.subplots(1,2,figsize=(10,4.2),layout='constrained')
labels=[r['case'].replace('SkullBreak_train__','SB ').replace('SkullFix_','SF ').replace('__bilateral','') for r in j]
for ax,values,title in [(axs[0],[float(r['delta_cover_0_5mm'])*100 for r in j],'Same-cut-wall Cover@0.5mm delta (pp)'),
                       (axs[1],[float(r['Euclidean_elimination_point_count'])-float(r['V1_common_pool_point_count']) for r in j],'Cut-wall point-count delta')]:
    values=np.array(values);ax.bar(np.arange(len(j)),values,color=np.where(values>=0,'#0072B2','#D55E00'))
    ax.axhline(0,color='#444444',linewidth=.8);ax.set_xticks(range(len(j)),labels,rotation=40,ha='right')
    ax.set_title(title,fontsize=11);ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
fig.suptitle('Fine cut-wall tradeoff: elimination minus V1; three-seed means',fontsize=12)
fig.savefig(O/'fine_cutwall_tradeoff.png',dpi=170);plt.close(fig)
summary=json.loads((O/'summary.json').read_text())
text=['# 蓝噪声采样试验：科研结论与退化项','','本文件仅解读已经保存的54份点集与评分，不重新采样或运行模型。',
      '', '**结论：该固定点数候选显著改善这六例的2mm尺度几何覆盖，但不是无退化的多表面保护方案。值得保留研究，尚不能替换V1或直接进入训练。**',
      '', '## 粗尺度收益与细尺度代价必须同时报告','','| 来源（三例，各三种子） | J Cover@2mm：V1→候选 | J P95 mm：V1→候选 | 仅J点 Cover@0.5mm：V1→候选 |','|---|---:|---:|---:|']
for ds in ['SkullBreak','SkullFix']:
    u=summary['aggregate'][ds+'/J/unrestricted'];s=summary['aggregate'][ds+'/J/same_surface']
    text.append(f"| {ds} | {u['cover_2mm']['V1_common_pool']*100:.3f}% → {u['cover_2mm']['Euclidean_elimination']*100:.3f}% | {u['p95_mm']['V1_common_pool']:.3f} → {u['p95_mm']['Euclidean_elimination']:.3f} | {s['cover_0_5mm']['V1_common_pool']*100:.3f}% → {s['cover_0_5mm']['Euclidean_elimination']*100:.3f}% |")
text+=['', '![细尺度切壁取舍](fine_cutwall_tradeoff.png)',
       '', 'SkullBreak三个病例的切壁点数均值分别为166.0→152.3、167.3→148.7、358.7→323.0；其中001和002的仅J点Cover@1mm种子均值也略降。18个真实病例×种子组合中，5个组合的仅J点Cover@1mm下降，最大下降1.767个百分点。不能用总体2mm覆盖改善隐藏这些退化。',
       '', '在人工0.5/1/3mm带孔薄板中，各侧及孔壁的同类表面Cover@1mm种子均值均改善，且没有单种子下降；但这只是人工薄板证据，不能证明复杂真实颅骨内外板都受到保护。',
       '', '合理解释是：欧氏排斥减少堆叠和大空洞，同时可能重分配了切壁、相邻骨面之间的点数。现有结果与这种机制相容，但不能仅凭这些指标证明跨层抑制是唯一原因。局部点数减少不一定意味着覆盖下降；必须按尺度与支持来源分别检查。',
       '', '## 下一步建议',
       '', '保持8192点和本次参数不变，不扫描半径、不自动训练。优先用已保存点集，在同一批真实病例上核对切壁减少区域、邻面点的支持来源和剖面，再决定是否需要基于原始表面邻接的采样。该核对不需要新模型或GPU；不需要新造内外板标签。之后才决定是否扩大已开放来源的几何对照。',
       '', '本次实现是compact-kernel样本消除候选，不是严格最小间距Poisson保证；报告的输入几何收益不能替代模型精度验证。所有模型训练、GT和生产默认均保持不变。',
       '', '[完整方法与逐例结果](report_zh_v1.md)；[配对CSV](paired_case_region_summary.csv)；[冻结协议](protocol.json)。']
(O/'research_conclusion_zh_v1.md').write_text('\n'.join(text)+'\n',encoding='utf-8')
# Correct wording in the narrative only: the saved negative records belong to real cases.
p=O/'report_zh_v1.md';s=p.read_text(encoding='utf-8').replace('人工各区域各种子同面Cover@1mm的下降记录','真实各区域各种子同区域Cover@1mm的下降记录')
s+='\n**细尺度退化与最终解释见[科研结论](research_conclusion_zh_v1.md)：SkullBreak切壁点数减少，不能将本次候选称为无退化胜出。**\n'
p.write_text(s,encoding='utf-8')
files=['paired_case_region_summary.csv','coverage_deltas.png','report_zh_v1.md','report_verification.json','fine_cutwall_tradeoff.png','research_conclusion_zh_v1.md']
(O/'report_contents.json').write_text(json.dumps({name:hashlib.sha256((O/name).read_bytes()).hexdigest() for name in files},indent=2),encoding='utf-8')
print('INTERPRETATION_COMPLETE_NO_GEOMETRY_RERUN')
