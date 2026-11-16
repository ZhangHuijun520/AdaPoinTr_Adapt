import pathlib,json,hashlib,os,socket
P=pathlib.Path
p=P('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rive_fourmodel_prediction_20261115_v1/RIVE_fourmodel_native_prediction_execution_request_v1.json');b=p.read_bytes();assert hashlib.sha256(b).hexdigest()=='ef7c777af6fceb6836de2516de9bf10b1fc4c7603d71c33de53ef024f167f774'
q=json.loads(b);I=q['identity'];assert socket.gethostname()==I['hostname'] and os.getuid()==I['uid']==1000
import importlib.util
p=P(q['entry']['path']);assert hashlib.sha256(p.read_bytes()).hexdigest()=='935761e12bf42f728dab649c47d070710a7d31830ea3755abd568c0f83a20843'
s=importlib.util.spec_from_file_location('rive_installed_contract_only',p);e=importlib.util.module_from_spec(s);s.loader.exec_module(e)
records=[{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rive_fourmodel_prediction_20261115_v1/RIVE_fourmodel_native_prediction_execution_request_v1.json', 'bytes': 17683, 'sha256': 'ef7c777af6fceb6836de2516de9bf10b1fc4c7603d71c33de53ef024f167f774'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rive_fourmodel_prediction_20261115_v1/control/native_prediction_authorization_v1.json', 'bytes': 689, 'sha256': '4eb6e3a82e1f45ba12a6f76bf11e938efe4aab5389858771ec680e16580091a6'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rive_fourmodel_prediction_20261115_v1/control/native_prediction_runtime_v1.json', 'bytes': 228, 'sha256': 'b51af90679fcbe8c16fd25d452eb0d2b8f42601ebffe9ecb1aa068239fc7bc31'}]
v=e.authorize(*records)
index=e.bound(v['input_index']);runs,rows=e.validate_index(index,e.bound(v['fold_binding']))
e.validate_source(index,None,[json.loads(x) for x in e.exact(v['source_manifest']).read_text().splitlines()]);e.validate_evidence(v,index)
assert len(runs)==4 and len(rows)==420
print(json.dumps(dict(status='INSTALLED_FULL_AUTHORIZE_AND_EVIDENCE_PASS',models=4,rows=420,forwards=0,server_writes=0)))
