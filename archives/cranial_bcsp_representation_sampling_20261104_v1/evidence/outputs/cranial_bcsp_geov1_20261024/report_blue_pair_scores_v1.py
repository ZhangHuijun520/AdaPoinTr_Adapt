"""Interpret audited saved metrics only; no geometry, reference arrays or models."""
import hashlib,json,math
from pathlib import Path
B=Path(__file__).resolve().parent;N=B/'blue_pair_eval_v1';O=N/'paired_scores_v1';F=N/'post_scoring_freeze_audit_v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def mean(v):return math.fsum(v)/len(v)
def main():
    auditfile=F/'audit_report_v1.json';audit=json.loads(auditfile.read_bytes());assert audit['status']=='FORMAL_POST_SCORING_FREEZE_AUDIT_PASS'
    for r in audit['output_manifest']:assert Path(r['path']).stat().st_size==r['bytes'] and sha(r['path'])==r['sha256']
    metrics=json.loads((O/'paired_comparison.json').read_bytes())['comparison']['metrics'];sources=json.loads((O/'source_metrics.json').read_bytes());defects=json.loads((O/'defect_comparison.json').read_bytes())
    lookup={(r['source_id'],r['arm']):r['metrics'] for r in sources}
    keys=['E_P95_mm','J_P95_mm','E_coverage_2.0mm','J_coverage_2.0mm','CD_L1_mm']
    controls={a:{k:mean([r['metrics'][k] for r in sources if r['arm']==a]) for k in keys} for a in ['Nop_D_Euclidean_elimination','Nop_D_surface_graph','GT_8192']}
    e=metrics['E_P95_mm'];j=metrics['J_P95_mm'];cd=metrics['CD_L1_mm'];jc=metrics['J_coverage_2.0mm']
    assert e['mean_delta_graph_minus_Euclidean']>0 and j['mean_delta_graph_minus_Euclidean']>0 and jc['mean_delta_graph_minus_Euclidean']<0 and cd['mean_delta_graph_minus_Euclidean']<0
    lines=['# 欧氏／表面图距离采样：评分冻结审计与科研解读 v1','',
    '日期：2026-11-04。**本轮图距离采样没有取得主指标与接口指标的整体优势，暂不支持将其升级为默认采样。** 本轮两臂之间优先保留欧氏方案；CD均值有改善，但不能据此覆盖预先固定的主指标与接口退化。','',
    '## 正式冻结审计','',
    f"状态 `{audit['status']}`，{len(audit['checks'])}组检查全部通过，退出码0。固定105病例／21来源，210模型评分＋315控制评分，共525病例行、105来源行，其中模型来源行42。11个结果文件已冻结完整大小／SHA256。",'',
    '审计独立使用stdlib从保存病例指标重新计算来源内五缺损均值、来源等权均值、两臂差值、中位数／范围／改善来源计数、五类缺损汇总、全部回退排序及三份CSV，均一致。代码、人工测试、指标模块、授权链、下载四文件及315份输入／参考文件哈希均通过。读取前后内容相关属性稳定，atime不参与判定。','',
    f"读取{audit['read_bytes']:,} bytes，耗时{audit['elapsed_seconds']:.3f}秒；未重跑评分、重算几何距离、解码真实预测／参考数组、连接服务器或运行模型／GPU。汇总一致性审计不等同第二次独立几何距离计算；距离值依赖冻结实现及已通过的人工合同。",'',
    '## 研究设计与指标解释','',
    '固定SkullBreak Fold C、训练／采样seed0、B0 AdaPoinTr、8k输入／8k输出。两臂同初始化指纹、来源划分、训练顺序、3900更新、100遍历、31200曝光、300丢弃及数值环境已正式配对审计。每臂105次native eval，使用final权重，不BNCal、TTA或投票。','',
    '欧氏消减与表面图距离使用同一候选池和固定规则。后者是原表面邻接的离散路径近似，并非精确连续测地距离；本试验不证明严格最小半径Poisson-disk性质。研究的是各自训练／部署采样策略的整体效果，不分离训练采样与推理输入的效应。','',
    'E为缺失骨块的未知原始表面，J为与残缺骨共享的切壁。主指标为A1 E→预测的面积加权P95，先逐病例计算，再同来源五缺损取均值，最后21来源等权。单位mm，距离越小越好、覆盖率越大越好；差值统一为图距离−欧氏。J距离／覆盖率不认证骨厚度、连续接触间隙、网格拓扑或临床吻合。','',
    '## 固定主次指标','',
    '| 指标 | 欧氏 | 图距离 | 图−欧 | 改善／持平／退化来源 |','|---|---:|---:|---:|---:|']
    for k,label in [('E_P95_mm','E P95（主指标，mm）'),('J_P95_mm','J P95（mm）'),('E_coverage_2.0mm','E Cover@2mm'),('J_coverage_2.0mm','J Cover@2mm'),('CD_L1_mm','CD-L1（mm）')]:
        v=metrics[k];cov='coverage' in k
        a=f"{100*v['mean_Euclidean']:.2f}%" if cov else f"{v['mean_Euclidean']:.3f}"
        b=f"{100*v['mean_graph']:.2f}%" if cov else f"{v['mean_graph']:.3f}"
        d=f"{100*v['mean_delta_graph_minus_Euclidean']:+.3f}个百分点" if cov else f"{v['mean_delta_graph_minus_Euclidean']:+.3f}"
        lines.append(f"| {label} | {a} | {b} | {d} | {v['improved_sources']}／{v['tied_sources']}／{v['worse_sources']} |")
    lines+=['',f"E P95均值增加{100*e['mean_delta_graph_minus_Euclidean']/e['mean_Euclidean']:.2f}%，来源差值中位数{e['median_delta']:+.3f}mm，12/21来源退化。J P95中位数{j['median_delta']:+.3f}mm；J Cover@2mm在16/21来源下降。这不是只有单个极端来源才出现的主指标／接口负向信号，但单次训练仍不能估计随机性或宣称统计显著。",'',
    f"CD均值改善{abs(cd['mean_delta_graph_minus_Euclidean']):.3f}mm（{100*abs(cd['mean_delta_graph_minus_Euclidean'])/cd['mean_Euclidean']:.2f}%），但差值中位数为{cd['median_delta']:+.3f}mm，仍有12/21来源变差。少数较大改善与较大退化相互抵消，均值改善不等于多数来源改善。CD为平均距离，E/J P95与覆盖率反映不同误差分布；这些指标同时出现不同方向并不矛盾，不能把CD替换为事后主指标。",'',
    '## 输入支持与模型输出的区别','',
    '| 固定CPU控制 | J P95（mm） | J Cover@2mm | E Cover@2mm |','|---|---:|---:|---:|']
    for a,label in [('Nop_D_Euclidean_elimination','欧氏输入原样'),('Nop_D_surface_graph','图距离输入原样'),('GT_8192','共同GT8192点集')]:
        v=controls[a];lines.append(f"| {label} | {v['J_P95_mm']:.3f} | {100*v['J_coverage_2.0mm']:.2f}% | {100*v['E_coverage_2.0mm']:.2f}% |")
    x=controls['Nop_D_Euclidean_elimination'];y=controls['Nop_D_surface_graph'];input_gain=100*(y['J_coverage_2.0mm']-x['J_coverage_2.0mm'])
    lines+=['',f"图距离在同105例开发输入上将J Cover@2mm提高{input_gain:.3f}个百分点、J P95降低{x['J_P95_mm']-y['J_P95_mm']:.3f}mm，说明其输入侧局部几何支持收益在此开发集仍可观察到。但模型输出J Cover反而降低{abs(100*jc['mean_delta_graph_minus_Euclidean']):.3f}个百分点，E/J尾部误差也增大。可靠结论是：局部输入支持的改善没有稳定转化为当前模型的输出收益。",'',
    '不能据此断定某个FPS／proxy层、encoder、decoder或损失函数是原因。图距离同时改变邻域竞争和整体点分布，训练轨迹也会随输入变化；缺少中间轨迹和空间观察时，具体机制仍是假说。单独增加切壁点数或更均衡的间距不保证补全泛化。','',
    '输入原样覆盖残缺颅骨D，并非缺失骨块预测器，不能凭其J覆盖高于模型就认定其完成了补全。GT8192控制反映离散参考／采样尺度，不是理论最优下界。', '',
    '## 来源异质性：全部病例保留','',
    '| 来源 | E P95 欧氏 | 图距离 | Δmm | J Cover@2mm Δ百分点 | CD Δmm |','|---|---:|---:|---:|---:|---:|']
    for sid in ['train:081','train:042','train:003','train:051','train:013','train:053']:
        a=lookup[(sid,'Euclidean_elimination')];b=lookup[(sid,'surface_graph')]
        lines.append(f"| {sid} | {a['E_P95_mm']:.3f} | {b['E_P95_mm']:.3f} | {b['E_P95_mm']-a['E_P95_mm']:+.3f} | {100*(b['J_coverage_2.0mm']-a['J_coverage_2.0mm']):+.3f} | {b['CD_L1_mm']-a['CD_L1_mm']:+.3f} |")
    lines+=['','081在图距离臂明显回退，051与013明显改善；053虽P95和CD改善，J覆盖仍下降。不能把这些来源删除后重新报告“更好”的总体均值，也不能将另一轮Morton/V1的来源结论照搬到本轮。上述来源只用于解释异质性，完整21来源及105病例一直保留。','',
    '## 五类缺损的描述性差值','',
    '| 类别（各21来源） | E P95 Δmm | J P95 Δmm | E Cover@2mm Δ百分点 | J Cover@2mm Δ百分点 | CD Δmm |','|---|---:|---:|---:|---:|---:|']
    for name in ['bilateral','frontoorbital','parietotemporal','random_1','random_2']:
        v=defects[name]['mean_deltas'];lines.append(f"| {name} | {v['E_P95_mm']:+.3f} | {v['J_P95_mm']:+.3f} | {100*v['E_coverage_2.0mm']:+.3f} | {100*v['J_coverage_2.0mm']:+.3f} | {v['CD_L1_mm']:+.3f} |")
    lines+=['','颞顶parietotemporal的这五项均值方向均改善，是值得保留的描述性线索；但额眶frontoorbital的CD改善同时伴随明显覆盖率下降，双侧与两类随机缺损多项回退。不据此挑选有利缺损类型重新训练或宣称亚组已验证，类别不是独立额外训练复现。','',
    '## 反向误差与参考离散敏感性','']
    rev=metrics['reverse_A2_P95_mm'];out=metrics['reverse_A2_outlier_2.0mm']
    lines += [f"反向A2 P95均值为{rev['mean_Euclidean']:.3f}→{rev['mean_graph']:.3f}mm，差值{rev['mean_delta_graph_minus_Euclidean']:+.3f}mm；差值中位数却为{rev['median_delta']:+.3f}mm。反向>2mm离群比例为{100*out['mean_Euclidean']:.2f}%→{100*out['mean_graph']:.2f}%，增加{100*out['mean_delta_graph_minus_Euclidean']:.3f}个百分点。不能声称图距离普遍减少了离群点；空间形态仍需查看既有预测。",'',
    f"A2 E P95差值{metrics['A2_E_P95_mm']['mean_delta_graph_minus_Euclidean']:+.6f}mm，接近A1的{e['mean_delta_graph_minus_Euclidean']:+.6f}mm；A2 J差值{metrics['A2_J_P95_mm']['mean_delta_graph_minus_Euclidean']:+.6f}mm，亦与A1一致。B全表面P95差值{metrics['B_all_P95_mm']['mean_delta_graph_minus_Euclidean']:+.3f}mm。当前主要退化没有随这些参考离散版本发生方向翻转，但它们仍来自同源几何，不是独立解剖GT。",'',
    '## 决策与下一科研步骤','',
    '1. 本轮不升级图距离为默认，不追加半径／权重扫描或自动新增fold、seed、训练。保留其输入支持收益及模型端混合／负向结果。本次两臂中欧氏更符合主指标与接口目标；是否替代历史V1默认，需要对应的公平证据，不能仅凭不同轮次均值宣称欧氏已全局最优。',
    '2. 若需要解释失败机制，优先利用既有预测做一次限定空间可视化：例如固定退化来源081／042与改善来源051／013，各查看bilateral与frontoorbital，共8例，两臂同视角显示D、G、预测及剖面。此为事后解释样本，不构成新无偏评价，不据此剔除病例或改主指标。本次未执行该可视化。',
    '3. 先区分整体形状／位置错误、少量远端离群与切壁局部偏差，再决定模型端最小假设。当前结果更支持“采样几何收益不自动等于任务收益”，不足以证明需要定位器、特定proxy修补或新损失。可以收束采样候选搜索，为下一轮模型研究固定稳定输入策略。',
    '4. 本结果不推翻完整骨组织边界表面、体素实体缺损或缺失骨块完整边界目标；也不回答输出点数最优性。限制为SkullBreak、单Fold C、单训练seed、B0 AdaPoinTr和8k→8k，无bootstrap、p值、正式gate、临床精度或Mamba方法优劣结论。','',
    '## 冻结证据','',f"审计报告SHA256：`{sha(auditfile)}`。本报告仅解读已冻结指标，没有任何新几何评分、模型执行、服务器操作或数据修改。",'',
    '| 结果文件 | bytes | SHA256 |','|---|---:|---|']
    for r in audit['output_manifest']:lines.append(f"| {Path(r['path']).name} | {r['bytes']} | `{r['sha256']}` |")
    report=F/'formal_audit_and_scientific_interpretation_zh_v1.md'
    with report.open('x',encoding='utf-8') as f:f.write('\n'.join(lines)+'\n')
    summary={'status':'AUDITED_GRAPH_HAS_NO_OVERALL_PRIMARY_OR_CONTACT_ADVANTAGE','audit_sha256':sha(auditfile),'primary':e,'key_secondary':{k:metrics[k] for k in keys[1:]},'input_controls':controls,'input_J_coverage_gain_pp':input_gain,'model_J_coverage_delta_pp':100*jc['mean_delta_graph_minus_Euclidean'],'all_cases_retained':True,'bootstrap':False,'formal_gate':False,'new_training':False,'historical_V1_compared_as_matched_arm':False,'analysis_source':'audited saved metrics only'}
    with (F/'interpretation_summary_v1.json').open('x') as f:json.dump(summary,f,indent=2)
    with (F/'audit_and_interpretation_artifact_manifest_v1.json').open('x') as f:json.dump({'status':audit['status'],'files':{p.name:{'bytes':p.stat().st_size,'sha256':sha(p)} for p in F.iterdir() if p.is_file()}},f,indent=2)
    print(json.dumps({'status':audit['status'],'checks':len(audit['checks']),'primary_E_P95_delta_mm':e['mean_delta_graph_minus_Euclidean'],'model_J_coverage_delta_pp':100*jc['mean_delta_graph_minus_Euclidean'],'input_J_coverage_gain_pp':input_gain,'report':str(report)}))
if __name__=='__main__':main()
