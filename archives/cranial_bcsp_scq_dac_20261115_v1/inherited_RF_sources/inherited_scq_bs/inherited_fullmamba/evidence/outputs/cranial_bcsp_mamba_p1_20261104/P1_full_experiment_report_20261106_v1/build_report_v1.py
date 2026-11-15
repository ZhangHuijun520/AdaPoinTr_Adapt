import pathlib,json,hashlib,csv,statistics,re
O=pathlib.Path(__file__).resolve().parent; B=O.parent; CLOSE=B/'P1_closeout_20261106_v1'
def load(p):return json.loads(pathlib.Path(p).read_text(encoding='utf8'))
def rec(p):
 p=pathlib.Path(p).resolve();h=hashlib.sha256()
 with p.open('rb') as f:
  for x in iter(lambda:f.read(1048576),b''):h.update(x)
 return dict(path=str(p),bytes=p.stat().st_size,sha256=h.hexdigest())
def emit(name,v):
 with (O/name).open('x',encoding='utf8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def link(p,label):return '['+label+']('+pathlib.Path(p).resolve().as_posix()+')'
assert load(CLOSE/'P1_phase_closeout_receipt_v1.json')['status']=='P1_FORMALLY_CLOSED'
e=load(CLOSE/'P1_evidence_index_v1.json')
for r in e['evidence']+e['score_output_files_rehashed']:assert rec(r['path'])==r
runs=load(CLOSE/'P1_final_run_matrix_v1.json'); folds=load(CLOSE/'P1_final_fold_results_v1.json')
review=B/'CD_frozen_review_20261106_v1'; sel=load(review/'frozen_diagnostic_selection_v1.json'); geo=load(review/'selected_case_geometry_v1.json'); assert geo['selected_cases']==14
quantp=B/'gradient_quantification_v1/post_diagnostic_freeze_audit_v2/audit_report_v1.json';quant=load(quantp);assert quant['status']=='FORMAL_READONLY_POST_DIAGNOSTIC_FREEZE_AUDIT_PASS'
roots={'C':B/'paired_development_evaluator_v2','D':B/'FoldD_paired_development_entry_v1'}; allcases=[]; sources=[]
for f,R in roots.items():
 allcases += [json.loads(x) for x in (R/'paired_scores_v1/case_metrics.jsonl').read_text(encoding='utf8').splitlines()]
 sources += load(R/'paired_scores_v1/source_metrics.json')
assert len(allcases)==840 and len(sources)==168
for name,rows,base in [('P1_all840_case_scores_v1.csv',allcases,['fold','source_id','case_id','arm','status']),('P1_all168_source_scores_v1.csv',sources,['fold','source_id','arm','case_count'])]:
 with (O/name).open('x',encoding='utf8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=base+list(rows[0]['metrics']));w.writeheader()
  for r in rows:w.writerow({**{k:r[k] for k in base},**r['metrics']})
subs={};subs['RUNMATRIX']='\n'.join(f"| {r['run']} | {r['fold']} | {r['variant']} | 0 | 3900 | 31200 | 通过 |" for r in runs)
labels=[('E_P95_mm','E P95（mm）',1),('J_P95_mm','J P95（mm）',1),('E_coverage_2.0mm','E Cover@2mm（%）',100),('J_coverage_2.0mm','J Cover@2mm（%）',100),('CD_L1_mm','CD-L1（mm）',1),('reverse_A2_P95_mm','预测→A2 P95（mm）',1),('reverse_A2_outlier_20.0mm','预测→A2 >20mm（%）',100),('centroid_offset_mm','质心偏差（mm）',1),('radius_gyration_ratio','半径惯性比',1)]
for f,v in folds.items():
 rows=[]
 for key,label,k in labels:
  m=v['comparison']['metrics'][key];win=str(m['improved_sources'])+'/'+str(m['worse_sources']) if 'improved_sources' in m else '无优劣方向'
  rows.append(f"| {label} | {m['mean_T0']*k:.4f} | {m['mean_M0']*k:.4f} | {m['mean_delta_M0_minus_T0']*k:+.4f} | {win} |")
 subs['METRICS_'+f]='\n'.join(rows)
strata=[];risk=[];controls=[];resources=[];checkpoints=[];qrows=[];cases=[]
for typ in ['bilateral','frontoorbital','parietotemporal','random_1','random_2']:
 for f in ['C','D']:
  m=folds[f]['defects'][typ]['mean_deltas'];strata.append(f"| {typ} | {f} | {m['E_P95_mm']:+.4f} | {m['J_P95_mm']:+.4f} | {m['J_coverage_2.0mm']*100:+.3f} | {m['CD_L1_mm']:+.4f} | {m['reverse_A2_outlier_20.0mm']*100:+.3f} |")
for f,v in folds.items():
 for name,key in [('质心>20mm','placement_tail'),('半径比<0.9','compact_distribution'),('严重几何','severe_geometry')]:
  r=v['risks'][key];risk.append(f"| {f} | {name} | {r['T0_count']} | {r['M0_count']} | {r['new']} | {r['rescued']} |")
 for arm in ['Nop_D','GT_8192']:
  p=[r for r in sources if r['fold']==f and r['arm']==arm];m={k:statistics.mean(r['metrics'][k] for r in p) for k in ['E_P95_mm','J_P95_mm','J_coverage_2.0mm','CD_L1_mm']};controls.append(f"| {f} | {arm} | {m['E_P95_mm']:.4f} | {m['J_P95_mm']:.4f} | {m['J_coverage_2.0mm']*100:.3f} | {m['CD_L1_mm']:.4f} |")
for r in runs:
 a=load(r['audit']['path']);v=a['resources'];resources.append(f"| {r['run']} | {v['elapsed_seconds']:.2f} | {v['max_RSS']/1024**3:.3f} | {v['peak_allocated']/1024**3:.3f} | {v['peak_reserved']/1024**3:.3f} | {v['max_device_MiB']} |")
 checkpoints.append(f"| {r['run']} | {r['checkpoint']['bytes']} | `{r['checkpoint']['sha256']}` |")
for arm in ['T0','M0']:
 v=quant['models'][arm]['global_statistics'];qrows.append(f"| {arm} | {v['byte_different_tensors']} | {v['max_abs_diff']:.8g} | {v['relative_l2']:.8g} | {v['cosine_display']:.15f} |")
lookup={(r['fold'],r['case_id'],r['arm']):r for r in geo['records']}
for x in sel['selected_cases']:
 f,cid=x['fold'],x['case_id'];a,b=[lookup[(f,cid,arm)] for arm in ['T0','M0']];cases.append(f"| {f}/{cid.removeprefix('train__')} | {a['E_P95_mm']:.2f}→{b['E_P95_mm']:.2f} | {a['E_coverage_2mm']*100:.1f}→{b['E_coverage_2mm']*100:.1f} | {a['outlier20_count']}→{b['outlier20_count']} | {a['centroid_offset_mm']:.2f}→{b['centroid_offset_mm']:.2f} |")
for k,v in [('STRATATABLE',strata),('RISKTABLE',risk),('CONTROLTABLE',controls),('RESOURCETABLE',resources),('CHECKPOINTTABLE',checkpoints),('QUANTTABLE',qrows),('CASEGEOTABLE',cases)]:subs[k]='\n'.join(v)
links=[]
for f,R in roots.items():
 for label,p in [('预测冻结审计',R/'post_prediction_freeze_audit_v1/audit_report_v1.json'),('评分冻结审计',R/'post_scoring_freeze_audit_v1/audit_report_v1.json')]:links.append('- '+link(p,f+' '+label))
links += ['- '+link(CLOSE/'Cranial_BCSP_Mamba_P1_正式收束报告_zh_v1.md','P1正式收束报告'),'- '+link(review/'C_D综合复盘与退化几何诊断报告_zh_v1.md','14病例完整复盘与图索引'),'- '+link(review/'figures/D__train__079__frontoorbital.png','D/079整块错位与收缩图'),'- '+link(review/'figures/D__train__008__random_2.png','D/008无极端离群的漏覆盖图'),'- '+link(B/'coarse_anchor_minimal_hypothesis_20261106_v1/输入坐标系下coarse位置与范围约束_最小假设草案_zh_v1.md','H1下一阶段草案（未实施）')];subs['LINKS']='\n'.join(links)
text=(O/'report_template_v1.md').read_text(encoding='utf8')
for k,v in subs.items():assert '@@'+k+'@@' in text;text=text.replace('@@'+k+'@@',v)
assert not re.search(r'@@[A-Z_]+@@',text) and '\ufffd' not in text
report=O/'Cranial_BCSP_Mamba_P1_完整实验报告_zh_v1.md'
with report.open('x',encoding='utf8',newline='\n') as f:f.write(text)
claims=[dict(claim='实验完成且正式收束',strength='执行事实',evidence='四训练、两预测、两评分正式冻结'),dict(claim='M0尚无稳定整体优势',strength='单seed分折描述性结论',evidence='C E -1.5144mm / D E +0.3622mm；CD与离群方向不同'),dict(claim='coarse位置和范围是候选瓶颈',strength='机制线索，非因果',evidence='14固定病例和同forward出口汇总'),dict(claim='H1不属于P1结果',strength='阶段范围事实',evidence='正式收束与H1未实施草案')]
emit('report_claim_evidence_map_v1.json',claims)
extra=[quantp,review/'selected_case_geometry_v1.json',review/'selected_coarse_dense_evidence_v1.json',B/'minimal_implementation_v1/bcsp_mamba_encoder_v1.py',B/'minimal_implementation_v1/bcsp_p1_model_factory_v1.py',B/'minimal_implementation_v1/bcsp_p1_training_runtime_v1.py',B/'training_entry_v1/transport_payload/numeric_protocol_zh_v1.md',CLOSE/'P1_phase_closeout_receipt_v1.json']
emit('report_evidence_catalog_v1.json',dict(status='FROZEN_REPORT_SOURCES_VERIFIED',sources=e['evidence']+[rec(p) for p in extra],score_files=e['score_output_files_rehashed'],new_training=False,new_scoring=False,real_prediction_arrays_decoded=False,server_operations=0))
emit('report_manifest_v1.json',dict(status='COMPLETE_EXPERIMENT_REPORT_FROM_FROZEN_EVIDENCE',report=rec(report),files=[rec(p) for p in sorted(O.iterdir()) if p.is_file()],P1_status='P1_FORMALLY_CLOSED',H1_status='DRAFT_NOT_IMPLEMENTED',new_experiments=0))
print(json.dumps(dict(report=rec(report),characters=len(text),case_rows=len(allcases),source_rows=len(sources),new_experiments=0),ensure_ascii=True,indent=2))
