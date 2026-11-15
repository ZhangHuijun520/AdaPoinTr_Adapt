from pathlib import Path
import ast
R=Path(__file__).resolve().parent.parent;B=R/'outputs/scq_rf_Static_C_implementation_20261114_v1';O=R/'outputs/scq_rf_Requery_C_implementation_20261114_v1'
s=(B/'test_RF_Static_C_entry_cpu_v1.py').read_text(encoding='utf-8')
# Preserve true negative-arm cases while switching the positive caller to Requery.
s=s.replace("('arm','RF-Requery')","('arm','NEGATIVE_ARM')").replace("('variant','RF-Requery')","('variant','NEGATIVE_ARM')").replace("variant='RF-Requery'","variant='NEGATIVE_ARM'")
s=s.replace('RF-Static','RF-Requery').replace('NEGATIVE_ARM','RF-Static').replace('Static_C','Requery_C').replace('STATIC_C','REQUERY_C').replace('cpu_static_entry_batch_v1','cpu_requery_entry_batch_v1').replace('dispatch_Static','dispatch_Requery')
s=s.replace("['rf_initialization','paired_baseline','runtime','rf_factory','rf_residual']","['rf_initialization','paired_baseline','paired_static','runtime','rf_factory','rf_residual']")
s=s.replace("if field=='paired_baseline':bad[field]=None","if field in ('paired_baseline','paired_static'):bad[field]=None")
anchor="  script=e.render_launcher(q,'a'*64,'b'*64,'c'*64)"
assert anchor in s
s=s.replace(anchor,"""  bad=copy.deepcopy(q);bad['expected_full_initialization']['parameter_sha256']='0'*64
  reject('changed full Static initial fingerprint refused',lambda:authorize(bad))
"""+anchor)
s=s.replace("parts['N0_N1_equal'] and set(parts)","parts['N0_N1_equal'] is True and set(parts)")
old="check('Static indices exactly reused after nonzero Q1',torch.equal(info['N0'],info['N1']) and torch.equal(info['Qused'],out[0].detach()) and bool((info['Q1']!=info['Q0']).any()))"
new="check('Requery indices recomputed at Q1 and Q2 consumed',torch.equal(info['N1'],knn(8,partial[:,:256],info['Q1'])) and torch.equal(info['Qused'],out[0].detach()) and bool((info['Q1']!=info['Q0']).any()))"
assert old in s;s=s.replace(old,new)
s=s.replace("partial[:,:256][batch,info['N0']]-info['Q1'][:,:,None]","partial[:,:256][batch,info['N1']]-info['Q1'][:,:,None]")
s=s.replace("check('Q2 coarse identity and Static N0 reuse logged'","check('Q2 coarse identity and measured neighbor equality logged'")
s=s.replace("check('actual Static relative mean recomputed at Q1'","check('actual Requery relative mean uses Q1 and N1'")
anchor="  inert=SimpleNamespace(__file__=str(runtime_path)"
assert s.count(anchor)==1
extra="""  # One fixed nondegenerate mechanism fixture; no radius/axis/weight scan.
  base=build_s();static_model,_=rfactory.install(base,'RF-Static',rfinit)
  requery_model,_=build_rf()
  check('Static Requery full artificial initial states identical',set(static_model.state_dict())==set(requery_model.state_dict()) and all(tensor_sha(t)==tensor_sha(requery_model.state_dict()[n]) for n,t in static_model.state_dict().items()))
  M=torch.zeros(1,256,3);M[0,:,0]=torch.arange(256)*.01
  Ff=torch.arange(256*384,dtype=torch.float32).reshape(1,256,384)/1000
  z=torch.zeros(1,1024);Qraw=M.clone();Q1=Qraw+torch.tensor([.5,0.,0.]);N0=knn(8,M,Qraw)
  hs,ds=static_model.base_model.rf.describe(M,Ff,z,Q1,N0);hr,dr=requery_model.base_model.rf.describe(M,Ff,z,Q1,N0)
  check('fixed fixture has true changed neighbor sets',not torch.equal(ds['indices'],dr['indices']) and torch.equal(ds['indices'],N0) and torch.equal(dr['indices'],knn(8,M,Q1)))
  check('fixed fixture conditions differ without model changes',not torch.equal(hs,hr) and not torch.equal(ds['geometry'],dr['geometry']))
  fake_info=dict(info);fake_info.update(Q0=Qraw,delta=(Q1-Qraw),Q1=Q1,delta0=(Q1-Qraw),delta1=torch.zeros_like(Q1),Qused=Q1,N0=N0,N1=dr['indices'])
  logging_model=SimpleNamespace(base_model=SimpleNamespace(rf=SimpleNamespace(variant='RF-Requery'),_scq_last_info=fake_info))
  sample_ret=(Q1,Q1[:,:0],Q1[:,:0],Q1.repeat_interleave(32,1));summary=e.scq_geometry(logging_model,sample_ret)
  check('logging permits changed neighbors and measures overlap',summary['N0_N1_equal'] is False and len(summary['neighbor_set_overlap'])==1 and 0<=summary['neighbor_set_overlap'][0]<1)
"""
s=s.replace(anchor,extra+anchor)
for old,new in [('Static authorize','Requery authorize'),('Static indices','Requery indices'),('real RF install','real RF Requery install')]:s=s.replace(old,new)
p=O/'test_RF_Requery_C_entry_cpu_v1.py';ast.parse(s);compile(s,str(p),'exec')
with p.open('x',encoding='utf-8',newline='\n') as f:f.write(s)
print('REQUERY_C_CPU_BATCH_STATIC_PASS_NOT_EXECUTED')
