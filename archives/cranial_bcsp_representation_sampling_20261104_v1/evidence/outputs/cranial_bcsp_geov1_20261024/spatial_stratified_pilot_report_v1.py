# -*- coding: utf-8 -*-
"""Read-only saved pilot verification and Chinese reporting; no resampling."""
import csv,hashlib,json,sys
from pathlib import Path
import numpy as np
B=Path(__file__).resolve().parent;O=B/'spatial_stratified_pilot_20261103_v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,x):
    with p.open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False)
def main():
    s=json.loads((O/'summary.json').read_text(encoding='utf-8'));rows=json.loads((O/'metrics.json').read_text(encoding='utf-8'))
    protocol=json.loads((O/'frozen_protocol.json').read_text(encoding='utf-8'))
    assert not (O/'failure.json').exists() and len(rows)==54 and len({r['case'] for r in rows})==9
    seen=set()
    for r in rows:
        key=(r['case'],r['seed'],r['method']);assert key not in seen;seen.add(key)
        p=O/r['sample_path'];assert sha(p)==r['sample_sha256']
        with np.load(p,allow_pickle=False) as z:
            assert z['xyz'].shape==z['partial'].shape==(8192,3) and z['face_ids'].shape==(8192,)
            assert z['partial'].dtype==np.float32 and np.isfinite(z['xyz']).all() and np.isfinite(z['partial']).all()
            assert np.max(np.linalg.norm(z['partial'].astype(float)*z['scale']+z['center']-z['xyz'],axis=1))<1e-3
        if not r['phantom']:assert sha(r['target']['path'])==r['target']['sha256']
    for p,h in protocol['source_and_implementation_sha256'].items():assert sha(p)==h
    assert len(list((O/'samples').glob('*.npz')))==54
    pairs=[]
    for cid in sorted({r['case'] for r in rows}):
        for seed in [0,1,2]:
            a=next(r for r in rows if r['case']==cid and r['seed']==seed and r['method']=='uniform8k')
            b=next(r for r in rows if r['case']==cid and r['seed']==seed and r['method']=='Morton_area_stratified8k')
            p={'case':cid,'dataset':a['dataset'],'phantom':a['phantom'],'seed':seed}
            for reg in ['J','E','all']:
                for k in ['cover_1mm','cover_2mm','p95_mm']:
                    for method,r in [('baseline',a),('candidate',b)]:p[f'{reg}_{k}_{method}']=r[reg][k]
                    p[f'{reg}_{k}_delta']=b[reg][k]-a[reg][k]
            for k in ['J_face_point_count','support_2mm_center_reference_count','NN_median_mm','NN_p05_mm','NN_fraction_lt_0_5mm','FOV_sample_count','sampling_seconds_including_sort']:
                p[k+'_baseline']=a[k];p[k+'_candidate']=b[k]
            pairs.append(p)
    with (O/'paired_case_seed_metrics.csv').open('x',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(pairs[0]));w.writeheader();w.writerows(pairs)
    case_means=[]
    for cid in sorted({r['case'] for r in pairs if not r['phantom']}):
        rr=[r for r in pairs if r['case']==cid];m={'case':cid}
        for k in ['J_cover_2mm_baseline','J_cover_2mm_candidate','J_cover_2mm_delta','J_p95_mm_baseline','J_p95_mm_candidate','E_cover_2mm_delta','all_cover_2mm_delta']:
            m[k]=float(np.mean([r[k] for r in rr]))
        case_means.append(m)
    dump(O/'paired_case_means.json',case_means)
    ag=s['aggregate'];a=ag['all_real']['uniform8k'];b=ag['all_real']['Morton_area_stratified8k']
    lines=[]
    for group,title in [('all_real','六例等权'),('SkullFix','SkullFix三例'),('SkullBreak','SkullBreak三例')]:
        x,y=ag[group]['uniform8k'],ag[group]['Morton_area_stratified8k']
        lines.append(f"| {title} | {100*x['J']['cover_2mm']:.4f}% | {100*y['J']['cover_2mm']:.4f}% | {100*(y['J']['cover_2mm']-x['J']['cover_2mm']):+.4f} | {x['J']['p95_mm']:.4f} → {y['J']['p95_mm']:.4f} |")
    individual='\n'.join(f"| {r['case']} | {100*r['J_cover_2mm_baseline']:.4f}% | {100*r['J_cover_2mm_candidate']:.4f}% | {100*r['J_cover_2mm_delta']:+.4f} | {r['J_p95_mm_baseline']:.4f} → {r['J_p95_mm_candidate']:.4f} |" for r in case_means)
    flags='\n'.join(f"- `{k}`：{'通过' if v else '未通过'}。" for k,v in s['gates'].items())
    improvement=sum(r['J_cover_2mm_delta']>0 for r in pairs if not r['phantom'])
    report=f'''# 空间排序等面积分层8k：限定CPU采样对照报告 v1

日期：2026-11-03。结论：**本轮几何小试通过冻结的扩大核验筛选标准；保留候选，尚不替换生产V1或启动训练。**

## 目的、方法与冻结范围

只检验固定8192输入点时，减少随机空间聚集能否改善局部支持。输入为D的全部暴露体素面；目标为既有缺失骨块G的完整边界8192点，本轮不生成或修改目标。固定SkullFix 002/003/004、SkullBreak train:000/001/002的bilateral，三个既有球壳离散设置，seed 0/1/2。6真实来源×3seed×2方法=36行，3phantom×3seed×2方法=18行。

基线严格复用V1面积均匀有放回抽16384点后取前8192点。候选将D面中心双整数坐标平移为非负后按Morton顺序排序，按物理面积累积分成8192区间，每区间独立均匀取一个面积位置、再面内均匀取点。没有曲率定位、ROI、真实切壁增采配额或参数扫描；候选不增加J的期望面积配额，不承诺蓝噪声或最小间距。

输入每例三seed两方法共6份先完成并保存，再读取C/G生成J评价标签；目标信息不进入选点。归一化仅用D的世界前景体素中心包围盒中心和半对角线。FOV规则不变；候选只有固定8k合同，不宣称保持原8k/16k前缀配对性质。

## 执行与产物核验

人工7项合同通过：原面归属、同seed精确复现、面列表置换稳定、固定affine刚体协变、输入不变、各面分层面积计数偏差不超过2点、点数与有限值。刚体保证针对同一体素拓扑及索引框架，不覆盖重新体素化或更换扫描网格。

唯一批次退出0，耗时{s['seconds']:.2f}秒，检查点最大RSS {s['checkpoint_peak_RSS_bytes']/1024**3:.3f} GiB。54份点集重新加载，形状/有限值/坐标回读/文件哈希通过；18个原始NRRD及6个既有目标哈希保持不变。真实基线全部J/E/全边界指标与历史三seed记录在1e-10容差内复现。无forward、训练、GPU或服务器操作；无失败修复或重跑。

## 真实来源结果

以下先逐病例平均三个seed，再病例等权；并非将seed当独立患者。P95列为各行P95的均值，不是合并全部面后的P95。覆盖以原始体素面中心为参考、按物理面积加权；不是连续解剖或临床误差。

| 范围 | 基线J Cover@2mm | 候选J Cover@2mm | 差值（百分点） | J P95（mm） |
|---|---:|---:|---:|---:|
{chr(10).join(lines)}

| 病例（三seed平均） | 基线J Cover@2mm | 候选J Cover@2mm | 差值（百分点） | J P95（mm） |
|---|---:|---:|---:|---:|
{individual}

18个真实病例/seed配对中，J Cover@2mm提升{improvement}/18；这是采样重复的描述性结果，不做独立样本显著性检验。全部逐seed与phantom配对见`paired_case_seed_metrics.csv`。

## 全局保护与空间分布

- 原始边界E Cover@2mm：{100*a['E']['cover_2mm']:.4f}% → {100*b['E']['cover_2mm']:.4f}%；全边界：{100*a['all']['cover_2mm']:.4f}% → {100*b['all']['cover_2mm']:.4f}%。两数据集各自均未以全局覆盖退化换取J改善。
- J Cover@1mm：{100*a['J']['cover_1mm']:.4f}% → {100*b['J']['cover_1mm']:.4f}%，提高幅度小于2mm指标，不能声称亚毫米边缘精度已解决。
- 直接J采样点数：{a['J_face_point_count']:.2f} → {b['J_face_point_count']:.2f}；距J面中心≤2mm支持点数：{a['support_2mm_center_reference_count']:.2f} → {b['support_2mm_center_reference_count']:.2f}。覆盖提升没有伴随接口点数增加，与改善分布而非增加接口配额相符；尚不是模型利用机制的因果证据。
- 每行最近邻中位数的均值：{a['NN_median_mm']:.4f} → {b['NN_median_mm']:.4f} mm；最近邻距离低于0.5mm的点比例：{100*a['NN_fraction_lt_0_5mm']:.4f}% → {100*b['NN_fraction_lt_0_5mm']:.4f}%。近距离聚集减少，但不代表所有薄层结构均被充分表达。
- FOV点数均值：{a['FOV_sample_count']:.2f} → {b['FOV_sample_count']:.2f}。候选没有借排除截断面提高其他区域的预算。
- 每次采样耗时（含候选空间排序）：{a['sampling_seconds_including_sort']:.3f} → {b['sampling_seconds_including_sort']:.3f}秒。资源开销有所增加，当前小试未做大规模性能测量。

## 人工层面与筛选条件

三个解析球壳的内外层Cover@1mm三seed均值均提高，各层增量约2.59–3.24个百分点；两方法的2mm覆盖已接近饱和，因此不能只靠该指标判断层面质量。标签按面中心距17/20mm解析半径的近邻归属划分，只在这些phantom成立，不能外推为真实颅骨内外板覆盖认证。

在读取候选结果前，将方案中的“人工层面通过”具体化为每个球壳每层三seed平均Cover@1mm不下降且实际采到点，写入`frozen_protocol.json`；没有结果后改阈值。

{flags}

其中5个百分点收益和1个百分点保护容差是既定探索性筛选阈值，不是临床或文献标准。此次通过仅适用于该小试。

## 可靠解释及下一步

本轮支持一个有限结论：在这六个既有开发来源及三个固定seed上，空间分层可以在不增加输入点数和J点数的情况下提高几何覆盖；此前高曲率增强失败，不意味着所有分布改进都无效。

收益存在数据集差异：SkullFix仍只有约39.92%的J Cover@2mm，不能把小试通过说成局部支持问题已经解决。六例曾用于前序探索，不是未见独立测试；没有统计显著性、临床验证或补全预测收益结论。模型的局部聚合及解码可能仍无法利用更均衡的点分布。

下一步适合固定本候选、不再调排序或seed，在已开放来源上扩大配对几何核验，按来源汇总并检查最差病例、FOV及小成分。维持既有80/10和SkullBreak来源/fold边界，不读取内部留出、封存确认或官方测试payload。扩大核验前需明确批量范围与资源预算；本次不自动启动该批次。

扩大几何核验稳定通过后，才讨论同协议最少模型对照，区分几何收益与实际补全收益；当前不新增训练、接口定位器、Mamba模块或通用审计框架。原有90例V1点集和生产采样器均保留。

## 产物入口

`frozen_protocol.json`保存输入身份、预算及事前筛选条件；`artificial_checks.json`记录人工合同；`samples/`含54份科研输入点集（世界坐标、归一化输入、面索引，不含G标签）；`cases/`与`metrics.json`为全部原始结果；`summary.json`保存门槛及分数据集汇总；`paired_case_seed_metrics.csv`及`paired_case_means.json`便于复核；`saved_product_verification.json`与`artifact_manifest.json`记录本次产物核验和哈希。
'''
    with (O/'report_zh_v1.md').open('x',encoding='utf-8') as f:f.write(report)
    dump(O/'saved_product_verification.json',{'status':'PASS','sample_files':54,'rows':54,'unique_case_seed_method_keys':54,
      'all_saved_shapes_hashes_normalization_verified':True,'frozen_source_and_target_hashes_rechecked':True,
      'raw_decode_sampling_forward_calls_in_this_verification':0,'reporter_sha256':sha(Path(__file__))})
    # Preserve the closed execution log with an explicit byte-copy source binding.
    log=B/'spatial_stratified_pilot_20261103_v1.stdout.log'
    with (O/'execution_stdout.log').open('xb') as f:f.write(log.read_bytes())
    dump(O/'stdout_provenance.json',{'source':str(log),'source_sha256':sha(log),'copy_sha256':sha(O/'execution_stdout.log'),'kind':'byte copy of original completed subprocess stdout/stderr, not regenerated'})
    files={str(p.relative_to(O)).replace('\\','/'):{'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(O.rglob('*')) if p.is_file()}
    dump(O/'artifact_manifest.json',{'status':s['status'],'files':files,'excludes_itself':True})
    print(json.dumps({'status':'REPORT_AND_VERIFICATION_COMPLETED','sample_files':54,'manifest_files':len(files),'output_bytes':sum(v['bytes'] for v in files.values()),'all_real_J_improved_pairs':improvement},ensure_ascii=True))
if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');main()
