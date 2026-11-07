"""After AUX_D formal freeze, create only pending COUPLE_D bindings and transport."""
import copy,hashlib,io,json,shlex,shutil,tarfile
from pathlib import Path,PurePosixPath
S=Path(__file__).resolve().parent;P=S/'AUX_D_pending_request_v1/transport_payload';F=S/'post_training_freeze_audit_v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def bind(p):return dict(path=str(p.absolute()),bytes=p.stat().st_size,sha256=sha(p))
def emit(p,v):
 with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
aqp=P/'H2_AUX_foldD_seed0_training_execution_request_v1.json';assert sha(aqp)=='efba40fdc78db788798ba326d9a393c5e0cac48189bb507a8ec4e9fe1d5f2db9';aq=json.loads(aqp.read_bytes());ap=F/'audit_report_v1.json';a=json.loads(ap.read_bytes());assert a['status']=='FORMAL_H2_AUX_FOLDD_POST_TRAINING_FREEZE_AUDIT_PASS' and a['request_sha256']==sha(aqp) and a['checks_passed']==25 and all(a['checks'].values())
entry=S/'bcsp_h2_foldD_training_entry_v1.py';p3=json.loads((S/'implementation_P3_v1.json').read_bytes());assert sha(entry)==aq['implementation']['entry']['sha256']==p3['entry_sha256'] and p3['status']=='LOCAL_H2_FOLDD_TRAINING_ENTRY_P3_PASS' and p3['CPU_contracts']==33
for k,n in [('h2_range','bcsp_h2_range_v1.py'),('h2_adapter','bcsp_h2_model_adapter_v1.py'),('runtime','bcsp_h2_training_runtime_v1.py')]:assert sha(S.parent/'H2_implementation_v1'/n)==aq['implementation'][k]['sha256']==p3['H2_source_hashes'][k]
initial=F/'downloads/initialization.json';assert json.loads(initial.read_bytes())==a['initialization']['record']
O=S/'COUPLE_D_pending_request_v1';O.mkdir();T=O/'transport_payload';T.mkdir();remote='/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p2_H2_COUPLE_foldD_20261107_v1';output='/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2/H2_COUPLE_foldD_seed0_20261107_v1';mapping=[]
def stage(p,name=None):
 n=name or p.name;t=T/n;shutil.copyfile(p,t);r=dict(path=str(PurePosixPath(remote)/n),bytes=t.stat().st_size,sha256=sha(t));mapping.append(dict(local=str(t.absolute()),target=r['path'],bytes=r['bytes'],sha256=r['sha256'],write_policy='EXCLUSIVE_CREATE_NO_OVERWRITE'));return r
q=copy.deepcopy(aq);q.update(run_id='H2_COUPLE_foldD_seed0_20261107_v1',output=output,launch_attempt=remote+'/control/COUPLE_D_single_attempt_claim_v1.json',h2_config=dict(aq['h2_config'],mode='COUPLE'))
static=json.loads((P/'static_H2_AUX_foldD_training_config_v1.json').read_bytes());static['H2']['mode']='COUPLE';emit(O/'static_H2_COUPLE_foldD_training_config_v1.json',static);q['static_config']=stage(O/'static_H2_COUPLE_foldD_training_config_v1.json')
q['aux_pairing']=dict(request=dict(path=aq['launch_contract']['request_path'],bytes=aqp.stat().st_size,sha256=sha(aqp)),audit=stage(ap,'frozen_H2_AUX_D_post_training_audit_v1.json'),initialization=dict(path=aq['output']+'/initialization.json',bytes=initial.stat().st_size,sha256=sha(initial)))
lc=dict(tmux_session='bcsp_p2_H2_COUPLE_D_seed0_20261107_v1',authorization=remote+'/control/COUPLE_D_authorization_v1.json',runtime=remote+'/control/COUPLE_D_runtime_v1.json',launcher=remote+'/control/COUPLE_D_launch_once_v1.sh',request_path=remote+'/H2_COUPLE_foldD_seed0_training_execution_request_v1.json',log=output+'/launch.log',pid=output+'/worker.pid',exit_code=output+'/exit_code.txt',single_attempt=True,timeout_seconds=86400,materialization_order='authorization -> hash -> runtime -> hash -> launcher; exclusive claim before unique tmux',parent_directory_before_redirection=True,PowerShell_explicit_exit_LASTEXITCODE=True)
q['provenance']=dict(baseline='Frozen AUX_D pairing; original M0 D scratch initialization plus same zero H2 head, not AUX final checkpoint',only_scientific_delta_from_AUX='H2 mode COUPLE applies fixed bounded detached-delta radius scaling through all original coarse consumers',same_D_entry_and_H2_modules=True,AUX_D_formal_audit_sha256=sha(ap),AUX_D_initialization_sha256=sha(initial),no_loss_or_development_based_tuning=True,no_new_GPU_preflight=True,current_server_rechecked_for_this_request=False,readiness_snapshot_semantics='Inherited D snapshot, not new resource reservation or new-target absence proof',resource_policy=aq['provenance']['resource_policy'],numeric_policy=aq['provenance']['numeric_policy'],required_before_materialization=['Exact current hostname/UID/GPU/Python and idle GPU; disk meets frozen minimum','Uploaded archive/map hashes match; all new install/control/run targets absent and safe real parents','All reused entry/H2/provider/environment/metadata and315 D training file hashes match','Frozen AUX_D request, audit and initial fingerprints match; initial COUPLE full state must equal AUX_D','Original thresholds and scientific constants unchanged; fail stop, no auto retry/resume'],local_P3_reused=True,training_started=False)
q['not_authorized']=['Execution before separate full request SHA256 authorization','Automatic retry/resume','Other fold/mode/seed','BNCal/development evaluation','Data/sampling/point-count/order/3900-step/threshold changes','Loss-based tuning/case selection','Dependency download/build/install/upgrade','Final checkpoint initialization','Materializing authorized controls while pending']
args=['/usr/bin/timeout','--signal=TERM','--kill-after=5s','86400s',q['identity']['python_realpath'],'-I','-S','-B',q['implementation']['entry']['path'],'--request',lc['request_path'],'--request-sha256','REQUEST_SHA256','--authorization',lc['authorization'],'--authorization-sha256','AUTHORIZATION_SHA256','--runtime',lc['runtime'],'--runtime-sha256','RUNTIME_SHA256']
out=PurePosixPath(output);lines=['#!/bin/bash','set -u','umask 077','cd '+shlex.quote(q['identity']['project'])+' || exit 120']
for p in reversed((out,*out.parents)):
 if str(p)!='/':lines.append('[ ! -L '+shlex.quote(str(p))+' ] || exit 121')
lines+=['mkdir -p -- '+shlex.quote(str(out.parent))+' || exit 122','mkdir -- '+shlex.quote(output)+' || exit 123','exec >>'+shlex.quote(lc['log'])+' 2>&1','env '+chr(92)]
for k,v in q['environment'].items():lines.append(shlex.quote(k+'='+v.replace('<owned_output>',output))+' '+chr(92))
lines+=[' '+(' '+chr(92)+'\n ').join(map(shlex.quote,args)),'result=$?','printf "%s\\n" "$result" > '+shlex.quote(lc['exit_code']),'exit "$result"']
tpl=O/'COUPLE_D_launch_once_template_v1.sh'
with tpl.open('x',encoding='utf-8',newline='\n') as f:f.write('\n'.join(lines)+'\n')
assert max(map(len,tpl.read_text().splitlines()))<=2048;lc['launcher_template']=stage(tpl);q['launch_contract']=lc
assert set(q)==set(aq) and q['implementation']==aq['implementation'] and all(q[k]==aq[k] for k in ['identity','environment','QC','order_plan','data_root','model_root','initialization_reference','numeric_policy','numeric_protocol','pair_contract','dependencies','n_input','n_output','fold','variant','p3','readiness','baseline_request','baseline_audit','cuda_audit'])
auxstatic=json.loads((P/'static_H2_AUX_foldD_training_config_v1.json').read_bytes());assert dict(static,H2=dict(q['h2_config'],mode='AUX'))==auxstatic
request=T/'H2_COUPLE_foldD_seed0_training_execution_request_v1.json';emit(request,q);mapping.append(dict(local=str(request.absolute()),target=lc['request_path'],bytes=request.stat().st_size,sha256=sha(request),write_policy='EXCLUSIVE_CREATE_NO_OVERWRITE'))
emit(O/'installation_mapping_v1.json',dict(status='FROZEN_NOT_INSTALLED_READINESS_RECHECK_REQUIRED',remote_root=remote,files=mapping,reused_implementation=q['implementation'],reused_evidence={k:q[k] for k in ['p3','readiness','baseline_request','baseline_audit','cuda_audit']},reused_data_root=q['data_root'],aux_pairing=q['aux_pairing'],materials_not_created=[lc['authorization'],lc['runtime'],lc['launcher'],q['launch_attempt'],output],required_before_write=q['provenance']['required_before_materialization']))
archive=O/'bcsp_p2_H2_COUPLE_foldD_pending_20261107_v1.tar.gz';members=[(p,'payload/'+p.name) for p in sorted(T.iterdir())]+[(O/'installation_mapping_v1.json','installation_mapping_v1.json')]
with tarfile.open(archive,'w:gz') as tar:
 for p,n in members:
  b=p.read_bytes();info=tarfile.TarInfo(n);info.size=len(b);info.mode=0o600;info.mtime=0;tar.addfile(info,io.BytesIO(b))
with tarfile.open(archive,'r:gz') as tar:
 assert len(tar.getmembers())==len(members)
 for p,n in members:assert tar.extractfile(n).read()==p.read_bytes()
for suffix,text in [('.sha256',sha(archive)+'  '+archive.name+'\n'),('.bytes',str(archive.stat().st_size)+'\n'),('.contents.sha256',''.join(sha(p)+'  '+n+'\n' for p,n in members))]:
 with Path(str(archive)+suffix).open('x',encoding='ascii',newline='\n') as f:f.write(text)
flat=tpl.read_text().replace(chr(92)+'\n',' ');tokens=shlex.split(next(x for x in flat.splitlines() if x.startswith('env ')));assert tokens[tokens.index('--request')+1]==lc['request_path']
receipt=dict(status='AWAITING_EXPLICIT_USER_AUTHORIZATION',request=bind(request),archive=bind(archive),installation_files=len(mapping),existing_entry_and_P3_reused=True,AUX_D_formal_audit=bind(ap),AUX_D_initialization=bind(initial),scientific_config_only_mode_delta=True,new_tests=0,server_operations=0,training_started=False)
emit(O/'pending_request_receipt_v1.json',receipt);print(json.dumps(receipt,ensure_ascii=False,indent=2))
