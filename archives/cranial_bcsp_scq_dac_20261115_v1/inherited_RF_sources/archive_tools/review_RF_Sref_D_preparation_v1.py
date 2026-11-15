"""Bounded local Fold D metadata and entry review, no payload/model/server execution."""
from pathlib import Path
from collections import Counter
import ast,hashlib,importlib.util,json
R=Path(__file__).resolve().parent.parent
B=R/'outputs/scq_rf_Sref_C_training_implementation_20261114_v1/startup_chain_binding_v3'
O=R/'outputs/scq_rf_Sref_D_request_preparation_20261114_v1';O.mkdir()
def read(p):return json.loads(p.read_bytes())
def rec(p):return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
qc=read(B/'pending_transport_v3/payload/SCQ_RF_Sref_C_training_execution_request_v3.json')
mirror={k:Path(v) for k,v in read(B/'local_mirror_v3.json').items()}
dqp=R/'outputs/cranial_bcsp_scq_foldD_training_preparation_20261113_v1/pending_transport_v1/payload/SCQ_B_FoldD_training_execution_request_v1.json';dq=read(dqp)
oldpair=R/'outputs/cranial_bcsp_scq_foldC_training_preparation_20261113_v1/SCQ_BS_CD_pair_contract_v1.json';op=read(oldpair)
assert dq['QC']==op['FoldD']['QC'] and dq['order_plan']==op['FoldD']['order_plan'] and dq['data_root']==op['FoldD']['data_root']
ctx=read(R/'outputs/cranial_bcsp_scq_foldD_training_preparation_20261113_v1/FoldD_context_v1.json')
mirror.update({k:Path(v) for k,v in ctx['mirror'].items()})
contract=mirror[qc['implementation']['contract']['path']];assert rec(contract)['sha256']==qc['implementation']['contract']['sha256']
spec=importlib.util.spec_from_file_location('RF_D_metadata_only',contract);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
x=m.exact
def exact(r):
 p=mirror[r['path']];return x(dict(r,path=str(p.resolve())))
m.exact=exact
selected,fold=m.verify_qualified_receipt(read(exact(dq['QC']['qualified_receipt'])),dq['QC']['verification'],dq['QC']['manifests'],dq['QC']['fold_binding'],'D',8192)
plan=m.validate_order(read(exact(dq['order_plan'])),fold['train_case_ids'])
exposure,dropped=Counter(),Counter()
for epoch in plan['epochs']:
 for batch in epoch['batches']:exposure.update(batch)
 dropped.update(epoch['dropped'])
assert len(selected)==315 and len(fold['train_sources'])==63 and len(fold['dev_sources'])==21
assert not set(fold['train_sources'])&set(fold['dev_sources']) and set(Counter(r['source_id'] for r in selected).values())=={5}
assert sum(exposure.values())==31200 and sum(dropped.values())==300 and all(exposure[c]+dropped[c]==100 for c in plan['case_ids'])
assert len(plan['epochs'])==100 and all(len(e['batches'])==39 for e in plan['epochs'])
canonical=m.canonical_sha(plan);assert canonical==op['order_canonical_sha256']['D']
pairpath=mirror[qc['pair_contract']['path']];assert rec(pairpath)['sha256']==qc['pair_contract']['sha256'];pair=read(pairpath)
assert pair['arm_order']==['Sref_C','Static_C','Requery_C','Sref_D','Requery_D','Static_D'] and 'FoldD' not in pair
audits={}
for arm,path,status,n in [('Sref_C',B/'post_training_freeze_v1/freeze_verification_v1.json','FORMAL_SCQ_RF_SREF_POST_TRAINING_FREEZE_AUDIT_PASS',26),('Static_C',R/'outputs/scq_rf_Static_C_implementation_20261114_v1/post_training_freeze_v1/freeze_verification_v1.json','FORMAL_RF_STATIC_C_TRAINING_PAIR_FREEZE_AUDIT_PASS',34),('Requery_C',R/'outputs/scq_rf_Requery_C_implementation_20261114_v1/post_training_freeze_v1/freeze_verification_v1.json','FORMAL_RF_REQUERY_C_TRAINING_PAIR_FREEZE_AUDIT_PASS',43)]:
 a=read(path);assert a['status']==status and a['check_count']==n and all(a['checks'].values()) and a['identity']==qc['identity'] and a['updates']==3900 and a['exposures']==31200
 audits[arm]=rec(path)
entry=B/'bcsp_scq_rf_Sref_C_training_entry_v3.py';src=entry.read_text(encoding='utf-8');ast.parse(src)
tokens=["q['fold']=='C'","'S-ref_C first run only'","SCQ_RF_Sref_foldC_seed0_train_","'fold_binding'],'C',8192)","pair['FoldC']","fold='C'"]
anchors=[dict(line=i,text=l.strip()) for i,l in enumerate(src.splitlines(),1) if any(t in l for t in tokens)]
assert all(any(t in l for l in src.splitlines()) for t in tokens)
old_ready=R/'outputs/cranial_bcsp_scq_foldD_training_preparation_20261113_v1/FoldD_metadata_readiness_v1.json';ready=read(old_ready)
assert ready['identity']!=qc['identity']
metadata=[dq['QC']['qualified_receipt'],dq['QC']['verification'],*dq['QC']['manifests'].values(),dq['QC']['fold_binding'],dq['order_plan']]
result=dict(status='SREF_D_LOCAL_METADATA_PASS_ENTRY_AND_FOLD_BINDING_ADAPTATION_REQUIRED',frozen_C_audits=audits,metadata=[dict(remote=r,local=rec(exact(r))) for r in metadata],
 scope=dict(status='DRAFT_NOT_EXECUTION_REQUEST',arm='S-ref',variant='S',fold='D',seed=0,n_input=8192,n_output=8192,total_parameters=40596676,RF_second_head=False,train_cases=315,train_sources=63,dev_cases_metadata_only=105,dev_sources_metadata_only=21,traversals=100,updates=3900,exposures=31200,drops=300,order_canonical_sha256=canonical,train_allowlist_sha256=fold['train_allowlist_sha256'],QC=dq['QC'],order_plan=dq['order_plan'],data_root=dq['data_root'],identity_to_reverify_before_execution=qc['identity'],resources=qc['resources'],initialization=qc['initialization'],from_scratch=True,checkpoint_warmstart=False),
 blockers=dict(entry=rec(entry),C_only_anchors=anchors,RF_contract=rec(pairpath),missing_RF_FoldD_metadata_binding=True,old_D_readiness=rec(old_ready),old_D_readiness_identity_is_historical=True),
 next_minimal_scope=['Sref_D entry only; original Sref bridge is fold-neutral and needs no model change.','New version of RF matrix metadata adds exact pre-existing FoldD QC/order/data_root and preserves six-run order, science and FoldC binding.','Current-identity D metadata readiness record labels server unverified; never treat historical device record as current or auto-rebind at execution.','Targeted artificial CPU batch covers full authorize D selection, wrong-fold denial, exact read chain and3900 guards; complete P3 then final pending request.'],
 production_edits=0,CPU_tests=0,payload_arrays_read=0,checkpoint_loads=0,server_operations=0,execution_request_created=False)
with (O/'Sref_D_metadata_and_entry_review_v1.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
with (O/'Sref_D_准备核对与最小接入范围_zh_v1.md').open('x',encoding='utf-8') as f:f.write('''# S-ref Fold D 准备核对与最小接入范围

2026-11-14。本轮仅本机只读源码/元数据核对；未读取点集数组、加载模型/权重、操作服务器或运行测试。

## 已确认

C折S-ref、Static、Requery的正式冻结分别26、34、43项通过，当前冻结顺序下一臂为Sref_D。

沿用原先已经冻结的Fold D来源及V1点集，不重新划分：63训练来源/315病例，每来源5缺损；21开发来源/105病例仅核对元数据，训练来源与开发来源不相交。

完整100遍历×39批次元数据已校验；3900更新、31,200曝光、300丢弃，每病例曝光+丢弃恰为100。D折顺序canonical SHA256为`2c9f3e9afb2cfe9ae46c0566bdbced465c64acc2a564654914d2163d74e5e838`。数据根继承既有冻结Fold D记录，不按目录名称猜测。

保持S-ref原模型40,596,676参数，不安装RF第二头；seed0、8k→8k、从头初始化、原loss/优化器和资源阈值；不加载C折权重，不根据C折loss或结果调参、筛病例。

## 三项最小接口缺口

1. 当前S-ref入口的schema、fold准入、QC选择、矩阵读取及日志标识均固定C，需要新增D专用入口；bridge本身与fold无关，可原样复用。
2. 当前RF六运行合同列出了D运行顺序，但只写入FoldC元数据。需新增合同版本补入原已冻结的FoldD QC、顺序和数据根；保留旧文件、顺序及所有科研条件。
3. 历史D就绪凭据绑定旧设备，不能当作当前就绪证据。新元数据凭据应采用当前阶段冻结身份，并明确“尚未核验服务器”；执行时仍须重新核对身份、资产、315份训练文件哈希和资源，不能自动重绑定或虚报就绪。

## 下一步建议的单次限定implementation-only

新增Sref_D入口、版本化D元数据绑定/就绪记录及针对性人工CPU验证，复用原bridge/model/runtime。验证覆盖完整authorize的D折选择、拒绝错折/错顺序、C折冻结证据、16条精确读取绑定及异常回溯、原loss与3900计数。完成P3后创建绑定最终哈希的待授权request。

无需重复GPU准入。本次不直接生成一个与现有C专用入口不兼容的最终execution request，也不材料化授权回执、runtime或launcher。
''')
print(json.dumps(dict(status=result['status'],order_SHA256=canonical,updates=3900,output=str(O))))
