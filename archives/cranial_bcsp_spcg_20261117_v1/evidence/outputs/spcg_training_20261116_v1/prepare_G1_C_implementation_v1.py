from pathlib import Path
import ast,json,hashlib
S=Path(__file__).resolve().parent;V=S/'G1_C_implementation_v1';V.mkdir()
old=(S/'UTC_order_hotfix_v3/bcsp_spcg_training_entry_v3.py').read_text(encoding='utf-8')
new=old.replace('G0_C only','G1_C only').replace('bcsp-spcg-G0C-training-v1','bcsp-spcg-G1C-training-v1').replace("==('G0','C',0,8192,8192)","==('G1','C',0,8192,8192)").replace('SPCG_G0C_TRAINING_LOCAL_P3_PASS','SPCG_G1C_TRAINING_LOCAL_P3_PASS')
needle="    return q\ndef authorize";assert new.count(needle)==1
pair="""    pair=bound(q['G0_C_freeze'])
    need(pair['status']=='FORMAL_SPCG_G0_C_POST_TRAINING_FREEZE_PASS' and all(pair['checks'].values()),'G0 freeze')
    need((pair['arm'],pair['fold'],pair['seed'],pair['updates'],pair['traversals'],pair['exposures'],pair['drops'])==('G0','C',0,3900,100,31200,300),'G0 pairing')
    need(pair['order_plan']==q['order_plan'] and pair['initialization_raw_tensor_fingerprint']==q['parent_G0_initial_state_sha256'],'same order and untrained mother')
    for r in [q['probe_asset'],q['head_initialization'],q['mother_source']]:exact(r)
    return q
def authorize"""
new=new.replace(needle,pair)
new=new.replace("read_records=[*q['implementation'].values(),q['native_helper']]","read_records=[*q['implementation'].values(),q['native_helper'],q['probe_asset'],q['head_initialization']]")
needle="random.seed(0);np.random.seed(0);torch.manual_seed(0);model,evidence=sys.modules['bcsp_lqi_factory_v1'].build_model(lambda:cls(EasyDict(static['model'])),seed=0);helper.validate_model(model)";assert needle in new
new=new.replace(needle,"random.seed(0);np.random.seed(0);torch.manual_seed(0);model,evidence=build_G1(q,lambda:cls(EasyDict(static['model'])));helper.validate_model(model)")
new=new.replace("sum(p.numel() for p in model.parameters())==39903169,'G0 LQI'","sum(p.numel() for p in model.parameters())==39912132,'G1 LQI'").replace("arm='G0',fold='C'","arm='G1',fold='C'")
helpers='''
def raw_state_fingerprint(model):
    h=hashlib.sha256()
    for n,t in model.state_dict().items():h.update(n.encode());h.update(t.detach().cpu().contiguous().numpy().tobytes())
    return h.hexdigest()

def build_G1(q,legacy_builder):
    # Uses same LQI constructor first; never load G0's trained checkpoint.
    model,parent=sys.modules['bcsp_lqi_factory_v1'].build_model(legacy_builder,seed=0)
    need(raw_state_fingerprint(model)==q['parent_G0_initial_state_sha256'],'G0 shared scratch identity')
    factory=source('bcsp_spcg_factory_v1',q['implementation']['spcg_factory'])
    head=sys.modules['bcsp_spcg_head_v1'];U=head.from_bytes(exact(q['probe_asset']).read_bytes(),(256,3));H=exact(q['head_initialization']).read_bytes()
    model,change=factory.install(model,'G1',U,H,q['mother_source']['path'],q['mother_source']['sha256'])
    need(raw_state_fingerprint(model)==q['expected_initial_state_sha256'],'CUDA admitted G1 initial state')
    return model,dict(parent=parent,change=change,artificial_fixture=parent['artificial_fixture'])

'''
new=new.replace('\ndef main():',helpers+'\ndef main():',1)
entry=V/'bcsp_spcg_G1_C_training_entry_v1.py';ast.parse(new);entry.write_text(new,encoding='utf-8')
bridge=(S/'bcsp_spcg_training_bridge_v1.py').read_text(encoding='utf-8').replace("q['arm']=='G0'","q['arm']=='G1'")
assert bridge!=(S/'bcsp_spcg_training_bridge_v1.py').read_text(encoding='utf-8');(V/'bcsp_spcg_G1_C_training_bridge_v1.py').write_text(bridge,encoding='utf-8')
oldq=json.loads((S/'UTC_order_hotfix_v3/pending_transport_v3/payload/SPCG_G0_C_training_execution_request_v3.json').read_text(encoding='utf-8'));q=oldq
W=S.parents[1];base=W/'outputs/spcg_implementation_20261116_v1';cuda=json.loads((base/'output_policy_hotfix_v3/pending_transport_v3/payload/SPCG_CUDA_execution_request_v3.json').read_text(encoding='utf-8'));evidence=json.loads((base/'output_policy_hotfix_v3/post_CUDA_freeze_v3/server_evidence.json').read_text(encoding='utf-8'));completion=json.loads(evidence['output']['completion.json']['text']);audit=S/'UTC_order_hotfix_v3/post_training_freeze_v3/formal_freeze_result_v3.json'
def rec(p,target):return dict(path=target,bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
root=q['project']+'/third_party/bcsp_spcg_G1C_training_20261116_v1';run='SPCG_G1_foldC_seed0_train_20261116_v1';co=root+'/control/'+run
q.update(schema='bcsp-spcg-G1C-training-v1',arm='G1',run_id=run,output=q['project']+'/logs/cranial_bcsp_fullmamba/'+run,G0_C_freeze=rec(audit,root+'/G0_C_formal_training_freeze_v3.json'),parent_G0_initial_state_sha256=q['expected_initial_state_sha256'],expected_initial_state_sha256=completion['result']['models']['G1']['initial_state_sha256'],probe_asset=cuda['probe_asset'],head_initialization=cuda['head_initialization'],mother_source=cuda['mother_source'])
q.pop('supersedes_consumed_request_sha256',None);q['implementation']['entry']=rec(entry,root+'/'+entry.name);q['implementation']['bridge']=rec(V/'bcsp_spcg_G1_C_training_bridge_v1.py',root+'/bcsp_spcg_G1_C_training_bridge_v1.py');q['implementation']['spcg_factory']=cuda['implementation']['spcg_factory'];q['P3']=dict(path=root+'/training_P3_v1.json',bytes=0,sha256='0'*64);q['launch_contract']=dict(request_path=root+'/SPCG_G1_C_training_execution_request_v1.json',authorization_path=co+'/authorization_v1.json',runtime_path=co+'/runtime_v1.json',launcher_path=co+'/launch_once_v1.sh',launch_attempt_path=co+'/attempt_claim_v1.json',tmux_session=run)
(V/'draft_G1_C_request_v1.json').write_text(json.dumps(q,ensure_ascii=False,indent=2),encoding='utf-8')
scope=dict(status='FROZEN_BEFORE_SINGLE_G1_CPU_BATCH',attempts=1,checks=['entry science fixedG1C','parent bridge onlyarm guard differs','G0 freeze and shared orderbound','head U H mother source hashes fixed','actual buildG1 dispatch installs frozen head','G1 output256 dense8192 actualmotherpath','G1 expected initialization checked','missing/spoofed baseline rejected','GPU drift and G0arm rejected','oneway authorization finalfields','same logs fivegradstep code unchanged','real training module import chain regression inherited','CPU negative startup preserves guard order and failureexit','same3900order and original runtime hash','no-decay newhead matrix/bias covered','final candidate byte freeze'],server_operations=0,GPU=0)
(V/'CPU_scope_v1.json').write_text(json.dumps(scope,indent=2),encoding='utf-8');print('G1_C_STATIC_PREPARED')
