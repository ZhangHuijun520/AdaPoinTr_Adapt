"""20 frozen Requery natives +40 suffixes. Separate authorization; import is inert."""
import argparse,gc,hashlib,importlib.util,json,os,shlex,shutil,socket,sys,time
from pathlib import Path,PurePosixPath

SCHEMA='bcsp-scq-dac-r1-frozen-weight-v1'
BUDGET=dict(native=20,decoder_only=40,decoder=60,h1_new=20,h1_old=20,first_head=20)
PINNED_CP={'Requery_C':'4816c8768da60de7c8153fcd0793524b2fb3c1dddba04de9cdf0c6eb13f2602b',
           'Requery_D':'068288d4beb237dfe820286e22e122a5f427e4e32846c63087320aabc5b25bba'}
def require(ok,message):
    if not ok:raise RuntimeError(message)
def clean(path):
    p=Path(path).absolute()
    require(not any(x.is_symlink() for x in (p,*p.parents)),'linked original path: '+str(p))
    require(not {'.git','.ssh','.aws','.credentials'}&set(p.parts) and p.name not in ('.env','.netrc'),'secret path')
    return p
def sha(p):
    h=hashlib.sha256()
    with clean(p).open('rb') as f:
        for b in iter(lambda:f.read(4194304),b''):h.update(b)
    return h.hexdigest()
def exact(r):
    p=clean(r['path']);require(p.is_file() and p.stat().st_size==r['bytes'] and sha(p)==r['sha256'],'file drift: '+str(p));return p
def bound(r):return json.loads(exact(r).read_bytes())
def emit(p,value):
    with clean(p).open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False)
def source(name,record):
    require(name not in sys.modules,'preloaded module '+name)
    p=exact(record);m=importlib.util.module_from_spec(importlib.util.spec_from_file_location(name,p));sys.modules[name]=m
    try:exec(compile(p.read_bytes(),str(p),'exec',dont_inherit=True),m.__dict__)
    except BaseException:sys.modules.pop(name,None);raise
    return m
def authorize(qr,ar,rr):
    q,a,r=bound(qr),bound(ar),bound(rr)
    require(q['schema']==SCHEMA and q['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION' and q['execution_authorized'] is False,'pending exact request')
    require(q['calls']==BUDGET and all(q[k]==0 for k in ('loss','backward','optimizer_steps','BNCal','TTA','warmup')),'20+40 zero-update only')
    require(q['batch_size']==1 and q['limits']['wall_seconds']==600,'batch/time contract')
    require(a==dict(schema='bcsp-dac-r1-authorization-v1',request_sha256=qr['sha256'],explicit_user_authorization=True,user_authorization_text=a.get('user_authorization_text')) and isinstance(a.get('user_authorization_text'),str) and bool(a['user_authorization_text'].strip()),'explicit authorization')
    require(r==dict(schema='bcsp-dac-r1-runtime-v1',request_sha256=qr['sha256'],authorization_sha256=ar['sha256']),'one-way runtime')
    for k in ('hostname','gpu_uuid','driver_version'):require(q['identity'][k]==q['expected_identity'][k],'identity binding')
    require(q['readiness']['fresh_remote_recheck_required'] is True and q['readiness']['verified_this_preparation'] is False,'no fabricated readiness')
    require({x['label']:x['checkpoint']['sha256'] for x in q['models']}==PINNED_CP,'only frozen Requery C/D')
    require(q['formula']==dict(version='DAC-plan-v2',epsilon_norm=1e-6,alpha='0.5+0.5*relu(cosine)',near_zero='alpha=0.5',detach='alpha_only'),'unique formula')
    return q
def validate_selection(core,index,old_index):
    expected=core.select_cases(old_index);rows=index['cases']
    require(len(rows)==20 and len({r['case_id'] for r in rows})==20,'unique20')
    for row,original in zip(rows,expected):
        require({k:row[k] for k in original}==original,'selection/input/normalization drift')
        require(row['normalization_source']=='defective_bbox' and row['n_input']==row['n_output']==8192,'D-only frame')
        require(row['replay']['sha256']==row['replay_member_sha256'],'historical Native bytes')
    return rows
def render_launcher(q,qsha,asha,rsha):
    for s in (qsha,asha,rsha):require(len(s)==64 and set(s)<=set('0123456789abcdef'),'full hash')
    L=q['launch_contract'];out=PurePosixPath(q['output'])
    lines=['#!/bin/bash','set -eu','umask 077','cd '+shlex.quote(q['identity']['project'])]
    for p in reversed((out,*out.parents)):
        if str(p)!='/':lines.append('[ ! -L '+shlex.quote(str(p))+' ] || exit 121')
    lines+=['mkdir -p -- '+shlex.quote(str(out.parent)),'mkdir -- '+shlex.quote(str(out))]
    lines+=['export '+k+'='+shlex.quote(v.replace('<owned_output>',str(out))) for k,v in q['environment'].items()]
    cmd=['/usr/bin/timeout','--signal=TERM','--kill-after=5s','600s',q['identity']['python_realpath'],'-I','-S','-B',q['entry']['path']]
    for k,v in (('request',L['request_path']),('request-sha256',qsha),('authorization',L['authorization']),('authorization-sha256',asha),('runtime',L['runtime']),('runtime-sha256',rsha)):cmd+=['--'+k,v]
    lines+=['set +e',shlex.join(cmd)+' >'+shlex.quote(L['log'])+' 2>&1','rc=$?','set -e',"printf '%s\\n' \"$rc\" >"+shlex.quote(L['exit_code']),'exit "$rc"']
    require(max(map(len,lines))<=2048,'short launcher lines')
    return '\n'.join(lines)+'\n'
def execute_cases(torch,np,legacy,helper,core,models,rows,out,budget,builder,device='cuda:0',artificial=False):
    require((device=='cpu') is artificial,'production CUDA only')
    journal=out/'calls.jsonl';manifest=out/'diagnostic_manifest.jsonl'
    for p in (journal,manifest):p.open('x').close()
    def event(key,case,counts):legacy.append_event(journal,dict(event='CLAIMED_BEFORE_CALL',kind=key,case=case,counts=counts))
    calls=core.Calls(event);states=[];files=[];cuda=not artificial
    for run in models:
        model=builder(run);legacy.load_checkpoint(torch,model,run);model.eval().to(device)
        model.enable_full_instrumentation(False)
        if cuda:torch.cuda.synchronize();torch.cuda.reset_peak_memory_stats(0)
        before=helper.state_sha(model);rng=legacy.rng_state(torch,np,helper,cuda)
        for row in [r for r in rows if r['run']==run['label']]:
            helper.assert_numeric(torch);budget.sample('before_case',calls.counts['native'])
            x=torch.from_numpy(legacy.load_partial(np,row)).unsqueeze(0).to(device)
            with torch.inference_mode():arrays=core.diagnose_case(torch,model,x,calls,row['run']+':'+row['case_id'])
            with np.load(exact(row['replay']),allow_pickle=False) as old:
                require(old['prediction'].shape==(8192,3) and old['coarse'].shape==(256,3),'original Native shapes')
                differences={}
                for k,oldkey in (('P_R','prediction'),('Q2_R','coarse')):
                    a=arrays[k][0];v=old[oldkey];require(v.dtype==np.float32 and np.isfinite(v).all(),'Native FP32 finite')
                    differences[k]=dict(max_abs=float(np.abs(a-v).max()),mean_abs=float(np.abs(a-v).mean()))
                    require(np.allclose(a,v,atol=1e-5,rtol=1e-4),'frozen Native replay mismatch: '+k)
            path=out/'cases'/(row['run']+'__'+row['case_id']+'.npz')
            with path.open('xb') as f:np.savez_compressed(f,**arrays)
            record=dict(case_id=row['case_id'],fold=row['fold'],run=row['run'],input_sha256=row['input']['sha256'],checkpoint_sha256=run['checkpoint']['sha256'],normalization=row['normalization'],replay=differences,path=str(path.relative_to(out)),bytes=path.stat().st_size,sha256=sha(path))
            legacy.append_event(manifest,record);files.append(path)
            helper.assert_numeric(torch);budget.sample('after_case',calls.counts['native'])
        after=helper.state_sha(model);rng_after=legacy.rng_state(torch,np,helper,cuda)
        require(before==after and rng==rng_after,'state/RNG changed')
        require(all(p.grad is None for p in model.parameters()),'unexpected gradients')
        states.append(dict(run=run['label'],state_before=before,state_after=after,RNG_unchanged=True,cases=10))
        del model;gc.collect()
        if cuda:torch.cuda.empty_cache()
    require(calls.counts==BUDGET and len(files)==20,'exact final budgets')
    return files+[journal,manifest],states,calls.counts
def main():
    parser=argparse.ArgumentParser()
    for k in ('request','request-sha256','authorization','authorization-sha256','runtime','runtime-sha256'):parser.add_argument('--'+k,required=True)
    a=parser.parse_args();rec=lambda p,h:dict(path=p,bytes=clean(p).stat().st_size,sha256=h)
    qr=rec(a.request,a.request_sha256);q=authorize(qr,rec(a.authorization,a.authorization_sha256),rec(a.runtime,a.runtime_sha256))
    I=q['identity'];out=clean(q['output']);root=clean(q['model_root']);source_guard=None;utc=None
    try:
        require(sys.platform=='linux' and sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode,'Linux -I -S -B')
        require(socket.gethostname()==I['hostname'] and os.getuid()==I['uid'] and str(Path(sys.executable).resolve())==I['python_realpath'] and sys.version.split()[0]==I['python_version'],'identity/Python')
        require(Path.cwd().resolve()==Path(I['project']) and out.parent==Path(I['project'])/'logs/cranial_bcsp_fullmamba','project/output')
        require(Path(__file__).resolve()==exact(q['entry']),'entry pin')
        parent=Path('/proc/'+str(os.getppid())+'/cmdline').read_bytes().decode().rstrip('\0').split('\0')
        require(parent[:4]==['/usr/bin/timeout','--signal=TERM','--kill-after=5s','600s'],'external600s')
        require(bound(dict(path=q['launch_attempt'],bytes=clean(q['launch_attempt']).stat().st_size,sha256=sha(q['launch_attempt'])))==dict(status='CLAIMED_BEFORE_TMUX',request_sha256=qr['sha256']),'single attempt')
        require(out.is_dir() and {p.name for p in out.iterdir()}=={'launch.log'},'fresh launcher-only output')
        for name in ('cases','tmp','mplconfig','hf_cache','cache','triton_cache'):(out/name).mkdir()
        with (out/'worker.pid').open('x') as f:f.write(str(os.getpid()))
        for k,v in q['environment'].items():require(os.environ.get(k)==v.replace('<owned_output>',str(out)),'environment '+k)
        legacy=source('dac_r1_frozen_native',q['native_library']);core=source('dac_r1_core',q['core'])
        require(bound(q['P3'])['status']=='LOCAL_DAC_R1_P3_PASS','P3')
        rows=validate_selection(core,bound(q['selection']),bound(q['legacy_index']))
        for r in rows:exact(r['input']);exact(r['replay'])
        for run in q['models']:exact(run['checkpoint'])
        for r in q['dependencies']:exact(r)
        static=bound(q['static_config']);scope=bound(q['preflight_scope'])
        helper=source('dac_r1_helper',q['helper']);helper._MONITOR=None;records=helper.source_map(scope)
        for rel,r in records.items():helper.exact(root/rel,r['sha256'],r['bytes'])
        helper.exact(root/'base_model.yaml',scope['bindings']['base_config']['sha256'])
        for r in scope['bindings']['provider']+scope['bindings']['environment_metadata']:helper.exact(r['path'],r['sha256'],r['bytes'])
        smi=[x.strip() for x in helper.smi('uuid,name,driver_version,memory.total,memory.used')[0].split(',')]
        require(smi[:4]==[I['gpu_uuid'],I['gpu_name'],I['driver_version'],str(I['nvidia_smi_memory_total_MiB'])] and int(smi[4])<=256,'GPU identity/idle')
        tz=legacy.source_module('dac_exact_utc',q['implementation']['timezone']);utc=tz.ExactUTCReader(tz.UTC_RESOURCE)
        source_guard=legacy.make_source_guard(q['implementation'],q['initialization'],q['rf_initialization'],[q['entry'],q['core'],q['native_library'],q['helper']])
        envroot=Path('/opt/conda/envs/adapointr-mamba');provider=Path(scope['bindings']['provider'][0]['path']).parent.parent
        sys.path[:0]=[str(Path(q['implementation']['factory']['path']).parent),str(provider),str(envroot/'lib/python3.10/site-packages')]
        helper.namespace_packages(root);sys.meta_path.insert(0,helper.FiniteProjectImports(root,records))
        outputs=[out/'cases'/(r['run']+'__'+r['case_id']+'.npz') for r in rows]
        policy=legacy.make_policy(helper,[root,envroot,provider,Path(__file__).parent,'/usr/lib','/proc/'+str(os.getpid()),'/dev/null','/dev/urandom'],out,[r['input']['path'] for r in rows]+[r['replay']['path'] for r in rows],[r['checkpoint']['path'] for r in q['models']],outputs,utc,source_guard)
        sys.addaudithook(policy.audit)
        import numpy as np
        import torch,timm,yaml,importlib
        from easydict import EasyDict
        require((torch.__version__,np.__version__,timm.__version__)==(I['torch_version'],I['numpy_version'],I['timm_version']),'versions')
        require(torch.cuda.is_available() and torch.cuda.device_count()==1 and torch.version.cuda==I['torch_cuda_version'],'one admitted CUDA device')
        torch.cuda.set_device(0);helper.configure_numeric(torch)
        chamfer=importlib.import_module('extensions.chamfer_dist');pn=importlib.import_module('utils.pointnet2_utils');pm=importlib.import_module('pointnet2_ops.pointnet2_utils');native=importlib.import_module('pointnet2_ops._ext')
        require(str(Path(pm.__file__).resolve())==scope['bindings']['provider'][1]['path'] and str(Path(native.__file__).resolve())==scope['bindings']['provider'][2]['path'],'native provider origin');helper.check_backend(chamfer,pn,pm)
        transformer=importlib.import_module('models.Transformer_utils');model_class=importlib.import_module('models.AdaPoinTr').AdaPoinTr;transformer.enable_bcsp_knn()
        require(static['model']==yaml.safe_load((root/'base_model.yaml').read_text())['model'],'fixed model config')
        factory=legacy.load_scq_builder(q['implementation'])
        def builder(run):
            model,evidence=legacy.build_scq_model(factory,lambda:model_class(EasyDict(static['model'])),run,q['initialization'],q['rf_initialization']);legacy.validate_model(model,evidence);return model
        budget=legacy.Budget(q,out,torch,helper)
        files,states,counts=execute_cases(torch,np,legacy,helper,core,q['models'],rows,out,budget,builder)
        done=out/'diagnostic_complete.json';emit(done,dict(status='DAC_R1_CAPTURE_COMPLETE_AWAITING_FREEZE_AND_OFFLINE_INTERPRETATION',counts=counts,models=states,GT_used=False,loss=0,backward=0,optimizer_steps=0,request_sha256=qr['sha256']))
        archive=legacy.pack(out,files+[done,budget.path])
        budget.sample('archived',counts['native'])
        emit(out/'completion.json',dict(status='CAPTURE_ARCHIVED_AWAITING_FORMAL_FREEZE',archive=archive,counts=counts))
    except BaseException as exc:
        if out.exists() and not (out/'failure.json').exists():emit(out/'failure.json',dict(status='FAILED_STOP_NO_RETRY',error=repr(exc),automatic_retry=False,optimizer_steps=0))
        raise
    finally:
        if source_guard is not None:source_guard.close()
        if utc is not None:utc.close()
if __name__=='__main__':main()
