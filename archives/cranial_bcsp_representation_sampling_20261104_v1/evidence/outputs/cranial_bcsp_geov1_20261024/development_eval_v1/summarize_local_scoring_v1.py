"""Read completed fixed scores; check counts/pairing; write source-grounded Chinese report."""
from pathlib import Path
import csv,hashlib,json,math,statistics
N=Path(__file__).resolve().parent;A=N/'local_scoring_v1';R=A/'results'
def load(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bind(p):return dict(path=str(Path(p).absolute()),bytes=Path(p).stat().st_size,sha256=sha(p))
def emit(name,obj):
 p=A/name
 with p.open('x') as f:json.dump(obj,f,ensure_ascii=True,indent=2,allow_nan=False)
 return p
def finite(x):return isinstance(x,(int,float)) and math.isfinite(x)
def fmt(x,scale=1):return f'{x*scale:.4f}' if finite(x) else str(x)
process=load(A/'process_result.json');completion=load(R/'completion.json');comparison=load(R/'paired_comparison.json')
assert process['status']=='LOCAL_CPU_SCORING_PROCESS_EXIT0' and completion['status']=='LOCAL_CPU_SCORING_COMPLETE'
assert completion['model_predictions']==420 and completion['controls']==630 and completion['source_rows']==210
assert completion['plan_sha256']==sha(A/'scoring_plan_v1.json') and completion['archive_sha256']==load(A/'download_verification.json')['files'][0]['sha256']
cases=[json.loads(x) for x in (R/'case_metrics.jsonl').read_text().splitlines()];sources=load(R/'source_metrics.json')
assert len(cases)==1050 and len(sources)==210 and len({(r['case_id'],r['arm']) for r in cases})==1050
assert len({r['case_id'] for r in cases})==210 and len({r['source_id'] for r in cases})==42
arms=['8192','16384','Nop_D_8192','Nop_D_16384','GT_8192']
assert {r['arm'] for r in cases}==set(arms) and all(sum(r['arm']==a for r in cases)==210 for a in arms)
assert all(sum(r['arm']==a for r in sources)==42 for a in arms)
index=load(N/'development_input_index_v1.json');refs=load(N/'reference_bank_v2/reference_manifest_v1.json')
identity={r['case_id']:(r['fold'],r['source_id']) for r in refs['cases']}
for r in cases:assert identity[r['case_id']]==(r['fold'],r['source_id'])
for s in sources:
 part=[r for r in cases if (r['fold'],r['source_id'],r['arm'])==(s['fold'],s['source_id'],s['arm'])]
 assert len(part)==s['case_count']==5 and len({r['case_id'] for r in part})==5
 for k,v in s['metrics'].items():
  values=[r['metrics'][k] for r in part]
  if all(finite(x) for x in values):assert finite(v) and math.isclose(sum(values)/5,v,rel_tol=1e-12,abs_tol=1e-12)
assert comparison['unique_sources']==42 and comparison['case_count']==210 and comparison['model_predictions']==420
source_lookup={(s['source_id'],s['arm']):s for s in sources}
for fold,n in [('C',21),('D',21),('ALL',42)]:
 block=comparison['comparisons'][fold];assert block['source_count']==n
 for metric,m in block['metrics'].items():
  ids=sorted({s['source_id'] for s in sources if s['arm']=='8192' and (fold=='ALL' or s['fold']==fold)})
  a=[source_lookup[(i,'8192')]['metrics'][metric] for i in ids];b=[source_lookup[(i,'16384')]['metrics'][metric] for i in ids]
  if all(finite(x) for x in a+b):
   assert math.isclose(statistics.mean(a),m['mean_8192'],rel_tol=1e-12,abs_tol=1e-12) and math.isclose(statistics.mean(b),m['mean_16384'],rel_tol=1e-12,abs_tol=1e-12)
   d=m['delta_16k_minus_8k'];assert d['source_count']==n and d['bootstrap_replicates']==10000 and d['seed']==20261024
   assert math.isclose(statistics.mean(y-x for x,y in zip(a,b)),d['mean'],rel_tol=1e-12,abs_tol=1e-12)
for name,n in [('case_metrics.csv',1050),('source_metrics.csv',210)]:
 with (R/name).open(newline='') as f:assert len(list(csv.DictReader(f)))==n
invalid=sum(r['status']!='OK' for r in cases);assert invalid==sum(s['invalid_predictions'] for s in sources)
control_means={arm:{k:statistics.mean(s['metrics'][k] for s in sources if s['arm']==arm) for k in sources[0]['metrics'] if all(finite(s['metrics'][k]) for s in sources if s['arm']==arm)} for arm in arms}
# Descriptive sensitivity uses the already frozen A2 metric,not a new primary or bootstrap.
sensitivity={};wins={}
for fold in ['C','D','ALL']:
 sensitivity[fold]={}
 for metric,region in [('A2_E_P95_mm','E'),('A2_J_P95_mm','J')]:
  values={}
  for arm in ['8192','16384']:
   per_source={}
   for row in cases:
    if row['arm']==arm and (fold=='ALL' or row['fold']==fold):per_source.setdefault(row['source_id'],[]).append(row['full_metrics']['regions']['A2'][region]['p95_mm'])
   values[arm]=statistics.mean(statistics.mean(v) for v in per_source.values())
  sensitivity[fold][metric]=dict(mean_8192=values['8192'],mean_16384=values['16384'],delta_16k_minus_8k=values['16384']-values['8192'],descriptive_only=True)
 for metric in ['E_P95_mm','J_P95_mm','J_coverage_2.0mm']:
  deltas=[]
  for sid in sorted({s['source_id'] for s in sources if s['arm']=='8192' and (fold=='ALL' or s['fold']==fold)}):deltas.append(source_lookup[(sid,'16384')]['metrics'][metric]-source_lookup[(sid,'8192')]['metrics'][metric])
  wins[fold+'__'+metric]=dict(improved=sum((d>0 if 'coverage' in metric else d<0) for d in deltas),unchanged=sum(d==0 for d in deltas),worse=sum((d<0 if 'coverage' in metric else d>0) for d in deltas),source_count=len(deltas),descriptive_only=True)
worst={arm:[dict(source_id=s['source_id'],fold=s['fold'],E_P95_mm=s['metrics']['E_P95_mm'],J_P95_mm=s['metrics']['J_P95_mm']) for s in sorted([s for s in sources if s['arm']==arm],key=lambda s:s['metrics']['E_P95_mm'],reverse=True)[:5]] for arm in ['8192','16384']}
main=comparison['comparisons']['ALL']['metrics'];primary=main['E_P95_mm'];ci=primary['delta_16k_minus_8k']['CI95']
if ci and ci[1]<0:primary_sentence='在固定seed0的本轮开发集上，16k输入的未知原始表面主误差降低，配对区间整体位于0以下。'
elif ci and ci[0]>0:primary_sentence='在固定seed0的本轮开发集上，16k输入的未知原始表面主误差升高，配对区间整体位于0以上。'
else:primary_sentence='本轮主终点的配对区间跨越或接触0，尚未获得16k输入稳定改善未知原始表面补全的证据；这不等于证明两设置等效。'
interface=main['J_P95_mm'];jci=interface['delta_16k_minus_8k']['CI95'];coverage=main['J_coverage_2.0mm'];cci=coverage['delta_16k_minus_8k']['CI95']
if jci and cci and jci[1]<0 and cci[0]>0:interface_sentence='切壁J的P95降低且2mm覆盖增加，两者配对区间均支持改善方向；该结果只涉及离散接口几何指标。'
elif jci and cci and (jci[0]>0 or cci[1]<0):interface_sentence='切壁接口至少一项预设指标的配对区间支持恶化方向，不能将未知表面结果直接解释为接口吻合改善。'
else:interface_sentence='切壁接口的P95与2mm覆盖尚未同时给出方向稳定的改善证据，应保留点估计与区间，不宣称接口吻合已改善。'
desc=emit('descriptive_result_summary_v1.json',dict(status='COMPLETED_FIXED_METRIC_DESCRIPTIVE_SUMMARY',case_rows=1050,source_rows=210,invalid_rows=invalid,control_source_means=control_means,A2_sensitivity=sensitivity,source_direction_counts=wins,worst_sources=worst,primary_interpretation=primary_sentence,interface_interpretation=interface_sentence,additional_bootstrap_runs=0,formal_gate_computed=False,model_reruns=0))
lines=['# BCSP输入密度四模型开发集配对评价报告 v1','',
 '研究阶段：BCSP_INPUT_DENSITY_V1。四个B0 AdaPoinTr模型均已完成固定3900步训练；本报告只记录冻结预测的本机CPU评分，不增加训练、BNCal或GPU调用。','',
 '## 结论','',primary_sentence,'',interface_sentence,'',
 '下述数值均是“病例指标先在同一source的五种缺损间等权平均，再对source等权平均”，不是把210例当成210个独立颅骨，也不是将所有表面点混成一个P95。','',
 '## 评价设计与数据来源','',
 '- SkullBreak既定开发来源；Fold C和D各21个开发source、105病例，共42个不同source、210病例。各模型只预测自己的开发来源。没有增加病例筛选；本轮不检验SkullFix或MUG500+泛化。',
 '- 每fold比较8192与16384点输入，两臂均输出8192点；输入8k为16k的精确前缀，同病例目标、归一化、训练更新数及已核验批次顺序保持配对。',
 '- 使用训练最终checkpoint及原BN running statistics，native eval/inference_mode、FP32、严格确定性／TF32关闭；不热身、不投票。四模型各105次，共420次forward。',
 '- 输出目标为缺失实体G的完整边界点集；未知原始表面E_G和与残缺骨D共享的切壁J_G分开评分。D-only归一化逆变换到世界毫米，不增加内外板语义标签。',
 '- A1：G的暴露体素面中心，按真实面面积加权。A2：每暴露面固定四子面中心。B：同一G的固定MC三角形中心，按三角面积加权，仅all G；不伪造B参考的J标签。',
 '- 主终点为A1的E_G→预测点面积加权P95。覆盖阈值0.5／1／2mm只作描述。逆向A2／B距离属于离散参考近似；不称连续mesh距离、surface HD95或面积NSD。',
 '- 固定GT8192的CD-L1为双向欧氏最近邻均值之和的一半，单位mm；GT采样控制不视为严格最优上界。',
 '- 差值统一16k−8k：距离负值较好，覆盖正值较好。按42个source配对bootstrap10000次，seed20261024；Fold C／D另外报告，不新增正式gate、p值或多种子推断。','',
 '## 合并两折的预设指标','',
 '覆盖以百分比显示，差值及区间单位为百分点；其余单位为mm。区间是source配对bootstrap 95%百分位区间。','',
 '| 指标 | 8k | 16k | 16k−8k | 95%区间 |','|---|---:|---:|---:|---|']
labels={'E_P95_mm':'未知原始表面E P95（主终点）','J_P95_mm':'切壁J P95','all_P95_mm':'全G P95','E_coverage_2.0mm':'E 2mm覆盖（%）','J_coverage_0.5mm':'J 0.5mm覆盖（%）','J_coverage_1.0mm':'J 1mm覆盖（%）','J_coverage_2.0mm':'J 2mm覆盖（%）','reverse_A2_P95_mm':'预测→A2参考 P95','B_all_P95_mm':'B参考全G P95','CD_L1_mm':'固定GT点集CD-L1'}
for k,label in labels.items():
 m=main[k];d=m['delta_16k_minus_8k'];scale=100 if 'coverage' in k else 1;interval=d['CI95'];txt='NA' if interval is None else '['+fmt(interval[0],scale)+', '+fmt(interval[1],scale)+']'
 lines.append('| '+label+' | '+fmt(m['mean_8192'],scale)+' | '+fmt(m['mean_16384'],scale)+' | '+fmt(d['mean'],scale)+' | '+txt+' |')
lines+=['','## 分fold与固定参考交叉检查','','| Fold | E P95：8k→16k（mm） | E差值及95%区间（mm） | J P95：8k→16k（mm） | J 2mm覆盖：8k→16k（%） |','|---|---|---|---|---|']
for fold in ['C','D']:
 b=comparison['comparisons'][fold]['metrics'];e=b['E_P95_mm'];j=b['J_P95_mm'];cov=b['J_coverage_2.0mm'];ed=e['delta_16k_minus_8k'];eci=ed['CI95']
 lines.append('| '+fold+' | '+fmt(e['mean_8192'])+' → '+fmt(e['mean_16384'])+' | '+fmt(ed['mean'])+' '+str(eci)+' | '+fmt(j['mean_8192'])+' → '+fmt(j['mean_16384'])+' | '+fmt(cov['mean_8192'],100)+' → '+fmt(cov['mean_16384'],100)+' |')
lines+=['','A2敏感性仅作预设几何参考的描述，不替换主终点或新增bootstrap：','','| A2指标 | 8k（mm） | 16k（mm） | 差值（mm） |','|---|---:|---:|---:|']
for k,m in sensitivity['ALL'].items():lines.append('| '+k+' | '+fmt(m['mean_8192'])+' | '+fmt(m['mean_16384'])+' | '+fmt(m['delta_16k_minus_8k'])+' |')
lines+=['','## 固定控制与source方向','','| 设置 | E P95（mm） | J P95（mm） | J 2mm覆盖（%） |','|---|---:|---:|---:|']
for arm in arms:
 m=control_means[arm];lines.append('| '+arm+' | '+fmt(m['E_P95_mm'])+' | '+fmt(m['J_P95_mm'])+' | '+fmt(m['J_coverage_2.0mm'],100)+' |')
lines+=['','Nop-D只复制已观测骨面，不能代表未知表面补全能力；其接口覆盖较好也不能替代E主终点。Nop-D16k比8k使用更多输出点，属于点预算不同的控制，不能将其密度收益等同于两个均输出8192点的模型收益。GT8192控制反映固定目标采样的表示误差。','',
 '| 合并42个source | 改善 | 持平 | 变差 |','|---|---:|---:|---:|']
for k,label in [('E_P95_mm','E主误差'),('J_P95_mm','J误差'),('J_coverage_2.0mm','J 2mm覆盖')]:
 v=wins['ALL__'+k];lines.append('| '+label+' | '+str(v['improved'])+' | '+str(v['unchanged'])+' | '+str(v['worse'])+' |')
lines+=['','方向计数仅作描述，不是额外显著性检验；完整42个source及210病例见CSV，未删除无利病例。','',
 '## 可靠性、局限与下一阶段','',
 '本机四文件及423个成员与服务器正式冻结审计完全一致。实际输出420模型评分＋630固定控制＝1050条，source层210条（42×5设置）；无效评分记录 '+str(invalid)+' 条。CSV与JSON行数、身份、五缺损汇总及配对均值已交叉核对；未重复运行bootstrap或模型。',
 '',
 '模型state与CPU RNG前后不变来自已核验的运行记录；CUDA RNG未记录，不能作同等断言。16k两臂是否有效只能在本轮B0、固定seed0与开发来源范围内解释。两fold训练集有重叠，当前区间不覆盖重新训练、多seed或独立外部测试的不确定性。切壁点距离也不证明实体闭合、连续边界无缝、颅骨内外板语义正确或临床可用。',
 '',
 '下一阶段应先据主终点、接口指标、分fold方向及最差source共同选择输入设置。若改善证据不稳定，保留8k作为计算成本较低的默认设置，并把16k作为已报告的表示对照；若主终点改善而接口没有改善，明确区分两条结论，不能据此宣称接口方法创新。随后再提出一项与B0匹配数据、输出点数、更新数及评价合同的Mamba对照，以分离表示收益和模型收益；本报告不授权或启动该训练，也不追加病例筛选、参数扫描或BNCal。','',
 '## 最差source与可追溯文件','']
for arm in ['8192','16384']:
 lines+=['',arm+'模型按E主误差排序的最差五个source（描述性定位）：','','| source | Fold | E P95（mm） | J P95（mm） |','|---|---|---:|---:|']
 for s in worst[arm]:lines.append('| '+s['source_id']+' | '+s['fold']+' | '+fmt(s['E_P95_mm'])+' | '+fmt(s['J_P95_mm'])+' |')
lines+=['','- `results/case_metrics.jsonl`：1050条逐病例完整A1／A2／B及控制指标。','- `results/case_metrics.csv`、`results/source_metrics.csv`：可直接审阅的病例／source表。','- `results/paired_comparison.json`：两fold及合并42-source的固定配对bootstrap结果。','- `descriptive_result_summary_v1.json`：固定控制、A2描述、方向计数与最差source。','- `download_verification.json`、`scoring_plan_v1.json`、`scoring_authorization_v1.json`、`process_result.json`：下载、范围与过程证据。','',
 '预测归档SHA256：`'+completion['archive_sha256']+'`。','',
 '本报告由已完成的固定结果生成，未修改原预测、几何参考、评分实现、阈值或权重。','']
report=A/'four_model_development_results_zh_v1.md'
with report.open('x',encoding='utf-8') as f:f.write('\n'.join(lines))
review=emit('result_integrity_review_v1.json',dict(status='OUTPUT_COUNTS_PAIRING_AND_SOURCE_ARITHMETIC_CHECKED',case_rows=1050,source_rows=210,unique_sources=42,invalid_rows=invalid,CSV_JSON_counts_match=True,source_five_case_means_match=True,paired_point_estimates_match=True,bootstrap_replicates=10000,seed=20261024,bootstrap_reexecuted=False,formal_gate_computed=False,server_calls=0,GPU_calls=0))
files=[R/x for x in ['case_metrics.jsonl','case_metrics.csv','source_metrics.json','source_metrics.csv','paired_comparison.json','completion.json']]+[desc,review,report,A/'download_verification.json',A/'scoring_plan_v1.json',A/'scoring_authorization_v1.json',A/'process_result.json']
emit('result_manifest_v1.json',dict(status='LOCAL_SCORING_COMPLETE_AND_DESCRIPTIVE_REPORT_WRITTEN',files=[bind(p) for p in files],server_calls=0,GPU_calls=0,training=0,BNCal=0))
print(json.dumps(dict(status='RESULT_REPORT_WRITTEN',report=str(report),invalid_rows=invalid,primary=primary,interface_P95=interface,interface_coverage_2mm=coverage,source_direction_counts=wins)))
