"""Metadata/hash P3 and pending local CPU scoring request; no real metric calculation."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
import ast,hashlib,importlib.metadata as md,importlib.util,json,sys,time
from pathlib import Path
B=Path(__file__).resolve().parent;N=B/'sampling_model_AB_foldC_seed0_20261103_v1/paired_development_eval_v1';S=N/'score_implementation_v1'
ROOT=next(p for p in N.parents if p.name=='mamba-ccf-c-1-high-resolution')
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bind(p):p=Path(p).absolute();return dict(path=str(p),bytes=p.stat().st_size,sha256=h(p))
def bound(r):
 p=Path(r['path']);assert p.is_file() and not any(x.is_symlink() for x in (p,*p.parents)) and p.stat().st_size==r['bytes'] and h(p)==r['sha256'];return p
def dump(name,value):
 p=S/name
 with p.open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=True,indent=2,allow_nan=False)
 return p
def textfile(name,text):
 p=S/name
 with p.open('x',encoding='utf-8',newline='\n') as f:f.write(text)
 return p
def main():
 start=time.monotonic();tests=json.loads((S/'CPU_contract_result_v1.json').read_bytes());assert tests['status']=='PASS' and tests['tests']==24 and tests['failures']==tests['errors']==0
 assert tests['scorer_sha256']==h(S/'bcsp_sampling_pair_score_v1.py') and tests['test_sha256']==h(S/'test_pair_score_contract_v1.py') and tests['metric_sha256']==h(N/'bcsp_eval_metrics_v1.py')
 assert tests['stdout_sha256']==h(S/'cpu_contract_v1/stdout.txt')
 original=B/'development_eval_v1/bcsp_eval_metrics_v1.py';assert h(original)==h(N/'bcsp_eval_metrics_v1.py')
 parentfile=N/'development_execution_request_v1.json';parent=json.loads(parentfile.read_bytes());assert h(parentfile)=='76673ba94626253161dc70f0a33006d21c8094bced8148496c68c6c3490f0f4c'
 bound(parent['scoring']['metric_implementation']);bound(parent['scoring']['reference_manifest']);bound(parent['protocol'])
 verificationfile=N/'local_download_verification_v1/verification_result_v1.json';verification=json.loads(verificationfile.read_bytes());assert verification['status']=='LOCAL_DOWNLOADED_PREDICTION_ARCHIVE_VERIFIED' and verification['local_backup_verified'] and verification['scoring_executed'] is False
 auditfile=N/'freeze_audit_v1/audit_report.json';audit=json.loads(auditfile.read_bytes());assert h(auditfile)==verification['formal_server_audit_sha256'] and audit['status']=='FORMAL_POST_PREDICTION_FREEZE_AUDIT_PASS'
 for r in verification['download_files']:bound(r)
 indexfile=N/'development_input_index_v1.json';index=json.loads(indexfile.read_bytes());refsfile=N/'reference_manifest_foldC_v1.json';refs=json.loads(refsfile.read_bytes())
 inputs={(r['case_id'],r['arm']):r for r in index['inputs']};cases=[];readbindings=[]
 for ref in refs['cases']:
  r={k:ref[k] for k in ['case_id','source_id','fold','normalization','target_array_sha256']};r['reference']={k:ref[k] for k in ['path','bytes','sha256']};bound(r['reference']);readbindings.append(r['reference'])
  r['point_files']={}
  for arm in ['V1','Morton_area_stratified8k']:
   path=N/'data'/arm/'points'/(ref['case_id']+'_8192.npz');record=bind(path);bound(record);i=inputs[(ref['case_id'],arm)]
   assert all(record[k]==i['input'][k] for k in ['bytes','sha256'])
   r['point_files'][arm]=record;readbindings.append(record)
  r['common_point_order_sha256']=inputs[(ref['case_id'],'V1')]['common_point_order_sha256'];cases.append(r)
 assert len(cases)==105 and len(readbindings)==315
 casefile=dump('score_case_index_v1.json',dict(schema='bcsp-sampling-pair-score-case-index-v1',cases=cases,parent_reference_manifest=bind(refsfile),original_reference_files_changed=False,real_arrays_decoded_during_preparation=False))
 scorer=S/'bcsp_sampling_pair_score_v1.py';spec=importlib.util.spec_from_file_location('paired_score_metadata_reader',scorer);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 assert len(mod.validate_index(index,refs,json.loads(casefile.read_bytes()))[2])==105
 assert 'torch' not in sys.modules
 for p in [scorer,S/'test_pair_score_contract_v1.py',N/'bcsp_eval_metrics_v1.py']:ast.parse(p.read_text(encoding='utf-8'))
 assert not any(isinstance(n,ast.Call) and isinstance(n.func,(ast.Name,ast.Attribute)) and (n.func.id if isinstance(n.func,ast.Name) else n.func.attr)=='paired_bootstrap' for n in ast.walk(ast.parse(scorer.read_text(encoding='utf-8'))))
 packages={x:md.version(x) for x in ['numpy','scipy','psutil','scikit-image']};assert packages==tests['packages']
 output=N/'paired_scores_v1';assert not output.exists() and not output.is_symlink()
 assert not (S/'authorized_execution_v1').exists()
 note=textfile('scoring_implementation_and_authorization_note_zh_v1.md','''# V1／Morton两臂CPU评分：限定适配与待授权范围 v1

## 本次交付

仅新增评分专用文件，不修改旧四模型入口或固定metric模块。24项人工CPU合同一次通过；测试只读取人工构造的完整105例／213成员归档、解析phantom和合成点集，未读取真实预测或真实reference来计算指标。测试包括一次真实函数调用链的合成单病例五臂评分：两模型预测与三个CPU控制。没有模型、Torch、GPU、服务器操作。

从旧四模型评分器收敛为Fold C两个8k采样臂，固定105病例／21来源；读取已经独立核验的下载归档，使用训练阶段相同固定点序的两臂开发NPZ作为GT／输入控制来源。两个checkpoint只保留来源哈希，不读取权重。原105个参考NPZ及metric源码逐字节保持不变，本次只有内容哈希检查，不生成新参考或真实指标。

## 固定评分合同

主指标是A1未知原始表面E_G→prediction的面积加权P95(mm)。关键次指标为切壁J_G P95、J_G Cover@2mm、E_G Cover@2mm和共同GT8192的CD-L1（双向平均距离再取均值，不平方）。D-only逆归一化回mm。J是GT共享切壁，不能等同临床植入物间隙、骨厚度或拓扑认证。

先计算每个病例指标，再平均同来源五种固定缺损，最后21来源等权。输出Morton−V1差值：距离负为改善、覆盖率正为改善，严格零差为tie。不改变阈值，不挑病例，不池化全部几何点重新计算主P95，不把五缺损当独立来源。完整保留21来源及105病例差值和回退排序，并列出五类缺损各21来源的描述性差值。

共210模型评分＋315固定CPU控制评分（每病例GT8192、V1输入原样、Morton输入原样），525病例评分行／105来源汇总行，其中模型来源行42。控制用于表征离散采样尺度，不作为临床或模型性能基线。

继承原A1/A2/B离散参考及反向距离诊断。移除旧16k流程中的bootstrap路径：本次不执行bootstrap、不计算p值或正式gate，仅作一折一种子探索性比较。缺失／重复／损坏／非有限预测拒绝整批；未定义区域显式保留，不丢弃来源对后报告好结果。

## 验证与执行限制

人工CPU合同24项包含完整索引／归档读取、来源隔离、共同GT／框架／置换一致性、异常文件与状态/RNG拒绝、P95面积权重、mm换算、CD定义、单病例五臂集成、来源等权和方向、完整105病例／五缺损汇总、非有限对保留、无bootstrap/RNG消费及单向授权。旧metric源码哈希不变。CPU测试不是对真实预测质量的评估。

P3仅做最终源文件／测试／数据／参考／下载文件哈希核验及实际元数据reader检查。真实NPZ数组在本次P3未解码或评分。原始NRRD／STL、confirmation、Fold D、SkullFix／MUG和模型权重不在读取范围。

下一步需要单独授权最终评分request完整SHA256，随后才创建授权回执并执行一次CPU评分。固定已存在Python环境，-I -B，CUDA不可见，线程2；wall7200秒、RSS8GiB、输出2GiB，源／备份文件只读，结果只写全新paired_scores_v1。未来调用应由本机有界子进程施加wall超时并显式传递PowerShell退出码；程序在每次评分前采样检查资源，不声称硬内存隔离。失败即停，不自动修复重跑或追加病例。

```mermaid
flowchart LR
    A[限定适配及人工CPU合同] --> B[P3与待授权评分request]
    B --> C[单独授权完整哈希]
    C --> D[唯一一次本机CPU评分]
    D --> E[只读冻结审计后解读结果]
```

当前生产授权／执行attempt及结果目录均未创建。人工测试目录中的authorization仅是明确标记的合成fixture，不是生产授权。本机备份目录不写入、解压或删除；也不因已核验下载而删除服务器产物。
''')
 implementation=dict(scorer=bind(scorer),metrics=bind(N/'bcsp_eval_metrics_v1.py'))
 evidence=dict(formal_prediction_audit=bind(auditfile),local_download_verification=bind(verificationfile),prediction_execution_scope=bind(parentfile),paired_evaluation_protocol=parent['protocol'])
 p3=dump('local_P3_v1.json',dict(status='LOCAL_P3_PASS_FOR_PENDING_PAIRED_CPU_SCORING',tests=bind(S/'CPU_contract_result_v1.json'),test_count=24,test_stdout=bind(S/'cpu_contract_v1/stdout.txt'),implementation=implementation,test_source=bind(S/'test_pair_score_contract_v1.py'),parent_scorer=bind(B/'development_eval_v1/bcsp_development_score_v1.py'),metric_source_unchanged=bind(original),score_case_index=bind(casefile),prediction_index=bind(indexfile),reference_manifest=bind(refsfile),evidence=evidence,download_files=verification['download_files'],verified_case_input_and_reference_bindings=315,implementation_note=bind(note),checks=dict(final_code_matches_passing_tests=True,original_metrics_byte_identical=True,existing105_references_hashed_not_rebuilt=True,paired210_inputs_hashed_not_resampled=True,actual_metadata_reader_pass=True,all105_sources_cases_fixed=True,production_auth_absent=True,new_output_absent=True,real_metric_calls_zero=True,bootstrap_calls_absent=True),limitations=['One synthetic case executes five score_cloud calls; full105 real-case scoring not executed','CPU resource monitoring is sampled,not hard RSS isolation','Clinical fit and training-seed variability not established','Formal post-score audit remains separate'],server_calls=0,model_calls=0,real_prediction_scoring_calls=0,real_reference_arrays_decoded=0,seconds=time.monotonic()-start))
 request=dump('local_scoring_execution_request_v1.json',dict(schema='bcsp-sampling-pair-local-scoring-request-v1',status='AWAITING_EXPLICIT_USER_AUTHORIZATION',execution_authorized=False,date_Asia_Shanghai='2026-11-03',purpose='One bounded local CPU descriptive paired evaluation of frozen Fold C V1 vs Morton predictions; no training or GPU',authorized_attempts_after_separate_full_hash_grant=1,
  implementation=implementation,environment=dict(python=bind(Path(sys.executable).resolve()),python_version=sys.version,flags=['-I','-B'],packages=packages,CUDA_VISIBLE_DEVICES='',threads=2),downloaded_prediction_archive=verification['download_files'][0],download_sidecars=verification['download_files'][1:],reference_manifest=bind(refsfile),prediction_index=bind(indexfile),score_case_index=bind(casefile),prediction_entry_request_sha256=parent['entry_request']['sha256'],evidence=evidence,P3=bind(p3),implementation_note=bind(note),output=str(output.absolute()),counts=dict(unique_cases=105,unique_sources=21,defects_per_source=5,model_predictions=210,CPU_controls=315,total_case_score_rows=525,source_score_rows=105,model_source_pairs=21,input_points=8192,output_points=8192),
  scientific_contract=parent['scoring'],statistics=dict(descriptive_only=True,delta='Morton minus V1',aggregation='mean of five defect-specific metrics,then21 sources equal',distance_improves='negative',coverage_improves='positive',bootstrap=0,p_values=False,formal_gate=False,drop_cases=False),limits=dict(wall_seconds=7200,RSS_bytes=8589934592,output_bytes=2147483648,threads=2),
  future_authorization=dict(path=str((S/'authorized_execution_v1/score_authorization_v1.json').absolute()),schema='bcsp-sampling-pair-score-authorization-v1',required_fields=['schema','request_sha256','explicit_user_authorization','user_authorization_text'],reverse_bindings_forbidden=True,materialized=False),
  invocation_contract=dict(executable=str(Path(sys.executable).resolve()),flags=['-I','-B'],entry=str(scorer.absolute()),CLI_fields=['--request','--request-sha256','--authorization','--authorization-sha256'],external_wall_timeout_seconds=7205,PowerShell_exit_LASTEXITCODE=True,request_bytes_immutable=True,production_authorization_required=True),
  expected_result_files=['single_attempt_claim.json','execution_environment.json','case_metrics.jsonl','source_metrics.json','paired_comparison.json','defect_comparison.json','regression_rankings.json','case_metrics.csv','source_metrics.csv','paired_case_deltas.csv','completion.json'],failed_attempt_policy='FAILED_STOP_NO_RETRY; retain partial evidence; do not overwrite,repair/retry or resume',completion_boundary='Stop after single CPU scoring; separate formal read-only freeze audit before scientific interpretation',forbidden=['no server/WSL/network access','no GPU/Torch/model/checkpoint load or forward','no training/BNCal','no changing references/GT/normalization/sampling/thresholds','no bootstrap/p-values/formal gate','no extra folds/seeds/cases or confirmation/SkullFix/MUG/raw NRRD/STL reads','no writes/extraction/deletion in backup directory','no production authorization materialization or scoring in preparation turn'],execution_materialized_now=False,real_scoring_executed_now=False))
 textfile('local_scoring_execution_request_v1.json.sha256',h(request)+'  '+request.name+'\n')
 # Read request through the real scorer's metadata reader only; no authorization or main call.
 reread=json.loads(request.read_bytes());assert reread['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION' and not reread['execution_authorized']
 for r in reread['implementation'].values():bound(r)
 bound(reread['P3']);bound(reread['score_case_index']);assert not output.exists() and not (S/'authorized_execution_v1').exists()
 textfile('README_pending_score_request_zh_v1.md','# 待授权两臂CPU评分request\n\n限定实现、24项人工CPU合同与P3已完成。未计算真实预测指标，不需上传服务器。\n\nrequest：`'+str(request.absolute())+'`\n\n完整SHA256：`'+h(request)+'`\n\n状态：`AWAITING_EXPLICIT_USER_AUTHORIZATION`。只有单独授权该完整哈希后，才能材料化评分授权回执并执行唯一一次本机CPU评分。结果拟写入全新 `'+str(output.absolute())+'`。\n\n保持主E P95、关键J P95／J与E Cover@2mm及共同GT CD-L1；105病例、21来源，来源等权，描述性Morton−V1差值，不bootstrap或正式gate。未来CPU控制也按既定方案计算，210模型评分＋315控制评分共525行。\n\n评分完成后仍须另行只读冻结审计，再解读科研结果。\n')
 dump('preparation_completion_v1.json',dict(status='SCORING_IMPLEMENTATION_AND_P3_PASS_REQUEST_AWAITING_AUTHORIZATION',request=bind(request),P3=bind(p3),tests=24,real_scores=0,real_reference_arrays_decoded=0,server_calls=0,model_calls=0,production_authorization_materialized=False))
 files=[dict(name=str(p.relative_to(S)).replace('\\','/'),bytes=p.stat().st_size,sha256=h(p)) for p in sorted(S.rglob('*')) if p.is_file()]
 dump('implementation_artifact_manifest_v1.json',dict(status='PREPARED_NOT_EXECUTED',files=files))
 print(json.dumps(dict(status='PENDING_SCORING_REQUEST_FROZEN',request_sha256=h(request),tests=24,real_scores=0,source_pairs=21,CPU_score_rows=525,server_calls=0)))
if __name__=='__main__':main()
