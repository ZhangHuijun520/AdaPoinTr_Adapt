# -*- coding: utf-8 -*-
"""One foreground-owned CPU child, bounded by the retained parent session. No retry."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
for key in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS'):os.environ[key]='2'
import hashlib,importlib.metadata,json,subprocess,sys,time
from pathlib import Path
import psutil

V=Path(__file__).resolve().parent
Q=V/'TRACE_D0_CPU_analysis_execution_request_v1.json'
EXPECTED='78952610006e441f49c0f84caf95134652dea133c0526974325cae86c038d5e9'
D=V/'authorized_execution_v1'

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(4194304),b''):h.update(b)
    return h.hexdigest()

def exact(r):
    p=Path(r['path']);assert p.is_file() and p.stat().st_size==r['bytes'] and sha(p)==r['sha256'],str(p)
    return p

def write(p,obj):
    with p.open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')

def main():
    assert sha(Q)==EXPECTED
    q=json.loads(Q.read_text(encoding='utf-8'));assert q['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION' and q['execution_authorized'] is False
    assert not D.exists() and not Path(q['output']).exists()
    exact(q['environment']['python']);assert Path(sys.executable).resolve()==Path(q['environment']['python']['path']).resolve()
    for name,version in q['environment']['packages'].items():assert importlib.metadata.version(name)==version,(name,version)
    refs=[q[k] for k in ('preparation_scope','case_manifest','trace_archive','prediction_archive','historical_scores','scoring_source','metric_source','entry','analysis_implementation','local_download_verification','implementation_P3')]+[q['trace_freeze']['evidence']]+q['reference_bindings']
    for r in refs:exact(r)
    assert len(q['input_records'])==80 and q['scientific_scope']['new_forward']==q['scientific_scope']['training']==0
    D.mkdir()
    write(D/'prelaunch_verification_v1.json',dict(status='EXACT_INPUTS_AND_CPU_ENVIRONMENT_PASS',records=len(refs),python=sys.version,packages=q['environment']['packages'],CUDA_VISIBLE_DEVICES=os.environ['CUDA_VISIBLE_DEVICES'],request_sha256=EXPECTED))
    auth=D/'TRACE_D0_CPU_analysis_authorization_v1.json'
    write(auth,dict(schema='bcsp-trace-D0-analysis-authorization-v1',request_sha256=EXPECTED,explicit_user_authorization=True,user_authorization_text='下一步单独授权该哈希后，执行唯一一次本机CPU历史重放与空间证据分析；不新增forward或训练。承接完整SHA256 '+EXPECTED))
    write(D/'single_execution_claim_v1.json',dict(status='CLAIMED_BEFORE_CHILD_START',request_sha256=EXPECTED,attempt=1))
    command=[sys.executable,'-I','-B',q['analysis_implementation']['path'],'--entry',q['entry']['path'],'--entry-sha256',q['entry']['sha256'],'--request',str(Q),'--request-sha256',EXPECTED,'--authorization',str(auth),'--authorization-sha256',sha(auth)]
    write(D/'frozen_launch_command_v1.json',dict(command=command,request_sha256=EXPECTED,limits=q['limits'],no_retry=True))
    start=time.monotonic();violation=None;peak=0;output=Path(q['output'])
    with (D/'stdout.log').open('xb') as stdout,(D/'stderr.log').open('xb') as stderr,(D/'resources.jsonl').open('x',encoding='utf-8') as journal:
        child=subprocess.Popen(command,stdout=stdout,stderr=stderr,env=dict(os.environ))
        write(D/'worker_pid_v1.json',dict(pid=child.pid,parent_pid=os.getpid()))
        print(json.dumps(dict(status='CPU_ANALYSIS_STARTED',pid=child.pid,request_sha256=EXPECTED)),flush=True)
        while True:
            elapsed=time.monotonic()-start;rss=0
            try:
                proc=psutil.Process(child.pid);rss=proc.memory_info().rss
                for sub in proc.children(recursive=True):
                    try:rss+=sub.memory_info().rss
                    except psutil.NoSuchProcess:pass
            except psutil.NoSuchProcess:pass
            size=sum(p.stat().st_size for root in (D,output) if root.exists() for p in root.rglob('*') if p.is_file())
            checks=dict(wall=elapsed<=q['limits']['wall_seconds'],RSS=rss<=q['limits']['RSS_bytes'],output=size<=q['limits']['output_bytes'])
            peak=max(peak,rss);journal.write(json.dumps(dict(elapsed_seconds=elapsed,RSS_bytes=rss,output_bytes=size,checks=checks))+'\n');journal.flush()
            if not all(checks.values()):
                violation=[k for k,v in checks.items() if not v]
                try:
                    proc=psutil.Process(child.pid)
                    for sub in proc.children(recursive=True):sub.kill()
                    proc.kill()
                except psutil.NoSuchProcess:pass
                break
            if child.poll() is not None:break
            time.sleep(1)
        rc=child.wait(timeout=10)
    write(D/'execution_exit_v1.json',dict(status='PROCESS_EXIT_ZERO_PENDING_FORMAL_FREEZE' if rc==0 and violation is None else 'FAILED_STOP_NO_RETRY',exit_code=rc,monitor_violation=violation,peak_RSS_bytes=peak,seconds=time.monotonic()-start,attempts=1,forward=0,GPU=False,training=0))
    print(json.dumps(dict(status='CPU_ANALYSIS_PROCESS_FINISHED',exit_code=rc,monitor_violation=violation)),flush=True)
    return 0 if rc==0 and violation is None else 1

if __name__=='__main__':sys.exit(main())
