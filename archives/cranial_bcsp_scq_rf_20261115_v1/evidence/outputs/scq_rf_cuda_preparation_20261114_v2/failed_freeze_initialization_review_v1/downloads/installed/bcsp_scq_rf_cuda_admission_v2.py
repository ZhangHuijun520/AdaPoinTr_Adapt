"""RF five synthetic CUDA forwards, four original losses/backwards, zero steps; import is stdlib-only."""
import argparse

import ast

import contextlib

import gc

import hashlib

import importlib.util

import json

import os

from pathlib import Path, PurePosixPath

import random

import shlex

import signal

import socket

import sys

import threading

import time

def need(ok, message):
    if not ok:
        raise RuntimeError(message)

def clean(path):
    p = Path(path).absolute()
    need(not any(x.is_symlink() for x in (p, *p.parents)), 'linked path: '+str(p))
    need(not {'.ssh', '.aws', '.credentials', '.git'} & set(p.parts)
         and p.name not in ('.env', '.netrc', 'auth.json'), 'secret path')
    return p

def sha(path):
    h = hashlib.sha256()
    with clean(path).open('rb') as f:
        for b in iter(lambda: f.read(1048576), b''):
            h.update(b)
    return h.hexdigest()

def exact(record):
    p = clean(record['path'])
    need(p.is_file() and p.stat().st_size == record['bytes']
         and sha(p) == record['sha256'], 'binding: '+str(p))
    return p

def emit(path, value):
    with clean(path).open('x', encoding='ascii') as f:
        json.dump(value, f, indent=2, allow_nan=False)

def source_module(name, record):
    need(name not in sys.modules, 'preloaded module: '+name)
    p = exact(record)
    spec = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    exec(compile(p.read_bytes(), str(p), 'exec', dont_inherit=True), m.__dict__)
    return m

def counters():
    return dict(full_forward=0, full_backward=0, full_loss=0,
                decoder_forward=0, decoder_backward=0, optimizer_steps=0)

def render_launcher(q, request_sha, authorization_sha, runtime_sha):
    """Render only after authorization; callers must preserve these original UTF-8 bytes."""
    for value in (request_sha, authorization_sha, runtime_sha):
        need(len(value) == 64 and all(c in '0123456789abcdef' for c in value), 'full lowercase hash')
    L = q['launch_contract']; out = PurePosixPath(q['output'])
    command = ['/usr/bin/timeout', '--signal=TERM', '--kill-after=10s',
               str(q['limits']['wall_seconds'])+'s', q['identity']['python_realpath'], '-I', '-S', '-B',
               q['entry']['path'], '--request', L['request_path'], '--request-sha256', request_sha,
               '--authorization', L['authorization_path'], '--authorization-sha256', authorization_sha,
               '--runtime', L['runtime_path'], '--runtime-sha256', runtime_sha]
    env = '\n'.join('export '+k+'='+shlex.quote(v.replace('<owned_output>', str(out)))
                    for k, v in q['environment'].items())
    link_checks = ''.join('[ ! -L '+shlex.quote(str(p))+' ] || exit 121\n'
                          for p in reversed((out, *out.parents)) if str(p) != '/')
    script = ('#!/bin/bash\nset -eu\numask 077\ncd '+shlex.quote(q['project'])+'\n'+link_checks+
            'mkdir -p '+shlex.quote(str(out.parent))+'\nmkdir '+shlex.quote(str(out))+'\n'+env+
            '\nset +e\n'+shlex.join(command)+' >'+shlex.quote(str(out/'launch.log'))+' 2>&1\n'
            'rc=$?\nset -e\nprintf "%s\\n" "$rc" >'+shlex.quote(str(out/'exit_code.txt'))+'\nexit "$rc"\n')
    need(max(len(line.encode()) for line in script.splitlines()) <= 2048, 'launcher line bound')
    return script

def claim(c, key, event):
    need(key != 'optimizer_steps' and c[key] < SCIENCE[key], 'call cap: '+key)
    c[key] += 1
    event(dict(kind='ATTEMPT_BEFORE_CALL', operation=key, counts=dict(c)))

def compare(torch, a, b):
    d = (a.detach()-b.detach()).abs()
    return dict(max_abs=float(d.max()), close=bool(torch.allclose(
        a.detach(), b.detach(), atol=TOLERANCE['atol'], rtol=TOLERANCE['rtol'])))

def gradients(torch, model, prefixes):
    norms = {}
    for n, p in model.named_parameters():
        if p.grad is not None:
            need(bool(torch.isfinite(p.grad).all()), 'nonfinite gradient: '+n)
            norms[n] = float(p.grad.detach().double().norm())
    totals = {prefix: sum(v for n, v in norms.items() if n.startswith(prefix)) for prefix in prefixes}
    need(all(v > 0 for v in totals.values()), 'inactive gradient modules: '+repr(totals))
    return dict(parameter_norms=norms, module_norm_sums=totals)
SCIENCE=dict(full_forward=5,full_backward=4,full_loss=4,decoder_forward=0,decoder_backward=0,optimizer_steps=0,real_data_reads=0,checkpoint_loads=0,input_points=8192,output_points=8192,full_batches=[1,1,1,8,8])
PHASES=[('S_ref_eval1','S-ref',1,False),('Static_eval1','RF-Static',1,False),('Requery_eval1','RF-Requery',1,False),('Static_train8','RF-Static',8,True),('Requery_train8','RF-Requery',8,True)]
TOLERANCE=dict(atol=1e-6,rtol=1e-5)
LIMITS=dict(wall_seconds=1800,RSS_bytes=8589934592,torch_peak_bytes=21474836480,device_MiB=22528,output_bytes=1073741824,minimum_free_disk_bytes=4294967296)
FIXTURE=dict(input_seed=20261110,target_seed=20261112,distribution='NumPy_default_rng_uniform_minus0.5_plus0.5',shape=[8,8192,3],dtype='float32')

def authorize(q,digest,auth,auth_digest,runtime):
    need(q['schema']=='bcsp-scq-rf-artificial-cuda-v1' and q['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION' and q['execution_authorized'] is False,'pending request')
    need(q['science']==SCIENCE and q['phases']==[list(p) for p in PHASES] and q['limits']==LIMITS and q['fixture']==FIXTURE and q['tolerances']==TOLERANCE,'frozen5F4loss4B0step')
    need(q['readiness']['fresh_reverification_required'] is True,'fresh readiness required')
    need(set(auth)=={'schema','request_sha256','explicit_user_authorization','user_authorization_text'} and auth['schema']=='bcsp-scq-rf-cuda-authorization-v1' and auth['request_sha256']==digest and auth['explicit_user_authorization'] is True and bool(auth['user_authorization_text'].strip()),'separate full hash authorization')
    need(runtime==dict(schema='bcsp-scq-rf-cuda-runtime-v1',request_sha256=digest,authorization_sha256=auth_digest),'one-way runtime')
    return q

class ExactSCQReads:
    """Three new exact read-only files; all other decisions delegated to inherited guard."""
    def __init__(self,base,records):
        self.base=base;self.records={};self.fds={}
        try:
            for r in records:
                p=exact(r);fd=os.open(p,os.O_RDONLY|getattr(os,'O_NOFOLLOW',0)|getattr(os,'O_BINARY',0));self.records[p]=r;self.fds[p]=fd;self.verify(p)
        except BaseException:self.close();raise
    def verify(self,p):
        r=self.records[p];fd=self.fds[p];before=p.stat();opened=os.fstat(fd)
        need((before.st_dev,before.st_ino,before.st_size)==(opened.st_dev,opened.st_ino,r['bytes']),'SCQ file identity')
        os.lseek(fd,0,os.SEEK_SET);parts=[];remaining=r['bytes']+1
        while remaining:
            chunk=os.read(fd,min(remaining,1048576))
            if not chunk:break
            parts.append(chunk);remaining-=len(chunk)
        data=b''.join(parts)
        need(len(data)==r['bytes'] and hashlib.sha256(data).hexdigest()==r['sha256'],'SCQ exact content')
        after=p.stat();need((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns),'SCQ changed during read')
    def allow(self,filename,write=False):
        if not isinstance(filename,int):
            p=clean(os.fsdecode(filename))
            if p in self.records:
                need(not write,'SCQ bound write denied');self.verify(p);return True
        return self.base.allow(filename,write)
    def close(self):
        for fd in self.fds.values():os.close(fd)
        self.fds.clear();self.base.close()

def gradient_prefixes():
    return ['base_model.coarse_pred.','base_model.decoder.coordinate_pe.','reduce_map.','increase_dim.','decode_head.']+['base_model.encoder.blocks.blocks.'+str(i)+'.attn.mixer.' for i in range(6)]+['base_model.decoder.blocks.'+str(i)+'.'+s+'.' for i in range(8) for s in ('self_ssm','cond_ssm')]+['base_model.decoder.blocks.'+str(i)+'.norm_v.' for i in range(8)]

def check_coordinate_consumers(torch,consumers,coarse,dense,event,label):
    """Observe both PE roles, persist all decisions, then assert exact contracts."""
    required=dict(query=1,decoder=1,Memory=1,PE=2,rebuild=1,relative=1)
    calls={k:len(v) for k,v in consumers.items()}
    def snapshot(name,index=0):
        values=consumers.get(name,[])
        return values[index] if len(values)>index else None
    def compare(name,value,expected):
        present=value is not None and expected is not None
        same_shape=present and value.shape==expected.shape
        finite=present and bool(torch.isfinite(value).all()) and bool(torch.isfinite(expected).all())
        exact=bool(same_shape and finite and value.dtype==expected.dtype and value.device==expected.device and torch.equal(value,expected))
        return dict(role=name,present=present,actual_shape=None if value is None else list(value.shape),
                    expected_shape=None if expected is None else list(expected.shape),
                    dtype=None if value is None else str(value.dtype),device=None if value is None else str(value.device),
                    finite=bool(finite),exact_equal=exact,
                    max_abs=float((value-expected).abs().max()) if same_shape and finite and value.device==expected.device else None)
    rows=[compare('query_MLP',snapshot('query'),coarse),compare('decoder_query',snapshot('decoder'),coarse),
          compare('PE_query_first',snapshot('PE',0),coarse),compare('PE_Memory_second',snapshot('PE',1),snapshot('Memory')),
          compare('FC_rebuild',snapshot('rebuild'),coarse)]
    relative=snapshot('relative')
    valid_relative=relative is not None and tuple(relative.shape)==(coarse.shape[0],256,32,3)
    center=(relative+coarse.detach()[:,:,None]).reshape(coarse.shape[0],8192,3) if valid_relative else None
    rows.append(compare('dense_center',dense.detach(),center))
    record=dict(kind='COORDINATE_CONSUMERS_BEFORE_ASSERTIONS',phase=label,call_counts=calls,expected_call_counts=required,
                exact_call_contract=calls==required,relative_shape=None if relative is None else list(relative.shape),comparisons=rows)
    event(record)
    need(calls==required,'actual coordinate consumer call count/role mismatch')
    need(all(row['exact_equal'] for row in rows),'actual coordinate consumer value mismatch')
    return record


def phase_checks(torch,np,model,helper,parent,x,target,phase,reference,counts,event,sample):
    label,variant,batch,training=phase
    initial={n:v.detach().cpu().clone() for n,v in model.state_dict().items()}
    before=helper.state_sha(model);weights=helper.state_sha(model,parameters_only=True)
    rng=(random.getstate(),np.random.get_state(),torch.get_rng_state().clone(),torch.cuda.get_rng_state(0).clone())
    rng_record=parent.rng_state(torch,np,helper,True);modes=[m.training for m in model.modules()]
    bn=[(m,m.momentum) for m in model.modules() if isinstance(m,torch.nn.modules.batchnorm._BatchNorm)]
    baseline=None;ret=None;hooks=[];consumers={}
    try:
        model.train(training)
        for m,_ in bn:
            need(m.track_running_stats,'BN tracking')
            if training:m.momentum=.9
        b=model.base_model
        def remember(name,value):
            consumers.setdefault(name,[]).append(value.detach().clone())
        def decoder_inputs(m,args,kw):
            remember('decoder',kw['q_pos']);remember('Memory',kw['v_pos'])
        hooks=[b.mlp_query.register_forward_pre_hook(lambda m,a:remember('query',a[0][...,-3:])),
               b.decoder.register_forward_pre_hook(decoder_inputs,with_kwargs=True),
               b.decoder.coordinate_pe.register_forward_pre_hook(lambda m,a:remember('PE',a[0])),
               model.reduce_map.register_forward_pre_hook(lambda m,a:remember('rebuild',a[0][...,-3:])),
               model.decode_head.register_forward_hook(lambda m,a,v:remember('relative',v))]
        sample(label+':before',counts['full_forward']);claim(counts,'full_forward',event)
        with torch.set_grad_enabled(variant!='S-ref'):
            ret=model(x[:batch]);need(len(ret)==(4 if training else 2),'original return tuple')
            coarse,dense=ret[0],ret[-1]
            need(coarse.shape==(batch,256,3) and dense.shape==(batch,8192,3) and all(t.dtype==torch.float32 and bool(torch.isfinite(t).all()) for t in (coarse,dense)),'finite full output')
            consumer_record=check_coordinate_consumers(torch,consumers,coarse,dense,event,label)
            info=b._scq_last_info
            need(torch.equal(info['Q0'],info['Qused']) and torch.count_nonzero(info['delta'])==0 and torch.equal(coarse,info['Qused']),'zero initial identity')
            equivalence=None;loss=None;grad=None;head_grad=None
            if variant=='S-ref':
                baseline=(coarse.detach().cpu().clone(),dense.detach().cpu().clone())
                need(not training,'S reference forward only')
            else:
                need(torch.equal(info['Q1'],coarse) and torch.count_nonzero(info['delta0'])==0 and torch.count_nonzero(info['delta1'])==0,'both zero initialized heads')
                if not training:
                    need(reference is not None,'same-session S reference required')
                    equivalence=[compare(torch,t.detach().cpu(),r) for t,r in zip((coarse,dense),reference)]
                    need(all(r['close'] for r in equivalence),'RF initial Native equivalence')
                coarse.retain_grad();claim(counts,'full_loss',event)
                loss_ret=ret if training else (coarse,coarse[:,:0],dense[:,:0],dense)
                denoise,recon=model.get_loss(loss_ret,target[:batch],epoch=0,partial=x[:batch]);loss=denoise+recon
                need(float(denoise.detach())==0 and loss.ndim==0 and bool(torch.isfinite(loss)) and loss.requires_grad,'original full loss')
                sample(label+':before_backward',counts['full_forward']);claim(counts,'full_backward',event);loss.backward()
        torch.cuda.synchronize()
        if variant!='S-ref':
            grad=gradients(torch,model,gradient_prefixes())
            head_grad={}
            for key,head,hidden,last in [('scq',b.scq,'W1','W2'),('rf',b.rf,'V1','V2')]:
                rows={n:dict(present=p.grad is not None,finite=p.grad is not None and bool(torch.isfinite(p.grad).all()),norm=float(p.grad.detach().double().norm()) if p.grad is not None and bool(torch.isfinite(p.grad).all()) else None) for n,p in head.named_parameters()}
                head_grad[key]=rows
            qgrad=dict(present=coarse.grad is not None,finite=coarse.grad is not None and bool(torch.isfinite(coarse.grad).all()),norm=float(coarse.grad.detach().double().norm()) if coarse.grad is not None and bool(torch.isfinite(coarse.grad).all()) else None)
            event(dict(kind='HEAD_GRADIENTS_BEFORE_ASSERTIONS',phase=label,heads=head_grad,Q2=qgrad))
            need(qgrad['finite'] and qgrad['norm']>0,'Q2 gradient')
            for key,hidden,last in [('scq','W1','W2'),('rf','V1','V2')]:
                rows=head_grad[key]
                need(all(v['present'] and v['finite'] for v in rows.values()),key+' finite gradients')
                need(rows[last+'.weight']['norm']>0 and rows[last+'.bias']['norm']>0 and rows[hidden+'.weight']['norm']==rows[hidden+'.bias']['norm']==0,key+' initial zero-head gradient contract')
        need(helper.state_sha(model,parameters_only=True)==weights,'parameters changed')
        changes=[n for n,t in model.state_dict().items() if not torch.equal(t.detach().cpu(),initial[n])]
        need(all(n.endswith(('running_mean','running_var','num_batches_tracked')) for n in changes),'non-BN state drift')
        need(bool(changes) if training else not changes,'BN mode contract')
        after_rng=parent.rng_state(torch,np,helper,True);need(training or after_rng==rng_record,'eval RNG drift')
        record=dict(phase=label,variant=variant,batch=batch,loss=None if loss is None else float(loss.detach()),initial_equivalence=equivalence,gradients=grad,head_gradients=head_grad,actual_Q2_consumers=True,coordinate_consumers=consumer_record,BN_changed=changes,parameters_unchanged=True,RNG_before=rng_record,RNG_after=after_rng)
        event(record)
    finally:
        for handle in hooks:handle.remove()
        model.load_state_dict(initial,strict=True);model.zero_grad(set_to_none=True)
        random.setstate(rng[0]);np.random.set_state(rng[1]);torch.set_rng_state(rng[2]);torch.cuda.set_rng_state(rng[3],0)
        for m,momentum in bn:m.momentum=momentum
        for m,training_mode in zip(model.modules(),modes):m.training=training_mode
        model.base_model._scq_last_info=None
        restored=dict(kind='PHASE_RESTORATION',phase=label,state_restored=helper.state_sha(model)==before,RNG_restored=parent.rng_state(torch,np,helper,True)==rng_record,modes_restored=[m.training for m in model.modules()]==modes,BN_momenta_restored=all(m.momentum==momentum for m,momentum in bn),gradients_cleared=all(p.grad is None for p in model.parameters()))
        event(restored);need(all(v for k,v in restored.items() if k not in ('kind','phase')),'restoration failure')
    sample(label+':restored',counts['full_forward'])
    return record,baseline

def main():
    parser=argparse.ArgumentParser()
    for key in ('request','request-sha256','authorization','authorization-sha256','runtime','runtime-sha256'):parser.add_argument('--'+key,required=True)
    args=vars(parser.parse_args())
    def record(key):
        p=clean(args[key]);return dict(path=str(p),bytes=p.stat().st_size,sha256=args[key+'_sha256'])
    qr,ar,rr=(record(k) for k in ('request','authorization','runtime'))
    q=authorize(json.loads(exact(qr).read_bytes()),qr['sha256'],json.loads(exact(ar).read_bytes()),ar['sha256'],json.loads(exact(rr).read_bytes()))
    need(sys.platform=='linux' and sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode,'isolated Linux')
    I=q['identity'];out=clean(q['output']);root=clean(q['model_root'])
    need(socket.gethostname()==I['hostname'] and os.getuid()==I['uid'] and str(Path(sys.executable).resolve())==I['python_realpath'] and sys.version.split()[0]==I['python_version'],'identity')
    need(Path.cwd().resolve()==Path(q['project']) and out.parent==Path(q['project'])/'logs/cranial_bcsp_fullmamba','cwd and output root')
    cmd=Path('/proc/'+str(os.getppid())+'/cmdline').read_bytes().decode().rstrip('\0').split('\0')
    need(cmd[:4]==['/usr/bin/timeout','--signal=TERM','--kill-after=10s','1800s'],'external timeout')
    need(json.loads(clean(q['launch_contract']['launch_attempt_path']).read_bytes())==dict(status='CLAIMED_BEFORE_TMUX',request_sha256=qr['sha256']),'single claim')
    for k,v in q['environment'].items():need(os.environ.get(k)==v.replace('<owned_output>',str(out)),'environment '+k)
    exact(q['entry']);p3=json.loads(exact(q['entry_P3']).read_bytes())
    need(p3['status']=='RF_CUDA_ENTRY_LOCAL_P3_PASS' and p3['entry_sha256']==q['entry']['sha256'],'entry P3')
    ip3=json.loads(exact(q['implementation_P3']).read_bytes());need(ip3['status']=='LOCAL_RF_IMPLEMENTATION_P3_PASS_ARTIFICIAL_CPU_ONLY' and ip3['CPU_checks']==59,'implementation P3')
    for r in q['dependencies']+list(q['implementation'].values())+[q['initialization'],q['rf_initialization'],q['optimizer_policy']]:exact(r)
    helper=source_module('scq_inherited_preflight_helper',q['helper']);helper._MONITOR=None
    parent=source_module('scq_inherited_native_helpers',q['parent_helper'])
    timezone=source_module('scq_exact_utc',q['implementation']['timezone'])
    need(timezone.UTC_RESOURCE==q['timezone_resource'],'UTC binding')
    scope=json.loads(exact(q['preflight_scope']).read_bytes());static=json.loads(exact(q['static_config']).read_bytes())
    sources=helper.source_map(scope)
    for rel,r in sources.items():helper.exact(root/rel,r['sha256'],r['bytes'])
    helper.exact(root/'base_model.yaml',scope['bindings']['base_config']['sha256'])
    for r in scope['bindings']['provider']+scope['bindings']['environment_metadata']:helper.exact(r['path'],r['sha256'],r['bytes'])
    gpu=[s.strip() for s in helper.smi('uuid,name,driver_version,memory.total,memory.used')[0].split(',')]
    need(gpu[:4]==[I['gpu_uuid'],I['gpu_name'],I['driver_version'],str(I['nvidia_smi_memory_total_MiB'])] and int(gpu[4])<=256,'exact idle GPU')
    helper.claim_output(out)
    for n in ('tmp','cache','mplconfig','triton_cache','hf_cache'):(out/n).mkdir()
    journal=out/'events.jsonl';journal.open('x').close()
    def event(value):
        with journal.open('a',encoding='ascii') as f:f.write(json.dumps(value,allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())
    counts=counters();stop=threading.Event();watcher=None
    utc=timezone.ExactUTCReader(q['timezone_resource'])
    base=parent.ExactSourceReads(q['implementation'])
    guard=ExactSCQReads(base,[q['implementation'][k] for k in ('scq_residual','scq_factory','rf_residual','rf_factory')]+[q['initialization'],q['rf_initialization'],q['optimizer_policy']])
    try:
        envroot=Path('/opt/conda/envs/adapointr-mamba');provider=Path(scope['bindings']['provider'][0]['path']).parent.parent
        sys.path[:0]=[str(Path(__file__).parent),str(provider),str(envroot/'lib/python3.10/site-packages')]
        helper.namespace_packages(root);sys.meta_path.insert(0,helper.FiniteProjectImports(root,sources))
        policy=parent.make_policy(helper,[root,envroot,provider,Path(__file__).parent,'/usr/lib','/proc/'+str(os.getpid()),'/dev/null','/dev/urandom'],out,[],[],[],utc,guard)
        sys.addaudithook(policy.audit)
        import numpy as np
        import torch,timm,yaml,importlib
        from easydict import EasyDict
        need((torch.__version__,np.__version__,timm.__version__)==(I['torch_version'],I['numpy_version'],I['timm_version']),'versions')
        need(torch.cuda.is_available() and torch.cuda.device_count()==1 and torch.version.cuda==I['torch_cuda_version'],'one CUDA device')
        torch.cuda.set_device(0);helper.configure_numeric(torch)
        chamfer=importlib.import_module('extensions.chamfer_dist');pn=importlib.import_module('utils.pointnet2_utils');pm=importlib.import_module('pointnet2_ops.pointnet2_utils');ext=importlib.import_module('pointnet2_ops._ext')
        helper.check_backend(chamfer,pn,pm)
        need(str(Path(pm.__file__).resolve())==scope['bindings']['provider'][1]['path'] and str(Path(ext.__file__).resolve())==scope['bindings']['provider'][2]['path'],'provider origins')
        transformer=importlib.import_module('models.Transformer_utils');cls=importlib.import_module('models.AdaPoinTr').AdaPoinTr
        need(static['model']==yaml.safe_load((root/'base_model.yaml').read_text())['model'],'config');transformer.enable_bcsp_knn()
        for name,key in [('bcsp_mamba_encoder_v1','encoder'),('bcsp_p1_model_factory_v1','factory'),('bcsp_lqi_decoder_v1','lqi_decoder'),('bcsp_lqi_factory_v1','lqi_factory'),('bcsp_scq_residual_v1','scq_residual')]:source_module(name,q['implementation'][key])
        scq_factory=source_module('bcsp_scq_factory_v1',q['implementation']['scq_factory'])
        source_module('bcsp_scq_rf_residual_v1',q['implementation']['rf_residual'])
        factory=source_module('bcsp_scq_rf_factory_v1',q['implementation']['rf_factory'])
        lock=threading.Lock();budget=parent.Budget(q,out,torch,helper)
        def sample(label,count):
            with lock:helper.assert_numeric(torch);budget.sample(label,count)
        def watch():
            while not stop.wait(2.):
                try:sample('MONITOR',counts['full_forward'])
                except BaseException as exc:
                    try:emit(out/'monitor_failure.json',dict(error=repr(exc),counts=dict(counts)))
                    finally:os.kill(os.getpid(),signal.SIGTERM)
                    return
        watcher=threading.Thread(target=watch,daemon=True);watcher.start();sample('before_construction',0)
        x=torch.from_numpy(np.random.default_rng(FIXTURE['input_seed']).uniform(-.5,.5,(8,8192,3)).astype(np.float32)).to('cuda:0')
        target=torch.from_numpy(np.random.default_rng(FIXTURE['target_seed']).uniform(-.5,.5,(8,8192,3)).astype(np.float32)).to('cuda:0')
        random.seed(0);np.random.seed(0);torch.manual_seed(0)
        reference=None;common=None;ssm_calls={};records=[];construction=[];origins=None
        for phase in PHASES:
            label,variant,batch,training=phase
            if variant=='S-ref':
                model,built=scq_factory.build_model(lambda:cls(EasyDict(static['model'])),'S',q['initialization'],seed=0)
                native_total=built['scq']['total_parameters'];new_parameters=0
                need(not built['parent']['artificial_fixture'],'native S factory only')
            else:
                model,built=factory.build_model(lambda:cls(EasyDict(static['model'])),variant,q['initialization'],q['rf_initialization'],seed=0)
                native_total=built['rf']['total_parameters'];new_parameters=built['rf']['additional_parameters']
                need(not built['parent']['parent']['artificial_fixture'],'native RF factory only')
            helper.validate_model(model)
            grouping=ast.parse(exact(q['optimizer_policy']).read_text(encoding='utf-8'))
            fn=next(n for n in grouping.body if isinstance(n,ast.FunctionDef) and n.name=='optimizer_groups')
            group_scope=dict(require=need);exec(compile(ast.Module([fn],[]),q['optimizer_policy']['path'],'exec'),group_scope)
            _,optimizer_rows=group_scope['optimizer_groups'](model)
            need(len(optimizer_rows)==len([p for p in model.parameters() if p.requires_grad]),'native group partition')
            for row in optimizer_rows:
                if row['name'].startswith('base_model.rf.'):
                    need(row['weight_decay']==(0. if row['name'].endswith('.bias') else .0005),'RF native decay')
            event(dict(kind='NATIVE_OPTIMIZER_CLASSIFICATION_ONLY',phase=label,rows=optimizer_rows))
            need(native_total==(40596676 if variant=='S-ref' else 40827847),'native total parameters')
            state={n:scq_factory.parent.parent.tensor_sha(t) for n,t in model.state_dict().items() if not n.startswith('base_model.rf.')}
            if common is None:common=state
            else:need(state==common,'shared initial states differ')
            names=['mamba_ssm','mamba_ssm.modules.mamba_simple','mamba_ssm.ops.selective_scan_interface','causal_conv1d','causal_conv1d.causal_conv1d_interface','selective_scan_cuda','causal_conv1d_cuda']
            mods=[importlib.import_module(n) for n in names];origins=[str(Path(m.__file__).resolve()) for m in mods]
            need(set(origins)<={r['path'] for r in q['dependencies']} and mods[0].__version__=='2.3.1','native origins')
            model.eval().to('cuda:0');torch.cuda.reset_peak_memory_stats(0)
            hooks=[]
            def hook_for(name):
                def hook(m,args):
                    need(args[0].shape[1] in (256,512),'native token length');ssm_calls[name]=ssm_calls.get(name,0)+1
                return hook
            for n,m in model.named_modules():
                if type(m).__module__=='mamba_ssm.modules.mamba_simple':hooks.append(m.register_forward_pre_hook(hook_for(n)))
            need(len(hooks)==22,'native22 modules')
            try:r,ref=phase_checks(torch,np,model,helper,parent,x,target,phase,reference,counts,event,sample)
            finally:
                for h in hooks:h.remove()
            if ref is not None:reference=ref
            records.append(r);construction.append(dict(phase=label,variant=variant,parameters=native_total,new_parameters=new_parameters,shared_initial_state_SHA256=hashlib.sha256(json.dumps(state,sort_keys=True).encode()).hexdigest(),logical_capacity=torch.cuda.get_device_properties(0).total_memory))
            del model;gc.collect();torch.cuda.empty_cache()
        need(counts=={k:SCIENCE[k] for k in counts},'exact5F4loss4B0step')
        need(len(ssm_calls)==22 and sum(ssm_calls.values())==180 and all(v==(5 if '.cond_ssm' in n else 10) for n,v in ssm_calls.items()),'180 actual native calls')
        stop.set();watcher.join(15.);need(not watcher.is_alive(),'monitor shutdown');sample('complete',5)
        emit(out/'construction.json',dict(models=construction,native_origins=origins))
        emit(out/'completion.json',dict(status='RF_NATIVE_CUDA_COMPLETE_PENDING_FORMAL_FREEZE',request_sha256=qr['sha256'],counts=counts,phases=records,native_SSM_calls=ssm_calls,initial_common_state_equal=True,initial_RF_Sref_equivalence=True,real_data_reads=0,checkpoint_loads=0,optimizer_constructed=False,training_admission=False,BNCal=False,finite_gradient_nondeterminism_disclosed=True))
        emit(out/'payload_manifest.json',[dict(name=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(out.iterdir()) if p.is_file() and p.name not in ('launch.log','worker.pid')])
    except BaseException as exc:
        stop.set()
        if watcher is not None:watcher.join(15.)
        emit(out/'failure.json',dict(status='FAILED_STOP_NO_RETRY',error=repr(exc),counts=counts));raise
    finally:guard.close();utc.close()

if __name__=='__main__':main()
