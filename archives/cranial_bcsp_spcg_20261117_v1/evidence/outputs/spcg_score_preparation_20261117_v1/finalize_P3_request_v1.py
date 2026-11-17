"""Read-only implementation review, then freeze a pending local request; no scoring."""
from pathlib import Path
import ast,json,hashlib,datetime
R=Path(__file__).resolve().parents[2];O=R/'outputs/spcg_score_implementation_20261117_v1';P=Path(__file__).parent
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def rec(p):
 p=Path(p).resolve();return dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))
def emit(p,v):
 with Path(p).open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False)
def check(r):
 p=Path(r['path']);assert p.is_file() and not any(q.is_symlink() for q in [p,*p.parents]);assert p.stat().st_size==r['bytes'] and sha(p)==r['sha256'];return p
scorer=O/'bcsp_spcg_three_arm_score_v1.py';test=O/'test_SPCG_three_arm_score_cpu_v1.py';result=O/'CPU_contract_v1/result_v1.json'
rr=json.loads(result.read_bytes());static=json.loads((O/'static_review_v1.json').read_bytes());scope=json.loads((O/'SPCG_scoring_protocol_v1.json').read_bytes());case=json.loads((O/'SPCG_score_case_index_v1.json').read_bytes())
assert rr['status']=='SPCG_THREE_ARM_SCORING_CPU_CONTRACT_PASS' and rr['checks_passed']==len(rr['checks'])==61
for r in rr['source_bindings']+static['files']:check(r)
for a in case['archive_inputs'].values():
 check(a['archive'])
 for r in a['sidecars']+[a['prediction_index'],a['prediction_protocol']]:check(r)
for c in case['cases']:
 check(c['reference']);check(c['point_file'])
check(scope['metric']);check(scope['frozen_baseline_scores']);check(scope['environment']['python']);check(scope['inherited_protocol'])
def functions(p):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(Path(p).read_text(encoding='utf-8')).body if isinstance(n,ast.FunctionDef)}
orig=functions(R/'outputs/scq_rf_score_impl_20261115_v1/bcsp_scq_rf_three_arm_score_v1.py');new=functions(scorer)
keep=['select_metrics','position_shape','risk_labels','stage_geometry','score_case','aggregate_source','describe_pairs','case_differences','defect_summary','csv_rows','risk_transitions']
assert all(orig[k]==new[k] for k in keep)
assert not (O/'unified_scores_v1').exists() and not (O/'authorized_execution_v1').exists()
art=O/'CPU_contract_v1/full1050';done=json.loads((art/'completion.json').read_bytes());assert done['score_rows']==1050 and done['source_rows']==210
inventory=[rec(p) for p in sorted((O/'CPU_contract_v1').rglob('*')) if p.is_file()]
emit(O/'CPU_contract_artifact_inventory_v1.json',dict(files=inventory,file_count=len(inventory),content_bytes=sum(r['bytes'] for r in inventory),note='Artificial fixtures only; atime is not a content fingerprint.'))
checks=dict(single_artificial_batch_61_checks=True,source_and_test_hashes_match_test=True,static_sources_unchanged=True,frozen_metric_unchanged=True,eleven_metric_risk_aggregation_functions_AST_unchanged=True,local_archive_and_sidecars_match=True,all210_reference_and210_point_hashes_match=True,baseline_control_file_match=True,source_pairing_42_sources_five_defects=True,seed_and_CI_regression_pass=True,one_matrix_per_fold_all_metrics_all_pairs=True,no_real_scoring_or_bootstrap=True,CPU_only_no_torch_import=True,no_output_or_authorization_materialized=True,device_qualifications_preserved=True)
gaps=['No real score or bootstrap has run; CPU phantom tests do not establish scientific improvement.','10 analytic phantom metric rows;1050 artificial orchestration rows reuse templates, not1050 independent metric calculations.','Training seed0 only; bootstrap covers paired source sampling, not training randomness or development-set selection.','G0_D training on previous GPU; G1_D/G2_D same new GPU. Common inference device does not remove training-device confounding.','Native archive contains coarse256/dense8192, not Memory or internal stage arrays. Memory NOT_COLLECTED; no automatic extra forward.','Some test display labels are inherited (e.g.636/nine keys/raw queries); actual assertions require635 members/two keys/no Qraw. Labels do not change checks.','Formal post-score freeze audit remains separately authorized after the true CPU run.']
p3=dict(status='LOCAL_SPCG_SCORING_P3_PASS',date_Asia_Shanghai='2026-11-17',scorer=rec(scorer),test=rec(test),CPU_result=rec(result),CPU_artifact_inventory=rec(O/'CPU_contract_artifact_inventory_v1.json'),checks=checks,unchanged_AST_functions=keep,bootstrap_contract=scope['bootstrap'],limits_and_open_qualifications=gaps,real_score_rows=0,real_bootstrap_replicates=0,server_operations=0,GPU_calls=0)
emit(O/'implementation_P3_v1.json',p3)
old=json.loads((R/'outputs/scq_rf_score_impl_20261115_v1/local_scoring_execution_request_v1.json').read_bytes())
q=dict(schema='bcsp-spcg-local-scoring-request-v1',status='AWAITING_EXPLICIT_USER_AUTHORIZATION',execution_authorized=False,date_Asia_Shanghai='2026-11-17',purpose='SPCG G0/G1/G2 twofold fixed Native scoring and preregistered paired-source bootstrap; no new inference',authorized_attempts_after_separate_full_hash_grant=1,implementation=dict(scorer=rec(scorer),metrics=scope['metric']),environment=scope['environment'],archive_inputs=case['archive_inputs'],reference_manifest=old['reference_manifest'],prediction_index=case['archive_inputs']['SPCG']['prediction_index'],score_case_index=rec(O/'SPCG_score_case_index_v1.json'),evidence=dict(protocol=rec(O/'SPCG_scoring_protocol_v1.json'),inherited_protocol=scope['inherited_protocol'],local_archive_verification=rec(P/'local_archive_verification_v1.json'),CPU_contract=rec(result),static_review=rec(O/'static_review_v1.json')),P3=rec(O/'implementation_P3_v1.json'),output=str(O/'unified_scores_v1'),counts=scope['counts'],scientific_contract=dict(arms=['G0','G1','G2'],pairs=[['G1','G2'],['G0','G2'],['G0','G1']],controls=['Nop_D','GT_8192'],delta='candidate minus reference; negative errors and positive coverage favor candidate',primary=scope['primary_metric'],geometry=scope['geometry_labels'],alignment='Native D-only inverse normalization to world mm; no GT alignment/ICP/filter',coarse='Only actual coarse256/dense8192;exact two keys;no Memory/stage arrays',baseline_archive_handling='630 models and420 recomputed shared controls;exact equality with frozen controls required',archive_member_byte_limit=60933613,comparison_qualification=scope['comparison_qualification']),statistics=scope['bootstrap'],limits=scope['limits'],future_authorization=dict(path=str(O/'authorized_execution_v1/score_authorization_v1.json'),schema='bcsp-spcg-score-authorization-v1'),invocation_contract=old['invocation_contract'],expected_result_files=old['expected_result_files']+['bootstrap_indices_C.npy','bootstrap_index_record_C.json','bootstrap_indices_D.npy','bootstrap_index_record_D.json'],failed_attempt_policy=old['failed_attempt_policy'],completion_boundary='Separate formal read-only post-score freeze audit before effect interpretation',forbidden=scope['prohibited'],execution_materialized_now=False,real_scoring_executed_now=False,frozen_baseline_scores=scope['frozen_baseline_scores'],comparison_qualification=scope['comparison_qualification'],limitations=gaps,p_values=False,formal_gate=False)
q['invocation_contract']['readiness']='Rehash SPCG scorer/metric/evidence/archive/three sidecars/frozen controls/CPU Python/210 references/210points; require fresh output and authorization paths'
emit(O/'SPCG_local_scoring_execution_request_v1.json',q)
request=rec(O/'SPCG_local_scoring_execution_request_v1.json')
emit(O/'pending_request_binding_v1.json',dict(status=q['status'],request=request,materialized_authorization=False,started=False))
report='''# SPCG 三臂两折统一 CPU 评分：实现、人工验证与 P3

日期：2026-11-17。状态：实现与本机 P3 通过；正式评分尚未授权执行。

## 已完成范围

新增隔离评分入口，适配 G0/G1/G2、C/D 两折，共630份冻结预测。共享 Nop_D 与 GT_8192 每病例各计算一次，共420行；总1050行病例评分、210个来源×角色汇总。42个独立来源，各5种缺损；1050行不是1050个独立患者。

沿用冻结指标源码、参考库、GT8192、D-only 世界坐标反归一化和风险阈值。11个指标、风险和来源聚合函数与既有实现 AST 完全相同。共享控制须与冻结控制逐行完全相等，否则停止。

## 预注册来源 bootstrap

每折21来源按 canonical_source_id 字典序排序，先对每来源5种缺损等权平均，再计算候选减参考。NumPy1.26.4、Generator(PCG64)，C种子2026111601、D种子2026111602；每折固定2000×21整数抽样矩阵。两折分别计算，不合并构造区间。每折全部指标与三组比较复用同一矩阵，保存 NPY、来源顺序、种子和 SHA256。95%百分位区间用 quantile(method='linear')；未定义来源保留并标明，不能删掉后继续算区间。无p值或正式gate。

比较方向固定 G2−G1、G2−G0、G1−G0。C三臂同设备；D的G1/G2同设备，G0_D是跨训练设备参考。区间不消除该混杂，也不估计训练种子方差。

## 唯一一批人工 CPU 验证

61项检查全部通过，进程退出码0。使用人工解析体素 phantom 和8192点张量，10行调用真实冻结指标；1050行流程验证复用人工评分模板，验证计数、控制一致性、来源配对、退化标签、首次失败停止等。另验证固定PCG64矩阵、线性百分位区间、常数差值、未定义值、非法索引，以及所有指标/比较复用同一抽样矩阵。未读取真实预测数组或真实参考点阵进行评分；只读取冻结元数据和做文件哈希核验。

部分检查名称沿用旧测试的文字（636成员、nine-key、raw-query等），但断言已适配635成员、两数组和不保存Qraw；以实际断言与本说明为准。旧科研源码与既有RF评分入口未修改。

## P3 与边界

已核验评分源码、测试源码与静态/运行绑定一致；归档及三个校验文件、210份参考文件与210份点集、冻结控制、Python及预注册协议哈希一致。人工产物完整清单见 CPU_contract_artifact_inventory_v1.json。

本机运行预算：18000秒、8GiB RSS、2GiB输出、2线程；前台托管保留执行会话，失败停止、不自动重试或resume。正式输出目录与授权目录均未创建。尚不能判断任何模型收益。

实际Native范围只保存coarse/dense，原计划Memory观察为 NOT_COLLECTED；不补造证据、不自动追加forward。真实CPU评分成功后，仍需另行正式只读冻结审计才能解读。

## 待授权 request

文件：SPCG_local_scoring_execution_request_v1.json

完整SHA256：`REQUEST_SHA`

状态：`AWAITING_EXPLICIT_USER_AUTHORIZATION`。本次没有材料化授权回执、启动评分或真实bootstrap，没有服务器操作。
'''.replace('REQUEST_SHA',request['sha256'])
with (O/'评分实现_CPU验证_P3与待授权说明_zh_v1.md').open('x',encoding='utf-8') as f:f.write(report)
emit(O/'final_delivery_manifest_v1.json',dict(files=[rec(p) for p in sorted(O.iterdir()) if p.is_file()],request=request,status='AWAITING_EXPLICIT_USER_AUTHORIZATION'))
print(json.dumps(dict(status='P3_PASS_REQUEST_PENDING',CPU_checks=61,request=request,real_score_rows=0,server_operations=0),ensure_ascii=False))
