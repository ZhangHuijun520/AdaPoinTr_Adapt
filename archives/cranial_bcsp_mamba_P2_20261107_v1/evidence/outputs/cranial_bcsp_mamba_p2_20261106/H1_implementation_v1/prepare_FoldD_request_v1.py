"""Local Fold D request preparation only; no server, model, test or launch calls."""
import ast
import copy
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import shutil
import tarfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
P1=ROOT/'outputs/cranial_bcsp_mamba_p1_20261104'
OUT=HERE/'FoldD_request_v1'
REMOTE='/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p2_h1_foldD_20261106_v1'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def emit(p,v):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')

c_path=HERE/'first_FoldC_request_v1/transport_payload/M_H1_foldC_seed0_training_execution_request_v1.json'
assert sha(c_path)=='e5fa766a408762a9a3bf3e2bd1dc993886b3422f7afaf69f9a994dc0ca20413d'
c=read(c_path)
baseline_path=P1/'M0_FoldD_request_v1/transport_payload/M0_foldD_seed0_training_execution_request_v1.json'
baseline_audit=P1/'M0_FoldD_request_v1/post_training_freeze_audit_v1/audit_report_v1.json'
assert sha(baseline_path)=='55793bca2fa9472d45b3cca0b9598154cdb12a84a3eb89633daa52b85a039d5f'
assert sha(baseline_audit)=='f65c3dd7d82814f705a09f11f5fa95f2583fba71380cdd29cd8b9f4f59e5bb61'
b=read(baseline_path);a=read(baseline_audit)
assert a['request_sha256']==sha(baseline_path) and a['status']=='FORMAL_P1_M0_POST_TRAINING_AND_PAIR_FREEZE_AUDIT_PASS'
assert a['checks_passed']==len(a['checks']) and all(a['checks'].values())
cf_path=HERE/'post_training_freeze_audit_v1/audit_report_v1.json';cf=read(cf_path)
assert cf['status']=='FORMAL_P2_H1_FOLDC_POST_TRAINING_AND_PAIR_FREEZE_AUDIT_PASS'
assert cf['request_sha256']==sha(c_path) and cf['checks_passed']==len(cf['checks']) and all(cf['checks'].values())
p3=read(HERE/'implementation_P3_v1.json')
assert p3['status']=='LOCAL_P2_H1_IMPLEMENTATION_P3_PASS'
assert sha(HERE/'bcsp_p2_h1_training_entry_v1.py')==p3['entry_sha256']==c['implementation']['entry']['sha256']
assert sha(HERE/'bcsp_p2_h1_training_runtime_v1.py')==p3['runtime_sha256']==c['implementation']['runtime']['sha256']
tree=ast.parse((HERE/'bcsp_p2_h1_training_entry_v1.py').read_text(encoding='utf-8'))
constants={n.targets[0].id:ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='FROZEN_BASELINES'}
assert constants['FROZEN_BASELINES']['D']==dict(request_sha256=sha(baseline_path),audit_sha256=sha(baseline_audit))
assert b['fold']=='D' and b['variant']=='M0' and b['n_input']==b['n_output']==8192
assert all(c['implementation'][k]==v for k,v in b['implementation'].items() if k not in ('entry','runtime'))
assert c['identity']==b['identity'] and c['dependencies']==b['dependencies'] and c['environment']==b['environment']
config_path=HERE/'first_FoldC_request_v1/transport_payload/static_H1_training_config_v1.json'
config=read(config_path);plain=copy.deepcopy(config);h1=plain['model'].pop('coarse_geometry_guard')
base_static=ROOT/'outputs/cranial_bcsp_geov1_20261024/first_run_freeze_foldC_8192_v1/static_training_config_v1.json'
assert sha(base_static)==b['static_config']['sha256'] and plain==read(base_static)
assert h1==c['h1_config']==dict(enabled=True,mode='centroid_radius',weight=.1,smooth_l1_beta=.1,cvar_fraction=.1,eps=1e-6)
order_path=P1/'FoldD_pair_preparation_20261106_v1/shared_order_foldD_seed0_v1.json'
assert sha(order_path)==b['order_plan']['sha256']=='4f68edd55912be0dccfb3d2a1cc72e499d3d499a36aa5f3788550145b3095720'
order=read(order_path);assert len(order['epochs'])==100 and len(order['case_ids'])==len(set(order['case_ids']))==315
for e,row in enumerate(order['epochs']):
    assert row['epoch']==e and len(row['batches'])==39 and all(len(x)==8 for x in row['batches']) and len(row['dropped'])==3
    all_ids=sum(row['batches'],[])+row['dropped'];assert len(set(all_ids))==315 and set(all_ids)==set(order['case_ids'])
canonical_order=hashlib.sha256(json.dumps(order,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
assert canonical_order==a['order']['canonical_sha256']

OUT.mkdir(exist_ok=False);payload=OUT/'transport_payload';payload.mkdir()
mapping=[]
def stage(p,name):
    target=payload/name;shutil.copyfile(p,target)
    r=dict(path=REMOTE+'/'+name,bytes=target.stat().st_size,sha256=sha(target))
    mapping.append(dict(local=str(target),target=r['path'],bytes=r['bytes'],sha256=r['sha256'],write_policy='EXCLUSIVE_CREATE_NO_OVERWRITE'))
    return r

q=copy.deepcopy(b)
q.update(schema='bcsp-p2-H1-training-request-v1',status='AWAITING_EXPLICIT_USER_AUTHORIZATION',
    stage='CRANIAL_BCSP_MAMBA_P2_H1',run_id='M_H1_foldD_seed0_20261106_v1',
    output='/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2_h1/M_H1_foldD_seed0_20261106_v1',
    launch_attempt=REMOTE+'/control/single_attempt_claim_v1.json',h1_config=copy.deepcopy(h1))
for key in ('entry','runtime'):q['implementation'][key]=copy.deepcopy(c['implementation'][key])
for key in ('static_config','h1_formula','p3'):q[key]=copy.deepcopy(c[key])
q['baseline_request']=stage(baseline_path,'frozen_M0_D_request_v1.json')
q['baseline_audit']=stage(baseline_audit,'frozen_M0_D_post_training_audit_v1.json')
cf_binding=stage(cf_path,'frozen_FoldC_H1_post_training_audit_v1.json')
lc=copy.deepcopy(c['launch_contract'])
lc.update(tmux_session='bcsp_p2_H1_D_seed0_20261106_v1',authorization=REMOTE+'/control/H1_authorization_v1.json',
    runtime=REMOTE+'/control/H1_runtime_v1.json',launcher=REMOTE+'/control/H1_launch_once_v1.sh',
    log=q['output']+'/launch.log',pid=q['output']+'/worker.pid',exit_code=q['output']+'/exit_code.txt')
lc['launcher_argv_template']=['/usr/bin/timeout','--signal=TERM','--kill-after=5s','86400s',q['identity']['python_realpath'],'-I','-S','-B',q['implementation']['entry']['path'],
    '--request',REMOTE+'/M_H1_foldD_seed0_training_execution_request_v1.json','--request-sha256','<THIS_REQUEST_SHA256>',
    '--authorization',lc['authorization'],'--authorization-sha256','<AUTHORIZATION_SHA256>',
    '--runtime',lc['runtime'],'--runtime-sha256','<RUNTIME_SHA256>']
q['launch_contract']=lc
reused={k:q[k] for k in ('static_config','h1_formula','p3')}
reused.update({k:q['implementation'][k] for k in ('entry','runtime')})
q['provenance']=dict(baseline='P1 frozen M0 Fold D seed0; identical scratch initialization, no final-checkpoint resume',
    FoldC_H1_post_training_freeze_audit=cf_binding,
    same_H1_and_resources_as_FoldC=True,decision_rule='Precommitted two-fold falsification; no Fold C loss-based tuning or case selection',
    reused_exact_existing_bindings=reused,server_rechecked_this_turn=False,training_started=False,
    identity_source='Frozen M0 D identity; also matched during preceding C audit, not rechecked in this preparation task',
    readiness_required=['Current exact hostname/UID/GPU UUID and idle resources match','All reused implementation and evidence hashes match',
        'Fold D QC/order/315 training payload hashes match','All new install/control/run targets absent; parents safe','Any mismatch stops; no automatic repair/rebind'],
    expected_counts=dict(updates=3900,traversals=100,case_exposures=31200,drop_events=300),
    transport='Only four new evidence/request files; no code/data/weights duplicated')
q['not_authorized']=['Execution before separate complete request SHA256 authorization','Materialized authorization/runtime/launcher before that authorization',
    'Fold C or P1 retraining','Automatic retry/resume','Changing H1, sampling, point counts, batch order, resource thresholds or optimizer',
    'BNCal/development evaluation','New cases or protected data','Dependency download/build/install/upgrade','Final-checkpoint initialization']
assert all(q[k]==v for k,v in b.items() if k not in {'schema','stage','run_id','static_config','implementation','output','launch_attempt','launch_contract','provenance','not_authorized'})
assert set(q)==set(b)|{'baseline_request','baseline_audit','h1_formula','p3','h1_config'}
assert PurePosixPath(lc['authorization']).parent==PurePosixPath(REMOTE+'/control')
request=payload/'M_H1_foldD_seed0_training_execution_request_v1.json';emit(request,q)
mapping.append(dict(local=str(request),target=REMOTE+'/'+request.name,bytes=request.stat().st_size,sha256=sha(request),write_policy='EXCLUSIVE_CREATE_NO_OVERWRITE'))
emit(OUT/'installation_mapping_v1.json',dict(status='FROZEN_NOT_INSTALLED',remote_root=REMOTE,files=mapping,reused_exact_existing_bindings=reused,
    required_before_write='Recheck exact identity, upload bytes/hash, all reused bindings, all targets absent and safe parents',
    materials_not_created=[lc['authorization'],lc['runtime'],lc['launcher'],q['launch_attempt'],q['output']]))
review=dict(status='LOCAL_STATIC_REQUEST_REVIEW_PASS',request_sha256=sha(request),same_entry_runtime_static_H1_formula_P3_as_C=True,
    exact_D_baseline_audit_and_request_pins=True,full_D_order_structure_checked=True,updates=3900,traversals=100,exposures=31200,drops=300,
    no_C_loss_based_tuning=True,production_files_changed=0,tests_run=0,server_calls=0,controls_materialized=False,
    limits='Local static request preparation, not current server readiness or new CUDA verification')
emit(OUT/'request_static_review_v1.json',review)
archive=OUT/'bcsp_p2_H1_foldD_pending_20261106_v1.tar.gz'
members=[(p,'payload/'+p.name) for p in sorted(payload.iterdir())]+[(OUT/'installation_mapping_v1.json','installation_mapping_v1.json')]
with tarfile.open(archive,'w:gz') as t:
    for p,name in members:
        raw=p.read_bytes();info=tarfile.TarInfo(name);info.size=len(raw);info.mode=0o600;info.mtime=0;t.addfile(info,io.BytesIO(raw))
Path(str(archive)+'.sha256').write_text(sha(archive)+'  '+archive.name+'\n',encoding='ascii')
Path(str(archive)+'.bytes').write_text(str(archive.stat().st_size)+'\n',encoding='ascii')
Path(str(archive)+'.contents.sha256').write_text(''.join(sha(p)+'  '+name+'\n' for p,name in members),encoding='utf-8')
emit(OUT/'preparation_receipt_v1.json',dict(status='AWAITING_EXPLICIT_USER_AUTHORIZATION',request_path=str(request),request_sha256=sha(request),
    archive_path=str(archive),archive_sha256=sha(archive),archive_bytes=archive.stat().st_size,new_install_files=4,
    code_reused_unchanged=True,server_operations=0,tests_run=0,controls_materialized=False,training_started=False))
print(json.dumps(dict(status='AWAITING_EXPLICIT_USER_AUTHORIZATION',request_sha256=sha(request),archive_sha256=sha(archive),archive_bytes=archive.stat().st_size,new_install_files=4),indent=2))
