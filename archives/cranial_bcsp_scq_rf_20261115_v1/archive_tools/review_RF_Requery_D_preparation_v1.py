"""Finite local preparation only. Preserve Requery_D-before-Static_D matrix order."""
from pathlib import Path
import ast,hashlib,json
R=Path(__file__).resolve().parent.parent;B=R/'outputs/scq_rf_Sref_D_implementation_20261114_v1'
O=R/'outputs/scq_rf_Requery_D_request_preparation_20261115_v1';O.mkdir()
def read(p):return json.loads(p.read_bytes())
def rec(p):return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
qp=B/'pending_transport_v1/payload/SCQ_RF_Sref_D_training_execution_request_v1.json';q=read(qp)
assert rec(qp)['sha256']=='888ad3b1a519d26ba907b061643e602aafe42df0e0006c7d0606d242e9a5c00d'
mirror={k:Path(v) for k,v in read(B/'final_local_mirror_v1.json').items()}
ap=B/'post_training_freeze_v1/freeze_verification_v1.json';a=read(ap)
assert a['status']=='FORMAL_SCQ_RF_SREF_POST_TRAINING_FREEZE_AUDIT_PASS' and a['fold']=='D' and a['check_count']==30 and all(a['checks'].values())
assert a['updates']==3900 and a['exposures']==31200 and a['order_sha256']=='2c9f3e9afb2cfe9ae46c0566bdbced465c64acc2a564654914d2163d74e5e838'
pairpath=mirror[q['pair_contract']['path']];assert rec(pairpath)['sha256']==q['pair_contract']['sha256'];pair=read(pairpath)
assert pair['arm_order']==['Sref_C','Static_C','Requery_C','Sref_D','Requery_D','Static_D'] and all(pair['FoldD'][k]==q[k] for k in ['QC','order_plan','data_root'])
CP=R/'outputs/scq_rf_Requery_C_implementation_20261114_v1'
cqp=CP/'pending_transport_v1/payload/SCQ_RF_Requery_C_training_execution_request_v1.json';cq=read(cqp)
cmirror={k:Path(v) for k,v in read(CP/'final_local_mirror_v1.json').items()}
entry=CP/'bcsp_scq_rf_Requery_C_training_entry_v1.py';source=entry.read_text(encoding='utf-8');ast.parse(source)
bridge=cmirror[cq['implementation']['bridge']['path']];bridge_text=bridge.read_text(encoding='utf-8');ast.parse(bridge_text)
assert "q['fold']=='C'" in source and "b=q['paired_static']" in source and "q[key]==reference[key]" in source and "fold='C'" in source
assert "['fold']" not in bridge_text and 'RF-Requery' in bridge_text
ca_path=R/'outputs/scq_rf_Static_C_implementation_20261114_v1/post_training_freeze_v1/freeze_verification_v1.json';ca=read(ca_path)
assert ca['status']=='FORMAL_RF_STATIC_C_TRAINING_PAIR_FREEZE_AUDIT_PASS' and all(ca['checks'].values()) and ca['identity']==a['identity'] and ca['common_initial_state_SHA256']==a['common_initial_state_SHA256']
for k in ['initialization','static_config','admission','resources','identity','model_root','environment','dependencies']:assert q[k]==cq[k]
rf_sources={}
for key in ['rf_residual','rf_factory']:
 r=cq['implementation'][key];p=cmirror[r['path']];assert rec(p)['sha256']==r['sha256'] and p.stat().st_size==r['bytes'];rf_sources[key]=dict(binding=r,local=rec(p))
rp=cmirror[cq['rf_initialization']['path']];assert rec(rp)['sha256']==cq['rf_initialization']['sha256']
static_init_path=ca_path.parent/'output/initialization.json';assert rec(static_init_path)['sha256']==ca['artifacts']['output/initialization.json']['sha256']
init=read(static_init_path);assert init==ca['initialization']
record=dict(status='REQUERY_D_PREPARATION_COMPLETE_MINIMAL_ENTRY_ADAPTATION_REQUIRED',Sref_D_freeze=rec(ap),Sref_D_request=rec(qp),Requery_C_entry=rec(entry),fold_neutral_Requery_bridge=rec(bridge),matrix=rec(pairpath),RF_sources=rf_sources,
 scope=dict(status='DRAFT_NOT_EXECUTION_REQUEST',arm='RF-Requery',fold='D',seed=0,n_input=8192,n_output=8192,parameters=40827847,RF_parameters=231171,train_sources=63,train_cases=315,updates=3900,traversals=100,exposures=31200,drops=300,
 QC=q['QC'],order_plan=q['order_plan'],data_root=q['data_root'],identity_to_reverify=q['identity'],resources=q['resources'],pair_contract=q['pair_contract'],Sref_initialization=q['initialization'],RF_initialization=cq['rf_initialization'],admission=q['admission'],
 same_model_initialization_reference=dict(source=rec(static_init_path),formal_audit=rec(ca_path),parameter_sha256=init['parameter_sha256'],persistent_state_sha256=init['persistent_state_sha256'],seed=init['seed'],scope='Model fingerprints only. The C order_sha256 is NOT the D training order. No checkpoint loading.'),
 same_fold_baseline='Frozen Sref_D; RF-Static_D follows Requery_D and is not a prerequisite',scientific_branch='N1=KNN(M,Q1); unchanged existing RF factory/residual, loss and runtime'),
 gaps=['C-only schema/fold/QC/order/log identifiers require new D entry','Current Requery_C validation requires already-frozen same-fold Static_C: cannot substitute nonexistent Static_D or reorder matrix','Separate model initialization identity from fold-specific order; D QC/order must stay exact FoldD','Reuse original fold-neutral Requery bridge; no GPU preflight repetition'],
 next_minimal_scope=['Requery_D entry + targeted artificial CPU batch + P3','Bind formal Sref_D evidence; retain C-stage continuation/model initialization provenance without transplanting C order/data or requiring Static_D','Reuse admitted model/residual/bridge/runtime and existing D matrix/readiness; no framework expansion','Create final pending execution request only after final implementation hashes and P3'],production_edits=0,CPU_tests=0,server_operations=0,new_forward=0,execution_request_created=False)
with (O/'Requery_D_scope_and_compatibility_v1.json').open('x',encoding='utf-8') as f:json.dump(record,f,ensure_ascii=False,indent=2)
with (O/'RF_Requery_D_准备与最小接入范围_zh_v1.md').open('x',encoding='utf-8') as f:f.write('''# RF-Requery Fold D 准备与最小接入范围

2026-11-15。本轮仅本机只读核对，不操作服务器、测试或训练。

S-ref_D正式冻结30项通过；D折数据、顺序和计数合同完整。冻结矩阵下一臂为Requery_D，Static_D在其后，不能颠倒顺序。

保持seed0、8k→8k、315病例/63来源、3900更新、100遍历、31,200曝光、300丢弃；原RF模型40,827,847参数、第二头231,171参数。复用已准入RF源码、两份初始化、loss、优化器、阈值及D折矩阵/就绪记录。已有Requery bridge功能与fold无关，可原样复用。

现有Requery_C入口仍限定C折，并要求Static_C先冻结。D折不能照搬该依赖：既定顺序是先Requery_D，再Static_D。因此需新增D专用入口，将同折参考绑定为S-ref_D，保留C阶段已冻结证据作为完成顺序及模型初始化来源；不要求尚不存在的Static_D。

可以沿用C阶段已冻结RF模型的完整初始参数/持久状态指纹作为同seed、同源码、同初始化的身份合同，但必须与D折顺序分开。C初始化记录中的order_sha256不能移植为D顺序；真正D顺序固定为2c9f3e9afb2cfe9ae46c0566bdbced465c64acc2a564654914d2163d74e5e838。不加载C或D已有checkpoint，不warm-start，不根据C折loss调整D设置。

下一步建议单独授权：Requery_D最小入口接入、一批针对性人工CPU验证及P3。集中覆盖D折完整authorize、S-ref_D冻结证据、模型初始化与顺序分离、真实RF重查询/梯度、几何日志、精确读取链及异常回溯。已有bridge、模型和runtime保持不变，无需重复GPU准入。

通过后再创建绑定最终哈希的待授权execution request。本次未创建可执行request或任何授权控制文件。
''')
print(json.dumps(dict(status=record['status'],output=str(O),final_request=False)))
