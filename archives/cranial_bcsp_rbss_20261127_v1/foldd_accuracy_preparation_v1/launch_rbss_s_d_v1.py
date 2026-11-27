"""Single-attempt S_D launcher and resource monitor. Runs only after authorization."""
import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import sys
import time


def need(ok, what):
    if not ok:
        raise ValueError(what)


def exact(path, digest):
    p = Path(path)
    need(p.is_file() and p.resolve() == p, str(p))
    b = p.read_bytes()
    need(hashlib.sha256(b).hexdigest() == digest, str(p))
    return b


def gpu(i, r):
    args = [q.strip() for q in subprocess.check_output(
        ['/usr/bin/nvidia-smi', '--id='+i['gpu_uuid'],
         '--query-gpu=uuid,driver_version,memory.used,memory.free', '--format=csv,noheader,nounits'],
        text=True, timeout=r['smi_timeout_seconds']).strip().split(',')]
    need(args[:2] == [i['gpu_uuid'], i['driver_version']], 'GPU identity')
    return tuple(map(int,args[2:]))


def observe(job, out, i, r):
    used, free = gpu(i,r)
    if job.poll() is not None:
        return None
    try:
        s = Path(f'/proc/{job.pid}/status').read_text()
    except FileNotFoundError:
        if job.poll() is not None:
            return None
        raise
    line = next((x for x in s.splitlines() if x.startswith('VmRSS:')), None)
    if line is None and job.poll() is not None:
        return None
    need(line is not None, 'worker RSS unavailable')
    rss = int(line.split()[1])*1024
    disk = shutil.disk_usage(out.parent).free
    size = sum(p.stat().st_size for p in out.rglob('*') if p.is_file()) if out.exists() else 0
    need(used <= r['device_used_MiB'] and rss <= r['rss_bytes'] and disk >= r['minimum_disk_bytes']
         and size <= r['output_bytes'], f'resource limit: {used=} {rss=} {disk=} {size=}')
    return dict(gpu_used_MiB=used,gpu_free_MiB=free,RSS_bytes=rss,disk_free_bytes=disk,output_bytes=size)


def main():
    p = argparse.ArgumentParser()
    keys = ('request','request-sha256','authorization','authorization-sha256','runtime','runtime-sha256')
    for k in keys:
        p.add_argument('--'+k,required=True)
    a=vars(p.parse_args()); flags=lambda k:a[k.replace('-','_')]
    req=flags('request-sha256')
    q=json.loads(exact(flags('request'),req)); auth=json.loads(exact(flags('authorization'),flags('authorization-sha256')))
    rt=json.loads(exact(flags('runtime'),flags('runtime-sha256')))
    b=q['binding'];i=b['identity'];r=b['resources'];policy=q['launch'];out=Path(b['output'])
    need(q['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION' and q['execution_authorized'] is False
         and q['arm']=='S' and q['counts']==dict(steps=3900,epochs=100,exposures=31200,drops=300), 'S_D frozen request')
    need(auth.get('schema')=='bcsp-development-authorization-v1' and auth.get('request_sha256')==req
         and auth.get('explicit_user_authorization') is True and bool(auth.get('user_authorization_text','').strip())
         and rt==dict(schema='bcsp-development-runtime-v1',request_sha256=req,authorization_sha256=flags('authorization-sha256')),
         'authorization chain')
    need((socket.gethostname(),os.getuid(),str(Path(sys.executable).resolve()),sys.version.split()[0])==
         (i['hostname'],i['uid'],i['python_realpath'],i['python_version']), 'server identity')
    need(all(flags(k)==policy[k+'_path'] for k in ('request','authorization','runtime')), 'control paths')
    need(str(Path(__file__).resolve())==policy['launcher']['path'], 'launcher identity')
    for x in (policy['launcher'],b['interpreter'],*q['files'].values()):
        need(len(exact(x['path'],x['sha256']))==x['bytes'], x['path'])
    need(datetime.now().astimezone()<datetime.fromisoformat(policy['deadline']), 'research deadline')
    need(out.resolve()==out and out.parent.is_dir() and not os.path.lexists(out), 'new output')
    need(shutil.disk_usage(out.parent).free>=policy['matrix_disk_budget_bytes'], 'matrix disk budget')
    used,free=gpu(i,r)
    need(used<=r['idle_used_MiB'] and free>=r['minimum_start_free_MiB'], 'GPU startup reserve')
    log=Path(policy['single_attempt_log']); mon=Path(policy['resource_log'])
    need(not os.path.lexists(log) and not os.path.lexists(mon), 'attempt unused')
    env={**os.environ,'CUDA_VISIBLE_DEVICES':i['gpu_uuid']}
    argv=[sys.executable,'-I','-S','-B',q['files']['worker']['path']]
    for k in keys:
        argv.extend(('--'+k, flags(k)))
    with log.open('xb',buffering=0) as runlog, mon.open('x',encoding='ascii') as evidence:
        start=time.monotonic()
        job=subprocess.Popen(argv,env=env,stdin=subprocess.DEVNULL,stdout=runlog,stderr=runlog,start_new_session=True)
        def record(payload):
            evidence.write(json.dumps(payload)+'\n');evidence.flush()
        try:
            while job.poll() is None:
                need(time.monotonic()-start<=r['wall_seconds'] and datetime.now().astimezone()<datetime.fromisoformat(policy['deadline']), 'wall/deadline')
                sample=observe(job,out,i,r)
                if sample is not None:
                    record(dict(elapsed_seconds=time.monotonic()-start,**sample))
                try:
                    job.wait(timeout=r['monitor_interval_seconds'])
                except subprocess.TimeoutExpired:
                    pass
            need(job.returncode==0 and (out/'completion.json').is_file(), f'worker exit {job.returncode}')
            record(dict(state='WORKER_COMPLETE',exit_code=0))
        except BaseException as error:
            if job.poll() is None:
                os.killpg(job.pid,signal.SIGTERM)
                try:
                    job.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(job.pid,signal.SIGKILL)
                    job.wait()
            record(dict(state='FAILED_STOP_NO_RETRY',error=repr(error),exit_code=job.returncode))
            raise


if __name__=='__main__':
    main()
