"""Source-level descriptive readout; no geometry rerun, gate or bootstrap."""
import os
from pathlib import Path
B=Path(__file__).resolve().parent;O=B/'blue_noise_surface_graph_expanded_20261103_v1'
os.environ['MPLBACKEND']='Agg';os.environ['MPLCONFIGDIR']=str(B/'blue_noise_surface_graph_expanded_plot_cache_v1')
import csv,hashlib,json
import numpy as np
import matplotlib.pyplot as plt
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):
    with p.open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False)
def csvout(p,rows):
    with p.open('x',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

complete=json.loads((O/'completion.json').read_text());protocol=json.loads((O/'protocol.json').read_text());rows=json.loads((O/'metrics.json').read_text())
manifest=json.loads((O/'contents.json').read_text())
assert complete['status']=='COMPLETED_EXPANDED_GEOMETRY_ONLY' and len(rows)==216
assert all((O/k).stat().st_size==v['bytes'] and sha(O/k)==v['sha256'] for k,v in manifest.items())
methods=['V1_common_pool','Euclidean_elimination','surface_graph']
keys={'J_own_cover05':('J','same_region','cover_0_5mm',100),
      'J_all_cover2':('J','unrestricted','cover_2mm',100),
      'E_all_cover2':('E','unrestricted','cover_2mm',100),
      'J_own_p95':('J','same_region','p95_mm',1),
      'J_own_cover1':('J','same_region','cover_1mm',100),
      'J_own_cover2':('J','same_region','cover_2mm',100)}
sources=[];seedrows=[]
for c in protocol['cases']:
    rr=[r for r in rows if r['case']==c['case']];assert len(rr)==9
    rec={k:c[k] for k in ['case','dataset','source_id','phase','split']}
    for method in methods:
        sub=[r for r in rr if r['method']==method];assert {r['seed'] for r in sub}=={0,1,2}
        rec[method+'_J_count']=float(np.mean([r['regions']['J']['point_count'] for r in sub]))
        for key,(region,mode,metric,scale) in keys.items():rec[method+'_'+key]=float(np.mean([r['regions'][region][mode][metric]*scale for r in sub]))
    for key in keys:
        rec['delta_graph_minus_Euclidean_'+key]=rec['surface_graph_'+key]-rec['Euclidean_elimination_'+key]
        rec['delta_graph_minus_V1_'+key]=rec['surface_graph_'+key]-rec['V1_common_pool_'+key]
    sources.append(rec)
    for r in rr:
        rec={k:r[k] for k in ['case','dataset','source_id','phase','seed','method']}
        rec['J_count']=r['regions']['J']['point_count']
        for key,(region,mode,metric,scale) in keys.items():rec[key]=r['regions'][region][mode][metric]*scale
        seedrows.append(rec)
csvout(O/'source_level_metrics.csv',sources);csvout(O/'seed_level_metrics.csv',seedrows)
summary={}
for ds in ['SkullFix','SkullBreak']:
    for phase in ['prior_six','new_expansion','all']:
        sub=[r for r in sources if r['dataset']==ds and (phase=='all' or r['phase']==phase)]
        assert len(sub)==({'prior_six':3,'new_expansion':9,'all':12}[phase])
        record={'sources':len(sub),'metrics':{}}
        for key in keys:
            v=np.array([r['delta_graph_minus_Euclidean_'+key] for r in sub]);record['metrics'][key]={
                'mean':float(v.mean()),'median':float(np.median(v)),'min':float(v.min()),'max':float(v.max()),
                'positive_sources':int((v>1e-12).sum()),'negative_sources':int((v< -1e-12).sum()),'ties':int((np.abs(v)<=1e-12).sum())}
        summary[ds+'/'+phase]=record
dump(O/'source_stability_summary.json',summary)

fig,axs=plt.subplots(2,2,figsize=(13,8),layout='constrained')
for rowidx,ds in enumerate(['SkullBreak','SkullFix']):
    sub=[r for r in sources if r['dataset']==ds];x=np.arange(12)
    for col,key in enumerate(['J_own_cover05','J_all_cover2']):
        ax=axs[rowidx,col];v=np.array([r['delta_graph_minus_Euclidean_'+key] for r in sub])
        ax.axhline(0,color='#555555',linewidth=.9);ax.axvline(2.5,color='#999999',linestyle='--',linewidth=.8)
        ax.scatter(x[:3],v[:3],s=45,c='#888888',marker='o',label='Original 3')
        ax.scatter(x[3:],v[3:],s=45,c='#0072B2',marker='D',label='Additional 9')
        ax.set_xticks(x,[r['source_id'].split(':')[-1] for r in sub],rotation=45,ha='right')
        ax.set_title(ds+': '+('own-wall Cover@0.5mm' if col==0 else 'all-point wall Cover@2mm'),fontsize=11)
        ax.set_ylabel('Graph minus Euclidean (percentage points)');ax.set_xlabel('Source ID; means of three paired seeds')
        ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
        if rowidx==0 and col==0:ax.legend(fontsize=8)
fig.suptitle('Fixed sampling rules: source expansion, no parameter tuning',fontsize=13)
fig.savefig(O/'source_stability.png',dpi=170);plt.close(fig)

lines=['# 扩大已开放来源：欧氏与表面图采样的配对几何核验',
       '', '日期：2026-11-03。已完成限定本机CPU核验，不涉及训练、GPU、服务器或部署。',
       '', '## 范围与方法',
       '', '每数据集从原3个来源扩大到12个，合计24个来源。原六例直接复用哈希绑定的既有结果；新增18例各完成三个种子、三种采样，合计216条方法×病例×种子评分。新增来源依据冻结的SHA256顺序选择，不看结果；不是按有利或退化病例挑选。',
       '', 'SkullFix来源来自已开放90例，SkullBreak来自已开放84来源，但本轮仍仅比较bilateral缺损，一来源一病例，不能外推其余四类缺损。三个种子先在来源内平均；患者来源数是12，不是36。新增9来源单列，用来避免原例子主导判断。',
       '', '保持32768面积随机候选点、8192输入点、(1-d/R)^8及R=2√(面积/8192)。欧氏与原始表面图距离版本均调用未改动的科学实现。图仍采用共享完整边、歧义边阻断、面中心／角点合法路径和同面／相邻面局部精确改进；没有半径扫描、权重追加或图方法修补。',
       '', '全部九份输入点集先保存，再解码该病例implant并推导J标签用于评价。GT、原始数据和生产点集均不修改。引用面仍是全部原生暴露面的中心与物理面积权重；真实数据没有可信的内外板标签，J是共享切壁，E是其余边界。本轮V1指共同32768候选池的面积随机前8192点，与历史训练V1同分布，但不声称全部历史训练点坐标逐字节复用。',
       '', '## 新增9来源：是否重复原方向',
       '', '下表仅使用新增来源；差值均为图版减欧氏版，覆盖单位为百分点，P95单位mm。正负来源数按三个种子均值判断，不做显著性／正式gate。',
       '', '| 数据 | 指标 | 均值差 | 中位差 | 正／负／持平来源 | 范围 |',
       '|---|---|---:|---:|---|---|']
names={'J_own_cover05':'切壁自身Cover@0.5mm','J_all_cover2':'切壁总体Cover@2mm','E_all_cover2':'其它边界总体Cover@2mm','J_own_p95':'切壁自身P95（下降更好）'}
for ds in ['SkullBreak','SkullFix']:
    for key,label in names.items():
        v=summary[ds+'/new_expansion']['metrics'][key]
        lines.append(f"| {ds} | {label} | {v['mean']:+.3f} | {v['median']:+.3f} | {v['positive_sources']}/{v['negative_sources']}/{v['ties']} | {v['min']:+.3f}至{v['max']:+.3f} |")
lines+=['', '## 原3例与新增9例的比较',
        '', '| 数据 | 范围 | 切壁自身0.5mm覆盖平均差pp | 切壁总体2mm覆盖平均差pp |',
        '|---|---|---:|---:|']
for ds in ['SkullBreak','SkullFix']:
    for phase in ['prior_six','new_expansion','all']:
        ss=summary[ds+'/'+phase]['metrics']
        lines.append(f"| {ds} | {phase} | {ss['J_own_cover05']['mean']:+.3f} | {ss['J_all_cover2']['mean']:+.3f} |")
lines+=['', '![来源级方向](source_stability.png)',
        '', '每个点是一个来源的三个种子均值；灰色为原3来源，蓝色为新增9来源。图中没有将多个随机种子当作独立患者。',
        '', '## 全12来源的绝对覆盖',
        '', '| 数据 | 方法 | J自身Cover@0.5mm % | J总体Cover@2mm % | E总体Cover@2mm % |',
        '|---|---|---:|---:|---:|']
for ds in ['SkullBreak','SkullFix']:
    sub=[r for r in sources if r['dataset']==ds]
    for method in methods:
        vals=[float(np.mean([r[method+'_'+key] for r in sub])) for key in ['J_own_cover05','J_all_cover2','E_all_cover2']]
        lines.append('| '+ds+' | '+method+' | '+' | '.join(f'{v:.3f}' for v in vals)+' |')
lines+=['', '## 全部来源与退化记录',
        '', '| 数据／来源 | 阶段 | J自身0.5mm差pp | J总体2mm差pp | E总体2mm差pp |',
        '|---|---|---:|---:|---:|']
for r in sources:
    lines.append(f"| {r['dataset']} {r['source_id']} | {r['phase']} | {r['delta_graph_minus_Euclidean_J_own_cover05']:+.3f} | {r['delta_graph_minus_Euclidean_J_all_cover2']:+.3f} | {r['delta_graph_minus_Euclidean_E_all_cover2']:+.3f} |")
lines+=['', '## 可靠性与限制',
        '', '- 18个新增病例的162份点集均精确8192点，三方法使用同一病例／种子的候选池；六个旧病例没有重新执行。',
        '- 科学核心文件、选定原始D/G、既有点集和目标所在文件哈希均保持不变。报告阶段验证保存内容清单，不重新执行几何。',
        '- 图距离仍是保守的离散路径近似，不是连续精确测地距离；变化混合了曲率、体素阶梯、跨层绕行和离散偏差。不能把差异唯一归因于内外板竞争。',
        '- 这不是未使用测试集：所有来源此前已开放，部分曾用于其它候选几何研究。因此只能报告探索性的跨来源重复性，不能当最终确认性结果。',
        '- 不按数据集或病例选择更有利的一组拼接成新方法，不改变GT、不据结果调整半径或权重，也不自动授权模型训练。',
        '',f"总用时{complete['seconds']:.1f}秒，三工作进程的总RSS监测峰值{complete['monitored_aggregate_RSS_peak_bytes']/1024**3:.3f}GiB；资源为监测而非硬隔离。", 
        '', '完整来源均值见source_level_metrics.csv，逐种子见seed_level_metrics.csv；源数据和各病例拓扑记录在protocol.json与cases/*/result.json。']
with (O/'report_zh_v1.md').open('x',encoding='utf-8') as f:f.write('\n'.join(lines)+'\n')
verify={'status':'SAVED_CONTENT_VERIFICATION_PASS','original_manifest_files':len(manifest),'source_rows':len(sources),'seed_rows':len(seedrows),
        'files':{n:sha(O/n) for n in ['source_level_metrics.csv','seed_level_metrics.csv','source_stability_summary.json','source_stability.png','report_zh_v1.md']}}
dump(O/'report_verification.json',verify);print(json.dumps(verify,ensure_ascii=False))
