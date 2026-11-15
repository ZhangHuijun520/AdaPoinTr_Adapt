"""Finite local metadata/source review only. No imports, tests or executable request."""
from pathlib import Path
import ast,hashlib,json
R=Path(__file__).resolve().parent.parent
B=R/'outputs/scq_rf_Sref_C_training_implementation_20261114_v1/startup_chain_binding_v3'
O=R/'outputs/scq_rf_Static_C_request_preparation_20261114_v1';O.mkdir()
def read(p):return json.loads(p.read_bytes())
def rec(p):return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
qp=B/'pending_transport_v3/payload/SCQ_RF_Sref_C_training_execution_request_v3.json';q=read(qp)
assert rec(qp)['sha256']=='6370a9887893b510c95850616eb664198982131df67d5e9a06ae725f9b860a88'
ap=B/'post_training_freeze_v1/freeze_verification_v1.json';a=read(ap)
assert a['status']=='FORMAL_SCQ_RF_SREF_POST_TRAINING_FREEZE_AUDIT_PASS' and a['check_count']==26 and all(a['checks'].values()) and a['updates']==3900 and a['exposures']==31200
mirror={k:Path(v) for k,v in read(B/'local_mirror_v3.json').items()}
pair=mirror[q['pair_contract']['path']];assert rec(pair)['sha256']==q['pair_contract']['sha256'];p=read(pair)
assert p['arm_order']==['Sref_C','Static_C','Requery_C','Sref_D','Requery_D','Static_D']
entry=B/'bcsp_scq_rf_Sref_C_training_entry_v3.py';src=entry.read_text(encoding='utf-8');ast.parse(src)
cuda=mirror[q['admission']['request']['path']];assert rec(cuda)['sha256']==q['admission']['request']['sha256'];cq=read(cuda)
rf=cq['implementation']['rf_factory'];factory=R/'outputs/scq_rf_implementation_20261114_v1/bcsp_scq_rf_factory_v1.py'
residual=R/'outputs/scq_rf_initialization_loader_20261114_v2/bcsp_scq_rf_residual_v2.py'
assert rec(factory)['sha256']==rf['sha256'] and rec(residual)['sha256']==cq['implementation']['rf_residual']['sha256']
rfinit=R/'outputs/scq_rf_implementation_20261114_v1/rf_initialization_v1.bin'
if not rfinit.exists():
    matches=[x for x in (R/'outputs/scq_rf_implementation_20261114_v1').glob('*.bin') if rec(x)['sha256']==cq['rf_initialization']['sha256']]
    assert len(matches)==1;rfinit=matches[0]
assert rec(rfinit)['sha256']==cq['rf_initialization']['sha256']
blockers=[]
patterns=[('S-ref-only authorization',"q['arm']=='S-ref'"),('S-ref variant gate',"q['variant']=='S'"),('reject RF installation',"not hasattr(model.base_model,'rf')"),('original S parameter count',"40596676"),('old factory signature',"factory(model_builder,q['variant'],q['initialization'])"),('old factory evidence shape',"evidence['scq']"),('legacy S geometry omits RF stages',"Q0=dict(")]
for name,pattern in patterns:
    hits=[dict(line=i,text=line.strip()) for i,line in enumerate(src.splitlines(),1) if pattern in line]
    assert hits,name
    blockers.append(dict(issue=name,evidence=hits))
scope=dict(status='DRAFT_TRAINING_SCOPE_NOT_EXECUTION_REQUEST',arm='RF-Static',fold='C',seed=0,n_input=8192,n_output=8192,updates=3900,traversals=100,exposures=31200,drops=300,train_cases=315,train_sources=63,expected_total_parameters=40827847,RF_new_parameters=231171,
    initialization='FROM_SCRATCH_FROZEN_S_PLUS_FROZEN_RF_BYTES_NO_CHECKPOINT_WARMSTART',rf_initialization=cq['rf_initialization'],original_initialization=q['initialization'],Sref_checkpoint_for_provenance_only=a['checkpoint'],
    Sref_formal_audit=rec(ap),Sref_construction=rec(B/'post_training_freeze_v1/output/model_construction.json'),Sref_initialization=rec(B/'post_training_freeze_v1/output/initialization.json'),Sref_exposure=rec(B/'post_training_freeze_v1/output/exposure.json'),
    order_plan=q['order_plan'],QC=q['QC'],data_root=q['data_root'],identity=q['identity'],resources=q['resources'],static_config=q['static_config'],pair_contract=q['pair_contract'],
    next_required='Separate implementation-only Static_C entry/bridge compatibility, targeted artificial CPU regression and P3; final executable request only after final hashes',
    rules=['N0 reused; relative geometry recomputed at Q1; no extra gate/clamp/loss or parameter scan','Preserve existing runtime AdamW grouping with four RF tensors classified by ndim/bias; no optimizer changes','Shared initialization fingerprint excludes only RF, and must match formal Sref common state','Preserve full frozen source exact-read set, add admitted RF source and RF initializer records explicitly','No CUDA preflight repeat; no server operation, materialized execution control or training in this preparation'])
result=dict(status='READONLY_STATIC_C_REQUEST_REVIEW_ENTRY_INCOMPATIBLE_NO_FINAL_REQUEST',Sref_audit=rec(ap),current_entry=rec(entry),admitted_rf_factory=rec(factory),admitted_rf_residual=rec(residual),admitted_rf_initializer=rec(rfinit),blockers=blockers,scope=scope,production_edits=0,CPU_tests=0,server_operations=0,new_forward=0,execution_request_created=False)
with (O/'request_readiness_review_v1.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
with (O/'RF_Static_C_入口核对与待冻结范围_zh_v1.md').open('x',encoding='utf-8') as f:f.write('''# RF-Static Fold C 入口核对与待冻结范围

日期：2026-11-14。仅完成本机只读证据及源码核对，没有部署、测试或训练。

S-ref_C正式审计26项通过，3900更新、100遍历、31,200曝光、300丢弃事件。已绑定其审计、构造、初始化和曝光记录。既定矩阵下一臂确为Static_C。

现有入口不能直接执行RF-Static：它只授权S-ref/S，禁止安装RF，校验40,596,676参数，调用三参数SCQ factory，并按旧SCQ evidence层级读取。真实RF factory需要原SCQ初始化与RF初始化两份冻结记录，返回parent/rf层级，模型为40,827,847参数。原SCQ日志也没有分开记录Q1、delta0与delta1。

因此没有生成一个明知不能执行的最终execution request。机器可读范围保存在request_readiness_review_v1.json的scope字段；该scope不是执行请求，不能授权训练。

建议下一步单独授权最小implementation-only接入：Static_C专用入口、必要bridge适配、针对性人工CPU回归及P3。复用现有RF模型和原3900-step runtime；不修改科研公式、loss、数据、初始化或资源阈值，不重复GPU准入。

该次接入应集中覆盖：RF factory参数与evidence层级；总参数和四个RF新增参数分组；排除仅RF后的共有初始化与S-ref一致；全部冻结源码和两份初始化的精确只读绑定；正常加载顺序、runtime再哈希和异常回溯；RF几何阶段日志；最终authorize与launcher合同。人工验证不使用真实点集或训练checkpoint。

Static_C仍从头初始化，S-ref最终checkpoint仅作冻结证据，不warm-start。保持同一Fold C、seed0、8k→8k、315训练病例/63来源、同批次顺序、3900步。只复用N0，第二头相对几何在Q1重新计算，不增加gate、clamp、额外loss或参数扫描。

实施和P3通过后，才创建绑定最终实现哈希的新request，保持AWAITING_EXPLICIT_USER_AUTHORIZATION；本次未创建runtime、launcher或授权回执。
''')
print(json.dumps(dict(status=result['status'],output=str(O),blockers=len(blockers))))
