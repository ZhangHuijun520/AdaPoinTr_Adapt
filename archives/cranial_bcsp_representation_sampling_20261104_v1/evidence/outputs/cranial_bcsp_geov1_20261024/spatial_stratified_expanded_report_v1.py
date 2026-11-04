# -*- coding: utf-8 -*-
"""Summarize frozen expanded results by case/source; verify saved products."""
import csv,hashlib,json,sys
from pathlib import Path
import numpy as np
B=Path(__file__).resolve().parent;O=B/'spatial_stratified_expanded_20261103_v1'
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for v in iter(lambda:f.read(1048576),b''):h.update(v)
    return h.hexdigest()
def dump(p,x):
    with p.open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False)
def table(p,rows):
    with p.open('x',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
REGIONS=['J','E_MC','all_mixed_quadrature']
METHODS=['uniform8k','Morton_area_stratified8k']
def main():
    completion=json.loads((O/'completion.json').read_text(encoding='utf-8'))
    assert completion['cases']==510 and not (O/'failure.json').exists()
    cases=json.loads((O/'all_case_results.json').read_text(encoding='utf-8'))
    protocol=json.loads((O/'frozen_protocol.json').read_text(encoding='utf-8'))
    paired=[];means=[]
    for c in cases:
        assert len(c['metrics'])==6
        local=[]
        for seed in [0,1,2]:
            rr={m:next(r for r in c['metrics'] if r['method']==m and r['seed']==seed) for m in METHODS}
            p={'case':c['id'],'dataset':c['dataset'],'source_id':c['source_id'],'defect_type':c['defect_type'],'split':c['split'],'seed':seed}
            for method,r in rr.items():
                path=O/r['sample_path'];assert sha(path)==r['sample_sha256']
                with np.load(path,allow_pickle=False) as z:
                    assert z['xyz'].shape==z['partial'].shape==(8192,3) and z['face_ids'].shape==(8192,)
                    assert z['partial'].dtype==np.float32 and np.isfinite(z['partial']).all() and np.isfinite(z['xyz']).all()
                    assert np.max(np.linalg.norm(z['partial'].astype(float)*z['scale']+z['center']-z['xyz'],axis=1))<1e-3
            for region in REGIONS:
                for k in ['cover_1mm','cover_2mm','p95_mm']:
                    p[f'{region}_{k}_baseline']=rr[METHODS[0]][region][k]
                    p[f'{region}_{k}_candidate']=rr[METHODS[1]][region][k]
                    p[f'{region}_{k}_delta']=rr[METHODS[1]][region][k]-rr[METHODS[0]][region][k]
            for k in ['J_face_point_count','support_2mm_center_reference_count','NN_median_mm','NN_fraction_lt_0_5mm','FOV_sample_count','sampling_seconds']:
                for method,key in [(METHODS[0],'baseline'),(METHODS[1],'candidate')]:p[f'{k}_{key}']=rr[method][k]
            local.append(p);paired.append(p)
        d={k:local[0][k] for k in ['case','dataset','source_id','defect_type','split']}
        d.update({k:float(np.mean([r[k] for r in local])) for k in local[0] if k not in ['case','dataset','source_id','defect_type','split','seed']})
        d.update({'J_area_fraction':c['J_area_fraction'],'FOV_area_fraction':c['FOV_area_fraction'],
          'negative_seed_count':sum(r['J_cover_2mm_delta']<0 for r in local),'fold_C':c['fold_roles'].get('C','not_applicable'),'fold_D':c['fold_roles'].get('D','not_applicable')})
        means.append(d)
    assert len(paired)==1530 and len(means)==510 and len(list((O/'samples').glob('*.npz')))==3060
    table(O/'paired_case_seed_metrics.csv',paired);table(O/'paired_case_mean_metrics.csv',means)
    sources=[]
    numeric=[k for k,v in means[0].items() if isinstance(v,(float,int)) and k not in ['negative_seed_count']]
    for dataset in ['SkullFix','SkullBreak']:
        for source in sorted({c['source_id'] for c in means if c['dataset']==dataset}):
            rr=[c for c in means if c['dataset']==dataset and c['source_id']==source]
            assert len(rr)==(5 if dataset=='SkullBreak' else 1)
            sources.append({'dataset':dataset,'source_id':source,'defect_cases':len(rr),
                'split':rr[0]['split'],'fold_C':rr[0]['fold_C'],'fold_D':rr[0]['fold_D'],
                **{k:float(np.mean([r[k] for r in rr])) for k in numeric},'negative_defect_cases':sum(r['J_cover_2mm_delta']<0 for r in rr)})
    table(O/'source_mean_metrics.csv',sources)
    def stats(rr):
        assert rr
        d=np.array([r['J_cover_2mm_delta'] for r in rr])
        return {'units':len(rr),'J_cover2_baseline':float(np.mean([r['J_cover_2mm_baseline'] for r in rr])),
          'J_cover2_candidate':float(np.mean([r['J_cover_2mm_candidate'] for r in rr])),
          'J_cover2_delta':float(d.mean()),'J_delta_quantiles':np.quantile(d,[0,.05,.25,.5,.75,.95,1]).tolist(),
          'J_negative_units':int((d<0).sum()),'J_loss_gt_1pp_units':int((d<-.01).sum()),'J_loss_gt_5pp_units':int((d<-.05).sum()),
          'J_p95_baseline':float(np.mean([r['J_p95_mm_baseline'] for r in rr])),
          'J_p95_candidate':float(np.mean([r['J_p95_mm_candidate'] for r in rr])),
          'J_p95_worsened_units':sum(r['J_p95_mm_delta']>0 for r in rr),
          'E_MC_cover2_delta':float(np.mean([r['E_MC_cover_2mm_delta'] for r in rr])),
          'all_MC_cover2_delta':float(np.mean([r['all_mixed_quadrature_cover_2mm_delta'] for r in rr])),
          'E_MC_loss_gt_1pp_units':sum(r['E_MC_cover_2mm_delta']<-.01 for r in rr)}
    groups={}
    for ds in ['SkullFix','SkullBreak']:
        rr=[r for r in sources if r['dataset']==ds];groups[ds]=stats(rr)
        excluded={'SkullFix:002','SkullFix:003','SkullFix:004'} if ds=='SkullFix' else {'train:000','train:001','train:002'}
        groups[ds+'_excluding_pilot_sources']=stats([r for r in rr if r['source_id'] not in excluded])
    for split in ['train','val']:groups['SkullFix_'+split]=stats([r for r in sources if r['dataset']=='SkullFix' and r['split']==split])
    for fold in ['C','D']:
        for role in ['train','dev']:groups[f'SkullBreak_fold{fold}_{role}']=stats([r for r in sources if r['dataset']=='SkullBreak' and r['fold_'+fold]==role])
    for kind in sorted({r['defect_type'] for r in means if r['dataset']=='SkullBreak'}):
        groups['SkullBreak_defect_'+kind]=stats([r for r in means if r['dataset']=='SkullBreak' and r['defect_type']==kind])
    # Reconcile selected exact full-surface reviews with stage-one MC estimates.
    reviews=json.loads((O/'full_reference_review_results.json').read_text(encoding='utf-8'));full=[]
    for review in reviews:
        cid=review['case'];rr=review['metrics'];stage=next(c for c in means if c['case']==cid)
        r={'case':cid,'dataset':stage['dataset']}
        for reg in ['J','E','all']:
            for k in ['cover_1mm','cover_2mm','p95_mm']:
                vals={m:float(np.mean([v[reg][k] for v in rr if v['method']==m])) for m in METHODS}
                r[f'{reg}_{k}_baseline']=vals[METHODS[0]];r[f'{reg}_{k}_candidate']=vals[METHODS[1]]
                r[f'{reg}_{k}_delta']=vals[METHODS[1]]-vals[METHODS[0]]
        assert abs(r['J_cover_2mm_delta']-stage['J_cover_2mm_delta'])<1e-10
        r['E_MC_delta_error_pp']=100*(stage['E_MC_cover_2mm_delta']-r['E_cover_2mm_delta'])
        full.append(r)
    table(O/'full_reference_review_summary.csv',full)
    regressed=[r for r in means if r['J_cover_2mm_delta']<0]
    table(O/'worst_cases_ranked.csv',sorted(means,key=lambda r:r['J_cover_2mm_delta']))
    regression_profiles={}
    for ds in ['SkullFix','SkullBreak']:
        rr=[r for r in regressed if r['dataset']==ds]
        regression_profiles[ds]={'negative_cases':len(rr),
           'negative_cases_with_fewer_mean_direct_J_points':sum(r['J_face_point_count_candidate']<r['J_face_point_count_baseline'] for r in rr),
           'negative_cases_with_fewer_mean_near_J_support_points':sum(r['support_2mm_center_reference_count_candidate']<r['support_2mm_center_reference_count_baseline'] for r in rr),
           'negative_cases_with_all_three_seeds_negative':sum(r['negative_seed_count']==3 for r in rr),
           'negative_cases_with_E_MC_mean_still_improved':sum(r['E_MC_cover_2mm_delta']>0 for r in rr),
           'cases':[{k:r[k] for k in ['case','negative_seed_count','J_cover_2mm_delta','J_face_point_count_baseline','J_face_point_count_candidate','support_2mm_center_reference_count_baseline','support_2mm_center_reference_count_candidate','E_MC_cover_2mm_delta','J_area_fraction','FOV_area_fraction']} for r in rr]}
    dump(O/'regression_profiles.json',regression_profiles)
    summary={'status':'COMPLETED_SOURCE_LEVEL_EXPLORATORY_SUMMARY','groups':groups,
       'SkullFix_case_regressions':sum(r['dataset']=='SkullFix' for r in regressed),
       'SkullBreak_defect_case_regressions':sum(r['dataset']=='SkullBreak' for r in regressed),
       'selected_full_reference_reviews':len(full),'max_selected_E_MC_delta_error_pp':max(abs(r['E_MC_delta_error_pp']) for r in full),
       'regression_rule':'case/source mean J Cover2 delta <0; descriptive, no clinical/significance threshold',
       'regression_profiles':regression_profiles,'training_authorized_or_executed':False}
    dump(O/'source_level_summary.json',summary)
    lines=[]
    for key,title in [('SkullFix','SkullFix：90来源'),('SkullBreak','SkullBreak：84来源，每来源5缺损'),
        ('SkullFix_excluding_pilot_sources','SkullFix：排除原3个小试来源'),('SkullBreak_excluding_pilot_sources','SkullBreak：排除原3个小试来源')]:
        g=groups[key];lines.append(f"| {title} | {g['units']} | {100*g['J_cover2_baseline']:.4f}% | {100*g['J_cover2_candidate']:.4f}% | {100*g['J_cover2_delta']:+.4f} | {g['J_negative_units']} | {g['J_p95_baseline']:.4f} → {g['J_p95_candidate']:.4f} |")
    worst=[]
    for ds in ['SkullFix','SkullBreak']:
        for r in sorted([r for r in means if r['dataset']==ds],key=lambda r:r['J_cover_2mm_delta'])[:10]:
            worst.append(f"| {r['case']} | {100*r['J_cover_2mm_baseline']:.4f}% | {100*r['J_cover_2mm_candidate']:.4f}% | {100*r['J_cover_2mm_delta']:+.4f} | {r['negative_seed_count']}/3 | {100*r['J_area_fraction']:.4f}% |")
    splitlines=[]
    for k,g in groups.items():
        if k in ['SkullFix','SkullBreak'] or 'excluding' in k:continue
        splitlines.append(f"| {k} | {g['units']} | {100*g['J_cover2_delta']:+.4f} | {g['J_negative_units']} | {100*g['E_MC_cover2_delta']:+.4f} |")
    sf004=next(r for r in means if r['case']=='SkullFix_004')
    profile_lines=[]
    for ds,p in regression_profiles.items():
        profile_lines.append(f"- {ds}：{p['negative_cases']}个退化病例中，{p['negative_cases_with_fewer_mean_direct_J_points']}例直接J点数平均减少，{p['negative_cases_with_fewer_mean_near_J_support_points']}例近J支持点数平均减少；{p['negative_cases_with_all_three_seeds_negative']}例三个seed全部退化；{p['negative_cases_with_E_MC_mean_still_improved']}例的其他原始表面E仍平均改善（MC参考）。")
    stable=all(groups[ds+'_excluding_pilot_sources']['J_cover2_delta']>0 and groups[ds]['J_p95_candidate']<=groups[ds]['J_p95_baseline'] and groups[ds]['E_MC_cover2_delta']>=-.01 for ds in ['SkullFix','SkullBreak'])
    decision='可以讨论最少规模、同协议模型对照；本轮不创建或启动训练。' if stable else '暂不建议进入模型对照，先讨论已冻结结果中的泛化或退化问题；不得自动调采样参数补救。'
    report=f'''# 固定Morton等面积分层8k：已开放来源扩大配对几何核验 v1

日期：2026-11-03。状态：510病例、1530个病例/seed配对完成；没有训练或GPU执行。候选源码保持小试版本，不作参数扫描。本报告是描述性开发证据，不是独立确认试验。

## 固定范围和评价方法

SkullFix 90来源（80训练、10验证），SkullBreak 84来源×5缺损=420病例。全部已经开放；没有读取其余SkullFix内部留出、SkullBreak封存确认/monitor/官方测试payload。不改变划分、实体缺损、目标8192点或生产采样器。源文件1194个、既有输入/目标点集及候选实现哈希前后核验一致。

每例输入仍8192点。基线按V1抽16384后取前8192；候选按原Morton面积分层规则直接生成8192。seed固定0/1/2，每例六份输入先保存，后解码原始G体素构造评价J。既有NPZ中的目标数组在选点前为身份哈希核验读入；未传给采样函数、未用于选点。因此这里只保证采样函数参数及计算的数据依赖为D-only，不宣称全进程在选点前从未接触任何GT payload，亦无操作系统级隔离。C的实体互补QC通过原始哈希继承，本轮未重新解码C、未冒充新一轮完整解剖QC。

J评价使用全部原生切壁面中心、按物理面积加权。E沿用既有SkullBreak的固定seed99173、131072个面积IID参考面中心；两方法和三个seed共享同一参考。全表面评价混合精确J与MC E，并按各自物理面积赋权。因此E/all指标是近似量，与小试全量E/all不能无说明地直接拼接。退化复核另对预定选择病例使用全部原生面中心，不重新采样输入。

先平均每例三个seed，再在SkullBreak每来源平均五种缺损，再来源等权；SkullFix每来源一缺损。不同seed、同来源不同缺损及CV重叠训练集都不是独立患者重复。不把两数据集强行合成一个总均值。

## 来源级主结果

| 范围 | 来源数 | 基线J Cover@2mm | 候选J Cover@2mm | 差值（百分点） | 退化来源数 | J P95（mm） |
|---|---:|---:|---:|---:|---:|---:|
{chr(10).join(lines)}

SkullFix逐例J Cover@2mm下降{summary['SkullFix_case_regressions']}/90；SkullBreak逐缺损下降{summary['SkullBreak_defect_case_regressions']}/420。来源平均正收益仍可同时存在个别缺损或seed退化。完整分位数、超过1/5个百分点损失的计数及P95退化计数见`source_level_summary.json`。

原六例已参与过探索；排除小试来源后仍是已开放开发材料，不是新确认集。SkullBreak排除的是三个来源的全部15种缺损，而非只排除原来的三个bilateral病例。

## 划分、Fold与缺损类型

以下SkullBreak缺损类型行每来源一病例；Fold行仍先按来源平均全部五缺损。E为MC近似，不进行显著性检验。

| 分组 | 来源数 | J Cover@2mm差值（百分点） | 退化来源数 | E Cover@2mm差值（百分点） |
|---|---:|---:|---:|---:|
{chr(10).join(splitlines)}

## 退化病例重点复核

按两数据集各自最小的病例三seed平均J差值选最差10例，同时加入原小试六例、SkullFix 018/062，共{len(full)}例去重后做全量E/all复核。规则在扩大结果产生前冻结，未挑选有利病例。以下按病例列出各数据集最差10例；来源平均结果与逐缺损结果不能互换。

| 病例 | 基线J Cover@2mm | 候选J Cover@2mm | 差值（百分点） | 退化seed数 | J面积占比 |
|---|---:|---:|---:|---:|---:|
{chr(10).join(worst)}

SkullFix 004本轮沿用原三seed与同一候选，J差值为{100*sf004['J_cover_2mm_delta']:+.4f}个百分点、{sf004['negative_seed_count']}/3个seed退化；保留该负结果，没有改变seed或排序补救。018/062的小连通成分与FOV规则均保留；采样比较不能认证或修复原始分割质量。

全量复核中J差值与第一阶段在1e-10容差内一致。所选{len(full)}例中E的MC配对差值与全量差值最大偏差{summary['max_selected_E_MC_delta_error_pp']:.4f}个百分点。该误差只针对所选病例，不是对全部E误差的上界，也不是置信区间。全量J/E/all与1mm、2mm、P95详见`full_reference_review_summary.csv`。

目前只能把局部退化与点数、近J支持、J面积、FOV及seed波动并列观察，不能凭相关性归因于某一解剖结构。没有真实内外板语义标签，不虚构分层覆盖或“所有微小结构均保留”的结论。

退化证据分解如下，病例而非seed作为计数单位；详见`regression_profiles.json`。这些关联不证明点数减少是唯一原因，也不能把不同来源的切壁面积差异当作算法因果效应。

{chr(10).join(profile_lines)}

## 对模型对照的建议

{decision}

判断依据是两数据集及排除小试来源后的J改善方向、P95、全局保护和负例，而不是只沿用原六例合并5个百分点门槛。此次没有预注册正式统计gate，不将描述性条件包装成显著性或临床达标。

若讨论模型对照，应只比较同输入点数下的V1与固定候选，目标、母版、source/fold、更新计数与评价保持一致；保留原有V1对照资产。候选8k没有原8k/16k前缀配对合同，不能直接替换原密度实验后继续宣称只改变输入密度。几何收益不能保证模型会利用这些点，最少训练范围应另行明确。

## 运行、交付和限制

唯一扩大批次耗时{completion['seconds']/60:.2f}分钟，检查点最大进程RSS {completion['checkpoint_peak_RSS_bytes']/1024**3:.3f} GiB，3060份科研输入点集已全部回读核验形状、有限值、哈希与归一化。无forward、GPU、训练、服务器或自动重试。资源是监测预算，非硬隔离或连续峰值认证。

`paired_case_seed_metrics.csv`保留1530配对；`paired_case_mean_metrics.csv`保留510病例；`source_mean_metrics.csv`保留174来源；`worst_cases_ranked.csv`不删任何退化行；`source_level_summary.json`包含全部分组。`full_reference_review/`与对应CSV为定向全量复核。`samples/`为科研对照资产，不覆盖旧点集；`diagnostics/`仅含事后J/FOV标签，不作模型输入特征。

Morton排序依赖原始体素索引框架。小试的刚体协变保证是同拓扑/索引下改变物理affine，不覆盖重新体素化或任意新扫描方向。物理面面积与离散面中心仍受分割分辨率、阶梯面和FOV截断影响；这里的覆盖与P95不是连续解剖误差或临床适配认证。全部数据已开放，且无训练性能验证，不宣称论文最终方法已确定。
'''
    with (O/'report_zh_v1.md').open('x',encoding='utf-8') as f:f.write(report)
    dump(O/'saved_product_verification.json',{'status':'PASS','sample_files_read_and_verified':3060,'case_seed_pairs':1530,'cases':510,'sources':174,
       'target_source_hash_verification':'batch completion + every sample checksum/readback','full_review_J_deltas_match':True,
       'reporter_sha256':sha(Path(__file__)),'sampling_forward_training_calls':0})
    log=B/'spatial_stratified_expanded_20261103_v1.stdout.log'
    with (O/'execution_stdout.log').open('xb') as f:f.write(log.read_bytes())
    dump(O/'stdout_provenance.json',{'source':str(log),'sha256':sha(log),'copy_sha256':sha(O/'execution_stdout.log'),'kind':'byte copy of closed execution log'})
    files={str(p.relative_to(O)).replace('\\','/'):{'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(O.rglob('*')) if p.is_file()}
    dump(O/'artifact_manifest.json',{'status':'EXPANDED_EXPLORATORY_GEOMETRY_COMPLETE_NO_MODEL_RUN','files':files,'excludes_itself':True})
    print(json.dumps({'status':'REPORT_VERIFIED','summary':summary,'files':len(files),'bytes':sum(x['bytes'] for x in files.values())},ensure_ascii=True))
if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');main()
