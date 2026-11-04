"""Read completed geometry artifacts; write paired results, no experiment rerun."""
import os
from pathlib import Path
B=Path(__file__).resolve().parent;O=B/'blue_noise_real_surface_graph_20261103_v1'
os.environ['MPLBACKEND']='Agg';os.environ['MPLCONFIGDIR']=str(B/'blue_noise_real_surface_graph_plot_cache_v1')
import csv,hashlib,json
import numpy as np
import matplotlib.pyplot as plt

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
s=json.loads((O/'summary.json').read_text());rows=json.loads((O/'metrics.json').read_text());manifest=json.loads((O/'contents.json').read_text())
assert s['status']=='COMPLETED_REAL_SURFACE_GRAPH_CPU_ONLY' and len(rows)==54
assert all((O/k).stat().st_size==v['bytes'] and sha(O/k)==v['sha256'] for k,v in manifest.items())
methods=['V1_common_pool','Euclidean_elimination','surface_graph'];cases=sorted({r['case'] for r in rows})
paired=[]
for cid in cases:
    for region in ['J','E']:
        for mode in ['same_region','unrestricted']:
            for seed in [0,1,2]:
                rr={r['method']:r for r in rows if r['case']==cid and r['seed']==seed}
                rec={'case':cid,'region':region,'mode':mode,'seed':seed}
                for method in methods:
                    rec[method+'_point_count']=rr[method]['regions'][region]['point_count']
                    for k,v in rr[method]['regions'][region][mode].items():rec[method+'_'+k]=v
                for baseline in ['V1_common_pool','Euclidean_elimination']:
                    for k in ['cover_0_5mm','cover_1mm','cover_2mm','p95_mm']:
                        rec['delta_graph_minus_'+baseline+'_'+k]=rec['surface_graph_'+k]-rec[baseline+'_'+k]
                paired.append(rec)
with (O/'paired_metrics.csv').open('x',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(paired[0]));w.writeheader();w.writerows(paired)
def avg(cid,method,region,mode,key):
    return float(np.mean([r['regions'][region][mode][key] for r in rows if r['case']==cid and r['method']==method]))
def count(cid,method):return float(np.mean([r['regions']['J']['point_count'] for r in rows if r['case']==cid and r['method']==method]))
panels=[('J','same_region','cover_0_5mm','Cut-wall own-point Cover@0.5mm delta (pp)',100),
        ('J','unrestricted','cover_2mm','Cut-wall all-point Cover@2mm delta (pp)',100),
        ('E','unrestricted','cover_2mm','Other-boundary Cover@2mm delta (pp)',100),
        ('J','same_region','p95_mm','Cut-wall own-point P95 delta (mm)',1)]
fig,axs=plt.subplots(2,2,figsize=(12,8),layout='constrained');labels=[c.replace('SkullBreak_train__','SB ').replace('__bilateral','').replace('SkullFix_','SF ') for c in cases]
for ax,(region,mode,key,title,scale) in zip(axs.ravel(),panels):
    for bi,baseline in enumerate(['V1_common_pool','Euclidean_elimination']):
        values=np.array([[scale*(next(r for r in rows if r['case']==cid and r['seed']==seed and r['method']=='surface_graph')['regions'][region][mode][key]-
                                 next(r for r in rows if r['case']==cid and r['seed']==seed and r['method']==baseline)['regions'][region][mode][key]) for seed in [0,1,2]] for cid in cases])
        m=values.mean(1);xx=np.arange(len(cases))+(bi-.5)*.34
        ax.bar(xx,m,.34,color=['#0072B2','#E69F00'][bi],label='graph minus '+('V1' if bi==0 else 'Euclidean'))
        ax.errorbar(xx,m,yerr=np.vstack([m-values.min(1),values.max(1)-m]),fmt='none',ecolor='#333333',linewidth=.8,capsize=2)
    ax.axhline(0,color='#555555',linewidth=.8);ax.set_xticks(range(len(cases)),labels,rotation=30,ha='right');ax.set_title(title,fontsize=10)
    ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
axs[0,0].legend(fontsize=8);fig.suptitle('Six existing cases; N=8192; mean and range of three paired seeds',fontsize=12)
fig.savefig(O/'paired_geometry.png',dpi=160);plt.close(fig)
lines=['# 真实六例：原始体素边界邻接图距离采样对照',
       '', '日期：2026-11-03。仅本机CPU几何验证；未训练、使用GPU、操作服务器或修改生产采样器。',
       '', '## 研究范围',
       '', '在此前开放的SkullFix 002/003/004和SkullBreak train 000/001/002 bilateral上，保持原始完整骨边界、32768点候选池、8192输入点、固定核规则及评价参考，比较V1、已有欧氏样本消除和本次原始表面图距离版本。三个种子；共54个方法×病例×种子评分记录。六例是重复用于方法诊断的开放来源，不是全新最终检验集。',
       '', '## 图的定义与限制',
       '', '原始暴露体素四边形只在共享完整边且恰好两个面相交处连接。四面相交歧义边阻断并计数；仅顶点接触的独立表面不连接。除共享边中点路径外，加入经过同一中间面角点的合法路径，减少平面图的方向偏差；不进行Marching Cubes、平滑、删岛或填孔。',
       '', '距离为点到所在面中心、图上最短路径、中心到目标点构成的合法表面路径长度；同一面用直线距离，相邻面用沿共享边展开的局部精确路径改进。核仍为max(0,1-d/R)^8，R保持原冻结的2√(面积/8192)。',
       '', '**这是保守的离散表面路径近似，不是连续精确测地距离。**平面面中心标定示例相对误差约7.97%，并不构成所有点端偏移或曲面误差的界。真实距离增加同时包含合法曲率、体素阶梯、跨层绕行与数值近似，不能将核变化全部归因于阻断跨层。',
       '', '历史完整候选池未单独保存，本次用原始未改动采样器和种子重建；前8192点与V1保存坐标逐点完全一致，欧氏保留索引对应坐标也逐点完全一致。新方法保留索引先保存，然后读取implant推导J评价标签；不使用GT指导选点。',
       '', '## 切壁自身支持：三个种子均值',
       '', 'J为真实D/G共享切壁；同区域测距只使用J点。E为其余全部骨边界，不等于外板。',
       '', '| 病例 | 方法 | J点数 | J自身Cover@0.5mm % | J自身Cover@1mm % | J自身Cover@2mm % | J自身P95 mm |',
       '|---|---|---:|---:|---:|---:|---:|']
for cid in cases:
    for method in methods:
        lines.append(f"| {cid} | {method} | {count(cid,method):.2f} | {100*avg(cid,method,'J','same_region','cover_0_5mm'):.3f} | {100*avg(cid,method,'J','same_region','cover_1mm'):.3f} | {100*avg(cid,method,'J','same_region','cover_2mm'):.3f} | {avg(cid,method,'J','same_region','p95_mm'):.3f} |")
lines+=['', '## 与已有欧氏候选的配对变化',
        '', '| 病例 | J自身0.5mm覆盖变化pp | J总体2mm覆盖变化pp | E总体2mm覆盖变化pp | J自身P95变化mm |',
        '|---|---:|---:|---:|---:|']
for cid in cases:
    vals=[]
    for reg,mode,k,scale in [('J','same_region','cover_0_5mm',100),('J','unrestricted','cover_2mm',100),('E','unrestricted','cover_2mm',100),('J','same_region','p95_mm',1)]:
        vals.append(scale*(avg(cid,'surface_graph',reg,mode,k)-avg(cid,'Euclidean_elimination',reg,mode,k)))
    lines.append('| '+cid+' | '+' | '.join(f'{v:+.3f}' for v in vals)+' |')
lines+=['', '![配对几何差值](paired_geometry.png)',
        '', '柱为三个种子均值，误差线为最小—最大范围，不是置信区间。完整逐种子和V1对照数据见paired_metrics.csv。不能只看近饱和的2mm覆盖忽略亚毫米细支持。',
        '', '## 表面图与原始拓扑记录',
        '', '| 病例 | 原始暴露面数 | 阻断歧义边数 | 图连通分量 | 有限核内图距离/欧氏距离中位数（三种子均值） |',
        '|---|---:|---:|---:|---:|']
for g in s['geometry']:
    ratio=np.mean([p['median_ratio_graph_to_Euclidean_for_retained_pairs'] for p in g['path_diagnostics']])
    lines.append(f"| {g['case']} | {g['faces']} | {g['blocked_ambiguous_original_edges']} | {g['components']} | {ratio:.3f} |")
lines+=['', '原始非连通结构没有被删除；图分量数不是解剖结构数。歧义边阻断是保守选择，可能切断真实应连通的路径；不能把所有阻断边解释为伪结构。以上距离比也不是数值误差估计，不能区分真实表面绕行与图离散偏差。',
        '', '## 核验与判断边界',
        '', '- 人工闭盒连通、平面标定、四面相交边阻断及仅顶点接触不连通检查通过。54条评分中的V1和欧氏历史覆盖值复现；原始输入及旧工具哈希不变。',
        '- 18份新点集均为冻结候选池的原坐标子集，未改变目标点集、坐标归一化或模型；选择时未使用J/E或真实解剖标签。',
        '- 当前真实数据没有可信的内外板解剖标注，只能核查原始表面连接和J/E支持，不能据此宣布真实内外板完整保留。',
        '- 这只检验一个离散表面图版本，不是测地算法普遍优劣的证明。结果不自动授权模型训练或改变生产默认。',
        '',f"CPU实验总用时{s['seconds']:.1f}秒；检查点RSS峰值{s['checkpoint_peak_RSS_bytes']/1024**3:.3f}GiB，不是硬内存隔离。报告阶段只读取既有产物，不重新采样或重复实验。"]
with (O/'report_zh_v1.md').open('x',encoding='utf-8') as f:f.write('\n'.join(lines)+'\n')
verification={'status':'SAVED_CONTENT_VERIFICATION_PASS','manifest_files':len(manifest),'metric_rows':len(rows),'paired_rows':len(paired),
              'new_artifacts':{n:sha(O/n) for n in ['paired_metrics.csv','paired_geometry.png','report_zh_v1.md']}}
with (O/'report_verification.json').open('x',encoding='utf-8') as f:json.dump(verification,f,ensure_ascii=False,indent=2)
print(json.dumps(verification,ensure_ascii=False))
