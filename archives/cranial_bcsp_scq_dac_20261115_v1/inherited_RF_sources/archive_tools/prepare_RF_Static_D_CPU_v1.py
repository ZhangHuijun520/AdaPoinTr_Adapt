from pathlib import Path
import ast
R=Path(__file__).resolve().parent.parent;B=R/'outputs/scq_rf_Requery_D_implementation_20261115_v1';O=R/'outputs/scq_rf_Static_D_implementation_20261115_v1'
s=(B/'test_RF_Requery_D_entry_cpu_v1.py').read_text(encoding='utf-8')
s=s.replace("('arm','RF-Static')","('arm','NEGATIVE_ARM')").replace("('variant','RF-Static')","('variant','NEGATIVE_ARM')").replace("variant='RF-Static'","variant='NEGATIVE_ARM'")
s=s.replace('RF-Requery','RF-Static').replace('NEGATIVE_ARM','RF-Requery')
s=s.replace("BR=R/'outputs/scq_rf_Requery_C_implementation_20261114_v1'","BR=R/'outputs/scq_rf_Static_C_implementation_20261114_v1'")
s=s.replace('bcsp_scq_rf_Requery_D_training_entry_v1.py','bcsp_scq_rf_Static_D_training_entry_v1.py').replace('bcsp_scq_rf_Requery_C_training_bridge_v1.py','bcsp_scq_rf_Static_C_training_bridge_v1.py').replace('RF_REQUERY_D','RF_STATIC_D').replace('cpu_requery_D_entry_batch_v1','cpu_static_D_entry_batch_v1')
s=s.replace("'initialization_reference'","'paired_requery'")
s=s.replace("ctx['parent_C_request']","ctx['parent_Requery_D_request']")
# D-to-C substitution tests use the real frozen C request, not the historical D source.
s=s.replace("bad[field]=copy.deepcopy(ctx['parent_Requery_D_request'][field])", "bad[field]=copy.deepcopy(json.loads((R/'outputs/scq_rf_Requery_C_implementation_20261114_v1/pending_transport_v1/payload/SCQ_RF_Requery_C_training_execution_request_v1.json').read_bytes())[field])")
old="torch.equal(info['N1'],knn(8,partial[:,:256],info['Q1']))"
assert old in s;s=s.replace(old,"torch.equal(info['N1'],info['N0'])")
s=s.replace("requery_model,_=build_rf()", "requery_base=build_s();requery_model,_=rfactory.install(requery_base,'RF-Requery',rfinit)")
# Keep the explicit Static/Requery mechanism fixture; only the dispatch arm is Static.
s=s.replace("static_model,_=rfactory.install(base,'RF-Static',rfinit)", "static_model,_=rfactory.install(base,'RF-Static',rfinit)")
start=s.index("  sample_ret=(Q1,");end=s.index('  inert=SimpleNamespace',start)
s=s[:start]+"""  sample_ret=(Q1,Q1[:,:0],Q1[:,:0],Q1.repeat_interleave(32,1))
  reject('Static logging refuses mixed neighbor selection',lambda:e.scq_geometry(logging_model,sample_ret))
"""+s[end:]
anchor="  script=e.render_launcher(q,'a'*64,'b'*64,'c'*64)"
extra="""  check('historical CUDA admission explicitly qualified',admission['native_validation_scope']=='HISTORICAL_IMPLEMENTATION_ONLY' and admission['cross_device_continuation'])
  for key,value in [('hostname','UNBOUND-HOST'),('gpu_uuid','GPU-UNBOUND'),('driver_version','UNKNOWN'),('torch_version','OTHER')]:
   bad=copy.deepcopy(q);bad['identity'][key]=value;reject('unaccepted current identity drift '+key,lambda bad=bad:authorize(bad))
  bad=copy.deepcopy(q);bad['historical_identity']['gpu_uuid']='GPU-FAKE';reject('historical identity rewrite refused',lambda:authorize(bad))
  bad=copy.deepcopy(q);bad['accepted_device_migration']['sha256']='0'*64;reject('unbound migration supplement refused',lambda:authorize(bad))
  bad=copy.deepcopy(q);bad['comparison_qualification']['strict_same_device_D_pair']=True;reject('false strict paired claim refused',lambda:authorize(bad))
"""
assert s.count(anchor)==1;s=s.replace(anchor,extra+anchor)
p=O/'test_RF_Static_D_entry_cpu_v1.py';ast.parse(s);compile(s,str(p),'exec')
with p.open('x',encoding='utf-8',newline='\n') as f:f.write(s)
print('STATIC_D_CPU_BATCH_STATIC_PASS_NOT_EXECUTED')
