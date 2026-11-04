"""Five-defect source-paired descriptive report from saved CPU artifacts."""
import os
from pathlib import Path
B=Path(__file__).resolve().parent;O=B/'blue_noise_defect_types_20261103_v1'
os.environ['MPLBACKEND']='Agg';os.environ['MPLCONFIGDIR']=str(B/'blue_noise_defect_types_plot_cache_v1')
import csv,hashlib,json
import numpy as np
import matplotlib.pyplot as plt
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):
    with p.open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False)
def csvout(p,rs):
    with p.open('x',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rs[0]));w.writeheader();w.writerows(rs)

complete=json.loads((O/'completion.json').read_text());protocol=json.loads((O/'protocol.json').read_text())
rows=json.loads((O/'metrics.json').read_text());manifest=json.loads((O/'contents.json').read_text())
assert complete['status']=='COMPLETED_ALL_FIVE_DEFECT_GEOMETRY_ONLY' and len(rows)==540
assert all((O/k).stat().st_size==v['bytes'] and sha(O/k)==v['sha256'] for k,v in manifest.items())
sources=protocol['sources'];types=['bilateral',*protocol['defect_types']]
methods=['V1_common_pool','Euclidean_elimination','surface_graph']
metrics={'J_own_cover05':('J','same_region','cover_0_5mm',100),
         'J_all_cover2':('J','unrestricted','cover_2mm',100),
         'E_all_cover2':('E','unrestricted','cover_2mm',100),
         'J_own_p95':('J','same_region','p95_mm',1),
         'J_own_cover1':('J','same_region','cover_1mm',100),
         'J_own_cover2':('J','same_region','cover_2mm',100)}
cases=[];seed_rows=[]
for source in sources:
    for defect in types:
        rr=[r for r in rows if r['source_id']==source and r['defect_type']==defect];assert len(rr)==9
        rec={'case':rr[0]['case'],'source_id':source,'defect_type':defect,'phase':'reused' if defect=='bilateral' else 'new'}
        for method in methods:
            subset=[r for r in rr if r['method']==method];assert {r['seed'] for r in subset}=={0,1,2}
            rec[method+'_J_count']=float(np.mean([r['regions']['J']['point_count'] for r in subset]))
            for key,(region,mode,metric,scale) in metrics.items():
                rec[method+'_'+key]=float(np.mean([r['regions'][region][mode][metric]*scale for r in subset]))
        for key in metrics:
            for base in ['Euclidean_elimination','V1_common_pool']:
                rec['graph_minus_'+base+'_'+key]=rec['surface_graph_'+key]-rec[base+'_'+key]
        cases.append(rec)
        for r in rr:
            rec={k:r[k] for k in ['case','source_id','defect_type','seed','method']}
            rec['J_count']=r['regions']['J']['point_count']
            for key,(region,mode,metric,scale) in metrics.items():rec[key]=r['regions'][region][mode][metric]*scale
            seed_rows.append(rec)
csvout(O/'case_level_metrics.csv',cases);csvout(O/'seed_level_metrics.csv',seed_rows)

def describe(values):
    a=np.array(values)
    return {'mean':float(a.mean()),'median':float(np.median(a)),'min':float(a.min()),'max':float(a.max()),
            'positive':int((a>1e-12).sum()),'negative':int((a< -1e-12).sum()),'ties':int((np.abs(a)<=1e-12).sum())}
summary={}
for defect in types:
    subset=[r for r in cases if r['defect_type']==defect];assert len(subset)==12
    summary[defect]={key:describe([r['graph_minus_Euclidean_elimination_'+key] for r in subset]) for key in metrics}
source_rows=[]
for source in sources:
    subset=[r for r in cases if r['source_id']==source];assert len(subset)==5
    rec={'source_id':source,'defects_averaged':5,'seeds_per_defect':3}
    for key in metrics:
        rec['graph_minus_Euclidean_'+key]=float(np.mean([r['graph_minus_Euclidean_elimination_'+key] for r in subset]))
        for method in methods:rec[method+'_'+key]=float(np.mean([r[method+'_'+key] for r in subset]))
    source_rows.append(rec)
csvout(O/'five_defect_source_level_metrics.csv',source_rows)
summary['five_defect_source_equal']={key:describe([r['graph_minus_Euclidean_'+key] for r in source_rows]) for key in metrics}
dump(O/'defect_stability_summary.json',summary)

fig,axs=plt.subplots(1,2,figsize=(14,7.5),layout='constrained')
for ax,key,title in [(axs[0],'J_own_cover05','Own-wall Cover@0.5mm delta (pp)'),(axs[1],'J_all_cover2','All-point wall Cover@2mm delta (pp)')]:
    a=np.array([[next(r for r in cases if r['source_id']==source and r['defect_type']==defect)['graph_minus_Euclidean_elimination_'+key] for defect in types] for source in sources])
    vmax=max(float(np.abs(a).max()),.001);im=ax.imshow(a,aspect='auto',cmap='RdBu',vmin=-vmax,vmax=vmax)
    ax.set_xticks(range(5),types,rotation=30,ha='right');ax.set_yticks(range(12),[s.split(':')[-1] for s in sources]);ax.set_ylabel('SkullBreak source')
    ax.set_title(title,fontsize=11)
    for i in range(12):
        for j in range(5):ax.text(j,i,f'{a[i,j]:+.2f}',ha='center',va='center',fontsize=8,color='white' if abs(a[i,j])>.6*vmax else 'black')
    fig.colorbar(im,ax=ax,shrink=.75,label='Graph minus Euclidean; mean of 3 seeds')
fig.suptitle('Same 12 sources, all 5 defects; fixed sampling rules',fontsize=13)
fig.savefig(O/'defect_source_heatmap.png',dpi=170);plt.close(fig)

names={'J_own_cover05':'切壁自身Cover@0.5mm','J_all_cover2':'切壁总体Cover@2mm','E_all_cover2':'其它边界Cover@2mm','J_own_p95':'切壁自身P95（下降更好）'}
lines=['# SkullBreak五类缺损：固定采样规则的适用性核验',
       '', '启动日期：2026-11-03；完成日期：2026-11-04。目录名保留启动日期。已完成同12个已开放来源的另外四类缺损48例，原bilateral 12例直接复用。合计60病例、三个种子、三种方法、540条评分。',
       '', '## 范围与不变项',
       '', '四类新增缺损为frontoorbital、parietotemporal、random_1、random_2，均为既有固定mask，不是重新构造缺损。没有新来源、没有访问封存／官方测试数据。',
       '', '复用上一轮逐例函数，仅替换输出根目录和冻结的病例清单。32768候选点、8192输入点、种子0/1/2、指数8、R=2√(面积/8192)、欧氏与原表面图实现、原始面中心评价参考均不变。全部九份输入先保存，再读取该例implant推导J评价标签；不使用J选点。',
       '', '真实内外板没有可信标签：J仅指D/G共享切壁，E为残缺输入骨D上的其余边界；这里的E不是模型输出评分中待补骨块的未知表面。图距离仍是保守的离散路径近似，不是连续精确测地距离。V1为共同32768点池的面积随机前8192点，与历史训练采样同分布，但不宣称历史训练坐标逐字节复用。',
       '', '## 按缺损类型报告配对差值',
       '', '每例先平均三个种子；下表每类12个来源，差值均为图版减欧氏版。覆盖单位百分点，P95单位mm。正负计数不等于显著性检验。',
       '', '| 缺损类型 | 指标 | 均值差 | 中位差 | 正／负／持平来源 | 范围 |',
       '|---|---|---:|---:|---|---|']
for defect in types:
    for key,label in names.items():
        v=summary[defect][key]
        lines.append(f"| {defect} | {label} | {v['mean']:+.3f} | {v['median']:+.3f} | {v['positive']}/{v['negative']}/{v['ties']} | {v['min']:+.3f}至{v['max']:+.3f} |")
lines+=['', '![来源与缺损配对差值](defect_source_heatmap.png)',
        '', '蓝色表示图版覆盖增加，红色表示下降。每格是同一来源、同一缺损的三种子均值；不能把60格当成60个独立患者。全部退化格保留。',
        '', '## 五类平均后的来源级结果',
        '', '每个来源先平均五种缺损，再对12来源等权汇总；有效来源数为12。没有bootstrap、p值或正式gate。',
        '', '| 指标 | 图－欧氏均值 | 中位数 | 正／负／持平来源 |',
        '|---|---:|---:|---|']
for key,label in names.items():
    v=summary['five_defect_source_equal'][key]
    lines.append(f"| {label} | {v['mean']:+.3f} | {v['median']:+.3f} | {v['positive']}/{v['negative']}/{v['ties']} |")
lines+=['', '## 分类型绝对覆盖',
        '', '| 缺损 | 方法 | J自身Cover@0.5mm % | J总体Cover@2mm % | E总体Cover@2mm % |',
        '|---|---|---:|---:|---:|']
for defect in types:
    sub=[r for r in cases if r['defect_type']==defect]
    for method in methods:
        v=[np.mean([r[method+'_'+key] for r in sub]) for key in ['J_own_cover05','J_all_cover2','E_all_cover2']]
        lines.append('| '+defect+' | '+method+' | '+' | '.join(f'{x:.3f}' for x in v)+' |')
lines+=['', '## 可靠性与适用边界',
        '', '- 新增48例的432份点集均为原候选池的8192点子集。科学核心与输入哈希不变；原有bilateral未重复执行。',
        '- 缺损类型共享相同来源，报告按来源分层，不把多个缺损或随机种子计为独立患者；所有来源已开放且参与过开发研究，不是最终确认集。',
        '- 不能用总体均值隐藏某一缺损类型的退化，也不按类型或病例挑选更有利采样器拼接为新方法。',
        '- 该对照不能把效果唯一归因于跨内外板竞争：真实曲面绕行、体素阶梯、歧义边阻断及图离散偏差均参与距离定义。没有真实内外板完整保留或模型精度的证明。',
        '- 本轮仅完成训练前科研适用性检查，不创建训练执行内容；后续模型比较需另行冻结数据与训练合同。',
        '',f"本机CPU总用时{complete['seconds']:.1f}秒，总RSS监测峰值{complete['monitored_aggregate_RSS_peak_bytes']/1024**3:.3f}GiB；监测不是硬隔离。未使用GPU、连接服务器、修改采样参数或启动训练。", 
        '', '完整逐例见case_level_metrics.csv，来源平均见five_defect_source_level_metrics.csv，逐种子见seed_level_metrics.csv。']
with (O/'report_zh_v1.md').open('x',encoding='utf-8') as f:f.write('\n'.join(lines)+'\n')
dump(O/'report_verification.json',{'status':'SAVED_CONTENT_VERIFICATION_PASS','manifest_files':len(manifest),
  'case_rows':len(cases),'source_rows':len(source_rows),'seed_rows':len(seed_rows),
  'files':{n:sha(O/n) for n in ['case_level_metrics.csv','seed_level_metrics.csv','five_defect_source_level_metrics.csv','defect_stability_summary.json','defect_source_heatmap.png','report_zh_v1.md']}})
print('FIVE_TYPE_REPORT_COMPLETE')
