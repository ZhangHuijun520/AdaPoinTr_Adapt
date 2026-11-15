"""Finite local request preparation: frozen C-pair evidence and exact interface review only."""
from pathlib import Path
import ast,hashlib,json
R=Path(__file__).resolve().parent.parent;B=R/'outputs/scq_rf_Static_C_implementation_20261114_v1'
O=R/'outputs/scq_rf_Requery_C_request_preparation_20261114_v1';O.mkdir()
def read(p):return json.loads(p.read_bytes())
def rec(p):return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
qp=B/'pending_transport_v1/payload/SCQ_RF_Static_C_training_execution_request_v1.json';q=read(qp)
assert rec(qp)['sha256']=='a3275c69e78f95d59358ba8c621c63cb053b54b97467c8583e67feedb2b1051f'
mirror={k:Path(v) for k,v in read(B/'final_local_mirror_v1.json').items()}
ap=B/'post_training_freeze_v1/freeze_verification_v1.json';a=read(ap)
assert a['status']=='FORMAL_RF_STATIC_C_TRAINING_PAIR_FREEZE_AUDIT_PASS' and a['check_count']==34 and all(a['checks'].values())
assert (a['updates'],a['traversals'],a['exposures'],a['drops'])==(3900,100,31200,300)
sref_path=mirror[q['paired_baseline']['audit']['path']];sa=read(sref_path)
assert rec(sref_path)['sha256']==q['paired_baseline']['audit']['sha256']==a['paired_baseline_audit_sha256']
assert sa['status']=='FORMAL_SCQ_RF_SREF_POST_TRAINING_FREEZE_AUDIT_PASS' and all(sa['checks'].values()) and sa['check_count']==26
assert sa['identity']==a['identity']==q['identity'] and sa['common_initial_state_SHA256']==a['common_initial_state_SHA256']
pairpath=mirror[q['pair_contract']['path']];assert rec(pairpath)['sha256']==q['pair_contract']['sha256'];pair=read(pairpath)
assert pair['arm_order']==['Sref_C','Static_C','Requery_C','Sref_D','Requery_D','Static_D']
sources={}
for key,r in q['implementation'].items():
 p=mirror[r['path']];assert rec(p)['sha256']==r['sha256'] and p.stat().st_size==r['bytes'];sources[key]=rec(p)
for r in [q['initialization'],q['rf_initialization']]:assert rec(mirror[r['path']])['sha256']==r['sha256']
entry=mirror[q['implementation']['entry']['path']];bridge=mirror[q['implementation']['bridge']['path']]
et=entry.read_text(encoding='utf-8');bt=bridge.read_text(encoding='utf-8');ast.parse(et);ast.parse(bt)
hits={}
for label,src,patterns in [('entry',et,["q['arm']=='RF-Static'","q['variant']=='RF-Static'","SCQ_RF_Static_foldC_seed0_train_","model.base_model.rf.variant=='RF-Static'","evidence['rf']['variant']=='RF-Static'","torch.equal(info['N0'],info['N1'])","N0_N1_equal=True"]),('bridge',bt,["model.base_model.rf.variant!='RF-Static'"])]:
 hits[label]=[dict(line=i,text=l.strip()) for i,l in enumerate(src.splitlines(),1) if any(p in l for p in patterns)]
 assert all(any(p in l for l in src.splitlines()) for p in patterns)
rf=mirror[q['implementation']['rf_residual']['path']];rftext=rf.read_text(encoding='utf-8')
assert "idx = N0 if self.variant == 'RF-Static' else self.knn(8, M, Q1)" in rftext
records={k:rec(B/'post_training_freeze_v1/output'/name) for k,name in [('construction','model_construction.json'),('initialization','initialization.json'),('order_plan','order_plan.json'),('exposure','exposure.json'),('optimizer_groups','optimizer_parameter_groups.json'),('optimizer_defaults','optimizer_actual_defaults.json')]}
for key,r in records.items():
 name=Path(r['path']).name;assert all(r[k]==a['artifacts']['output/'+name][k] for k in ('bytes','sha256'))
scope=dict(status='DRAFT_NOT_EXECUTION_REQUEST',arm='RF-Requery',fold='C',seed=0,n_input=8192,n_output=8192,train_sources=63,train_cases=315,batch=8,updates=3900,traversals=100,exposures=31200,drops=300,total_parameters=40827847,RF_parameters=231171,
    science=q['science'],identity=q['identity'],resources=q['resources'],QC=q['QC'],data_root=q['data_root'],model_root=q['model_root'],order_plan=q['order_plan'],static_config=q['static_config'],pair_contract=q['pair_contract'],original_initialization=q['initialization'],rf_initialization=q['rf_initialization'],admission=q['admission'],
    sole_model_branch='Second head N1=knn(8,M,Q1), instead of reusing N0; feature and relative geometry construction still at Q1.',
    Static_formal_audit=rec(ap),Sref_formal_audit=rec(sref_path),Static_reference_request=rec(qp),Static_reference_artifacts=records,
    exact_Static_full_initialization=a['initialization'],common_full_S_state_SHA256=a['common_initial_state_SHA256'],checkpoint_warmstart=False,
    next_required=['Requery_C strict entry and necessary bridge variant adaptation; keep existing Sref and Static paths immutable.','Bind Static formal evidence as principal pair plus inherited Sref evidence; same science/assets/order.','Replace Static-only neighbor-equality assertion by actual measured equality/overlap logging; first-step equality allowed, no observed-difference gate.','Retain RF model/residual/factory and both frozen initializer bytes; exact read bindings and traceback coverage.','One targeted artificial CPU batch and P3; verify zero-head initial equality and nontrivial changed-neighbor fixture without new GPU.','Then create final-hash pending execution request; no deployment or training now.'])
result=dict(status='REQUERY_C_LOCAL_READONLY_REVIEW_COMPLETE_ENTRY_ADAPTATION_REQUIRED',scope=scope,exact_sources=sources,blocking_interfaces=hits,admitted_RF_model_branch=rec(rf),production_edits=0,tests=0,server_operations=0,new_forward=0,final_execution_request_created=False)
with (O/'compatibility_and_frozen_scope_v1.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
with (O/'RF_Requery_C_准备核对与最小接入范围_zh_v1.md').open('x',encoding='utf-8') as f:f.write('''# RF-Requery Fold C 准备核对与最小接入范围

日期：2026-11-14。仅本机冻结证据和有限源码核对，未运行测试、GPU或服务器操作。

## 核对结论

S-ref_C正式冻结26项通过；RF-Static_C正式冻结及配对核验34项通过。两者共有S初始化、数据、完整顺序及计数一致。当前六运行顺序的下一臂确为Requery_C。

原生RF残差源码已经实现Requery分支：在Q1处调用KNN获得N1。模型公式无需修改，RF额外参数仍为231,171，总参数40,827,847。两臂均以Q1构造特征和相对几何，只有第二头邻居选择不同；下游统一使用Q2。

当前Static专用入口和bridge不能原样复用：授权、variant、run ID、factory evidence、模型类型均限制RF-Static；几何日志还强制N0=N1并固定写入True。直接修改request臂名称将失败。因此本次只冻结拟执行范围，尚不生成最终execution request。

## 已绑定的配对合同

- Fold C、seed0、63来源/315病例、8k输入/8k输出。
- 同初始化字节、同实际批次顺序、100遍历、3900更新、31,200曝光、300丢弃。
- 复用既定RF factory、残差源码、两份初始化、loss、AdamW分组及资源阈值。
- Static完整初始化的参数/持久状态指纹及共有S状态指纹均已记录，后续用于初始化配对核验。
- Static和S-ref checkpoint只作为冻结证据；Requery从头训练，不加载任一最终权重，不resume。

## 下一次限定implementation-only范围

1. 新增Requery_C专用入口及必要bridge适配，保留Static和S-ref原文件。
2. 同时绑定Static正式审计/构造/初始化/顺序/曝光/分组及S-ref证据；保留原科学合同。
3. 邻居相等性改为按实际N0/N1记录；允许初始零头导致N1=N0，不要求每个batch发生变化，不设置新的成功门槛。保留Qraw、Q1、Q2及两级残差日志。
4. 复用有限精确源码读取集合、两份初始化和异常回溯覆盖，不扩展目录根或环境框架。
5. 一批针对性人工CPU回归应覆盖：完整authorize、真实RF调用/梯度、零头初态一致、固定非退化fixture邻居变化、Q1相对几何、共有初始化和参数分组、实际读取链及异常回溯。
6. P3通过后创建绑定最终实现哈希的新request，保持AWAITING_EXPLICIT_USER_AUTHORIZATION。无需重复GPU准入；真实训练仍需单独完整哈希执行授权。

本次未修改实现、未创建执行控制、未部署或启动训练，也不依据训练loss选择参数或病例。
''')
print(json.dumps(dict(status=result['status'],scope=str(O),source_records=len(sources),final_request=False)))
