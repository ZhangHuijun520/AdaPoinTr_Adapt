# -*- coding: utf-8 -*-
import os
os.environ.update(OPENBLAS_NUM_THREADS='2',MPLBACKEND='Agg')
import pathlib,json,hashlib
import numpy as np
N=pathlib.Path(__file__).resolve().parent/'outputs/cranial_bcsp_geov1_20261024';O=N/'multisurface_CPU_20261102_v1';os.environ['MPLCONFIGDIR']=str(O/'mplconfig')
import matplotlib.pyplot as plt
r=json.loads((O/'results.json').read_text());fig,axes=plt.subplots(1,2,figsize=(11,4.5),constrained_layout=True)
for n,style in [(8192,'o-'),(16384,'s--')]:
 rr=[x for x in r['parallel'] if x['n']==n]
 for m,color in [('A','#0072b2'),('B','#d55e00')]:axes[0].plot([x['thickness_mm'] for x in rr],[100*x[m]['best_label_swap_accuracy_mean'] for x in rr],style,color=color,label=m+' / '+str(n))
 axes[1].plot([x['thickness_mm'] for x in rr],[100*x['A']['both_layers_present_fraction'] for x in rr],style,label=str(n))
axes[0].set_title('Balanced groups: best binary layer assignment (%)');axes[1].set_title('Neighborhoods that actually contain both layers (%)')
for ax in axes:ax.set_xlabel('Existing phantom layer separation (mm)');ax.set_xticks([1,3,5]);ax.grid(alpha=.2);ax.legend()
fig.suptitle('Fixed k=16 CPU experiment: strong gain at 1mm does not generalize across settings');fig.savefig(O/'parallel_layer_results.png',dpi=150);plt.close(fig)
# Fixed query0, no performance-based example selection.
prefix='C_8192__train__001__bilateral_trace';fig=plt.figure(figsize=(10,5))
for i,m in enumerate(['A','B']):
 z=np.load(O/(prefix+'_'+m+'_groups.npz'));p=z['neighbors_relative_mm'][0];ix=z['groups'][0];ax=fig.add_subplot(1,2,i+1,projection='3d');ax.scatter(*p[ix[:8]].T,c='#0072b2',s=35,label='group1');ax.scatter(*p[ix[8:]].T,c='#d55e00',s=35,label='group2');ax.scatter(0,0,0,c='black',marker='x',label='query');ax.set_title(m+' / actual C8k query0');ax.set_xlabel('dx mm');ax.set_ylabel('dy mm');ax.set_zlabel('dz mm');ax.set_box_aspect(np.maximum(np.ptp(p,axis=0),.1));ax.legend()
fig.suptitle('Saved actual graph2 neighborhood; groups are not anatomical labels');fig.tight_layout();fig.savefig(O/'fixed_actual_neighborhood_groups.png',dpi=150);plt.close(fig)
lines=['# 无定位双组局部表征：限定CPU检查报告 v1','日期：2026-11-02。单一PCA轴、k=16、8+8分组和原冻结阈值；没有定位器、模型加载、新GPU或训练。','## 结论','**科学准入失败，停止当前候选，不修改PCA轴或扩大邻域补救。**程序exit0，基础实现合同通过，失败发生在人工分层收益的适用范围及刚体分组稳定性。不能将该结果推广为所有多表面表征无效。','## 实现与范围','A按query距离排序后奇偶交错分组；B按16点协方差最小特征向量投影取前后各8点，最小特征值间隙不足时按冻结规则回退A。两组共有的组交换不变摘要使用max池化后concat(mean(s1,s2),abs(s1-s2))。本轮只以人工64维特征验证该摘要合同，未实施或训练Linear(128,64)、模型edge-MLP或任何学习分支。','完整范围：原有1/3/5mm双平面×8k/16k两种密度（只用既有k16，不比较k32）；三组既有球壳；单平面与未切球壳；六例8k历史CPU邻域近似；四模型已保存的512个实际graph2邻域。后者使用真实CUDA索引回读坐标，CPU近似与实际轨迹分开报告，不将二者混称。','点序合同仅在固定人工无平距随机邻域上严格检查，不声称全部平距数据均已验证。刚体检查旋转固定为z轴0.37rad；平移在相对坐标表示中抵消。不是完整SO(3)认证。','## 实现合同','9项检查通过：A/B各自均衡覆盖16邻居、组交换摘要不变、普通点序置换分组及融合一致；输入不变；协方差退化回退；错误形状及非有限值拒绝。CPU基础合同通过不等于科学假设成立。','## 人工双层','此处“层纯度”采用**两组与两真实层的最佳二元标签分配准确率**，允许整体组交换。它不是每组各自取多数标签后平均的普通purity；如果邻域全为同一层，固定8+8的该分数为50%，并不表示原邻域混合。另报告真正包含双层的邻域比例及条件准确率，防止误解。','|厚度|点数|双层邻域比例|A分配准确率|B分配准确率|B−A|','|---|---:|---:|---:|---:|---:|']
for x in r['parallel']:lines.append('|%.0fmm|%d|%.3f%%|%.3f%%|%.3f%%|%+.3fpp|'%(x['thickness_mm'],x['n'],100*x['A']['both_layers_present_fraction'],100*x['A']['best_label_swap_accuracy_mean'],100*x['B']['best_label_swap_accuracy_mean'],100*(x['B']['best_label_swap_accuracy_mean']-x['A']['best_label_swap_accuracy_mean'])))
lines+=['1mm两密度均有明显改善；3mm改善约6.204/0.270个百分点；5mm约0.049/0个百分点。按原门先在每厚度平均两个既有密度，仅1mm超过10个百分点，没有达到至少两厚度。5mm/16k所有邻域都只有一个真实层，不能把其50%分配分数解释为“算法把两层混合”。','在确实包含双层的3mm/8k邻域中，A/B准确率为56.211%/64.101%；3mm/16k为55.466%/59.321%。这说明条件下可能有局部收益，但不足以事后改成只报告有双层的容易子集来放行。','两组层间距估计使用组均值在已知真实法向上的投影差，仅作评价；没有将真法向输入B。无双层邻域的层间距缺失按原厚度计误差。各厚度平均误差未恶化，但不能因此证明真实薄骨厚度恢复正确。','## 刚体、球壳与真实邻域','人工非退化双平面邻域在固定旋转后的分组一致率（允许交换）并非100%：1mm约99.99%/99.97%；3mm约83.51%/27.74%；5mm约24.28%/22.54%。组交换对称融合不能解决跨组归属本身改变。共面投影平距、浮点微扰及排序可能相关，但本轮未额外重跑定位具体数值原因；不把此推断当作证实根因。','三组球壳的非J邻域中，A/B标签分配准确率均接近50%，B只增加约0.03–0.13个百分点，不是实质分层恢复。实际原生内/外侧由解析17/20mm半径近似标注；含J邻域只报告J邻居在两组中的均衡程度，不把切壁归成内外板。离散面及球壳曲率限制其解释。','单层平面与未切球壳仍被强制拆成两组，这属于设计行为；两个组存在不能证明检测出两侧骨面。球壳结果没有出现按本轮冻结规则判定的系统混合加重，但这只是未恶化门，不是正面有效性证据。','四份实际CUDA graph2邻域的B退化回退比例均0，固定旋转后的分组一致率分别为C8k99.414%、C16k99.023%、D8k99.414%、D16k98.633%。没有解剖层标签，不报告这些真实分组的内外板准确率。固定query0示例按清单选取，不依据表现挑选。','## 准入门与决定']
for k,v in r['gates'].items():lines.append('- '+k+': '+('PASS' if v else 'FAIL'))
lines+=['基础合同通过、任一厚度未下降超过5pp、平均层间距误差不增大及球壳未系统恶化均通过；但**人工非退化刚体分组一致性、至少两厚度增加10pp均失败**，因此不能进入模型实施或训练。','停止本固定PCA二分候选，不切换特征向量、不调整邻域、不继续平距修补后重跑。保留1mm情形的局部正结果和其他情形的负结果。下一步只宜汇总已有失败与有效条件，判断是否存在值得另立方案的有限问题；不要将目前证据直接包装成颅骨接口改善或Mamba创新。','## 完整性与资源',f'执行用时{r["seconds"]:.2f}秒，RSS采样峰值{r["RSS_sampled_peak_bytes"]} bytes；15分钟/8GiB/256MiB预算通过。既有六例输入NPZ与历史绑定SHA256核验，实际轨迹归档SHA256核验。没有读取新病例mask或修改原始数据。', 'scope.json保留事前门值解释与代码/协议哈希，results.json保留全部结果。实际模型特征未加载，不能由几何结果断言max-pooling是模型误差的确定来源。采样几何与实际模型改进的因果关系尚未建立。']
(O/'report_zh_v1.md').write_text('\n\n'.join(lines).replace('|\n\n|','|\n|'),encoding='utf-8');print('report and plots saved')
