"""Interpret only audited saved scores; no prediction/reference arrays or geometry calls."""
import hashlib,json,math
from pathlib import Path
B=Path(__file__).resolve().parent;N=B/'sampling_model_AB_foldC_seed0_20261103_v1/paired_development_eval_v1';O=N/'paired_scores_v1';F=N/'post_scoring_freeze_audit_v1'
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def mean(x):return math.fsum(x)/len(x)
def save(name,text):
 with (F/name).open('x',encoding='utf-8',newline='\n') as f:f.write(text)
def main():
 audit=json.loads((F/'audit_report_v1.json').read_bytes());assert audit['status']=='FORMAL_POST_SCORING_FREEZE_AUDIT_PASS'
 for r in audit['output_manifest']:assert Path(r['path']).stat().st_size==r['bytes'] and h(r['path'])==r['sha256']
 comparison=json.loads((O/'paired_comparison.json').read_bytes())['comparison'];metrics=comparison['metrics'];sources=json.loads((O/'source_metrics.json').read_bytes());defects=json.loads((O/'defect_comparison.json').read_bytes())
 lookup={(r['source_id'],r['arm']):r['metrics'] for r in sources};ids=sorted({r['source_id'] for r in sources})
 controls={arm:{key:mean([r['metrics'][key] for r in sources if r['arm']==arm]) for key in ['E_P95_mm','J_P95_mm','E_coverage_2.0mm','J_coverage_2.0mm','CD_L1_mm']} for arm in ['V1','Morton_area_stratified8k','Nop_D_V1','Nop_D_Morton_area_stratified8k','GT_8192']}
 rows=['# Fold C V1／Morton采样对照：正式评分冻结审计与科研解读 v1','',
 '## 核心结论','',
 '**评分产物通过正式只读冻结审计，但本次Morton候选没有获得模型端整体优于V1的证据。** 主终点未知表面E的来源等权P95由8.410增至9.139 mm；切壁J P95和CD-L1也变差。输入侧接口支持确实改善，但没有稳定转化为输出侧补全和接口几何收益。因此当前保留V1作为主线默认，Morton保留为有输入几何依据、尚未取得模型收益的候选，不直接替换主实验采样。', '',
 '本结论限定于当前SkullBreak Fold C、seed0、B0 AdaPoinTr、8k→8k和固定训练合同；没有bootstrap、p值、正式gate、跨seed复现或临床结论，也不是Mamba方法的否定性实验。', '',
 '## 正式审计结果','',
 f"机器状态：`{audit['status']}`，24组检查通过。授权request SHA256：`{audit['request_sha256']}`。退出码0，105病例、21来源；210模型评分＋315 CPU控制，共525病例行，105来源行，其中42行来自两模型。",'',
 '独立使用stdlib从保存病例指标重新计算同来源五缺损均值、21来源等权均值、Morton−V1差值、差值中位数／范围／胜负数、五缺损类别汇总、完整回退排序及三份CSV，全部与结果文件一致。11个结果文件的完整大小／SHA256清单已冻结。', '',
 f"同时核对最终代码／测试／metric、授权链、下载归档及全部315个开发输入／参考文件哈希；内容相关指纹读取前后稳定（排除atime）。读取{audit['read_bytes']:,} bytes，耗时{audit['elapsed_seconds']:.3f}秒。未重算几何距离或解码真实预测／参考数组，未运行评分、模型、GPU或服务器操作。",'',
 '本审计证实产物身份、计算记录和汇总一致性；几何距离本身依赖固定实现及已通过的人工CPU合同，不能把汇总审计表述为第二次独立几何复算。资源成功依据原采样守卫与完成记录，不是独立峰值RSS监测。', '',
 '## 设计和指标','',
 '两臂fresh scratch训练，共同初始化、来源划分、批次顺序、3900更新、31200曝光、配置、数值后端及共同点序政策已分别审计配对。评价均为native eval，final权重与原BN状态，无BNCal、TTA、投票或模型更新。每来源五缺损作为一个汇总单位，21来源等权；每例指标先算后平均，不把全部面点池化重算P95。', '',
 'E为缺失骨块的未知原始表面，J为与残缺骨共享的切壁。A1参考采用原G边界面心及面积权重，逆D-only归一化回mm。P95和CD越低越好，覆盖率越高越好。J距离／覆盖仅描述离散几何支持，不等同临床接触间隙、骨厚度或网格拓扑合格。该设计比较“训练与评价均使用各自采样”的整体策略，不能分离训练采样和测试采样的各自效应。', '',
 '## 模型主结果','',
 '| 指标 | V1 | Morton | Morton−V1 | 改善／变差来源 |','|---|---:|---:|---:|---:|']
 labels=[('E_P95_mm','E P95（主终点，mm）',False),('J_P95_mm','J P95（mm）',False),('E_coverage_2.0mm','E Cover@2mm',True),('J_coverage_2.0mm','J Cover@2mm',True),('CD_L1_mm','CD-L1（mm）',False)]
 for key,label,coverage in labels:
  v=metrics[key]
  if coverage:values=[f"{100*v['mean_V1']:.2f}%",f"{100*v['mean_Morton']:.2f}%",f"{100*v['mean_delta_Morton_minus_V1']:+.3f}个百分点"]
  else:values=[f"{v['mean_V1']:.3f}",f"{v['mean_Morton']:.3f}",f"{v['mean_delta_Morton_minus_V1']:+.3f}"]
  rows.append('| '+label+' | '+' | '.join(values)+f" | {v['improved_sources']}／{v['worse_sources']} |")
 e=metrics['E_P95_mm'];j=metrics['J_P95_mm']
 rows+=['',f"主终点均值变差{100*e['mean_delta_Morton_minus_V1']/e['mean_V1']:.2f}%，但E差值中位数为{e['median_delta']:.3f} mm，21来源中11个改善、10个变差。J差值中位数为{j['median_delta']:.3f} mm，同样11改善／10变差。均值与中位数方向不同，表明来源间差异及较大回退需要关注；不能凭11比10或中位数轻微改善宣布候选胜出。",'',
 'J Cover@2mm仅增加约0.092个百分点，而J P95仍增加0.663 mm。局部阈值覆盖可以略好，同时远端尾部误差变差，两者不矛盾；单独挑覆盖率不足以证明接口吻合改善。', '',
 '## 输入几何改善是否真的存在','',
 '| CPU几何控制 | J P95（mm） | J Cover@2mm | E Cover@2mm |','|---|---:|---:|---:|']
 for arm,label in [('Nop_D_V1','V1输入原样'),('Nop_D_Morton_area_stratified8k','Morton输入原样'),('GT_8192','共同GT8192点集')]:
  v=controls[arm];rows.append(f"| {label} | {v['J_P95_mm']:.3f} | {100*v['J_coverage_2.0mm']:.2f}% | {100*v['E_coverage_2.0mm']:.2f}% |")
 input_delta=controls['Nop_D_Morton_area_stratified8k']['J_coverage_2.0mm']-controls['Nop_D_V1']['J_coverage_2.0mm']
 rows+=['',f"同105例输入的J覆盖从61.04%升至68.40%，增加{100*input_delta:.3f}个百分点，J P95从3.491降至2.958 mm。说明本次候选在开发输入侧的接口支持改善是真实记录到的，不只是在之前全数据几何检查中观察到。",'',
 '然而模型输出并未保留同量级改善：J覆盖仍约46%，且E、J尾部距离和CD变差。可靠表述是“输入支持改善没有稳定转化为当前模型输出收益”。不能仅凭此定位为FPS／proxy、encoder或decoder某一处丢失，也不能诊断具体优化机制。此问题应从既有预测的几何形态进一步区分。', '',
 '输入原样控制覆盖全部残缺颅骨D，不是缺失骨块预测器；不能因它在J上较近而声称其整体补全更优。共同GT8192的E P95约1.310 mm、E/J覆盖约99.51%／99.76%，提示离散采样自身仍有误差尺度；该点集不是最优点配置，不能把其数值当不可突破的理论误差下界。', '',
 '## 来源异质性和大回退','',
 '| 来源 | E P95 V1（mm） | Morton（mm） | 差值（mm） |','|---|---:|---:|---:|']
 for sid in ['train:051','train:053','train:041','train:013']:
  a=lookup[(sid,'V1')]['E_P95_mm'];b=lookup[(sid,'Morton_area_stratified8k')]['E_P95_mm'];rows.append(f"| {sid} | {a:.3f} | {b:.3f} | {b-a:+.3f} |")
 rows+=['',
 '051、053来源有明显回退，041、013则明显改善，两臂都存在较大的病例依赖性。表格用于解释异质性，不剔除任何来源，不重算“去异常后”的主结果。相同初始化和seed控制了起点，但不估计训练随机性的分布；输入变化会改变后续优化轨迹，不能从单次对照把所有差异归结为某一种网络机制。', '',
 '## 按固定缺损类别的描述性差值','',
 '| 缺损类别（各21来源） | E P95 Δmm | J P95 Δmm | E Cover@2mm Δ百分点 | J Cover@2mm Δ百分点 | CD Δmm |','|---|---:|---:|---:|---:|---:|']
 for name in ['bilateral','frontoorbital','parietotemporal','random_1','random_2']:
  v=defects[name]['mean_deltas'];rows.append(f"| {name} | {v['E_P95_mm']:+.3f} | {v['J_P95_mm']:+.3f} | {100*v['E_coverage_2.0mm']:+.3f} | {100*v['J_coverage_2.0mm']:+.3f} | {v['CD_L1_mm']:+.3f} |")
 reverse=metrics['reverse_A2_P95_mm'];outlier=metrics['reverse_A2_outlier_2.0mm']
 rows+=['',
 '额眶frontoorbital和颞顶parietotemporal的E P95方向较差；双侧和两类随机缺损的E P95均值差值接近零或略有改善，但CD在五类中均变差，因此没有哪一类能据此直接认定为整体胜出。类别结果不用于追加挑选训练子集或修改当前结论。', '',
 '## 反向误差和离散参考敏感性','',
 f"反向A2 P95从{reverse['mean_V1']:.3f}增至{reverse['mean_Morton']:.3f} mm，增加{reverse['mean_delta_Morton_minus_V1']:.3f} mm，14／21来源变差。预测点到参考的>2mm离群比例从{100*outlier['mean_V1']:.2f}%增至{100*outlier['mean_Morton']:.2f}%，增加{100*outlier['mean_delta_Morton_minus_V1']:.3f}个百分点。它与CD变差共同提示预测点偏离目标表面的尾部误差增加，但不能在未看空间分布前直接诊断为整体平移、零散漂移或错误骨块。",'',
 f"A2的E P95差值为{metrics['A2_E_P95_mm']['mean_delta_Morton_minus_V1']:+.6f} mm，与A1的{e['mean_delta_Morton_minus_V1']:+.6f} mm接近，J方向也一致；B全表面P95差值为{metrics['B_all_P95_mm']['mean_delta_Morton_minus_V1']:+.3f} mm。当前负向模型结果没有呈现为仅由A1面心离散选择导致的方向翻转。但A2/B仍是同源离散参考，不是独立解剖真值或临床验证。", '',
 '## 下一步建议','',
 '1. 本次采样最小模型对照到此收束：保留V1默认；不把Morton升级为“已胜出”方案，不自动新增Fold D、seed、采样参数扫描或训练。完整保留候选的几何收益和模型负向／混合结果。',
 '2. 若继续定位原因，先只用既有预测和开发数据做一次限定可视化审阅：固定两个明显回退来源051／053与两个改善来源013／041，各看bilateral与frontoorbital，共8病例，两个模型同视角叠加D、G、预测，并查看剖面和远端离群。该选择用于解释，不构成无偏新评价或新的成功率；不得删去它们后重报主指标。',
 '3. 先区分整块位置／形状错误、少量远端离群和切壁附近局部误差，再决定是否值得研究模型如何利用局部多表面信息。现有证据不足以给某一proxy阶段或模块定责；目前不授权新模型、定位器或工程框架扩展。',
 '4. 第三个问题“表面采样方法”已有一个可执行默认和一个被检验的候选：完整骨边界、V1采样可继续使用，Morton改善输入局部支持但没有稳定输出收益。该结果不推翻完整骨边界表面、实体缺损或缺失骨块完整表面目标，也不回答输出点数最优性；当前对照固定8k→8k。', '',
 '## 证据文件','',
 f"正式评分审计：`audit_report_v1.json`，SHA256 `{h(F/'audit_report_v1.json')}`。",'',
 '原始结果位于同级`paired_scores_v1`，审计冻结的11文件哈希见下表。报告只读取已冻结指标，不更改结果，不新增几何距离计算。', '',
 '| 文件 | bytes | SHA256 |','|---|---:|---|']
 for r in audit['output_manifest']:rows.append(f"| {Path(r['path']).name} | {r['bytes']} | `{r['sha256']}` |")
 save('formal_audit_and_scientific_interpretation_zh_v1.md','\n'.join(rows)+'\n')
 with (F/'interpretation_summary_v1.json').open('x') as f:json.dump(dict(status='AUDITED_DESCRIPTIVE_RESULT_NO_STABLE_MORTON_MODEL_BENEFIT',primary=metrics['E_P95_mm'],key_secondary={k:metrics[k] for k in ['J_P95_mm','E_coverage_2.0mm','J_coverage_2.0mm','CD_L1_mm']},input_controls=controls,all_cases_retained=True,bootstrap=False,formal_gate=False,new_training=False,analysis_source='audited saved metrics only',audit_sha256=h(F/'audit_report_v1.json')),f,indent=2)
 files=[dict(name=p.name,bytes=p.stat().st_size,sha256=h(p)) for p in sorted(F.iterdir()) if p.is_file()]
 with (F/'audit_and_interpretation_artifact_manifest_v1.json').open('x') as f:json.dump(dict(status=audit['status'],files=files),f,indent=2)
 print(json.dumps(dict(status=audit['status'],report=str(F/'formal_audit_and_scientific_interpretation_zh_v1.md'),conclusion='No stable model-level benefit for Morton in this pilot',primary_delta=e['mean_delta_Morton_minus_V1'],input_J_coverage_delta_pp=100*input_delta,model_J_coverage_delta_pp=100*metrics['J_coverage_2.0mm']['mean_delta_Morton_minus_V1'],no_new_experiment=True)))
if __name__=='__main__':main()
