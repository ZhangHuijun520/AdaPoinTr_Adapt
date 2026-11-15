"""Prepare RF CUDA entry from the exact existing SCQ engine; local files only."""
from pathlib import Path
import ast
import hashlib

R = Path(__file__).resolve().parent.parent
O = R / 'outputs/scq_rf_cuda_preparation_20261114_v1'
O.mkdir()
source = R / 'outputs/cranial_bcsp_scq_cuda_preparation_20261113_v1/bcsp_scq_cuda_admission_v3.py'
assert hashlib.sha256(source.read_bytes()).hexdigest() == 'fe7fc491cdeed22ba939b1a0c45b08905f8ebdb67d5f09b41b6f1975d2630ad6'
src = source.read_text(encoding='utf-8')


def change(old, new):
    global src
    assert src.count(old) == 1, old[:100]
    src = src.replace(old, new)


change('SCQ-only four synthetic CUDA forward/loss/backward phases', 'RF five synthetic CUDA forwards, four original losses/backwards, zero steps')
change('SCIENCE=dict(full_forward=4,full_backward=4,full_loss=4,decoder_forward=0,decoder_backward=0,optimizer_steps=0,real_data_reads=0,checkpoint_loads=0,input_points=8192,output_points=8192,full_batches=[1,1,1,8])',
       'SCIENCE=dict(full_forward=5,full_backward=4,full_loss=4,decoder_forward=0,decoder_backward=0,optimizer_steps=0,real_data_reads=0,checkpoint_loads=0,input_points=8192,output_points=8192,full_batches=[1,1,1,8,8])')
change("PHASES=[('B_eval1','B',1,False),('F_eval1','F',1,False),('S_eval1','S',1,False),('S_train8','S',8,True)]",
       "PHASES=[('S_ref_eval1','S-ref',1,False),('Static_eval1','RF-Static',1,False),('Requery_eval1','RF-Requery',1,False),('Static_train8','RF-Static',8,True),('Requery_train8','RF-Requery',8,True)]")
src = src.replace('bcsp-scq-artificial-cuda-v1', 'bcsp-scq-rf-artificial-cuda-v1').replace('bcsp-scq-cuda-authorization-v1', 'bcsp-scq-rf-cuda-authorization-v1').replace('bcsp-scq-cuda-runtime-v1', 'bcsp-scq-rf-cuda-runtime-v1').replace('frozen4F4B0step', 'frozen5F4loss4B0step')
change("need(p3['status']=='SCQ_CUDA_ENTRY_LOCAL_P3_PASS' and p3['entry_sha256']==q['entry']['sha256'],'entry P3')", "need(p3['status']=='RF_CUDA_ENTRY_LOCAL_P3_PASS' and p3['entry_sha256']==q['entry']['sha256'],'entry P3')")
change("need(ip3['status']=='LOCAL_SCQ_IMPLEMENTATION_P3_PASS' and ip3['CPU_checks']==49,'implementation P3')", "need(ip3['status']=='LOCAL_RF_IMPLEMENTATION_P3_PASS_ARTIFICIAL_CPU_ONLY' and ip3['CPU_checks']==59,'implementation P3')")
change("for r in q['dependencies']+list(q['implementation'].values())+[q['initialization']]:exact(r)", "for r in q['dependencies']+list(q['implementation'].values())+[q['initialization'],q['rf_initialization'],q['optimizer_policy']]:exact(r)")
change("[q['implementation']['scq_residual'],q['implementation']['scq_factory'],q['initialization']]", "[q['implementation'][k] for k in ('scq_residual','scq_factory','rf_residual','rf_factory')]+[q['initialization'],q['rf_initialization'],q['optimizer_policy']]")
change("factory=source_module('bcsp_scq_factory_v1',q['implementation']['scq_factory'])", "scq_factory=source_module('bcsp_scq_factory_v1',q['implementation']['scq_factory'])\n        source_module('bcsp_scq_rf_residual_v1',q['implementation']['rf_residual'])\n        factory=source_module('bcsp_scq_rf_factory_v1',q['implementation']['rf_factory'])")
change("model,built=factory.build_model(lambda:cls(EasyDict(static['model'])),variant,q['initialization'],seed=0)", """if variant=='S-ref':
                model,built=scq_factory.build_model(lambda:cls(EasyDict(static['model'])),'S',q['initialization'],seed=0)
                native_total=built['scq']['total_parameters'];new_parameters=0
                need(not built['parent']['artificial_fixture'],'native S factory only')
            else:
                model,built=factory.build_model(lambda:cls(EasyDict(static['model'])),variant,q['initialization'],q['rf_initialization'],seed=0)
                native_total=built['rf']['total_parameters'];new_parameters=built['rf']['additional_parameters']
                need(not built['parent']['parent']['artificial_fixture'],'native RF factory only')""")
change("need(not built['parent']['artificial_fixture'],'native factory only');helper.validate_model(model)", "helper.validate_model(model)\n            grouping=ast.parse(exact(q['optimizer_policy']).read_text(encoding='utf-8'))\n            fn=next(n for n in grouping.body if isinstance(n,ast.FunctionDef) and n.name=='optimizer_groups')\n            group_scope=dict(require=need);exec(compile(ast.Module([fn],[]),q['optimizer_policy']['path'],'exec'),group_scope)\n            _,optimizer_rows=group_scope['optimizer_groups'](model)\n            need(len(optimizer_rows)==len([p for p in model.parameters() if p.requires_grad]),'native group partition')\n            for row in optimizer_rows:\n                if row['name'].startswith('base_model.rf.'):\n                    need(row['weight_decay']==(0. if row['name'].endswith('.bias') else .0005),'RF native decay')\n            event(dict(kind='NATIVE_OPTIMIZER_CLASSIFICATION_ONLY',phase=label,rows=optimizer_rows))")
change("need(built['scq']['total_parameters']==(39903169 if variant=='B' else 40596676),'native total parameters')", "need(native_total==(40596676 if variant=='S-ref' else 40827847),'native total parameters')")
change("state={n:factory.parent.parent.tensor_sha(t) for n,t in model.state_dict().items() if not n.startswith('base_model.scq.')}", "state={n:scq_factory.parent.parent.tensor_sha(t) for n,t in model.state_dict().items() if not n.startswith('base_model.rf.')}")
change("parameters=built['scq']['total_parameters'],new_parameters=built['scq']['new_parameters']", "parameters=native_total,new_parameters=new_parameters")
change("'exact4F4loss4B0step'", "'exact5F4loss4B0step'")
change("sum(ssm_calls.values())==144 and all(v==(4 if '.cond_ssm' in n else 8)", "sum(ssm_calls.values())==180 and all(v==(5 if '.cond_ssm' in n else 10)")
change("'144 actual native calls'", "'180 actual native calls'")
change("sample('complete',4)", "sample('complete',5)")
src = src.replace('SCQ_NATIVE_CUDA_COMPLETE_PENDING_FORMAL_FREEZE', 'RF_NATIVE_CUDA_COMPLETE_PENDING_FORMAL_FREEZE').replace('initial_FS_equivalence=True', 'initial_RF_Sref_equivalence=True')
# The inherited phase engine is replaced, not run. Everything else retains the existing guard.
begin = src.index('def phase_checks(')
end = src.index('\ndef main():', begin)
phase = '''def phase_checks(torch,np,model,helper,parent,x,target,phase,reference,counts,event,sample):
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
        hooks=[b.mlp_query.register_forward_pre_hook(lambda m,a:consumers.update(query=a[0][...,-3:].detach().clone())),
               b.decoder.register_forward_pre_hook(lambda m,a,kw:consumers.update(decoder=kw['q_pos'].detach().clone()),with_kwargs=True),
               b.decoder.coordinate_pe.register_forward_pre_hook(lambda m,a:consumers.update(PE=a[0].detach().clone())),
               model.reduce_map.register_forward_pre_hook(lambda m,a:consumers.update(rebuild=a[0][...,-3:].detach().clone())),
               model.decode_head.register_forward_hook(lambda m,a,v:consumers.update(relative=v.detach().clone()))]
        sample(label+':before',counts['full_forward']);claim(counts,'full_forward',event)
        with torch.set_grad_enabled(variant!='S-ref'):
            ret=model(x[:batch]);need(len(ret)==(4 if training else 2),'original return tuple')
            coarse,dense=ret[0],ret[-1]
            need(coarse.shape==(batch,256,3) and dense.shape==(batch,8192,3) and all(t.dtype==torch.float32 and bool(torch.isfinite(t).all()) for t in (coarse,dense)),'finite full output')
            need(set(consumers)=={'query','decoder','PE','rebuild','relative'},'all actual Q2 consumers observed')
            need(all(torch.equal(consumers[k],coarse) for k in ('query','decoder','PE','rebuild')),'actual Q2 consumer mismatch')
            need(torch.equal(dense,(consumers['relative']+coarse.detach()[:,:,None]).reshape(batch,8192,3)),'actual dense Q2 centers')
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
        record=dict(phase=label,variant=variant,batch=batch,loss=None if loss is None else float(loss.detach()),initial_equivalence=equivalence,gradients=grad,head_gradients=head_grad,actual_Q2_consumers=True,BN_changed=changes,parameters_unchanged=True,RNG_before=rng_record,RNG_after=after_rng)
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
'''
src = src[:begin] + phase + src[end:]
p = O / 'bcsp_scq_rf_cuda_admission_v1.py'
compile(src, str(p), 'exec')
with p.open('x', encoding='utf-8', newline='\n') as f:
    f.write(src)
assert len([n for n in ast.walk(ast.parse(src)) if isinstance(n, ast.FunctionDef) and n.name=='phase_checks']) == 1
print('RF_CUDA_ENTRY_PREPARED_NO_EXECUTION')
