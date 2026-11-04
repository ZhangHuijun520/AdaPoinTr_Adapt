"""Summarize existing pilot outputs only; no geometry/model rerun."""
import os
os.environ['MPLBACKEND']='Agg'
os.environ['MPLCONFIGDIR']=str(__import__('pathlib').Path(__file__).resolve().parent/'blue_noise_pilot_20261103_v1'/'mpl_cache')
import csv,hashlib,json
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

B=Path(__file__).resolve().parent;O=B/'blue_noise_pilot_20261103_v1'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    assert not (O/'failure.json').exists()
    rows=json.loads((O/'metrics.json').read_text());summary=json.loads((O/'summary.json').read_text())
    content=json.loads((O/'contents.json').read_text())
    assert len(rows)==54 and summary['status']=='COMPLETED_CPU_GEOMETRY_ONLY'
    assert all((O/p).stat().st_size==x['bytes'] and sha(O/p)==x['sha256'] for p,x in content.items())
    assert all(r['count']==8192 and r['point_displacement_mm']==0 for r in rows)
    for r in rows:
        p=O/'samples'/f"{r['case']}_seed{r['seed']}_{r['method']}.npz"
        with np.load(p,allow_pickle=False) as z:
            assert z['xyz'].shape==(8192,3) and np.isfinite(z['xyz']).all()
            assert len(np.unique(z['pool_indices']))==8192
    records=[];cases=sorted({r['case'] for r in rows})
    for cid in cases:
        rr=[r for r in rows if r['case']==cid]
        for reg in rr[0]['regions']:
            for mode in ['unrestricted','same_surface']:
                rec={'case':cid,'region':reg,'distance':mode}
                for method in ['V1_common_pool','Euclidean_elimination']:
                    sub=[r for r in rr if r['method']==method];assert len(sub)==3
                    for metric in ['cover_0_5mm','cover_1mm','cover_2mm','p95_mm','max_mm']:
                        rec[method+'_'+metric]=float(np.mean([r['regions'][reg][mode][metric] for r in sub]))
                    rec[method+'_point_count']=float(np.mean([r['regions'][reg]['point_count'] for r in sub]))
                for metric in ['cover_0_5mm','cover_1mm','cover_2mm','p95_mm','max_mm']:
                    rec['delta_'+metric]=rec['Euclidean_elimination_'+metric]-rec['V1_common_pool_'+metric]
                records.append(rec)
    with (O/'paired_case_region_summary.csv').open('x',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(records[0]));writer.writeheader();writer.writerows(records)
    phantom=[r for r in records if r['case'].startswith('phantom') and r['distance']=='same_surface']
    real=[r for r in records if not r['case'].startswith('phantom') and r['distance']=='unrestricted']
    fig,axs=plt.subplots(1,2,figsize=(12,4.9),layout='constrained')
    for ax,rr,title,met in [(axs[0],phantom,'Thin solid plate: same-surface coverage','cover_1mm'),(axs[1],real,'Six existing cases: unrestricted coverage','cover_2mm')]:
        x=np.arange(len(rr));delta=np.array([r['delta_'+met]*100 for r in rr]);color=np.where(delta>=0,'#0072B2','#D55E00')
        ax.bar(x,delta,color=color);ax.axhline(0,color='#444444',linewidth=.8)
        labels=[r['case'].replace('phantom_','t=').replace('SkullBreak_train__','SB ').replace('SkullFix_','SF ').replace('__bilateral','')+' '+r['region'] for r in rr]
        ax.set_xticks(x,labels,rotation=70,ha='right',fontsize=8);ax.set_title(title,fontsize=11)
        ax.set_ylabel('Elimination minus V1 (percentage points)');ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
    fig.suptitle('Fixed 8192 input points; means of three seeds; geometry only',fontsize=12)
    fig.savefig(O/'coverage_deltas.png',dpi=170);plt.close(fig)
    negatives=[]
    for cid in cases:
        rr=[r for r in rows if r['case']==cid]
        for reg in rr[0]['regions']:
            for seed in [0,1,2]:
                a=next(r for r in rr if r['seed']==seed and r['method']=='V1_common_pool')['regions'][reg]['same_surface']
                b=next(r for r in rr if r['seed']==seed and r['method']=='Euclidean_elimination')['regions'][reg]['same_surface']
                if b['cover_1mm']<a['cover_1mm']:negatives.append({'case':cid,'region':reg,'seed':seed,'delta_cover1_pp':100*(b['cover_1mm']-a['cover_1mm'])})
    audit={'status':'OUTPUT_CONTENT_VERIFICATION_PASS','original_manifest_files_checked':len(content),'sample_sets_checked':54,
      'exact_count_each':8192,'summary_rows':len(records),'negative_same_region_cover1_seed_records':negatives,
      'scope':'content re-read and count checks; no independent geometry re-computation or formal P3',
      'no_model_or_server_execution':True}
    (O/'report_verification.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
    lines=['# 固定点数欧氏蓝噪声样本消除：限定CPU几何试验报告',
      '', '日期：2026-11-03。仅本机CPU；未训练、推理、连接服务器或改动生产数据。',
      '', '## 方法与冻结范围',
      '', '候选是受Yuksel样本消除启发的紧支撑核实现，不宣称逐字复现cyCodeBase、不保证严格最小间距，也未做频谱蓝噪声认证。从同一物理面积随机候选池32768点中消除至8192点；半径R=2√(面积/8192)，权重为(1-d/R)^8，对半径内全部点对求和，迭代移除权重最大点。参数仅一次冻结，无半径扫描、无移动点或表面修改。',
      '', '对照为同一候选池前8192点，分布与V1面积随机一致，但因候选池长度影响随机数消耗，不声称重现历史V1点集字节。采样器不接收标签、植入物、J或目标；真实病例的候选索引在读取implant之前保存。输出GT、归一化和生产样本均未改动。',
      '', '六例为SkullFix 002/003/004及SkullBreak train 000/001/002 bilateral，均为此前开放的诊断来源，不是全新的最终检验集。人工几何为80×80mm实体薄板、30×30mm贯穿方孔，厚度0.5/1/3mm；标注内外面、孔切壁及外侧边。每例三个种子，共54个8192点集合。这里inner/outer只是人工两侧，不代表解剖标注。',
      '', '## 人工多表面结果',
      '', '下表使用“同类表面点”测距，避免另一侧点替代而掩盖丢层；面积加权参考为独立0.5mm或更细的矩形中点积分。表中为三个种子均值，不是统计显著性检验。',
      '', '| 厚度mm | 区域 | V1 Cover@1mm % | 候选 % | 差值pp | V1 P95 mm | 候选 P95 mm |',
      '|---|---|---:|---:|---:|---:|---:|']
    for r in phantom:
        lines.append(f"| {r['case'][8:]} | {r['region']} | {r['V1_common_pool_cover_1mm']*100:.3f} | {r['Euclidean_elimination_cover_1mm']*100:.3f} | {r['delta_cover_1mm']*100:+.3f} | {r['V1_common_pool_p95_mm']:.3f} | {r['Euclidean_elimination_p95_mm']:.3f} |")
    lines+=['','## 真实数据结果','','J为由原始D/G互补关系精确确认的共享切壁；E为其它骨边界，**E不等于外板**。真实数据没有可信内外板标注，不做真实内外板分层保留宣称。主距离允许任何输入点提供支持；CSV另列仅同J/E区域的距离，避免局部支持来源混淆。参考为精确体素暴露面的中心及物理面积权重，并非连续表面Hausdorff保证。','','| 病例 | 区域 | V1 Cover@2mm % | 候选 % | 差值pp | V1 P95 mm | 候选 P95 mm |','|---|---|---:|---:|---:|---:|---:|']
    for r in real:
        lines.append(f"| {r['case']} | {r['region']} | {r['V1_common_pool_cover_2mm']*100:.3f} | {r['Euclidean_elimination_cover_2mm']*100:.3f} | {r['delta_cover_2mm']*100:+.3f} | {r['V1_common_pool_p95_mm']:.3f} | {r['Euclidean_elimination_p95_mm']:.3f} |")
    lines+=['','![配对几何覆盖差值](coverage_deltas.png)','','## 可靠性与局限',
      '',f"- 人工合同检查通过：堆实现与逐次全量删除一致、复现、无并列的人工坐标刚体协变、精确点数、原始子集和输入不变。原始输入哈希不变；重新回读54份点集及完整内容清单通过。共用时{summary['seconds']:.1f}秒，检查点记录RSS峰值{summary['checkpoint_peak_RSS_bytes']/1024**3:.3f}GiB；不是硬隔离。",
      '- 三种子用于检查随机波动，不是独立患者数。六例不能替代批量来源和未知缺损类型验证。核半径按总面积确定可能受复杂孔腔或跨层邻近影响；尚未检验测地版本。',
      '- 人工各区域各种子同面Cover@1mm的下降记录见report_verification.json；所有下降均保留，不隐藏、不据此调参。仅Cover@2mm接近饱和不代表亚毫米精度，必须同时看0.5/1mm覆盖与P95。',
      '- 采样仍基于原始体素面边界，不能改善上游分割真实性；未生成平滑网格，不把体素阶梯误当重建精度。',
      '- 点数与分层支持并不等同于网络512/256 proxy保留，也不证明减少了既有整块骨片定位错误；模型收益尚无证据。当前V1生产默认不变。',
      '', '## 下一步决策边界',
      '', '若人工层面无系统性丢层且真实J/E配对覆盖确有改善，可保留为下一轮扩大既有开放来源几何核验的候选；仍不自动部署或训练。如果发现稳定的局部退化，应停止此实现并先解释，而非扫描半径补救。不要仅凭均匀外观宣称胜出。',
      '', '文献依据：[Yuksel 2015样本消除](https://www.cemyuksel.com/research/sampleelimination/)；颅骨任务中Poisson-disk先例：[Friedrich等MICCAI2023](https://arxiv.org/html/2303.08061v2)。本实现是本项目限定候选，文献先例不替代本次或后续验证。']
    (O/'report_zh_v1.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    (O/'report_contents.json').write_text(json.dumps({p.name:sha(p) for p in [O/'paired_case_region_summary.csv',O/'coverage_deltas.png',O/'report_zh_v1.md',O/'report_verification.json']},indent=2),encoding='utf-8')
    print(json.dumps({'status':'REPORT_COMPLETE','negative_same_region_cover1_records':len(negatives),'report':str(O/'report_zh_v1.md')},ensure_ascii=False))

if __name__=='__main__':main()
