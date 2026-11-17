"""Generate an isolated entry version and frozen regression scope; no execution."""
from pathlib import Path
import ast,json,hashlib
S=Path(__file__).resolve().parent;V=S/'binding_hotfix_v2';V.mkdir()
old=(S/'bcsp_spcg_cuda_entry_v1.py').read_text(encoding='utf-8')
extra='''
def validate_request_gpu(q):
    gpu=q['identity']['gpu_uuid']
    need(isinstance(gpu,str) and gpu.startswith('GPU-') and ',' not in gpu and gpu==q['environment']['CUDA_VISIBLE_DEVICES'],'identity/environment GPU selector mismatch')
    return gpu

def startup_query(helper,q,out):
    gpu=validate_request_gpu(q)
    need(os.environ.get('CUDA_VISIBLE_DEVICES')==gpu,'actual environment GPU selector mismatch')
    out=clean(out);need(out.is_dir(),'owned output directory')
    need(not (out/'worker.pid').exists(),'output already used')
    with (out/'worker.pid').open('x',encoding='ascii') as f:f.write(str(os.getpid()))
    command=['/usr/bin/nvidia-smi','--id='+gpu,'--query-gpu=uuid,name,driver_version,memory.total,memory.used','--format=csv,noheader,nounits']
    emit(out/'startup_query_attempt.json',dict(phase='STARTUP_SMI_BEFORE_MODEL_IMPORT',command=command,timeout_seconds=10,query_attempts=1))
    try:
        rows=helper.smi('uuid,name,driver_version,memory.total,memory.used')
    except Exception as exc:
        emit(out/'startup_failure.json',dict(status='FAILED_STOP_NO_RETRY',phase='STARTUP_SMI_BEFORE_MODEL_IMPORT',error=repr(exc),exception_type=type(exc).__name__,details=getattr(exc,'details',None),expected_command=command,counts=dict(full_forward=0,full_loss=0,full_backward=0,optimizer_steps=0)))
        raise
    emit(out/'startup_query_result.json',dict(status='OK',rows=rows))
    return [x.strip() for x in rows[0].split(',')]

'''
new=old.replace('def authorize(q,digest,a,ah,r):','def authorize(q,digest,a,ah,r):\n    validate_request_gpu(q)',1).replace('def render_launcher(q,qh,ah,rh):','def render_launcher(q,qh,ah,rh):\n    validate_request_gpu(q)',1)
line="    g=[x.strip() for x in helper.smi('uuid,name,driver_version,memory.total,memory.used')[0].split(',')]"
assert new.count(line)==1;new=new.replace(line,'    g=startup_query(helper,q,out)')
line="    need(not (out/'worker.pid').exists(),'output already used');(out/'worker.pid').write_text(str(os.getpid()),encoding='ascii')"
assert new.count(line)==1;new=new.replace(line,"    need((out/'worker.pid').read_text()==str(os.getpid()),'worker PID binding')")
new=new.replace('\ndef main():',extra+'\ndef main():',1);ast.parse(new)
p=V/'bcsp_spcg_cuda_entry_v2.py';p.write_text(new,encoding='utf-8')
q=json.loads((S/'pending_transport_v2/payload/SPCG_CUDA_execution_request_v1.json').read_text(encoding='utf-8'))
root=q['project']+'/third_party/bcsp_spcg_cuda_20261116_v2';run='SPCG_G0_G1_G2_CUDA_20261116_v2'
q['environment']['CUDA_VISIBLE_DEVICES']=q['identity']['gpu_uuid'];q['run_id']=run;q['output']=q['project']+'/logs/cranial_bcsp_fullmamba/'+run
q['entry']=dict(path=root+'/'+p.name,bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
q['P3']=dict(path=root+'/implementation_P3_v2.json',bytes=0,sha256='0'*64)
L=q['launch_contract'];L.update(tmux_session=run,request_path=root+'/SPCG_CUDA_execution_request_v2.json',authorization_path=root+'/control/authorization_v2.json',runtime_path=root+'/control/runtime_v2.json',launcher_path=root+'/control/launch_once_v2.sh',launch_attempt_path=root+'/control/launch_attempt_v2.json',log=q['output']+'/launch.log',PID=q['output']+'/worker.pid',exit_code=q['output']+'/exit_code.txt')
q['supersedes_consumed_request_sha256']='00a69c5cc3d42e04f4caa3c21650dd58db5d8c1b446741a1b42caf6730213d0f'
(V/'candidate_request_before_P3_v2.json').write_text(json.dumps(q,ensure_ascii=False,indent=2),encoding='utf-8')
scope=dict(status='FROZEN_BEFORE_SINGLE_REGRESSION',tests=['final candidate selector agrees','stale selector rejected by authorize','stale selector rejected by launcher','actual environment mismatch rejected before query','worker PID recorded before query','rich nonzero details preserved','timeout details preserved','query exception not retried','success rows preserved','one-way authorization/materialization for final candidate','new paths and unchanged11/3/3/0','only permitted original functions differ'],CPU_attempts=1,server_calls=0,GPU=0)
(V/'CPU_scope_v2.json').write_text(json.dumps(scope,indent=2),encoding='utf-8')
print('V2_STATIC_PREPARED')
