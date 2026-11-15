"""Artificial CPU contracts only; no native Mamba, data, WSL or GPU calls."""
import ast,hashlib,importlib.util,json,math,random
from pathlib import Path
import numpy as np
import torch
from torch import nn
HERE=Path(__file__).resolve().parent
def module(name,p):
    spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
stats=module('stats_under_test',HERE/'bcsp_gradient_statistics_v1.py')
entry=module('quant_entry_under_test',HERE/'bcsp_p1_gradient_quantification_v1.py');entry.QUANT=stats
oldtests=module('artificial_model_fixture',HERE.parent/'gpu_admission_v1/test_p1_gpu_admission_cpu_v1.py')
Helper=oldtests.Helper;Artificial=oldtests.ArtificialAdmissionModel
OUT=HERE/'CPU_contracts_v1'
def main():
    OUT.mkdir(exist_ok=False);checks=[]
    def check(name,ok):
        if not ok:raise AssertionError(name)
        checks.append(name)
    def rejects(name,fn):
        try:fn()
        except RuntimeError:checks.append(name)
        else:raise AssertionError(name)
    def pair(a,b,chunk=stats.CHUNK):
        model=nn.Module();model.p=nn.Parameter(torch.zeros(len(a),dtype=torch.float32));model.p.grad=torch.tensor(b,dtype=torch.float32)
        rows=[];result=stats.quantify(torch,dict(p=torch.tensor(a,dtype=torch.float32)),model,dict(p=True),Helper.tensor_sha,rows.append,lambda:None,chunk)
        return result['global_statistics'],rows
    try:
        torch.set_num_threads(2);torch.manual_seed(77);random.seed(77);np.random.seed(77)
        r,rows=pair([1.,2.,-3.],[1.,2.,-3.])
        check('identical gradients: zero difference and cosine one',r['relative_l2']==r['rms_difference']==0 and abs(r['cosine_raw']-1)<1e-14 and rows[0]['bytes_equal'])
        r,_=pair([1.,2.],[1.25,1.5],chunk=1)
        check('known differences against hand computation',r['max_abs_diff']==.5 and r['sum_squared_diff']==.3125 and r['mean_abs_difference']==.375 and math.isclose(r['relative_l2'],math.sqrt(.3125)/math.sqrt(5)))
        check('known dot product and direction',r['dot']==4.25 and math.isclose(r['cosine_raw'],4.25/(math.sqrt(5)*math.sqrt(3.8125))))
        r,_=pair([0.,0.],[0.,0.])
        check('both zero: relative zero cosine explicitly undefined',r['relative_l2']==0 and r['cosine_raw'] is None and r['cosine_reason']=='zero_norm')
        r,_=pair([0.,0.],[1.,0.])
        check('zero to nonzero: relative one and undefined cosine',r['relative_l2']==1 and r['zero_to_nonzero']==1 and r['cosine_raw'] is None)
        r,_=pair([1.,0.],[0.,2.])
        check('zero transition counters',r['nonzero_to_zero']==r['zero_to_nonzero']==1 and r['numeric_different']==2)
        r,rows=pair([0.,-0.],[-0.,0.])
        check('signed zero distinguishes bytes from numbers',not rows[0]['bytes_equal'] and rows[0]['numerically_equal'] and r['byte_different_tensors']==1 and r['numeric_different']==0)
        a=list(range(15));b=[v+.25 if v%3 else -v for v in a]
        one,_=pair(a,b,1);many,_=pair(a,b,7)
        check('chunked sums match one-element manual reduction',all(math.isclose(one[k],many[k],rel_tol=1e-14,abs_tol=1e-14) for k in ('sum_squared_diff','sum_squared_a','sum_squared_b','dot','sum_abs_diff','relative_l2','rms_difference')))
        check('maximum location values are attributable',one['maximum_location']==dict(parameter='p',flat_index=12,a=12.,b=-12.))
        rejects('reject NaN gradient',lambda:pair([1.],[float('nan')]))
        rejects('reject Inf reference',lambda:pair([float('inf')],[1.]))
        rejects('reject unbounded chunk size',lambda:pair([1.],[1.],stats.CHUNK+1))
        m=nn.Linear(2,1);m.weight.grad=torch.ones_like(m.weight);expected=stats.presence(m);budget=[]
        reference=stats.capture(torch,m,expected,lambda n,h:budget.append((n,h)),lambda:None)
        check('capture exact byte budget before clones',budget[0][0]==8 and budget[0][1]>=stats.HEADROOM+16)
        m.weight.grad.zero_();check('CPU reference is a detached independent copy',bool((reference['weight']==1).all()) and not reference['weight'].requires_grad)
        rows=[];out=stats.quantify(torch,reference,m,expected,Helper.tensor_sha,rows.append,lambda:None)
        check('frozen absent gradients recorded without fabricated zeros',rows[1]['presence_a'] is False and rows[1]['statistics'] is None and out['global_statistics']['parameter_tensors']==2 and out['global_statistics']['present_tensors']==1)
        m.weight.grad=None
        rejects('unexpected missing gradient rejected',lambda:stats.quantify(torch,reference,m,expected,Helper.tensor_sha,lambda r:None,lambda:None))
        rejects('reference capture presence mismatch rejected',lambda:stats.capture(torch,m,expected,lambda *a:None,lambda:None))
        m.weight.grad=torch.ones_like(m.weight)
        def insufficient(*args):raise RuntimeError('synthetic insufficient RSS')
        rejects('reference budget rejection before clone',lambda:stats.capture(torch,m,expected,insufficient,lambda:None))
        m.weight.grad=torch.ones_like(m.weight,dtype=torch.float32)
        bad=dict(reference);bad['weight']=torch.ones((1,3))
        rejects('gradient shape drift rejected',lambda:stats.quantify(torch,bad,m,expected,Helper.tensor_sha,lambda r:None,lambda:None))
        names=['base_model.encoder.blocks.blocks.0.attn.mixer.x','base_model.encoder.x','base_model.grouper.x','base_model.coarse_pred.x','base_model.decoder.x','offset']
        check('six module groups cover each name exactly once',tuple(stats.group_for(n) for n in names)==stats.GROUPS)
        # Two radically different tensor sizes: prove aggregate relative L2 is not a tensor average.
        model=nn.Module();model.a=nn.Parameter(torch.zeros(1));model.b=nn.Parameter(torch.zeros(3));model.a.grad=torch.tensor([2.]);model.b.grad=torch.tensor([10.,10.,10.])
        aggregate=stats.quantify(torch,dict(a=torch.tensor([1.]),b=torch.tensor([10.,10.,10.])),model,dict(a=True,b=True),Helper.tensor_sha,lambda r:None,lambda:None)['global_statistics']
        check('global metrics aggregate element sums',aggregate['relative_l2']==1/math.sqrt(304) and aggregate['rms_difference']==.5)
        x=torch.randn(8,8192,3);target=torch.randn_like(x);events=[];samples=[];counts=entry.counters();rowsets={}
        for arm in ('T0','M0'):
            model=Artificial().eval();before=Helper.state_sha(model);rng=torch.get_rng_state().clone();rows=[];rowsets[arm]=rows
            if arm=='M0':
                model.base_model.coarse_pred.weight.register_hook(lambda g:g*(1.0001 if model.calls==6 else 1.))
            presence={n:True for n,p in model.named_parameters()}
            result=entry.admit_model(torch,np,model,x,target,arm,counts,Helper,events.append,lambda p,c:samples.append(p),cuda=False,expected_presence=presence,write_gradient=rows.append,memory_prepare=lambda *a:None,memory_poll=lambda:None)
            check(arm+' exact six calls and finite statistics',model.calls==6 and len(rows)==len(presence) and result['gradient_quantification']['global_statistics']['parameter_tensors']==len(presence))
            check(arm+' final state RNG mode BN and gradients restored',Helper.state_sha(model)==before and torch.equal(torch.get_rng_state(),rng) and not model.training and model.bn.momentum==.1 and all(p.grad is None for p in model.parameters()))
            check(arm+' gradient discrepancy is diagnostic only',result['events'][-1]['gradient_exact_equal']==(arm=='T0') and result['events'][-1]['loss_exact_equal'])
        check('full 12 forwards 4 backwards zero steps',counts==dict(forward_attempts=12,forward_returns=12,loss_calls=4,backward_attempts=4,backward_returns=4,optimizer_steps=0))
        check('every backward has after-resource sample',sum('after_backward_before_statistics' in p for p in samples)==4)
        check('every call counter emitted before operation',sum(r.get('kind')=='FORWARD_ATTEMPT' for r in events)==12 and sum(r.get('kind')=='BACKWARD_ATTEMPT' for r in events)==4)
        for label,kwargs,calls in [('forward failure',dict(fail=True),1),('output drift',dict(drift=True),2),('RNG drift',dict(rng_drift=True),1)]:
            model=Artificial(**kwargs).eval();c=entry.counters();before=Helper.state_sha(model);rng=torch.get_rng_state().clone()
            rejects(label+' stops',lambda:entry.admit_model(torch,np,model,x,target,'T0',c,Helper,lambda r:None,lambda *a:None,cuda=False,expected_presence={},write_gradient=lambda r:None,memory_prepare=lambda *a:None,memory_poll=lambda:None))
            check(label+' restores without retry',model.calls==calls and Helper.state_sha(model)==before and torch.equal(torch.get_rng_state(),rng) and not model.recording and c['optimizer_steps']==0)
        model=Artificial().eval();model.base_model.coarse_pred.weight.register_hook(lambda g:torch.full_like(g,float('nan')));c=entry.counters()
        rejects('nonfinite actual backward stops before second replay',lambda:entry.admit_model(torch,np,model,x,target,'M0',c,Helper,lambda r:None,lambda *a:None,cuda=False,expected_presence={},write_gradient=lambda r:None,memory_prepare=lambda *a:None,memory_poll=lambda:None))
        check('nonfinite failure retains counts and clears gradients',c['forward_attempts']==5 and c['backward_returns']==1 and all(p.grad is None for p in model.parameters()))
        fixtures=OUT/'fixtures';fixtures.mkdir()
        def rec(n,v):
            p=fixtures/n
            with p.open('x') as f:json.dump(v,f)
            return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=entry.sha(p))
        q=rec('request.json',dict(schema='bcsp-p1-gradient-quantification-v1',status='AWAITING_EXPLICIT_USER_AUTHORIZATION',science=dict(forward_attempt_limit=12,backward_attempt_limit=4,optimizer_steps=0)))
        a=rec('auth.json',dict(schema='bcsp-p1-authorization-v1',request_sha256=q['sha256'],explicit_user_authorization=True,user_authorization_text='ARTIFICIAL_ONLY'))
        r=rec('runtime.json',dict(schema='bcsp-p1-runtime-v1',request_sha256=q['sha256'],authorization_sha256=a['sha256']))
        check('full authorize one-way contract',entry.authorize(q,a,r)['science']['optimizer_steps']==0)
        bad=rec('runtime_bad.json',dict(schema='bcsp-p1-runtime-v1',request_sha256=q['sha256'],authorization_sha256='0'*64))
        rejects('mismatched runtime rejected',lambda:entry.authorize(q,a,bad))
        tree=ast.parse((HERE/'bcsp_p1_gradient_quantification_v1.py').read_text(encoding='utf-8'))
        check('no optimizer construction step checkpoint load',not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in ('step','AdamW','Adam','load') and isinstance(n.func.value,ast.Name) and n.func.value.id in ('optimizer','torch') for n in ast.walk(tree)))
        # Persist only artificial summaries; no reference arrays.
        with (OUT/'artificial_parameter_rows_v1.json').open('x') as f:json.dump(rowsets,f,indent=2,allow_nan=False)
        result=dict(status='ARTIFICIAL_CPU_GRADIENT_QUANTIFICATION_CONTRACTS_PASS',count=len(checks),checks=checks,torch_version=torch.__version__,GPU_calls=0,server_calls=0,native_Mamba_calls=0,real_payload_reads=0,optimizer_steps=0)
        with (OUT/'result_v1.json').open('x') as f:json.dump(result,f,indent=2)
        print(json.dumps(result))
    except BaseException as exc:
        with (OUT/'failure_v1.json').open('x') as f:json.dump(dict(status='FAILED_STOP_NO_RETRY',checks=checks,error=repr(exc)),f,indent=2)
        raise
if __name__=='__main__':main()
