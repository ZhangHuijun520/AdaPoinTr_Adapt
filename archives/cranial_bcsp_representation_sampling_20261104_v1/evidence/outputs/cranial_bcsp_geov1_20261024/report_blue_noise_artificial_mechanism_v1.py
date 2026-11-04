"""Report saved artificial-mechanism experiment, without re-executing geometry."""
import os
from pathlib import Path
B=Path(__file__).resolve().parent;O=B/'blue_noise_artificial_mechanism_20261103_v1'
os.environ['MPLBACKEND']='Agg';os.environ['MPLCONFIGDIR']=str(B/'blue_noise_artificial_mechanism_plot_cache_v1')
import csv,hashlib,json
import numpy as np
import matplotlib.pyplot as plt

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
rows=json.loads((O/'metrics.json').read_text());logs=json.loads((O/'deletion_summary.json').read_text());summary=json.loads((O/'summary.json').read_text())
manifest=json.loads((O/'contents.json').read_text())
assert summary['status']=='COMPLETED_ARTIFICIAL_MECHANISM_ONLY' and len(rows)==36
assert all((O/k).stat().st_size==v['bytes'] and sha(O/k)==v['sha256'] for k,v in manifest.items())
methods=['Euclidean','no_opposite_shortcut','intrinsic_unrolled'];geometries=['flat_control','U_t0.5','U_t1.0','U_t3.0']
def group(geom,method):return [r for r in rows if r['geometry']==geom and r['method']==method]
def mean(geom,method,reg,key):return float(np.mean([r['regions'][reg]['same_patch'][key] for r in group(geom,method)]))
flat=[]
for r in rows:
    for patch in ['lower','wall','upper']:
        v=r['regions'][patch]
        flat.append({'geometry':r['geometry'],'seed':r['seed'],'method':r['method'],'patch':patch,'count':v['count'],
          **{'same_patch_'+k:x for k,x in v['same_patch'].items()},**{'all_intrinsic_'+k:x for k,x in v['intrinsic_all_points'].items()},
          **{'all_Euclidean_'+k:x for k,x in v['Euclidean_all_points'].items()}})
with (O/'paired_patch_metrics.csv').open('x',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(flat[0]));w.writeheader();w.writerows(flat)
fig,axs=plt.subplots(1,2,figsize=(12,4.6),layout='constrained');x=np.arange(4);width=.24
colors=['#0072B2','#E69F00','#009E73'];short=['Euclidean','Remove opposite shortcuts','Exact intrinsic']
for mi,method in enumerate(methods):
    c=np.array([[r['regions']['wall']['same_patch']['cover_1mm']*100 for r in group(g,method)] for g in geometries])
    counts=np.array([[r['regions']['wall']['count'] for r in group(g,method)] for g in geometries]);xx=x+(mi-1)*width
    for ax,a,title in [(axs[0],c,'Wall same-patch Cover@1mm (%)'),(axs[1],counts,'Retained wall points')]:
        m=a.mean(1);ax.bar(xx,m,width,color=colors[mi],label=short[mi]);ax.errorbar(xx,m,yerr=np.vstack([m-a.min(1),a.max(1)-m]),fmt='none',ecolor='#333333',capsize=2,linewidth=.8)
        ax.set_title(title,fontsize=11);ax.set_xticks(x,['Flat','U 0.5mm','U 1mm','U 3mm']);ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
axs[0].legend(fontsize=8);fig.suptitle('Same pool, N=8192, fixed kernel rule; bars=three-seed means, whiskers=range',fontsize=11)
fig.savefig(O/'wall_mechanism.png',dpi=170);plt.close(fig)

lines=['# 人工几何机制对照：同表面拥挤与跨表面捷径',
       '', '日期：2026-11-03。仅人工几何、本机CPU；未读取真实病例、改生产代码、使用GPU或训练。',
       '', '## 问题与可识别范围',
       '', '检验普通欧氏样本消除中，对侧板面之间的三维近邻是否改变保留结果；并区分移除这种捷径与改变合法切壁转折处距离的影响。该试验是人工几何机制干预，不是颅骨任务精度验证。',
       '', '## 冻结设计',
       '', 'U形表面由两块80×80mm平行板及80×t mm切壁连接，t固定为0.5/1/3mm；另有t=1mm的完全展开平面负对照。每个表面是一个连通的可展曲面，开放端不是闭合骨实体，不能直接替代颅骨。内侧距离在展开矩形(s,y)上精确计算，无KNN近似路径。',
       '', '每个几何三个种子，各32768个物理面积随机候选点，共用同一候选池，消除至8192点。核函数(1-d/R)^8和R=2√(面积/8192)保持不变，无半径扫描、无点移动。三种处理：',
       '', '- **Euclidean**：所有三维距离小于R的点对参与排斥。',
       '- **no_opposite_shortcut**：只移除“分属对侧板面、展开距离大于R、欧氏距离小于R”的点对。保持同面拥挤、切壁连接及近切壁合法跨板路径；不是按标签完全隔离曲面。',
       '- **intrinsic_unrolled**：所有权重用精确展开距离计算；还会改变切壁转折附近的距离，因此不能把它的全部收益归因于对侧捷径。',
       '', '每次删除均保存点索引及当时存活邻居的三类核权重：同面、连接邻面、对侧远路径捷径。与上一轮仅用最终存活点估计不同，本轮有实际删除时刻日志。但两个处理的删除顺序会改变，不把相同步号当成同一个点的反事实。',
       '', '## 三种子均值：切壁支持',
       '', '| 几何 | 方法 | 切壁点数 | 同壁Cover@0.5mm % | 同壁Cover@1mm % | 同壁Cover@2mm % | 同壁P95 mm |',
       '|---|---|---:|---:|---:|---:|---:|']
for geom in geometries:
    for method in methods:
        rr=group(geom,method);n=np.mean([r['regions']['wall']['count'] for r in rr])
        lines.append(f"| {geom} | {method} | {n:.2f} | {mean(geom,method,'wall','cover_0_5mm')*100:.3f} | {mean(geom,method,'wall','cover_1mm')*100:.3f} | {mean(geom,method,'wall','cover_2mm')*100:.3f} | {mean(geom,method,'wall','p95_mm'):.3f} |")
lines+=['', '![切壁机制结果](wall_mechanism.png)',
        '', '误差线只是三个随机种子的最小—最大范围，不是置信区间。same-patch距离只使用该切壁上的点，避免对侧板点造成虚假的近距离覆盖。CSV同时保存全部点的欧氏及精确曲面内距离指标。',
        '', '## 相邻板面是否付出代价',
        '', '| 几何 | 方法 | 下板同面Cover@1mm % | 上板同面Cover@1mm % |',
        '|---|---|---:|---:|']
for geom in geometries:
    for method in methods:
        lines.append(f"| {geom} | {method} | {100*mean(geom,method,'lower','cover_1mm'):.3f} | {100*mean(geom,method,'upper','cover_1mm'):.3f} |")
lines+=['', '## 删除时刻的直接证据',
        '', '| 几何 | 普通欧氏：下板删除时捷径核平均占比 % | 上板 % | 初始捷径点对数量（种子均值） |',
        '|---|---:|---:|---:|']
for geom in geometries:
    def share(patch):return float(np.mean([r['mean_live_weight_share'][2] for r in logs if r['geometry']==geom and r['method']=='Euclidean' and r['patch']==patch]))
    pairs=np.mean([r['edges']['shortcut_pairs'] for r in group(geom,'Euclidean')])
    lines.append(f'| {geom} | {100*share("lower"):.3f} | {100*share("upper"):.3f} | {pairs:.1f} |')
lines+=['', '捷径核占比说明实际删除时对侧远路径点参与过排斥，不等于“这个点一定因捷径而被删”。完整配对处理才检验移除这些边之后的最终结果。切壁点不是对侧板面捷径的直接端点，其点数变化也可能通过全局8192预算间接发生。',
        '', '## 验证与局限',
        '', '- 平面负对照三个种子的三组最终索引完全一致：没有折叠时，欧氏距离与精确展开距离一致；同面去拥挤的作用保留。',
        '- 堆删除与人工小集合的全量贪心删除顺序一致；合法切壁连接保留，对侧远路径分类通过；各输出恰好8192点。',
        '- 人工厚度是几何条件，核规则始终固定；不是调半径寻找收益。切壁为解析平面，不能模拟真实体素阶梯、曲面拓扑、孔腔或分割错误。',
        '- 两板并无患者解剖内外板身份，展开坐标在真实颅骨上不可直接获得。无新增真实数据、无临床推广结论、无模型收益结论。',
        '',f"实验{summary['seconds']:.1f}秒，检查点RSS峰值{summary['checkpoint_RSS_peak_bytes']/1024**3:.3f}GiB；原采样器哈希不变。原始12个候选池、36组保留索引及36份逐步删除日志已保存并回读哈希核验。", 
        '', '结论须结合上表逐项判断，不能预设表面邻接约束必胜。']
with (O/'report_zh_v1.md').open('x',encoding='utf-8') as f:f.write('\n'.join(lines)+'\n')
verification={'status':'SAVED_CONTENT_VERIFICATION_PASS','original_manifest_files':len(manifest),'patch_rows':len(flat),'no_experiment_rerun':True,
              'new_artifacts':{n:sha(O/n) for n in ['report_zh_v1.md','paired_patch_metrics.csv','wall_mechanism.png']}}
with (O/'report_verification.json').open('x',encoding='utf-8') as f:json.dump(verification,f,ensure_ascii=False,indent=2)
print(json.dumps(verification,ensure_ascii=False))
