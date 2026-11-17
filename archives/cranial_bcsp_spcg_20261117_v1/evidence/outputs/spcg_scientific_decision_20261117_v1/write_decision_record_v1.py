# -*- coding: utf-8 -*-
"""Record decisions from frozen evidence only; no scoring, bootstrap, gate, or experiment."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
S=R/'outputs/spcg_score_implementation_20261117_v1';SF=R/'outputs/spcg_score_freeze_20261117_v1';VF=R/'outputs/spcg_visualization_freeze_20261117_v2';V=R/'outputs/spcg_coarse_dense_visualization_20261117_v1';T=R/'outputs/spcg_native_prediction_preparation_20261117_v1/implementation_v1/pending_transport_v1/payload'
READ=[]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def rec(p):
 p=Path(p);return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=sha(p))
def bound(r):
 p=Path(r['path']);assert p.is_file() and not any(x.is_symlink() for x in [p,*p.parents]);assert p.stat().st_size==r['bytes'] and sha(p)==r['sha256'];READ.append(r);return p
def load(p):
 p=Path(p);READ.append(rec(p));return json.loads(p.read_bytes())
def emit(name,v):
 with (O/name).open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False)
q=load(S/'SPCG_local_scoring_execution_request_v1.json');assert sha(S/'SPCG_local_scoring_execution_request_v1.json')=='7b6b3e5f6ade721540397e2c7977a85e2c73298f7e5cedb489b79f257eae27f8'
score=load(SF/'audit_verification_v1.json');visual=load(VF/'audit_verification_v1.json');closure=load(VF/'closure_manifest_v2.json');summary=load(SF/'frozen_research_summary_v1.json');geo=load(V/'fixed_case_geometry_metrics_v1.json');pairs=load(S/'unified_scores_v1/paired_comparison.json')
assert score['status']=='FORMAL_SPCG_THREE_ARM_TWOFOLD_POST_SCORE_FREEZE_AUDIT_PASS' and all(score['checks'].values())
assert visual['status']=='FORMAL_SPCG_FIVE_CASE_POST_DIAGNOSTIC_FREEZE_AUDIT_V2_PASS' and all(visual['checks'].values())
for fold in ['C','D']:
 for key,comp in summary['folds'][fold]['comparisons'].items():
  for metric,value in comp['metrics'].items():assert value==pairs['comparison'][fold][key]['metrics'][metric]
for r in closure['files']:bound(r)
for root,inventory in [(S/'unified_scores_v1',score['inventory']['output']),(S/'authorized_execution_v1',score['inventory']['execution']),(V,visual['inventory'])]:
 for name,r in inventory.items():bound(dict(path=str(root/name),bytes=r['bytes'],sha256=r['sha256']))
index=load(bound(q['prediction_index']));train=[]
for run in index['runs']:
 p=T/('frozen_'+run['label']+'_training_audit_v1.json');r=rec(p);assert all(r[k]==run['training_audit'][k] for k in ['bytes','sha256']);x=load(p)
 assert x['status']=='FORMAL_SPCG_'+run['label']+'_POST_TRAINING_FREEZE_PASS' and all(x['checks'].values())
 assert (x['updates'],x['traversals'],x['exposures'],x['drops'])==(3900,100,31200,300) and x['checkpoint']==run['checkpoint']
 train.append(dict(run=run['label'],audit=r,updates=3900,traversals=100,exposures=31200,drops=300,checkpoint=x['checkpoint'],order_sha256=x['order_plan']['sha256'],initial_tensor_fingerprint=x['initialization_raw_tensor_fingerprint'],training_device=run['training_identity']['gpu_uuid'],accepted_pairing_limit=x.get('pairing',{})))
for fold in ['C','D']:
 rr=[r for r in train if r['run'].endswith('_'+fold)];assert len(rr)==3 and len({r['order_sha256'] for r in rr})==1
 g12=[r for r in rr if r['run'].startswith(('G1','G2'))];assert len({r['initial_tensor_fingerprint'] for r in g12})==len({r['training_device'] for r in g12})==1
protocol=bound(q['evidence']['inherited_protocol'])
decision=dict(schema='bcsp-spcg-scientific-conclusion-decision-v1',date_Asia_Shanghai='2026-11-17',status='CURRENT_FIXED_SPCG_G2_CANDIDATE_CLOSED_BY_EVIDENCE_REVIEW',scope='FixedG0/G1/G2, twofold, seed0,8k->8k,3900-step matrix; no claim all spatial conditioning is ineffective',decision='Close current fixedG2 candidate and pause further investment; do not promoteG1 to established baseline; retainG0 as frozen reference',scientific_hypotheses=dict(local8_better_than_global256='NOT_SUPPORTED_IN_THIS_PROTOCOL',G2_better_than_original_G0='NOT_ESTABLISHED',G1_head_better_than_G0='NOT_ESTABLISHED',better_radius_or_local_coverage_implies_reliable_full_block='NOT_SUPPORTED',selected_extreme_failures_first_appear_only_at_dense='NOT_SUPPORTED_FOR_THREE_SELECTED_CASES',unique_internal_cause='UNRESOLVED'),evidence_counts=dict(training_runs=6,updates_per_run=3900,model_predictions=630,shared_controls=420,case_score_rows=1050,unique_dev_cases=210,unique_dev_sources=42,bootstrap_per_fold=2000,diagnostic_cases=5,diagnostic_existing_predictions=15),training_matrix=train,source_request_sha256=score['request_sha256'],score_audit=rec(SF/'audit_verification_v1.json'),diagnostic_audit=rec(VF/'audit_verification_v1.json'),formal_investment_gate_executed=False,new_scores=0,new_bootstrap=0,new_forward=0,new_training=0,implementation_authorized=False,server_operations=0,unresolved=['Probe/neighborhood spatial support versus feature informativeness versus coarse-head use cannot be uniquely separated.','8 versus256 changes aggregation cardinality and smoothing as well as locality.','FullMemory/probe/index summaries missing in authorizedNative archive.','Coarse observation is not proof of earliest internal failure node.','One seed, development exposure, finite gradient nondeterminism and D_G0 training-device confound remain.'],future_minimum_question='Can coarse generation use D-only spatial evidence to reduce wrong-region placement and missing-target coverage without increasing reverse outliers or newly severe cases, under a frozen matched comparison?',next_actions_not_authorized=['Newformula/implementation','Secondseed or retraining','Memory restoration/new forward','Provider/environment changes','Archive/GitHub/deletion'])
emit('scientific_decision_record_v1.json',decision)
def link(label,p):return '['+label+']('+str(Path(p).resolve()).replace('\\','/')+')'
lines=['# Cranial-BCSP-FullMamba：BCSP-SPCG 科研结论与继续／收束决策记录','',
'版本：v1；日期：2026-11-17。记录性质：基于冻结证据的科研判定与后续投入建议，不是新增实验协议或执行授权。','',
'## 1. 决策','',
'**正式收束当前固定公式的SPCG G2候选，不继续投入第二seed、邻域/探针/权重扫描或自动追加训练。G1不升级为已证实优于G0的新基线；G0保留为既有冻结参考。**','',
'这一决定针对本轮具体模块、固定训练预算、点集与seed0。它不否定Mamba主线，也不等于全部空间条件、探针或局部表征机制无效。负结果仍是有效科研结果，应纳入完整报告、代码和结果归档。','',
'本记录不新算或宣称正式E0/M/U gate回执。原计划继续投入所需的主指标方向和无新增严重条件，已被现有结果中的正向误差差值及新增严重病例所反驳；据此停止投入不需要另立有利阈值、补扫参数或删病例。执行有效与方法有效分开表述。','',
'## 2. 本轮完成状态与证据边界','',
'- 六个模型G0/G1/G2×C/D均完成3900次更新、100次遍历、31200次样本曝光和300次丢弃；六份正式训练冻结凭据均通过，checkpoint身份与预测索引一致。本次只读复核凭据，未重新加载权重。','- 同折三臂冻结批次顺序一致；G1/G2的完整初态指纹一致。G0保留不同结构的旧coarse头，不宣称三臂完整state_dict逐字节相同。','- 630次Native预测及1050行统一评分（630模型、420共享控制）已冻结，来源汇总与每折2000次来源配对bootstrap已正式复核。210例来自42个独立来源，每来源5种缺损；病例行不能当独立患者。','- 5例、15份既有预测、30个coarse/dense阶段及20张图，经新版正式只读诊断冻结审计通过。原审计P95求和顺序差异已仅在辅助工具中修正，19项边界回归和20项新版审计通过；原图、原指标和旧失败记录均保留。','- 机制材料不完整：原计划探针、邻域索引/摘要及有限Memory观察未随本轮授权Native范围保存，应记为NOT_COLLECTED。不能把六模型评分完成写成原计划所有机制采集项目均已完成。','',
'C折三臂同训练设备；D折G1/G2同新设备，G0_D来自旧设备。因此G2−G1是两折都有同设备配对的核心证据，D折对G0的比较仅作跨设备参考。统一推理设备不消除此限制。','',
'## 3. 支撑决策的主要数值','',
'### 3.1 核心比较 G2−G1','',
'差值为候选减参考：误差越负越好；覆盖率越正越好。下列均为来源等权的病例指标均值差，不是把全部点混合求P95。','',
'|折|E P95差/mm及95%来源区间|J P95差/mm及95%来源区间|J Cover@2mm差/百分点|新增严重／挽回|','|---|---|---|---:|---:|']
for f in ['C','D']:
 c=summary['folds'][f]['comparisons']['G2_minus_G1'];e,j=c['metrics']['E_P95_mm'],c['metrics']['J_P95_mm'];ec=e['bootstrap']['CI95'];jc=j['bootstrap']['CI95'];risk=c['severe'];lines.append(f"|{f}|{e['mean_delta_b_minus_a']:+.4f} [{ec[0]:+.4f}, {ec[1]:+.4f}]|{j['mean_delta_b_minus_a']:+.4f} [{jc[0]:+.4f}, {jc[1]:+.4f}]|{100*c['metrics']['J_coverage_2.0mm']['mean_delta_b_minus_a']:+.4f}|{risk['new']}／{risk['rescued']}|")
lines+=['',
'C折E P95为12/21来源回退，区间跨0，不能声称确定的总体劣势或等效；D折18/21来源回退，E/J P95及CD-L1差值的区间均为正。两折均没有得到G2主指标优于G1的方向信号，且新增严重病例分别9和7例。','',
'C折J Cover@2mm提高7.0196个百分点，来源区间为[2.6035,12.1417]，但伴随更高的J P95与严重退化。D折对应覆盖差仅+0.3750个百分点，区间跨0；不能用C折单个次指标替代主指标或安全性表现。','',
'### 3.2 新头相对原头','',
'|折|G2−G0 E P95/mm|G1−G0 E P95/mm|G1−G0 J Cover@2mm/百分点|','|---|---:|---:|---:|']
for f in ['C','D']:
 c=summary['folds'][f]['comparisons'];lines.append(f"|{f}|{c['G2_minus_G0']['metrics']['E_P95_mm']['mean_delta_b_minus_a']:+.4f}|{c['G1_minus_G0']['metrics']['E_P95_mm']['mean_delta_b_minus_a']:+.4f}|{100*c['G1_minus_G0']['metrics']['J_coverage_2.0mm']['mean_delta_b_minus_a']:+.4f}|")
lines+=['',
'G2相对G0的主误差两折均回退约1.44mm。G1主误差变化很小、区间均跨0，接口覆盖反而下降。D折对G0比较保留设备混杂，不可用于严格单因素归因。没有足够证据将G1或G2作为优胜基线。','',
'## 4. 哪些假设未获支持','',
'|假设|本轮结论|证据与含义|','|---|---|---|',
'|固定8邻域局部Memory摘要比256全局摘要更适合补全|未获支持|两折G2−G1主误差均为正，D折多数来源与E/J/CD同时回退；不等于所有局部机制无效。|',
'|SPCG G2可直接提升原LQI母版的实用精度与可靠性|未建立|对G0无稳定整体收益并有新增严重病例；D对G0还混有设备变化。|',
'|引入探针/共享头本身足以获得提升|未建立|G1相对G0改善不稳定，接口覆盖下降；结构参数化也不同，不能把差值归于单一因素。|',
'|半径或局部覆盖改善意味着完整骨块可靠性提升|未获支持|G2半径比更接近1、C折J覆盖提高，但位置、尾部和严重病例没有同步改善。|',
'|这3例新增严重主要由dense把正确coarse放大成错误骨块|选中病例不支持此解释|明显偏位/漏覆盖在已保存coarse已存在；不代表所有病例或首次内部失败节点。|','',
'这些是对特定方案的证据判断，不是统计学证明整个研究方向不可能有效。bootstrap区间跨0不能解释为无差异已证实，区间不跨0也不自动成为跨seed或临床结论。','',
'## 5. 诊断明确了什么','',
'3例新增严重：`train__051__random_1`、`train__072__random_1`、`train__008__random_2`。G2 coarse质心偏差分别97.552、89.779、23.879mm；dense为97.699、90.631、22.314mm。前两例大范围位置错误，第三例还表现为明显收缩和漏覆盖。','',
'008病例反向>20mm离群为0，却有dense E95=35.557mm、J95=44.535mm，说明“预测点都离目标不远”不能替代“目标被完整覆盖”。072的coarse半径比接近1，却有约90mm位置偏差，说明尺度矩不能替代正确位置。','',
'改善对照`train__012__parietotemporal`的收益也在coarse阶段就出现；`train__046__parietotemporal`虽然E/J明显改善，仍有32.42%的dense点距目标A2超过20mm，不能当正常病例。','',
'因此可将下一问题的关注点放在coarse空间条件的可靠利用与目标覆盖，而非优先给dense追加补偿。但这里只观察到已保存节点的共现，不是因果定位。coarse256与dense8192点数不同，覆盖提升含点预算效应；不能直接称为dense机制修复。','',
'## 6. 哪些机制仍未知','',
'|未解决问题|为什么现有证据不能回答|不能据此做的决定|','|---|---|---|',
'|错误在输入Memory、探针覆盖、邻域读取还是坐标头产生|没有保存实际Memory、probe/索引/摘要，只有coarse/dense|不能宣称某个内部组件是唯一根因。|',
'|局部性还是聚合基数/平滑导致差异|G2取8个邻居，G1用全部256，两因素同时变化|不能将G2−G1全部解释为几何局部性效应。|',
'|coarse前哪个节点首次失效|缺少内部同次观测或同权重反事实|不能把返回coarse当成计算图中首次产生错误的位置。|',
'|具体数据分布、归一化或坐标敏感性如何作用|同病例共享坐标合同且三臂表现不同，仅削弱统一变换错误作为唯一解释|不能声称已排除所有上游空间因素。|',
'|是否对其他初始化、数据集或真实患者稳定|seed0、反复开放开发集、合成缺损、D部分跨设备|不能给出训练随机性、外部验证或临床可用性结论。|',
'|如何保证接口厚度、水密性和无穿透|当前是点云距离与离散切壁支持|不能将Cover@2mm当可植入的接口安全。|','',
'有限梯度非确定性、开发选择偏差和病例相关性仍存在。来源bootstrap以每来源五缺损为一个配对单位，刻画条件于这些已训练模型的来源抽样不确定性，不估计训练方差或消除混杂。','',
'## 7. 继续／收束动作清单','',
'|对象|决策|保存或停止的范围|','|---|---|---|',
'|当前G2固定公式|收束|保留全部正负结果，不补第二seed、扫描半径/邻域/权重或删退化病例。|',
'|G1候选|不晋升|作为解释性对照保存；少数均值下降不足以替换正式参考。|',
'|G0参考|保留|后续研究可复用其冻结基线证据，但新设备/入口变化仍需说明。|',
'|Mamba颅骨补全主线|继续研究，尚未批准新实验|不因当前负结果否定架构主线；新问题与新方案须另立最小协议。|',
'|本轮机制补采|不自动追加|Memory缺项披露为缺项；不为补齐旧结论启动新forward。|',
'|文档与归档|建议随后完成|完整实验报告、代码/结果清单、关键权重保存可另行开展；本记录不自动推送或清理服务器。|','',
'## 8. 新方案必须先回答的最小问题','',
'**在不改输入表示、dense重建和3900步预算的前提下，coarse生成能否可靠利用仅来自D的空间证据，减少错误区域生成与目标漏覆盖，同时不增加远端离群或新增严重病例？**','',
'这是一项待确认的研究问题，不是已经选定的公式。任何新方案至少应在实施前明确：','',
'1. **信息是什么、从哪里来。** 精确写出可用输入坐标/特征、进入coarse头的接口和公式；推理时不能依赖GT、GT框、事后配准或人工定位。GT仅用于独立评分与离线解释。','2. **改变了哪个单一因素。** 以冻结参考为基础，说明参数化、聚合基数、特征平均、局部性中的哪些变化不可分离。若要声称局部性有效，必须预先设计可辨识对照，而不是再次把8对256当作纯局部性消融。不要同时改采样、loss、decoder和训练预算。','3. **如何证明信息被真正利用。** 在真实主计算图中设置最少的同次观察量，记录输入证据到coarse输出的对应和响应；先冻结保存字段，避免研究结束才发现机制材料缺失。训练期附加头或矩预测改善不能代替主生成路径有收益。','4. **什么结果会推翻它。** 原生world-mm的E/J、双向覆盖/离群与新严重必须一起报告，两折、所有缺损、来源单位和种子策略预先固定。若只改善一个矩/单个覆盖指标而主误差或新严重变差，不应将其继续包装成有效方案。任何数值准入或投资条件均应在新结果前写清，不在结果出来后重定。','5. **最小证据能否改变决策。** 新诊断必须能区分至少两个竞争解释，并写出各结果对应的动作；若不能改变继续/收束决定，则不值得为其扩展采集工具或追加模型运行。','',
'建议优先完成一个可证伪的问题与唯一接口/公式，而不是马上叠加新的反馈或校准模块。也不应把“用输入均值/包围盒限制输出”视为现成答案：全颅骨范围并不等于缺损区域，既有矩改善也没有证明完整形状收益。当前记录不选择具体算法、不设新超参数、不创建request。','',
'## 9. 证据索引与溯源','']
for label,p in [('修订版预注册计划',protocol),('六模型预测索引',q['prediction_index']['path']),('评分正式冻结',SF/'audit_verification_v1.json'),('全量评分解读',SF/'正式评分后冻结审计与G0_G1_G2结果解读_zh_v1.md'),('五例几何诊断',V/'固定五例_coarse_dense几何诊断报告_zh_v1.md'),('诊断新版正式冻结',VF/'audit_verification_v1.json'),('诊断审计修正闭环',VF/'closure_manifest_v2.json')]:lines.append('- '+link(label,p))
lines+=['','六份训练凭据、checkpoint身份、顺序和设备绑定见同目录 `scientific_decision_record_v1.json`；本记录读取的证据文件哈希见 `evidence_manifest_v1.json`。没有重新计算真实评分、bootstrap或正式gate，没有服务器操作。','']
report=O/'SPCG_科研结论与继续收束决策记录_zh_v1.md'
with report.open('x',encoding='utf-8') as f:f.write('\n'.join(lines))
evidence=list({r['path']:r for r in READ}.values())
for r in evidence:bound(r)
emit('evidence_manifest_v1.json',dict(status='FROZEN_EVIDENCE_UNCHANGED_DECISION_RECORDED',source_files=evidence,source_files_checked=len(evidence),no_new_scoring=True,no_new_gate=True,no_new_forward=True,no_server_operations=True))
emit('delivery_manifest_v1.json',dict(status=decision['status'],files=[rec(p) for p in sorted(O.iterdir()) if p.is_file()]))
print(json.dumps(dict(status=decision['status'],training_audits=6,score_freeze_checks=score['check_count'],diagnostic_freeze_checks=visual['check_count'],evidence_files=len(evidence),report=str(report),new_experiment_calls=0),ensure_ascii=False))
