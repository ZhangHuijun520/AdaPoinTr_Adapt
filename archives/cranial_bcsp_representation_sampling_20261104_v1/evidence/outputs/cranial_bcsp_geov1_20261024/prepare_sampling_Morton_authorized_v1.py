"""Render candidate-only authorized operations from the proven transport and launcher."""
import ast,base64,hashlib,json
from pathlib import Path
B=Path(__file__).resolve().parent
O=B/'sampling_model_AB_foldC_seed0_20261103_v1'
C=O/'Morton_training_request_v1'
A=C/'authorized_execution_v1'
S='d4a44a990c0b3f0b91522c6f9803074a34e6c3803c243bf08e8a46ace42eeae3'
def h(b):return hashlib.sha256(b).hexdigest()
def save(n,b):
 with (A/n).open('xb') as f:f.write(b)
def main():
 sr=(C/'candidate_training_execution_request_v1.json').read_bytes();assert h(sr)==S
 s=json.loads(sr);qr=(C/'training_entry_request_v1.json').read_bytes();assert h(qr)==s['inner_request']['sha256']
 mr=(C/'non_overwrite_control_installation_mapping_v1.json').read_bytes();assert h(mr)==s['transport']['installation_mapping']['sha256'];m=json.loads(mr)
 for r in s['transport']['files']:
  raw=Path(r['path']).read_bytes();assert len(raw)==r['bytes'] and h(raw)==r['sha256']
 for r in m['files']:
  raw=Path(r['local_path']).read_bytes();assert len(raw)==r['bytes'] and h(raw)==r['sha256']
 audit=Path(s['parent_baseline_audit']['path']).read_bytes();assert h(audit)==s['parent_baseline_audit']['sha256'] and json.loads(audit)['status']=='FORMAL_POST_TRAINING_FREEZE_AUDIT_PASS'
 A.mkdir()
 tree=ast.parse((B/'prepare_sampling_AB_authorized_v2.py').read_text(encoding='utf-8'))
 values={}
 for n in ast.walk(tree):
  if isinstance(n,ast.Assign) and isinstance(n.value,ast.Constant) and isinstance(n.value.value,str):
   for t in n.targets:
    if isinstance(t,ast.Name):values[t.id]=n.value.value
 common=values['common'];common=common[:common.index('def destination(member):')]+'''def emit(v):print(json.dumps(v,ensure_ascii=True),flush=True)
def record_exact(r):return exact(r['path'],r['bytes'],r['sha256'])
def reused():
 for r in SCOPE['reused_bindings']:record_exact(r)
 rows=[json.loads(line) for line in record_exact(SCOPE['reused_payload']['manifest']).decode().splitlines()]
 need(len(rows)==315,'candidate count');root=Path(Q['data_root']);seen=set()
 for r in rows:
  p=root/r['point_path'];need(root in p.parents and p.suffix=='.npz' and p not in seen,'candidate path');seen.add(p)
  regular(p);need(h(p.read_bytes())==r['sha256'],'candidate hash: '+str(p))
 ref=json.loads(PAIR_RAW)
 for key in ['baseline_completion','baseline_initialization','baseline_checkpoint']:record_exact(ref[key])
 need(json.loads(Path(ref['baseline_completion']['path']).read_text())['updates']==3900,'baseline completion')
 need(Path(ref['baseline_completion']['path']).with_name('exit_code.txt').read_text().strip()=='0','baseline exit')
def fresh():
 f=SCOPE['future_paths'];p=Path(f['control']);parents(p.parent);absent(p);need(os.access(p.parent,os.W_OK),'control parent permission')
 parents(Path(f['output']).parent);absent(Path(f['output']))
 need(subprocess.run(['tmux','has-session','-t',f['tmux']],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=5).returncode!=0,'session exists')
def uploaded():
 for r in SCOPE['transport']['files']:record_exact(dict(r,path='/home/jovyan/'+r['filename']))
 prefix='bcsp_sampling_ab_foldc_morton_control_v1'
 rows={}
 for line in Path('/home/jovyan/'+prefix+'.contents.sha256').read_text().splitlines():
  digest,name=line.split('  ',1);need(name not in rows,'duplicate member');rows[name]=digest
 need(rows=={r['member']:r['sha256'] for r in MAPPING['files']},'exact3 member list')
 need(Path('/home/jovyan/'+prefix+'.bytes').read_text().strip()=='3311','archive bytes sidecar')
 payload={}
 with tarfile.open('/home/jovyan/'+prefix+'.tar.gz','r:gz') as tf:
  members=tf.getmembers();need(len(members)==3 and {x.name for x in members}==set(rows),'archive set')
  for x in members:
   need(x.isfile() and x.size<=65536,'archive regular member');raw=tf.extractfile(x).read();need(h(raw)==rows[x.name],'archive content hash');payload[x.name]=raw
 return payload
'''
 # Keep all other resource, source and single-launch behavior unchanged.
 common=common.replace("json.loads(Path(ref['baseline_completion']['path']).read_text())['updates']==3900", "json.loads(Path(ref['baseline_completion']['path']).read_text()).get('optimizer_updates',json.loads(Path(ref['baseline_completion']['path']).read_text()).get('updates'))==3900")
 const='SCOPE_RAW=base64.b64decode('+repr(base64.b64encode(sr).decode())+');SCOPE=json.loads(SCOPE_RAW)\n'
 const+='Q_RAW=base64.b64decode('+repr(base64.b64encode(qr).decode())+');Q=json.loads(Q_RAW)\n'
 const+='MAPPING='+repr(m)+'\nPAIR_RAW=base64.b64decode('+repr(base64.b64encode((C/'paired_initialization_receipt_v1.json').read_bytes()).decode())+')\n'
 const+='need(h(SCOPE_RAW)=='+repr(S)+' and h(Q_RAW)==SCOPE["inner_request"]["sha256"],"scope/inner hash")\n'
 grant='Exact user text: 已上传，单独授权上述哈希\nReference resolution (not quotation): current candidate execution scope SHA256 '+S+'; inner request SHA256 '+h(qr)
 const+='USER_GRANT='+repr(grant)+'\n'
 pre="identity();uploaded();reused();fresh();emit(dict(status='UPLOAD_AND_DESTINATION_READONLY_PASS',scope_sha256=h(SCOPE_RAW),candidate_files=315,new_metadata=3,server_writes=0,seconds=time.monotonic()-START))\n"
 install='''created=[]
try:
 identity();payload=uploaded();reused();fresh()
 for r in MAPPING['files']:absent(Path(r['destination']))
 os.mkdir(SCOPE['future_paths']['control'],0o755)
 for r in MAPPING['files']:
  p=Path(r['destination']);parents(p.parent);need(str(p.parent)==SCOPE['future_paths']['control'] and p.name==r['member'],'mapping boundary')
  fd=os.open(str(p),os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o644)
  with os.fdopen(fd,'wb') as f:f.write(payload[r['member']]);f.flush();os.fsync(f.fileno())
  created.append(str(p));record_exact(dict(r,path=r['destination']))
 emit(dict(status='INSTALLATION_3_HASH_PASS',created=created,scope_sha256=h(SCOPE_RAW),training_started=False))
except BaseException as e:
 emit(dict(status='FAILED_STOP_NO_RETRY',error=repr(e),created=created));raise
'''
 materialize=values['materialize']
 start=materialize.index(' identity();rows,archive=uploaded()');end=materialize.index(' import importlib.util',start)
 materialize=materialize[:start]+''' identity();uploaded();reused()
 for r in MAPPING['files']:record_exact(dict(r,path=r['destination']))
'''+materialize[end:]
 materialize=materialize.replace("=={'training_entry_request_v1.json'}","==set(SCOPE['launcher_contract']['control_initial_filenames'])")
 marker=" need('torch' not in sys.modules,'unexpected model import during preparation')"
 materialize=materialize.replace(marker," ref=json.loads(PAIR_RAW);entry.validate_pair_initialization(ref,Q,ref['parameter_sha256'],ref['persistent_state_sha256'],entry.canonical_sha(entry.json_bound(Q['order_plan'])))\n"+marker)
 template=(B/'resource_rebind_implementation_v1/first_training_request_foldC_8192_v1/local_byte_serialization_v2/short_driver_template_v2.py').read_text(encoding='utf-8')
 for name,body in [('precheck',pre),('install',install),('materialize',materialize)]:
  raw=(common+const+body).encode('utf-8');ast.parse(raw);save(name+'_server_v1.py',raw)
  driver=template.replace('__DERIVED_CONTROLLER_PAYLOAD_SHA256__',h(raw));ast.parse(driver);save(name+'_driver_v1.py',driver.encode())
 save('operation_plan_v1.json',json.dumps(dict(scope_sha256=S,payloads={n:h((A/(n+'_server_v1.py')).read_bytes()) for n in ['precheck','install','materialize']},only_one_training=True,metadata_files=3),indent=2).encode())
 inv=(B/'invoke_sampling_AB_authorized_v2.py').read_text(encoding='utf-8').replace("sampling_model_AB_foldC_seed0_20261103_v1/authorized_execution_v2","sampling_model_AB_foldC_seed0_20261103_v1/Morton_training_request_v1/authorized_execution_v1").replace('INSTALLATION_647_HASH_PASS','INSTALLATION_3_HASH_PASS')
 ast.parse(inv);(B/'invoke_sampling_Morton_authorized_v1.py').write_bytes(inv.encode())
 obs=(B/'observe_sampling_AB_status_v2.py').read_text(encoding='utf-8').replace("A=O/'authorized_execution_v2'","A=O/'Morton_training_request_v1/authorized_execution_v1'").replace("O/'V1_training_execution_request_v2.json'","O/'Morton_training_request_v1/candidate_training_execution_request_v1.json'").replace('4a889afad90b1a8a52fcb75691c71990d03af8b7d120a96608ac4b9b85cb7a62',S)
 ast.parse(obs);(B/'observe_sampling_Morton_status_v1.py').write_bytes(obs.encode())
 save('local_static_review_v1.json',json.dumps(dict(status='STATIC_PASS_NO_SERVER_ACTION',scope_sha256=S,authorized_user_text='已上传，单独授权上述哈希',only_new_controls=3,unchanged_production_code=True),indent=2).encode())
 print('CANDIDATE_OPERATIONS_RENDERED_STATIC_PASS')
if __name__=='__main__':main()
