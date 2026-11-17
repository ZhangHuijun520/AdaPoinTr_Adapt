"""Isolated G0_D entry/bridge and frozen local aliases; no server operations."""
from pathlib import Path,PurePosixPath
import json,hashlib,ast
S=Path(__file__).resolve().parent;W=S.parents[1];V=S/'G0_D_implementation_v1';V.mkdir(exist_ok=True);assert not list(V.iterdir())
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def rec(p,target=None):return dict(path=target or str(p.resolve()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def emit(n,d):
 with (V/n).open('x',encoding='utf-8') as f:json.dump(d,f,ensure_ascii=False,indent=2)
def write(n,s):
 ast.parse(s)
 with (V/n).open('x',encoding='utf-8',newline='\n') as f:f.write(s)
parent=S/'UTC_order_hotfix_v3/bcsp_spcg_training_entry_v3.py'
entry=parent.read_text(encoding='utf-8')
for a,b in [('G0_C','G0_D'),('G0C','G0D'),("('G0','C',0,8192,8192)","('G0','D',0,8192,8192)"),("q['QC']['fold_binding'],'C',8192)","q['QC']['fold_binding'],'D',8192)"),("arm='G0',fold='C'","arm='G0',fold='D'")]:
 assert a in entry,a;entry=entry.replace(a,b)
entry=entry.replace("    return q\ndef authorize", """    need(q['data_root']==q['project']+'/data/bcsp_geov1_foldd_8192_seed0_v1' and PurePosixPath(q['order_plan']['path']).name=='shared_order_foldD_seed0_v1.json','D data and order')
    need(set(q['C_matrix_freezes'])=={'G0','G1','G2'},'completed C matrix')
    for arm,record in q['C_matrix_freezes'].items():
        proof=bound(record)
        need(proof['status']=='FORMAL_SPCG_'+arm+'_C_POST_TRAINING_FREEZE_PASS' and all(proof['checks'].values()),'C matrix freeze '+arm)
        need((proof['arm'],proof['fold'],proof['seed'],proof['updates'],proof['traversals'],proof['exposures'],proof['drops'])==(arm,'C',0,3900,100,31200,300),'C matrix counts '+arm)
        if arm=='G0':need(proof['initialization_raw_tensor_fingerprint']==q['expected_initial_state_sha256'],'shared untrained G0 initial state')
    return q

def authorize""")
assert 'C_matrix_freezes' in entry
write('bcsp_spcg_G0_D_training_entry_v1.py',entry)
bridge=(S/'bcsp_spcg_training_bridge_v1.py').read_text(encoding='utf-8');assert bridge.count("q['fold']=='C'")==1;bridge=bridge.replace("q['fold']=='C'","q['fold']=='D'")
write('bcsp_spcg_G0_D_training_bridge_v1.py',bridge)
q=read(S/'G0_D_preparation_v1/G0_D_training_contract_draft_v1.json');root=str(PurePosixPath(q['required_new_implementation']['entry']).parent)
q['schema']='bcsp-spcg-G0D-training-v1';q['status']='AWAITING_EXPLICIT_USER_AUTHORIZATION';q['execution_authorized']=False;q['launch_contract']=q.pop('planned_launch_contract')
q.pop('required_new_implementation');q.pop('supersedes_consumed_request_sha256',None)
proofs=q.pop('completed_C_matrix_proofs_local');q['C_matrix_freezes']={arm:dict(r,path=root+'/'+arm+'_C_formal_training_freeze_v1.json') for arm,r in proofs.items()}
for k in ['entry','bridge']:q['implementation'][k]=rec(V/('bcsp_spcg_G0_D_training_'+k+'_v1.py'),root+'/bcsp_spcg_G0_D_training_'+k+'_v1.py')
q['P3']=dict(path=root+'/training_P3_v1.json',bytes=0,sha256='0'*64)
q['readiness']='Local D metadata and C matrix verified; before install/launch recheck current identity/GPU/free disk8.5GiB/all source hashes/D315 inputs/D order/new targets. No current server operations.'
emit('draft_G0_D_request_v1.json',q)
aliases=read(S/'G2_C_implementation_v1/local_metadata_map_v1.json')
M=W/'outputs/cranial_bcsp_scq_foldC_training_preparation_20261113_v1/candidate_payload'
aliases[q['QC']['qualified_receipt']['path']]=str(M/'qualified_SCQ_D_8192_v1.json');aliases[q['order_plan']['path']]=str(M/'shared_order_foldD_seed0_v1.json')
for arm,r in proofs.items():aliases[q['C_matrix_freezes'][arm]['path']]=r['path']
for k in ['entry','bridge']:aliases[q['implementation'][k]['path']]=str(V/('bcsp_spcg_G0_D_training_'+k+'_v1.py'))
required=list(q['implementation'].values())+[q['static_config'],q['order_plan'],q['CUDA_freeze'],q['QC']['qualified_receipt'],q['QC']['verification'],q['QC']['fold_binding'],*q['QC']['manifests'].values(),*q['C_matrix_freezes'].values()]
for r in required:
 p=Path(aliases[r['path']]);a=rec(p);assert (a['bytes'],a['sha256'])==(r['bytes'],r['sha256']),r['path']
emit('local_metadata_map_v1.json',aliases)
emit('unchanged_inputs_v1.json',[rec(parent),rec(S/'bcsp_spcg_training_bridge_v1.py'),rec(Path(aliases[q['implementation']['training_runtime']['path']]))])
checks=['G0D fixed science and no changed limits','bridge only fold guard differs','complete C matrix and G0 scratch initialization bound','actual G0 mother forward FC and original head retained','actual mother coarse plus dense loss backward','CUDA admitted G0 state identity retained','complete authorize actual D metadata315 and order100','wrong C fold and C data root rejected','C order or wrong G2 arm rejected','missing or altered C freeze rejected','GPU selector mismatch rejected','one-way authorization and runtime mismatch rejected','POSIX launcher mkdir before redirection','UTC-first and original exception handler unchanged','real import-chain evidence inherited','actual bridge3900 artificial observations and five gradient steps','actual bridge exact loss component logs and counts','actual bridge rejects C fold','actual optimizer grouping six? original coarse matrices and biases','candidate bytes and frozen inputs unchanged']
checks[18]='actual optimizer grouping original coarse matrices and biases'
emit('CPU_scope_v1.json',dict(status='FROZEN_BEFORE_SINGLE_G0D_CPU_BATCH',attempts=1,checks=checks,server_operations=0,GPU=0))
emit('S0_S1_static_review_v1.json',dict(status='STATIC_PASS_READY_SINGLE_CPU_BATCH',entry=rec(V/'bcsp_spcg_G0_D_training_entry_v1.py'),bridge=rec(V/'bcsp_spcg_G0_D_training_bridge_v1.py'),metadata_bindings=len(required),tests_run=0,server_operations=0))
print('STATIC_PASS_G0D_READY20')
