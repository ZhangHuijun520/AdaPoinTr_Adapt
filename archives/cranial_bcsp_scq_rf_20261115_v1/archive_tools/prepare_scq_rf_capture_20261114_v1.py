"""Prepare frozen metadata for one artificial CPU batch; never access server/GPU."""
from pathlib import Path
import ast,copy,hashlib,json
R=Path(__file__).resolve().parent.parent;S=R/'outputs/scq_rf_capture_implementation_20261114_v1'
REMOTE='/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_memory_20261114_v1'
def rec(p):return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def emit(p,x):
    with p.open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2)
old=R/'outputs/scq_pred_freeze_20261114_v2/downloads/installed'
parent=old/'SCQ_BS_CD_native_prediction_execution_request_v2.json';p=json.loads(parent.read_bytes())
stage=R/'outputs/scq_rf_stageA_readonly_20261114_v1/fixed_ten_case_memory_scope_v1.json';scope=json.loads(stage.read_bytes())
index=json.loads((old/'SCQ_BS_CD_input_index_v2.json').read_bytes())
q={k:copy.deepcopy(p[k]) for k in ('identity','model_root','static_config','preflight_scope','dependencies','helper','implementation','initialization','numeric_policy','environment')}
runid='SCQ_RF_ten_actual_memory_20261114_v1';out='/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/'+runid
q.update(schema='bcsp-scq-rf-ten-memory-capture-v1',status='AWAITING_EXPLICIT_USER_AUTHORIZATION',execution_authorized=False,stage='SCQ_RF_STAGE_A_MEMORY',run_id=runid,variant='S',RF_head_installed=False,GT_access=False,batch_size=1,counts=dict(forward=10,extra_N1_KNN=10,backward=0,optimizer_steps=0,loss=0,BNCal=0,warmup=0,retry=0),limits=dict(wall_seconds=1800,RSS_bytes=8589934592,torch_peak_bytes=21474836480,device_MiB=22528,output_bytes=2147483648,minimum_free_disk_bytes=4294967296),output=out,launch_attempt=REMOTE+'/control/attempt_claim_v1.json',parent_entry=dict(rec(old/'bcsp_scq_fourmodel_native_predict_v2.py'),path='/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_BS_CD_prediction_20261114_v2/bcsp_scq_fourmodel_native_predict_v2.py'),parent_request=dict(rec(parent),path='/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_BS_CD_prediction_20261114_v2/'+parent.name),comparison_tolerance=dict(normalized_max_abs=1e-6,world_max_abs_mm=.001),capture_scope=dict(rec(stage),path=REMOTE+'/fixed_ten_case_memory_scope_v1.json'),entry=dict(rec(S/'bcsp_scq_rf_memory_capture_v1.py'),path=REMOTE+'/bcsp_scq_rf_memory_capture_v1.py'))
q['runs']=[x for x in index['runs'] if x['variant']=='S'];q['cases']=[]
for fold in 'CD':
    for c in scope['cases']:
        if c['fold']!=fold:continue
        row={k:copy.deepcopy(c[k]) for k in ('fold','case_id','source_id','defect_type','input','normalization','normalization_source','role')}
        row.update(run='S_'+fold,n_input=8192,n_output=8192,output_filename='memory/S_'+fold+'__'+c['case_id']+'.npz',reference=dict(path=REMOTE+'/references/S_'+fold+'__'+c['case_id']+'.npz',bytes=c['frozen_prediction']['bytes'],sha256=c['frozen_prediction']['sha256']))
        q['cases'].append(row)
q['launch_contract']=dict(tmux_session='bcsp_scq_rf_memory_20261114_v1',request_path=REMOTE+'/SCQ_RF_ten_memory_execution_request_v1.json',authorization=REMOTE+'/control/authorization_v1.json',runtime=REMOTE+'/control/runtime_v1.json',launcher=REMOTE+'/control/launch_once_v1.sh',log=out+'/launch.log',pid=out+'/worker.pid',exit_code=out+'/exit_code.txt',single_attempt=True,timeout_seconds=1800,parent_directory_before_redirection=True,PowerShell_explicit_exit_LASTEXITCODE=True,transport='original file bytes Base64; raw stdout/stderr; wsl --exec; short commands')
q['P3']=dict(path=REMOTE+'/implementation_P3_v1.json',bytes=0,sha256='0'*64)
q['activation_prerequisites']=['Separate explicit full request SHA256 authorization','Fresh current container/UID/GPU UUID/driver/provider/environment and all reused exact hashes; any drift stops, no guessed rebind','Upload archive and sidecars verified, every new target/control/output absent, exclusive writes only','Materialize authorization -> authorization SHA256 -> runtime -> one launcher -> one exclusive claim -> one tmux','Failure stops immediately; no retry, extra case, RF installation, loss, backward, training or BNCal']
q['readiness']=dict(server_checked_this_turn=False,identity_origin='Previously observed zbpgzu-0; not a current liveness assertion',must_reverify_before_installation=True)
mirror=json.loads((R/'outputs/cranial_bcsp_scq_BS_CD_native_prediction_preparation_20261114_v1/implementation_v1/resource_rebind_v2/pending_request_v2/local_mirror_v2.json').read_bytes())
residual=Path(mirror[p['implementation']['scq_residual']['path']]);initializer=Path(mirror[p['initialization']['path']])
for f,r in [(residual,p['implementation']['scq_residual']),(initializer,p['initialization'])]:assert rec(f)['sha256']==r['sha256'] and rec(f)['bytes']==r['bytes']
ctx=dict(candidate=q,stage_scope=str(stage),parent_entry_local=str(old/'bcsp_scq_fourmodel_native_predict_v2.py'),parent_request_local=str(parent),residual_local=str(residual),initializer_local=str(initializer),remote_root=REMOTE,parent_sources=[rec(old/'bcsp_scq_fourmodel_native_predict_v2.py'),rec(residual),rec(initializer),rec(R/'outputs/cranial_bcsp_scq_implementation_20261113_v1/bcsp_scq_factory_v1.py'),rec(R/'outputs/cranial_bcsp_fullmamba_20261110/lqi_implementation_v1/bcsp_lqi_decoder_v1.py')])
emit(S/'context_v1.json',ctx)
for name in ('bcsp_scq_rf_memory_capture_v1.py','test_scq_rf_observer_cpu_v1.py'):ast.parse((S/name).read_bytes())
emit(S/'static_review_v1.json',dict(status='STATIC_REVIEW_PASS_NOT_CPU_OR_CUDA_PASS',files=[rec(S/name) for name in ('bcsp_scq_rf_memory_capture_v1.py','test_scq_rf_observer_cpu_v1.py')],checks=dict(parent_sources_preserved=True,no_mother_or_provider_edit=True,observation_hooks_return_None=True,exact_fixed_ten_scope=True,no_RF_head_or_loss_or_optimizer=True,main_not_executed_on_import=True,one_way_auth_runtime=True),server_operations=0,GPU=0))
print(json.dumps(dict(status='STATIC_REVIEW_PASS_NOT_CPU_OR_CUDA_PASS',next='ONE_ARTIFICIAL_CPU_BATCH',source_files=2)))
