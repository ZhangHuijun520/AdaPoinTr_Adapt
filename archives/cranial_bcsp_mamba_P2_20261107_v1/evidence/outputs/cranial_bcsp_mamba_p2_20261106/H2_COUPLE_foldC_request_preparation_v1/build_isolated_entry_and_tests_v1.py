"""Derive one COUPLE entry and one artificial test file, preserving AUX bytes."""
import ast,hashlib,json
from pathlib import Path
S=Path(__file__).resolve().parent;A=S.parent/'H2_AUX_foldC_training_preparation_v1'
def once(s,a,b):
 assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
source=(A/'bcsp_h2_aux_foldC_training_entry_v1.py').read_text(encoding='utf-8')
source=source.replace('H2-AUX','H2-COUPLE').replace('H2_AUX','H2_COUPLE').replace("'AUX'","'COUPLE'").replace('actual AUX metadata','actual COUPLE metadata').replace('first AUX C only','COUPLE C only')
source=source.replace('BOUNDED_H2_COUPLE_C_READINESS_PASS','BOUNDED_H2_AUX_C_READINESS_PASS')
audit=A/'post_training_freeze_audit_v1/audit_report_v1.json';initial=A/'post_training_freeze_audit_v1/downloads/initialization.json'
pins=dict(request='0ca0aeea9f918d037e5cff0e1f0e9af95ed3b17b9979ff63c6789a3672991517',audit='580a0b195c5730e56f260e357e135966e2ab954b9cef7582ff7298b35d33ee1c',initialization=hashlib.sha256(initial.read_bytes()).hexdigest())
assert hashlib.sha256(audit.read_bytes()).hexdigest()==pins['audit']
source=once(source,'\ndef validate_static_h2', '\nAUX_PAIR_PINS = '+repr(pins)+'\n\ndef validate_static_h2')
source=once(source,"'cuda_audit','readiness'}","'cuda_audit','readiness','aux_pairing'}")
anchor="    a,r=json_bound(ar),json_bound(rr)"
paircheck='''    pair=q['aux_pairing']
    require(set(pair)=={'request','audit','initialization'},'exact AUX pairing evidence')
    require(all(pair[k]['sha256']==h for k,h in AUX_PAIR_PINS.items()),'frozen AUX pairing pins')
    aux=json_bound(pair['request']);aux_audit=json_bound(pair['audit']);aux_initial=json_bound(pair['initialization'])
    require(aux_audit['status']=='FORMAL_H2_AUX_FOLDC_POST_TRAINING_FREEZE_AUDIT_PASS'
            and aux_audit['request_sha256']==pair['request']['sha256']
            and aux_audit['checks_passed']==len(aux_audit['checks'])>0 and all(aux_audit['checks'].values()),'AUX formal audit')
    require(aux_initial==aux_audit['initialization']['record'] and aux_initial['seed']==0,'AUX initial fingerprint evidence')
    require(aux['h2_config']==dict(H2,mode='AUX') and aux['fold']=='C' and aux['variant']=='M0','AUX pairing role')
    for key in ('identity','environment','QC','order_plan','data_root','model_root','initialization_reference','numeric_policy','numeric_protocol','pair_contract','dependencies','n_input','n_output'):
        require(q.get(key)==aux.get(key),'AUX scientific pairing '+key)
    require(all(q['implementation'][k]==v for k,v in aux['implementation'].items() if k!='entry'),'same H2 modules and inherited implementation')
    aux_static=json_bound(aux['static_config']);require(dict(static, H2=dict(H2,mode='AUX'))==aux_static,'only mode differs from AUX')
'''
# Static is needed before comparing the actual AUX config, while metadata remains payload-free.
before="    ready=json_bound(q['readiness'])"
setup="    metadata=load_bound('bcsp_training_contract_v1',q['implementation']['contract'])\n    static=validate_static_h2(json_bound(q['static_config']),json_bound(base['static_config']),metadata)\n"
source=once(source,before,setup+before)
source=once(source,anchor,paircheck+anchor)
bottom="    metadata=load_bound('bcsp_training_contract_v1',q['implementation']['contract'])\n    static=validate_static_h2(json_bound(q['static_config']),json_bound(base['static_config']),metadata)\n    selected,fold="
source=once(source,bottom,'    selected,fold=')
source=once(source,'    validate_model_h2(model)\n    dataset=',"    validate_model_h2(model)\n    aux_initial=json_bound(q['aux_pairing']['initialization'])\n    require(helper.state_sha(model,True)==aux_initial['parameter_sha256']\n            and helper.state_sha(model)==aux_initial['persistent_state_sha256'],'same full scratch initialization as AUX')\n    dataset=")
source=once(source,"budget.first_step_evidence=dict(factory=evidence,H2_head_initialization='ALL_ZERO_NO_RNG_DRAW')","budget.first_step_evidence=dict(factory=evidence,H2_head_initialization='ALL_ZERO_NO_RNG_DRAW',AUX_initialization_exact_match=True,AUX_initialization_sha256=q['aux_pairing']['initialization']['sha256'])")
source=once(source,"str(impl),str(factory_root)","str(impl),str(Path(q['implementation']['h2_range']['path']).parent),str(factory_root)")
source=once(source,"read_roots=[root,impl,factory_root,envroot", "read_roots=[root,impl,Path(q['implementation']['h2_range']['path']).parent,factory_root,envroot")
ast.parse(source)
with (S/'bcsp_h2_couple_foldC_training_entry_v1.py').open('x',encoding='utf-8',newline='\n') as f:f.write(source)

test=(A/'test_entry_cpu_v1.py').read_text(encoding='utf-8')
test=test.replace('bcsp_h2_aux_foldC_training_entry_v1.py','bcsp_h2_couple_foldC_training_entry_v1.py').replace('h2_aux_entry_test','h2_couple_entry_test').replace('H2_AUX_ENTRY_CPU_CONTRACT_PASS','H2_COUPLE_ENTRY_CPU_CONTRACT_PASS').replace('LOCAL_H2_AUX_TRAINING_ENTRY_P3_PASS','LOCAL_H2_COUPLE_TRAINING_ENTRY_P3_PASS').replace('bcsp-p2-H2-AUX-training-request-v1','bcsp-p2-H2-COUPLE-training-request-v1')
test=test.replace("'04 COUPLE not this run',lambda x:x['H2'].update(mode='COUPLE')","'04 AUX not this run',lambda x:x['H2'].update(mode='AUX')")
test=test.replace("builder,'AUX'","builder,'COUPLE'").replace('dispatch scratch AUX zero head','dispatch scratch COUPLE zero head')
needle="  oldpins=e.FROZEN_BASELINES;oldcuda=e.CUDA_AUDIT_SHA"
fixture='''  auxinitial=emit('aux_initial_fixture.json',dict(parameter_sha256='1'*64,persistent_state_sha256='2'*64,order_sha256=c.canonical_sha(plan),seed=0))
  auxq=copy.deepcopy(q);auxq['h2_config']=dict(e.H2,mode='AUX');auxq['static_config']=emit('aux_static_fixture.json',dict(static,H2=dict(e.H2,mode='AUX')))
  auxq['implementation']['entry']=bind(S.parent/'H2_AUX_foldC_training_preparation_v1/bcsp_h2_aux_foldC_training_entry_v1.py')
  auxqr=emit('aux_request_fixture.json',auxq)
  auxar=emit('aux_audit_fixture.json',dict(status='FORMAL_H2_AUX_FOLDC_POST_TRAINING_FREEZE_AUDIT_PASS',request_sha256=auxqr['sha256'],checks_passed=1,checks={'ARTIFICIAL_ONLY':True},initialization={'record':json.loads(Path(auxinitial['path']).read_bytes())}))
  q['aux_pairing']=dict(request=auxqr,audit=auxar,initialization=auxinitial)
  oldpairpins=e.AUX_PAIR_PINS;e.AUX_PAIR_PINS={k:r['sha256'] for k,r in q['aux_pairing'].items()}
'''
test=once(test,needle,fixture+needle)
test=once(test,"  finally:e.FROZEN_BASELINES=oldpins;e.CUDA_AUDIT_SHA=oldcuda","  finally:e.FROZEN_BASELINES=oldpins;e.CUDA_AUDIT_SHA=oldcuda;e.AUX_PAIR_PINS=oldpairpins")
test=once(test,"   rejects('07 explicit authorization required'", "   bad=copy.deepcopy(q);bad['aux_pairing']['audit']['sha256']='0'*64\n   rejects('25 AUX audit binding cannot drift',lambda:e.authorize(*triple(bad)))\n   rejects('07 explicit authorization required'")
test=once(test,"helper=types.SimpleNamespace(assert_numeric=lambda x:None,state_sha=lambda x:None)","helper=types.SimpleNamespace(assert_numeric=lambda x:None,state_sha=lambda x,parameter_only=False:('1' if parameter_only else '2')*64)")
test=once(test,"cuda_audit={'sha256':oldcuda},output='ARTIFICIAL_ONLY')","cuda_audit={'sha256':oldcuda},aux_pairing={'initialization':auxinitial},output='ARTIFICIAL_ONLY')")
needle="  emit('result_v1.json',dict(status='H2_COUPLE_ENTRY_CPU_CONTRACT_PASS'"
extra='''  check('26 AUX production pairing pins restored',e.AUX_PAIR_PINS==oldpairpins and e.AUX_PAIR_PINS['audit']=='580a0b195c5730e56f260e357e135966e2ab954b9cef7582ff7298b35d33ee1c')
  badhelper=types.SimpleNamespace(assert_numeric=lambda x:None,state_sha=lambda x,parameter_only=False:'0'*64)
  rejects('27 different full initialization rejected',lambda:e.dispatch_training(dq,candidate,selected,fold,plan,factory=Factory(),h2_adapter=a,model_builder=builder,runtime=Runtime(),helper=badhelper,budget=budget,torch=torch,knn_enable=lambda:None,expected_factory=expected,device='cpu'))
  aux,auxev=a.build_h2(t.Factory(),builder,'AUX');couple,coupleev=a.build_h2(t.Factory(),builder,'COUPLE')
  check('28 same full initial AUX COUPLE state',set(aux.state_dict())==set(couple.state_dict()) and all(torch.equal(v,couple.state_dict()[n]) for n,v in aux.state_dict().items()))
  m=captured['model'];m.h2_range_head.bias.data.fill_(.2);x,g=t.inputs();ret=m(x);context=m._h2_controller.context
  check('29 actual COUPLE path changes raw coarse',not torch.equal(context['raw'],context['used']) and context['scale'].item()>1)
  for value in [m.base_model.mlp_query.last[:,:,-3:],m.base_model.decoder.last_pos,m.reduce_map.last[:,:,-3:],ret[0]]:torch.testing.assert_close(value,context['used'],rtol=0,atol=0)
  torch.testing.assert_close(ret[3].reshape(1,256,32,3),context['used'].unsqueeze(2)+m.decode_head.last,rtol=0,atol=0)
  check('30 all five original coordinate consumers use coupled coarse',True)
  sparse,dense=m.get_loss(ret,g);event=m.h2_runtime_record()
  check('31 original actual loss adds auxiliary exactly once',event['H2_mode']=='COUPLE' and abs(float(dense)-event['loss_original_reconstruction']-event['H2_aux_weighted'])<1e-6)
  check('32 reused H2 module parent available to read policy',"read_roots=[root,impl,Path(q['implementation']['h2_range']['path']).parent" in raw)
'''
test=once(test,needle,extra+needle)
ast.parse(test)
with (S/'test_couple_entry_cpu_v1.py').open('x',encoding='utf-8',newline='\n') as f:f.write(test)
files=[S/'bcsp_h2_couple_foldC_training_entry_v1.py',S/'test_couple_entry_cpu_v1.py']
with (S/'static_review_v1.json').open('x',encoding='utf-8') as f:json.dump(dict(status='STATIC_S0_S1_PASS',files=[dict(name=p.name,bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in files],AUX_entry_sha256=hashlib.sha256((A/'bcsp_h2_aux_foldC_training_entry_v1.py').read_bytes()).hexdigest(),production_files_added=1,test_files_added=1,server_operations=0),f,indent=2)
print('STATIC_S0_S1_PASS')
