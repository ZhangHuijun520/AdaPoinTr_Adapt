from pathlib import Path
import ast,hashlib,json
R=Path(__file__).resolve().parent.parent;S=R/'outputs/scq_rf_sixmodel_native_prediction_preparation_20261115_v1/implementation_v1'
old=R/'outputs/cranial_bcsp_scq_BS_CD_native_prediction_preparation_20261114_v1/implementation_v1/test_scq_native_prediction_cpu_v1.py'
s=old.read_text(encoding='utf-8').replace("R=S.parents[2]", "R=S.parents[2]")
s=s.replace('bcsp_scq_fourmodel_native_predict_v1.py','bcsp_scq_rf_sixmodel_native_predict_v1.py').replace('SCQ_BS_CD_input_index_v1.json','RF_sixmodel_input_index_v1.json')
s=s.replace('420','630').replace('421','631').replace("R=S.parents[2]", "R=S.parents[2]")
# Original manifest contains420 entries, independent of prediction count.
s=s.replace("checks_passed", "checks_passed")
s=s.replace("bad['training_audits']['S_D']=bad['training_audits']['B_D']", "bad['training_audits']['Static_D']=bad['training_audits']['Sref_D']")
s=s.replace("['training_audits']['S_D']", "['training_audits']['Static_D']").replace("['training_audits']['B_D']", "['training_audits']['Sref_D']")
s=s.replace("lambda x:x['runs'][1].update(variant='B')", "lambda x:x['runs'][1].update(variant='S')")
s=s.replace("numeric=emit('artificial_numeric_policy.json',{})", "numeric=emit('artificial_numeric_policy.json',{})")
s=s.replace('LOCAL_SCQ_NATIVE_PREDICTION_P3_PASS','LOCAL_RF_NATIVE_PREDICTION_P3_PASS')
s=s.replace("p.make_source_guard(c['implementation'],c['initialization'])", "p.make_source_guard(c['implementation'],c['initialization'],c['rf_initialization'],[c['entry'],c['helper']])")
s=s.replace("import ctypes,hashlib,importlib.util,json,sys,types", "import ctypes,hashlib,importlib.util,json,sys,types,traceback,linecache")
s=s.replace("assert callable(f.build_model)", "assert callable(f['scq'].build_model) and callable(f['rf'].build_model)")
s=s.replace("assert p.exact(c['initialization']).read_bytes()", "assert p.exact(c['initialization']).read_bytes() and p.exact(c['rf_initialization']).read_bytes()\nfor r in [*c['implementation'].values(),c['entry'],c['helper']]:\n assert linecache.getline(r['path'],1)\ntry:exec(compile(\"raise RuntimeError('ARTIFICIAL_TRACEBACK')\",c['implementation']['rf_factory']['path'],'exec'))\nexcept RuntimeError as exc:assert 'ARTIFICIAL_TRACEBACK' in ''.join(traceback.format_exception(type(exc),exc,exc.__traceback__))")
s=s.replace("[*c['implementation'].values(),c['initialization']]", "[*c['implementation'].values(),c['initialization'],c['rf_initialization'],c['entry'],c['helper']]")
s=s.replace("implementation=impl,initialization=initialization,helper=", "implementation=impl,initialization=initialization,rf_initialization=rf_initialization,helper=")
s=s.replace("factory=p.load_scq_builder(impl)", "factories=p.load_scq_builder(impl);factory=factories['scq']")
s=s.replace("initialization=dict(q['initialization'],path=mirror[q['initialization']['path']])", "initialization=dict(q['initialization'],path=mirror[q['initialization']['path']]);rf_initialization=dict(q['rf_initialization'],path=mirror[q['rf_initialization']['path']])")
s=s.replace("for arm in ('B','S'):", "for arm in ('S','RF-Static','RF-Requery'):")
s=s.replace("m,ev=factory.build_artificial_fixture(legacy,mix,arm,initialization);m.eval();p.validate_model(m,ev,True)", "m,ev=(factory.build_artificial_fixture(legacy,mix,'S',initialization) if arm=='S' else factories['rf'].build_artificial_fixture(legacy,mix,arm,initialization,rf_initialization));m.eval();p.validate_model(m,ev,True)")
s=s.replace("if arm=='S':\n    with torch.no_grad():m.base_model.scq.W2.bias.copy_(torch.tensor([.1,-.05,.03]))", "with torch.no_grad():\n    m.base_model.scq.W2.bias.copy_(torch.tensor([.1,-.05,.03]))\n    if arm!='S':m.base_model.rf.V2.bias.copy_(torch.tensor([.02,.01,-.01]))")
s=s.replace("raw,delta=p.scq_arrays(torch,np,m,co)", "raw,delta,stages,applies=p.scq_arrays(torch,np,m,co)")
s=s.replace("(np.any(delta!=0) if arm=='S' else np.all(delta==0))", "np.any(delta!=0) and applies is (arm!='S') and np.allclose(stages['Q0']+stages['delta0'],stages['Q1']) and np.allclose(stages['Q1']+stages['delta1'],stages['Q2'])")
s=s.replace("built,be=p.build_scq_model(factory,legacy,dict(variant='S'),initialization)", "built,be=p.build_scq_model(factories,legacy,dict(variant='S'),initialization,rf_initialization)")
s=s.replace("check('22 actual production SCQ builder dispatch signature',be['scq']['variant']=='S' and hasattr(built.base_model,'scq'))", "check('22 actual production SCQ builder dispatch signature',be['scq']['variant']=='S' and hasattr(built.base_model,'scq'))\n   for v in ('RF-Static','RF-Requery'):\n    bm,bv=p.build_scq_model(factories,legacy,dict(variant=v),initialization,rf_initialization);check('production RF dispatch '+v,bv['rf']['variant']==v and bm.base_model.rf.variant==v);del bm")
s=s.replace("if arm=='S':self.scq=nn.Identity();self._scq_last_info=None", "self.scq=nn.Identity();self._scq_last_info=None\n    if arm.startswith('RF-'):self.rf=nn.Identity();self.rf.variant=arm")
s=s.replace("def __init__(self,arm='B',fail=False)", "def __init__(self,arm='S',fail=False)")
s=s.replace("self.base_model._scq_last_info=dict(Q0=raw,Qused=co,delta=delta)", "d0=delta;d1=torch.full_like(raw,.02) if hasattr(self.base_model,'rf') else torch.zeros_like(raw);q1=co;co=q1+d1;self.base_model._scq_last_info=dict(Q0=raw,Qused=co,delta=d0+d1,Q1=q1,delta0=d0,delta1=d1)")
s=s.replace("[105]*4", "[105]*6").replace("len(states)==4", "len(states)==6")
s=s.replace("{'prediction','coarse','Qraw','delta'}", "{'prediction','coarse','Qraw','delta','Q0','Q1','Q2','delta0','delta1'}")
s=s.replace("list(range(1,421))", "list(range(1,631))").replace("len(events)==845", "len(events)==1267").replace("==424", "==634").replace("['B_C']", "['Sref_C']")
s=s.replace("actual_mother_artificial_full_forwards=2", "actual_mother_artificial_full_forwards=3")
s=s.replace("SCQ_NATIVE_CPU_CONTRACT_PASS", "RF_NATIVE_CPU_CONTRACT_PASS")
s=s.replace("source_bindings=[*impl.values(),initialization]", "source_bindings=[*impl.values(),initialization,rf_initialization]")
# Assert unchanged inherited behavior against the actual parent entry, not older LQI.
s=s.replace("old=R/'outputs/cranial_bcsp_fullmamba_20261110/lqi_native_prediction_implementation_v1/bcsp_lqi_twofold_native_predict_v1.py'", "old=R/'outputs/cranial_bcsp_scq_BS_CD_native_prediction_preparation_20261114_v1/implementation_v1/resource_rebind_v2/bcsp_scq_fourmodel_native_predict_v2.py'")
# Additional authorization/identity/arm/path and stage diagnostics regressions before execution.
needle="original_exact=p.exact"
s=s.replace(needle,"""for name,change in [('wrong execution GPU selector',lambda v:v['environment'].update(CUDA_VISIBLE_DEVICES='GPU-WRONG')),('wrong device-confound disclosure',lambda v:v['comparison_qualification'].update(strict_same_device_D_pair=True)),('old model budget',lambda v:v.update(forward_budget=420)),('unauthorized current request flag',lambda v:v.update(execution_authorized=True))]:
   reject(name,lambda:p.authorize(*triplet(change)))
  original_exact=p.exact""")
needle="del built,actual;import gc;gc.collect()"
s=s.replace(needle,"""# Stage equations reject a silently permuted intermediate, even with Q2 correct.
  bad_info=dict(Q0=torch.zeros(1,256,3),Q1=torch.ones(1,256,3),Qused=torch.zeros(1,256,3),delta=torch.zeros(1,256,3),delta0=torch.zeros(1,256,3),delta1=torch.zeros(1,256,3))
  fake_rf=types.SimpleNamespace(base_model=types.SimpleNamespace(scq=True,rf=True,_scq_last_info=bad_info))
  reject('RF stage equation mismatch rejected',lambda:p.scq_arrays(torch,np,fake_rf,np.zeros((1,256,3),np.float32)))
  del built,actual;import gc;gc.collect()""")
ast.parse(s)
test=S/'test_RF_native_prediction_cpu_v1.py';test.open('x',encoding='utf-8',newline='\n').write(s)
# Refresh source binding after pre-test static review corrections; no validation has run yet.
def rec(p):return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
ctx=read=lambda p:json.loads(p.read_bytes())
c=ctx(S/'context_v1.json');e=S/'bcsp_scq_rf_sixmodel_native_predict_v1.py';c['candidate']['entry'].update(bytes=rec(e)['bytes'],sha256=rec(e)['sha256'])
(S/'context_v1.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
st=ctx(S/'static_review_v1.json');st['entry']=rec(e);st['test']=rec(test);st['checks']['actual_admission_schema_reviewed']=True;st['checks']['exact_runtime_reader_chain_includes_entry_helper_RF_sources']=True
(S/'static_review_v1.json').write_text(json.dumps(st,indent=2)+'\n',encoding='utf-8')
print(test)
