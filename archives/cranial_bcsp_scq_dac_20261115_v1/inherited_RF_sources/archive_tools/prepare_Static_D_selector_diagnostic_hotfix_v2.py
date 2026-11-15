"""Only GPU selector binding and bounded startup monitor diagnostics; no model changes."""
from pathlib import Path
import ast,copy,hashlib,json
R=Path(__file__).resolve().parent.parent;B=R/'outputs/scq_rf_Static_D_implementation_20261115_v1';O=B/'selector_diagnostic_hotfix_v2';O.mkdir()
C='/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v2'
def read(p):return json.loads(p.read_bytes())
def rec(p,path=None):return dict(path=path or str(p.resolve()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def emit(p,v):
 with p.open('x',encoding='utf-8') as f:json.dump(v,f,indent=2,ensure_ascii=False,allow_nan=False)
old=B/'bcsp_scq_rf_Static_D_training_entry_v1.py';s=old.read_text(encoding='utf-8')
oldq=read(B/'pending_transport_v1/payload/SCQ_RF_Static_D_training_execution_request_v1.json');assert rec(old)['sha256']==oldq['implementation']['entry']['sha256']
helper='''def validate_gpu_environment(q,historical_environment):
    current=q['environment']
    require(set(current)==set(historical_environment),'same environment keys')
    require(historical_environment['CUDA_VISIBLE_DEVICES']==q['historical_identity']['gpu_uuid'],'historical GPU selector provenance')
    require(current['CUDA_VISIBLE_DEVICES']==q['identity']['gpu_uuid'],'current GPU selector binding')
    require(all(current[k]==v for k,v in historical_environment.items() if k!='CUDA_VISIBLE_DEVICES'),'unchanged numerical/cache environment')


def startup_smi_identity_query(helper,q,out):
    out=no_links(out)
    require(out==no_links(q['output']) and out.is_dir(),'owned startup monitor output')
    try:
        return helper.smi('uuid,name,driver_version,memory.total,memory.used')
    except helper.MonitorQueryFailure as exc:
        details=exc.details
        require(len(json.dumps(details,allow_nan=False).encode('utf-8'))<=16384,'bounded monitor diagnostic details')
        emit(out/'startup_monitor_failure.json',dict(status='FAILED_STOP_NO_RETRY',stage='startup_smi_identity',run_id=q['run_id'],current_gpu_uuid=q['identity']['gpu_uuid'],CUDA_VISIBLE_DEVICES=q['environment']['CUDA_VISIBLE_DEVICES'],details=details))
        raise


'''
s=s.replace('def validate_admission(',helper+'def validate_admission(')
s=s.replace("('model_root','preflight_scope','dependencies','environment')","('model_root','preflight_scope','dependencies')")
s=s.replace("('data_root','model_root','QC','order_plan','static_config','preflight_scope','dependencies','environment','pair_contract','initialization','resources')", "('data_root','model_root','QC','order_plan','static_config','preflight_scope','dependencies','pair_contract','initialization','resources')")
s=s.replace("('science','data_root','model_root','QC','order_plan','static_config','preflight_scope','dependencies','environment','pair_contract','initialization','rf_initialization','resources','admission')", "('science','data_root','model_root','QC','order_plan','static_config','preflight_scope','dependencies','pair_contract','initialization','rf_initialization','resources','admission')")
s=s.replace("require(q['historical_identity']==cuda['identity'],'historical CUDA identity')", "require(q['historical_identity']==cuda['identity'],'historical CUDA identity');validate_gpu_environment(q,cuda['environment'])")
s=s.replace("require(b['order_plan']==q['order_plan'],'same order record')", "validate_gpu_environment(q,reference['environment'])\n    require(b['order_plan']==q['order_plan'],'same order record')")
s=s.replace("require(model['common_initial_state_SHA256']==audit['common_initial_state_SHA256']==common,'same Requery common S state')", "validate_gpu_environment(q,reference['environment'])\n    require(model['common_initial_state_SHA256']==audit['common_initial_state_SHA256']==common,'same Requery common S state')")
s=s.replace("require(q['historical_identity']==m['historical_identity']", "require(q['environment']['CUDA_VISIBLE_DEVICES']==q['identity']['gpu_uuid'],'exact current selector')\n    require(q['historical_identity']==m['historical_identity']")
anchor="helper.smi('uuid,name,driver_version,memory.total,memory.used')[0]";assert s.count(anchor)==1
s=s.replace(anchor,'startup_smi_identity_query(helper,q,out)[0]')
entry=O/'bcsp_scq_rf_Static_D_training_entry_v2.py'
with entry.open('x',encoding='utf-8',newline='\n') as f:f.write(s)
ast.parse(s);compile(s,str(entry),'exec')
q=copy.deepcopy(oldq);q['status']='DRAFT_NOT_EXECUTABLE';q['implementation']['entry']=rec(entry,C+'/'+entry.name)
q['environment']['CUDA_VISIBLE_DEVICES']=q['identity']['gpu_uuid'];q['run_id']='SCQ_RF_Static_foldD_seed0_train_20261115_v2';q['output']='/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/'+q['run_id']
q['launch_attempt']=C+'/control/attempt_claim_v2.json'
q['launch_contract'].update(tmux_session='bcsp_scq_rf_Static_D_train_20261115_v2',request_path=C+'/SCQ_RF_Static_D_training_execution_request_v2.json',authorization_path=C+'/control/authorization_v2.json',runtime_path=C+'/control/runtime_v2.json',launcher_path=C+'/control/launch_once_v2.sh',log=q['output']+'/launch.log',PID=q['output']+'/worker.pid',exit_code=q['output']+'/exit_code.txt')
mirror=read(B/'final_local_mirror_v1.json');mirror[q['implementation']['entry']['path']]=str(entry)
ctx=read(B/'implementation_context_v1.json');ctx.update(candidate=q,mirror=mirror,parent_consumed_request=oldq)
emit(O/'implementation_context_v2.json',ctx)
emit(O/'static_review_v2.json',dict(status='SELECTOR_AND_STARTUP_DIAGNOSTIC_STATIC_PASS',entry=rec(entry),parent=rec(old),only_environment_delta='CUDA_VISIBLE_DEVICES historical UUID -> accepted current UUID',source_read_roots_unchanged="roots=[root,entryroot,envroot,provider,'/usr/lib','/proc/'+str(os.getpid()),'/dev/null','/dev/urandom']" in s,model_runtime_and_formula_unchanged=True,SMI_timeout_changed=False,query_retries_added=False,CPU_tests=0,server_operations=0))
t=(B/'test_RF_Static_D_entry_cpu_v1.py').read_text(encoding='utf-8')
t=t.replace("O=Path(__file__).resolve().parent;R=O.parents[1];D=O/'cpu_static_D_entry_batch_v1'", "O=Path(__file__).resolve().parent;R=O.parents[2];D=O/'cpu_selector_diagnostic_batch_v2'")
t=t.replace('bcsp_scq_rf_Static_D_training_entry_v1.py','bcsp_scq_rf_Static_D_training_entry_v2.py').replace("O/'implementation_context_v1.json'","O/'implementation_context_v2.json'")
t=t.replace("status='RF_STATIC_D_ENTRY_ARTIFICIAL_CPU_PASS'","status='RF_STATIC_D_SELECTOR_DIAGNOSTIC_ARTIFICIAL_CPU_PASS'")
anchor="  script=e.render_launcher(q,'a'*64,'b'*64,'c'*64)"
extra="""  bad=copy.deepcopy(q);bad['environment']['CUDA_VISIBLE_DEVICES']=q['historical_identity']['gpu_uuid'];reject('stale selector refused',lambda:authorize(bad))
  bad=copy.deepcopy(q);bad['environment']['MKL_NUM_THREADS']='999';reject('numeric environment change refused',lambda:authorize(bad))
"""
assert t.count(anchor)==1;t=t.replace(anchor,extra+anchor)
anchor="  check('POSIX launcher directory before redirect bounded length'"
start=t.index(anchor);end=t.index('\n',start)
t=t[:end]+"\n  check('launcher exports only accepted current GPU selector','export CUDA_VISIBLE_DEVICES='+q['identity']['gpu_uuid'] in script and q['historical_identity']['gpu_uuid'] not in script)"+t[end:]
anchor="  owned=F/'policy_owned';owned.mkdir();impl="
extra="""  # Execute the real inherited SMI helper functions with a fake child only.
  import os,time,threading,types
  helper_path=mirror[q['implementation']['preflight_helper']['path']];ht=ast.parse(helper_path.read_text(encoding='utf-8'))
  names={'MonitorQueryFailure','_diagnostic_bytes','_smi_once','smi'};nodes=[n for n in ht.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in names]
  constants={}
  for n in ht.body:
   if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id in {'SMI_TIMEOUT','SMI_REAP_TIMEOUT','DIAGNOSTIC_BYTES'}:constants[n.targets[0].id]=ast.literal_eval(n.value)
  assert constants==dict(SMI_TIMEOUT=10.,SMI_REAP_TIMEOUT=2.,DIAGNOSTIC_BYTES=2048)
  for mode in ['nonzero','success','timeout']:
   calls=[];events=[]
   class FakeProcess:
    pid=424242
    def __init__(self,args,**kw):self.args=args;self.returncode=None;self.communications=0;calls.append(list(args))
    def communicate(self,timeout):
     self.communications+=1;events.append(('communicate',timeout))
     if mode=='timeout' and self.communications==1:raise subprocess.TimeoutExpired(self.args,timeout,output=b'partial',stderr=b'artificial timeout stderr')
     self.returncode=9 if mode=='nonzero' else -9 if mode=='timeout' else 0
     return (b'artificial stdout' if mode!='success' else b'ARTIFICIAL_OK\\n',b'artificial GPU query stderr' if mode=='nonzero' else b'artificial timeout stderr' if mode=='timeout' else b'')
    def poll(self):return self.returncode
    def kill(self):events.append(('kill',None));self.returncode=-9
   fake_subprocess=SimpleNamespace(Popen=FakeProcess,TimeoutExpired=subprocess.TimeoutExpired)
   ns=dict(time=time,threading=threading,subprocess=fake_subprocess,os=os,_MONITOR=None,**constants)
   exec(compile(ast.Module(nodes,[]),'actual_inherited_SMI_functions','exec'),ns);mon=SimpleNamespace(smi=ns['smi'],MonitorQueryFailure=ns['MonitorQueryFailure'])
   case=copy.deepcopy(q);out=F/('startup_query_'+mode);out.mkdir();case['output']=str(out.resolve());prior=os.environ.get('CUDA_VISIBLE_DEVICES');os.environ['CUDA_VISIBLE_DEVICES']=q['identity']['gpu_uuid']
   try:
    if mode=='success':assert e.startup_smi_identity_query(mon,case,out)==['ARTIFICIAL_OK'] and not (out/'startup_monitor_failure.json').exists()
    else:
     try:e.startup_smi_identity_query(mon,case,out)
     except ns['MonitorQueryFailure']:pass
     else:raise AssertionError('failed query accepted')
     saved=json.loads((out/'startup_monitor_failure.json').read_bytes());details=saved['details']
     assert details['returncode']==(9 if mode=='nonzero' else -9) and details['stderr']['text']==('artificial GPU query stderr' if mode=='nonzero' else 'artificial timeout stderr') and details['query_attempts']==1
     assert details['status']==('NONZERO_EXIT' if mode=='nonzero' else 'TIMEOUT') and details['timeout_seconds']==10. and saved['stage']=='startup_smi_identity'
     if mode=='timeout':assert ('kill',None) in events and ('communicate',2.) in events and details['cleanup_completed']
   finally:
    if prior is None:os.environ.pop('CUDA_VISIBLE_DEVICES',None)
    else:os.environ['CUDA_VISIBLE_DEVICES']=prior
   check('real helper current selector and one query '+mode,calls==[['/usr/bin/nvidia-smi','--id='+q['identity']['gpu_uuid'],'--query-gpu=uuid,name,driver_version,memory.total,memory.used','--format=csv,noheader,nounits']])
   check('startup diagnostic persists bounded real helper outcome '+mode,len(calls)==1 and all(x[1] in (10.,2.,None) for x in events))
"""
assert t.count(anchor)==1;t=t.replace(anchor,extra+anchor)
test=O/'test_Static_D_selector_diagnostic_cpu_v2.py';ast.parse(t);compile(t,str(test),'exec')
with test.open('x',encoding='utf-8',newline='\n') as f:f.write(t)
print('STATIC_D_SELECTOR_DIAGNOSTIC_STATIC_PASS_NOT_EXECUTED')
