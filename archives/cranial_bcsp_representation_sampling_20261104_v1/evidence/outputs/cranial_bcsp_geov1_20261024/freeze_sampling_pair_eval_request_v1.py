"""Freeze one pending 210-forward prediction request. No WSL/server/model calls."""
import ast,hashlib,importlib.util,io,json,tarfile
from pathlib import Path
B=Path(__file__).resolve().parent;O=B/'sampling_model_AB_foldC_seed0_20261103_v1';N=O/'paired_development_eval_v1';OLD=B/'development_eval_v1'
PROJECT='/home/jovyan/adapointr_work/PoinTr';CODE=PROJECT+'/third_party/bcsp_sampling_ab_foldc_seed0_v1'
DATA=PROJECT+'/data/bcsp_sampling_ab_foldc_seed0_dev_v1';OUT=PROJECT+'/logs/cranial_bcsp_sampling_ab_v1/bcsp_sampling_pair_foldC_seed0_dev_v1';CONTROL=CODE+'/control_eval_sampling_pair_v1'
def h(raw):return hashlib.sha256(raw).hexdigest()
def bind(p):p=Path(p);return dict(path=str(p.absolute()),bytes=p.stat().st_size,sha256=h(p.read_bytes()))
def dump(n,v):
 with (N/n).open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=True,indent=2,allow_nan=False)
 return N/n
def write(n,b):
 with (N/n).open('xb') as f:f.write(b)
 return N/n
def rem(p,path):return dict(bind(p),path=path)
def main():
 test=json.loads((N/'CPU_contract_result_v1.json').read_bytes());assert test['status']=='PASS' and test['tests']==20 and test['failures']==test['errors']==0 and test['source_sha256']==bind(N/'bcsp_sampling_pair_predict_v1.py')['sha256']
 deriv=json.loads((N/'implementation_derivation_v1.json').read_bytes());assert deriv['candidate']==bind(N/'bcsp_sampling_pair_predict_v1.py')
 index=json.loads((N/'development_input_index_v1.json').read_bytes());receipt=json.loads((N/'paired_development_data_receipt_v1.json').read_bytes());assert receipt['cases']==105 and receipt['model_case_pairs']==210
 proto=json.loads((O/'comparison_protocol_v1.json').read_bytes());foldfile=B/'consolidated_binding_v1/fold_binding.json'
 parent=json.loads((O/'Morton_training_request_v1/training_entry_request_v1.json').read_bytes())
 assets=json.loads((O/'server_assets_observation_v1.json').read_bytes())
 controller=(OLD/'development_controller_template_v1.py').read_text(encoding='utf-8')
 controller=controller.replace("len(files)==len(mapping)==2", "len(files)==len(mapping)==213 and len({r['member'] for r in mapping})==213 and len({r['target'] for r in mapping})==213")
 anchor="  exact(scope['upload']);mapping=scope['install_mapping'];content=archive_members(Path(scope['upload']['path']).read_bytes(),mapping)"
 assert controller.count(anchor)==1
 controller=controller.replace(anchor,anchor+"\n  for r in scope['upload_sidecars']:exact(r)\n  directories=scope['new_data_directories'];need(directories==FROZEN_DATA_DIRECTORIES,'exact new directories')\n  for d in directories:need(not os.path.lexists(str(safe(d))),'data directory exists: '+d)\n  need(safe(directories[0]).parent.is_dir(),'new data parent missing')")
 dirs=[DATA,DATA+'/V1',DATA+'/V1/points',DATA+'/Morton_area_stratified8k',DATA+'/Morton_area_stratified8k/points']
 controller=controller.replace("p.parent.is_dir(),'target occupied/parent missing: '+target)","(p.parent.is_dir() or str(p.parent) in directories),'target occupied/parent missing: '+target)")
 controller=controller.replace("  phase='exclusive_install'\n", "  phase='exclusive_install'\n  for d in directories:safe(d).mkdir(mode=0o700)\n")
 controller=controller.replace("from pathlib import Path\n","from pathlib import Path\nFROZEN_DATA_DIRECTORIES="+repr(dirs)+'\n',1)
 ast.parse(controller);controllerpath=write('paired_controller_template_v1.py',controller.encode())
 env=dict(json.loads((O/'Morton_training_request_v1/candidate_training_execution_request_v1.json').read_bytes())['launcher_contract']['environment'])
 env['TMPDIR']='<owned_output>/tmp';env['MPLCONFIGDIR']='<owned_output>/mplconfig'
 limits=dict(wall_seconds=7200,RSS_bytes=8589934592,torch_peak_bytes=21474836480,device_MiB=22528,output_bytes=1073741824,minimum_free_disk_bytes=4294967296)
 entry=rem(N/'bcsp_sampling_pair_predict_v1.py',CODE+'/bcsp_sampling_pair_predict_v1.py')
 ix=rem(N/'development_input_index_v1.json',CODE+'/evidence/development_pair_input_index_v1.json')
 dr=rem(N/'paired_development_data_receipt_v1.json',CODE+'/evidence/paired_development_data_receipt_v1.json')
 q=dict(schema='bcsp-sampling-pair-development-prediction-v1',status='AWAITING_EXPLICIT_USER_AUTHORIZATION',run_id='bcsp_sampling_pair_foldC_seed0_dev_v1',identity=parent['identity'],model_root=parent['model_root'],entry=entry,input_index=ix,paired_data_receipt=dr,fold_binding=parent['QC']['fold_binding'],static_config=parent['static_config'],preflight_scope=parent['preflight_scope'],helper=parent['implementation']['preflight_helper'],control=CONTROL,output=OUT,launch_attempt=CONTROL+'/launch_attempt.json',environment=env,limits=limits,
  science=dict(models=2,arms=['V1','Morton_area_stratified8k'],fold='C',training_seed=0,sampling_seed=0,cases_per_arm=105,sources=21,defects_per_source=5,total_forwards=210,n_input=8192,n_output=8192,checkpoint_stage='BCSP_SAMPLING_AB_V1',checkpoint_epoch=99,checkpoint_updates=3900,BNCal=False,training_updates=0,loss=False,backward=False,mode='native eval/inference_mode',precision='FP32',TF32=False,AMP=False,deterministic=True,warmup=0,voting=0,TTA=0,parameter_and_BN_state_invariance=True,CPU_CUDA_Python_numpy_RNG_invariance=True,loss_backend_during_training='same torch.cdist branch; loss not called in evaluation',PID_policy='DIAGNOSTIC_ONLY_NO_OWNERSHIP_GUARANTEE'))
 qp=dump('development_entry_request_v1.json',q)
 mapping=[]
 for name,target in [('bcsp_sampling_pair_predict_v1.py',entry['path']),('development_input_index_v1.json',ix['path']),('paired_development_data_receipt_v1.json',dr['path'])]:
  r=bind(N/name);mapping.append(dict(member=name,target=target,bytes=r['bytes'],sha256=r['sha256']))
 for row in index['inputs']:
  rel=row['input']['path'][len(DATA)+1:];p=N/'data'/rel;r=bind(p);assert (r['bytes'],r['sha256'])==(row['input']['bytes'],row['input']['sha256']);mapping.append(dict(member='data/'+rel,target=row['input']['path'],bytes=r['bytes'],sha256=r['sha256']))
 assert len(mapping)==len({r['target'] for r in mapping})==213
 archive=N/'bcsp_sampling_pair_foldc_development_v1.tar.gz'
 with archive.open('xb') as raw:
  with tarfile.open(fileobj=raw,mode='w:gz') as tf:
   for r in mapping:
    payload=(N/r['member']).read_bytes();assert h(payload)==r['sha256'];m=tarfile.TarInfo(r['member']);m.size=len(payload);m.mode=0o600;m.mtime=0;tf.addfile(m,io.BytesIO(payload))
 for suffix,text in [('sha256',bind(archive)['sha256']+'  '+archive.name+'\n'),('bytes',str(archive.stat().st_size)+'\n'),('contents.sha256',''.join(r['sha256']+'  '+r['member']+'\n' for r in mapping))]:write(archive.name+'.'+suffix,text.encode('ascii'))
 write(archive.name+'.contents.sha256.sha256',(bind(N/(archive.name+'.contents.sha256'))['sha256']+'  '+archive.name+'.contents.sha256\n').encode())
 # Full existing entry reader, no model imports, no production authorization.
 spec=importlib.util.spec_from_file_location('pair_metadata_only',N/'bcsp_sampling_pair_predict_v1.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 assert len(module.validate_index(index,json.loads(foldfile.read_bytes()))[1])==210
 refs=json.loads((N/'reference_manifest_foldC_v1.json').read_bytes());assert [x['case_id'] for x in refs['cases']]==proto['development_case_ids']
 for r in refs['cases']:assert bind(r['path'])['sha256']==r['sha256']
 cspec=importlib.util.spec_from_file_location('pair_controller_static',controllerpath);cm=importlib.util.module_from_spec(cspec);cspec.loader.exec_module(cm)
 blob=archive.read_bytes();assert len(cm.archive_members(blob,mapping))==213
 # Failure guards use the same actual transport bytes, without writes/server calls.
 rejection_checks=0
 for bad in [mapping[:-1],[dict(r,target=mapping[0]['target']) if j==1 else r for j,r in enumerate(mapping)]]:
  try:cm.archive_members(blob,bad)
  except RuntimeError:rejection_checks+=1
 assert rejection_checks==2
 dump('controller_transport_readback_v1.json',dict(status='PASS',actual_archive_all_213_member_hashes_verified=True,in_memory_missing_member_and_duplicate_target_rejected=2,controller_run_called=False,WSL_calls=0,server_calls=0,model_calls=0,controller_sha256=bind(controllerpath)['sha256']))
 source_files=['bcsp_sampling_pair_predict_v1.py','paired_controller_template_v1.py','bcsp_eval_metrics_v1.py','test_pair_predict_contract_v1.py']
 for name in source_files:ast.parse((N/name).read_text(encoding='utf-8'))
 scoring=dict(status='NOT_EXECUTED_SEPARATE_LOCAL_CPU_SCORING_AFTER_DOWNLOAD',primary='A1 E_G surface area-weighted G-to-prediction P95 in mm; five defects averaged then21 sources equal',key_secondary=['A1 J_G P95 mm','A1 J_G Cover@2mm','A1 E_G Cover@2mm','same fixed GT8192 symmetric mean CD-L1 mm'],diagnostics=['A1 E/J mean and max distance, Cover@0.5/1/2mm','reverse discrete-reference P95 and outlier fraction','A2/B discretization sensitivity'],delta='Morton minus V1; distance negative is improvement, coverage positive is improvement',aggregation='per-case then five fixed defects/source then source equal; report per-case/source deltas, win/tie/loss and worst regressions without posthoc exclusions',statistics='descriptive single-fold single-training-seed pilot; no bootstrap, p-value, formal gate or clinical-threshold claim',missing_policy='retain all105 fixed cases; malformed/incomplete prediction batch fails rather than silently dropping cases; undefined regions explicit, no success claim',reference_manifest=bind(N/'reference_manifest_foldC_v1.json'),metric_implementation=bind(N/'bcsp_eval_metrics_v1.py'),controls='GT8192 and each arm input-as-prediction, CPU only; not clinical baselines',interpretation='J is ground-truth shared cut-wall geometry; J proximity/coverage measures sampled geometric support, not thickness, mesh topology, contact clearance or clinical fit certification')
 protocol_text='''# V1与Morton两臂：Fold C开发集配对评价方案 v1

日期：2026-11-03。状态：待单独执行授权；本轮仅本机准备，未连接服务器。

## 研究问题与固定范围

比较面积均匀V1与冻结Morton等面积分层8k采样能否改变缺失骨块完整边界的预测质量，重点为未知原始表面E和缺损接触切壁J。本阶段模型为B0 AdaPoinTr，不是Mamba创新实验。使用已正式审计的两个final checkpoint，均epoch99、3900 updates；不选最佳epoch，不改权重或BN统计。

固定SkullBreak Fold C、seed0、21开发来源、每来源五缺损，共105例。每臂105次native forward，共210次，输入与输出均8192点。无warmup、重复投票、TTA、loss、backward、训练、BNCal。顺序固定为V1全部105例后Morton全部105例，逐病例顺序与冻结fold一致；模型逐个加载到GPU。

两臂使用各自同一采样规则的开发输入，延续训练阶段相同的逐病例PCG64固定点序政策。仅重排已存在的seed0点集，不重采样；GT8192、D-only归一化及病例身份相同。本机逐例回读及反置换验证已完成。训练来源与开发来源互斥；不接触确认集、SkullFix、MUG或Fold D。

该两臂设计比较训练与部署均采用各自采样方法的整体效果，不分离训练采样效应与测试输入采样效应；没有新增交叉采样四格推理。

## 评分定义与结论边界

继承已冻结、由真实G/D生成的A1面心及面积权重参考，复用105例原始参考，禁止依据当前预测重新构造参考或挑病例。G完整边界分成未知原始表面E和与D共享的切壁J。主终点是A1 E_G→预测的面积加权P95，单位mm；先对同source五缺损取算术均值，再21来源等权。关键次指标为J_G P95、J_G Cover@2mm、E_G Cover@2mm及同GT8192的CD-L1（双向最近邻平均距离之均值，不平方）。D-only逆归一化回物理mm，模型不读取GT。

统一报告Morton−V1差值：距离负向更好，覆盖率正向更好；报告来源级差值、五类缺损及退化病例，不因结果差而剔除病例。主指标改善但J退化时，明确报告权衡，不宣布整体胜出。辅助列出反向离群距离、A2/B离散敏感性，以及GT8192／输入原样预测的CPU控制。单折单训练seed，仅描述性探索比较；不新增bootstrap、p值或正式gate，不外推临床精度或Mamba收益。J覆盖和距离并非完整植入物接触吻合、骨厚度、实体/网格拓扑或临床验证。

## 执行与资源合同

固定FP32、严格deterministic、TF32/AMP关闭，复用原生PointNet2和全key query-chunk256 KNN，不安装、编译、下载或升级依赖。eval/inference_mode；参数/BN及Python、NumPy、CPU/CUDA RNG前后必须一致。资源阈值沿用既有评价：wall7200秒、RSS8GiB、torch allocated/reserved20GiB、SMI22528MiB、输出1GiB、最低空闲磁盘4GiB；PID仅作诊断，不声称独占cgroup。

执行授权后先实时核对固定hostname/GPU/Python、复用资产和两个checkpoint哈希、上传包哈希、全部新目标不存在、GPU空闲与磁盘。213文件包只含210开发点集和入口/index/receipt三个文件，不含checkpoint或原始NRRD。按冻结映射独占写入；五个全新数据目录、控制目录、输出目录均不得覆盖。授权回执单向绑定内层request，runtime再绑定回执哈希，随后单次launcher和claim；只启动一次tmux。异常立即停止，不自动修复、重试或resume。

## 验证与分阶段授权

新入口从既有四模型评价工具限定派生，仅改变两臂合同、路径、checkpoint阶段及补充RNG断言，模型、provider和数值内核不变。20项人工CPU合同通过；实际运输包213成员完整回读哈希及两项异常拒绝通过。CPU测试包含人工Tiny BN张量与人工checkpoint，不加载真实模型或权重，不能证明当前CUDA推理成功。当前容器信息继承刚完成的正式审计，不替代执行前实时核验。

```mermaid
flowchart LR
    A[本机准备与待授权request] --> B[手动上传并单独授权完整哈希]
    B --> C[实时核验及不覆盖安装]
    C --> D[唯一一次210预测]
    D --> E[另行授权正式只读冻结审计]
    E --> F[核验手动下载后单独授权统一CPU评分]
```

本次request只覆盖未来一次部署与GPU预测，不授权本机评分。预测成功后须先正式只读冻结审计，再下载归档并核验；使用当前冻结参考/指标适配两臂评分入口并单独授权。旧四模型评分入口硬编码420条，不能直接冒用为当前两臂评分实现。当前不材料化生产authorization、runtime、launcher或attempt文件。
'''
 protocol=write('paired_evaluation_protocol_zh_v1.md',protocol_text.encode('utf-8'))
 p3=dump('local_P3_v1.json',dict(status='LOCAL_P3_PASS_FOR_PENDING_PAIRED_PREDICTION_SCOPE',CPU_tests=bind(N/'CPU_contract_result_v1.json'),CPU_test_count=20,controller_readback=bind(N/'controller_transport_readback_v1.json'),implementation={n:bind(N/n) for n in source_files},derivation=bind(N/'implementation_derivation_v1.json'),data_receipt=bind(N/'paired_development_data_receipt_v1.json'),input_index=bind(N/'development_input_index_v1.json'),reference_manifest=bind(N/'reference_manifest_foldC_v1.json'),protocol=bind(protocol),parent_audits=[r['freeze_audit'] for r in index['runs']],limits=['No current server readiness query; live prewrite checks mandatory','CPU contracts do not prove CUDA behavior or Linux race immunity','Controller full deployment/launch not run locally','Existing historical A1 references reused unchanged','Local scoring implementation is a later separate scope'],server_calls=0,model_forwards=0,training_updates=0,BNCal=0,production_authorization_materialized=False))
 reused={r['path']:{k:r[k] for k in ['path','bytes','sha256']} for r in assets['assets']}
 for r in [parent['static_config'],parent['QC']['fold_binding'],parent['preflight_scope'],parent['implementation']['preflight_helper']]+[r['checkpoint'] for r in index['runs']]:reused[r['path']]=r
 # Freeze all exact30 metadata bindings plus explicit Python executable binding inherited from successful audits.
 py=dict(path='/opt/conda/envs/adapointr-mamba/bin/python3.10',bytes=17331920,sha256='01b4275dc374dcae51d245bda004daad6d7882d3f5de7f9852567bb7ab83180d');reused[py['path']]=py
 sidecars=[N/(archive.name+'.'+s) for s in ['sha256','bytes','contents.sha256','contents.sha256.sha256']]
 mappingfile=dump('non_overwrite_installation_mapping_v1.json',dict(status='FROZEN_NOT_INSTALLED',files=mapping,new_data_directories=dirs,new_control=CONTROL,new_output=OUT))
 request=dump('development_execution_request_v1.json',dict(schema='bcsp-sampling-pair-development-execution-scope-v1',status='AWAITING_EXPLICIT_USER_AUTHORIZATION',execution_authorized=False,date_Asia_Shanghai='2026-11-03',request_kind='ONE 210-forward Fold C native paired prediction batch after exclusive213-file install; later local scoring separate',entry_request=bind(qp),entry_request_future_server_path=CONTROL+'/entry_request.json',controller_template=bind(controllerpath),upload=rem(archive,'/home/jovyan/'+archive.name),upload_sidecars=[rem(p,'/home/jovyan/'+p.name) for p in sidecars],local_upload=bind(archive),install_mapping=mapping,installation_mapping_record=bind(mappingfile),new_data_directories=dirs,tmux_session='bcsp_sampling_pair_foldc_seed0_dev_v1',reused_assets=list(reused.values()),parent_training_audits=[r['freeze_audit'] for r in index['runs']],protocol=bind(protocol),local_P3=bind(p3),predictions=q['science'],scoring=scoring,resource_limits=limits,expected_output=OUT,result_archive_files=[OUT+'/development_predictions_v1.tar.gz'+suffix for suffix in ['', '.sha256','.bytes','.contents.sha256']],authorization_order=['Verify exact full outer SHA and explicit user grant','Recheck fixed live identity,upload hashes,all reused source/provider/checkpoints,disk,idle GPU,and all213 targets and new dirs absent','Exclusive creation five data dirs/install213 files/readback hashes','Create new control/output; entry request -> authorization -> SHA -> runtime -> launcher -> single-use claim','Single tmux launch, actual exit code persisted; PowerShell propagates LASTEXITCODE'],runtime_materialization_authorized_now=False,launcher_materialized_now=False,attempt_materialized_now=False,forwards_executed_now=0,failed_attempt_policy='STOP_NO_RETRY; no resume,repair/relaunch,case selection,parameter scans or new training',forbidden=['no training/optimizer/backward/loss/BNCal','no FoldD or extra seed/input count','no raw NRRD/STL/confirmation payload','no overwrite/delete','no dependency download/build/install/upgrade','no GPU warmup/voting/TTA','no local scoring or formal gate in this request'],readiness='Local preparation/P3 complete. No server queried this turn. Execution requires current live prewrite checks and separate full-hash grant.'))
 write('development_execution_request_v1.json.sha256',(bind(request)['sha256']+'  '+request.name+'\n').encode())
 dump('preparation_completion_v1.json',dict(status='READY_AWAITING_EXPLICIT_USER_AUTHORIZATION',request=bind(request),transport=bind(archive),upload_files=[bind(archive)]+[bind(p) for p in sidecars],P3=bind(p3),paired_inputs=210,unique_cases=105,sources=21,CPU_tests=20,model_predictions=0,server_calls=0,production_authorization_created=False))
 files=[dict(name=str(p.relative_to(N)).replace('\\','/'),bytes=p.stat().st_size,sha256=h(p.read_bytes())) for p in sorted(N.rglob('*')) if p.is_file()]
 dump('preparation_artifact_manifest_v1.json',dict(files=files,status='PREPARED_NOT_EXECUTED'))
 print(json.dumps(dict(status='PENDING_PAIRED_EVALUATION_REQUEST_FROZEN',request_sha256=bind(request)['sha256'],transport=bind(archive),upload_files=5,install_files=213,forwards_run=0)))
if __name__=='__main__':main()
