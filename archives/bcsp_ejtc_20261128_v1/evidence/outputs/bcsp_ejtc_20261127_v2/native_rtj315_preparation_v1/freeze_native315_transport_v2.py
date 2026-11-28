"""Path regression, bounded P3 delta, final pending request and seven-file transport."""
from pathlib import Path,PurePosixPath
import ast,copy,gzip,hashlib,importlib.util,io,json,tarfile
d=Path(__file__).resolve().parent;base=d.parent
h=lambda b:hashlib.sha256(b).hexdigest()
load=lambda p:json.loads(p.read_bytes())
def rec(p):return dict(local_path=str(p),bytes=p.stat().st_size,sha256=h(p.read_bytes()))
def write(p,q):
 with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(q,f,ensure_ascii=False,indent=2);f.write('\n')
def module(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
wpath=d/'ejtc_native_rtj315_v2.py';w=module('worker',wpath)
old=load(d/'EJTC_RTJ_D_native315_scope_v1.json');scope=load(d/'EJTC_RTJ_D_native315_scope_v2.json')
stripped=copy.deepcopy(scope);stripped.pop('input_root')
for a,b in zip(stripped['inputs'],old['inputs']):a['input']['path']=b['input']['path']
assert stripped==old
oldtext=(d/'ejtc_native_rtj315_v1.py').read_text();text=wpath.read_text()
expected=oldtext.replace("SCOPE_SHA = 'f61e62cf2cbaf9e81b2e60598c1e0fede3a7b058368694012df0c7fb121606d2'",f"SCOPE_SHA = '{h((d/'EJTC_RTJ_D_native315_scope_v2.json').read_bytes())}'").replace("str(PurePosixPath(parent['data_root']) / original['point_path'])","str(PurePosixPath(scope['input_root']) / original['point_path'])")
assert text==expected
parent=load(base.parent/'bcsp_oasg_20261124_v1/p3_a_d_v1/OASG_A_D_training_execution_request_v1.json')
geo=base.parent/'cranial_bcsp_geov1_20261024';fold=load(geo/'consolidated_binding_v1/fold_binding.json')
manifest=[json.loads(r) for r in (geo/'real_data_qc_v1/manifest_8192.jsonl').read_bytes().splitlines()]
assert len(w.select_inputs(scope,parent,fold,manifest))==105
def rejected(x):
 try:w.select_inputs(x,parent,fold,manifest)
 except ValueError:return True
 raise AssertionError('Changed path accepted')
x=copy.deepcopy(scope)
for a,b in zip(x['inputs'],old['inputs']):a['input']['path']=b['input']['path']
assert rejected(x)
x=copy.deepcopy(scope);x['input_root']=parent['data_root'];assert rejected(x)
x=copy.deepcopy(scope);x['inputs'][0]['input']['path']=old['inputs'][0]['input']['path'];assert rejected(x)
actual=load(d/'server_actual_paths_v1/Native315_actual_path_readonly_receipt_v1.json')
assert all(r['input']['path']==p['actual']['path'] and r['input']['sha256']==p['actual']['sha256'] and r['partial_array_sha256']==p['actual']['partial_array_sha256'] for r,p in zip(scope['inputs'],actual['cases']))
reg=d/'Native315_path_CPU_regression_v2.json'
write(reg,dict(status='PATH_BINDING_CPU_REGRESSION_PASS',checks=6,details=['105 corrected paths accepted against unchanged Fold D split','All old paths rejected','Wrong input root rejected','One stale path rejected','All file/partial hashes equal read-only server evidence','Scope delta limited to input_root and 105 paths; worker delta only root selection and scope hash'],test=rec(Path(__file__)),remote_operations=0))
cpu=d/'cpu_validation_v3/Native315_CPU_validation_receipt_v1.json';start=d/'cpu_startup_validation_v2/startup_receipt_v1.json'
c=load(cpu);s=load(start);assert c['passed']==28 and c['CUDA_initialized'] is False and s['worker_sha256']==c['worker_sha256']==h(wpath.read_bytes())
for p in (wpath,d/'launch_ejtc_native315_v1.py',d/'verify_native315_cpu_v3.py',d/'verify_native315_startup_cpu_v2.py'):compile(p.read_bytes(),str(p),'exec')
q=load(d/'Native315_execution_request_CPU_fixture_v2.json')
assert c['launcher_sha256']==q['launch']['launcher']['sha256']
p3=d/'Native315_P3_review_v2.json'
write(p3,dict(status='EJTC_NATIVE315_P3_LIMITED_REVIEW_PASS',review_type='Bounded local differential review, not an independent external review',worker=rec(wpath),prior_P3=rec(d/'Native315_P3_review_v1.json'),CPU=rec(cpu),startup_CPU=rec(start),path_regression=rec(reg),
 checks=['Exact worker text differs only in frozen scope hash and input path root expression','Launcher bytes unchanged','Original scope equal after reverting only 105 paths and removing input_root','Fold D case/source identities, schedule, input bytes/array hashes, normalization, checkpoint identities, seeds and 315/0 contract unchanged','28 full CPU contracts plus six path regression checks and actual main startup pass','No CUDA/preflight/server operation in this revision'],limitations=c['limitations']+s['limitations']))
q['readiness_status']='PATH_BINDING_CPU_P3_PASS_PENDING_UPLOAD_INSTALL_AND_EXECUTION_RECHECK'
q['validation_evidence']=dict(CPU=rec(cpu),startup_CPU=rec(start),path_regression=rec(reg),P3=rec(p3),CPU_does_not_certify_CUDA=True,GPU_preflight_not_repeated=True)
q['supersedes_request_sha256']='758f8297612a4c9b2253b88a4401df308002dd1426dd4edf48e0a2925500a5cb'
q['path_revision']['server_snapshot_not_execution_admission']=True
final=d/'EJTC_RTJ_D_native315_execution_request_h7vvrr_v2.json';write(final,q);raw=final.read_bytes();rid=h(raw)
m=module('materializer',Path(q['authorization_materializer']['local_path']))
a,r=m.materialize(raw,'Final-byte CPU fixture only; no live execution authorization',execution_authorized=True)
w.authorize(q,rid,json.loads(a),h(a),json.loads(r))
with Path(str(final)+'.sha256').open('x',encoding='ascii') as f:f.write(rid+'  '+final.name+'\n')
t=d/'transport_h7vvrr_v2';t.mkdir(exist_ok=False)
payload={};files=[];root=q['binding']['install_root']
def add(p,binding):
 b=p.read_bytes();assert len(b)==binding['bytes'] and h(b)==binding['sha256']
 member=PurePosixPath(binding['path']).name;assert str(PurePosixPath(root)/member)==binding['path'] and member not in payload
 payload[member]=b;files.append(dict(member=member,target=binding['path'],bytes=len(b),sha256=h(b)))
for key,p in [('worker',wpath),('scope',d/'EJTC_RTJ_D_native315_scope_v2.json')]:add(p,q['files'][key])
add(d/'launch_ejtc_native315_v1.py',q['launch']['launcher'])
for arm,p in scope['training_freeze_receipts'].items():add(Path(p['local_path']),q['files']['receipt_'+arm])
add(final,dict(path=q['launch']['request_path'],bytes=len(raw),sha256=rid));assert len(payload)==7
tar=io.BytesIO()
with tarfile.open(fileobj=tar,mode='w',format=tarfile.USTAR_FORMAT) as archive:
 for name in sorted(payload):
  info=tarfile.TarInfo(name);info.size=len(payload[name]);info.mode=0o644;info.mtime=0;info.uid=info.gid=0;archive.addfile(info,io.BytesIO(payload[name]))
packed=gzip.compress(tar.getvalue(),compresslevel=9,mtime=0);bp=t/'EJTC_RTJ_D_native315_h7vvrr_transport_v2.tar.gz'
with bp.open('xb') as f:f.write(packed)
with Path(str(bp)+'.sha256').open('x',encoding='ascii') as f:f.write(h(packed)+'  '+bp.name+'\n')
with tarfile.open(fileobj=io.BytesIO(packed),mode='r:gz') as archive:
 items=archive.getmembers();assert len(items)==7 and set(x.name for x in items)==set(payload)
 for item in items:assert item.isfile() and archive.extractfile(item).read()==payload[item.name]
prior=load(base/'p1_cuda_preparation_v1/server_readonly_h7vvrr_v1/server_readiness_receipt_v1.json')
reuse={p:dict(bytes=r['expected'][0],sha256=r['expected'][1]) for p,r in prior['files'].items() if 'training_input' not in r['groups']}
for binding in [q['binding']['interpreter'],*q['files'].values(),*q['checkpoints'].values()]:
 if not PurePosixPath(binding['path']).is_relative_to(PurePosixPath(root)):reuse[binding['path']]=dict(bytes=binding['bytes'],sha256=binding['sha256'])
for row in scope['inputs']:reuse[row['input']['path']]=dict(bytes=row['input']['bytes'],sha256=row['input']['sha256'])
assert len(reuse)==167
mapping=dict(schema='bcsp-ejtc-native315-install-mapping-v2',status='AWAITING_UPLOAD_VERIFICATION_AND_SEPARATE_INSTALL_AUTHORIZATION',request_sha256=rid,identity=q['binding']['identity'],
 upload=dict(path='/home/jovyan/'+bp.name,bytes=len(packed),sha256=h(packed)),upload_checksum_path='/home/jovyan/'+bp.name+'.sha256',
 new_install_root=root,directories_to_create=[root],files=files,new_file_count=7,reused_assets=reuse,reused_asset_count=len(reuse),
 output_must_be_absent=q['binding']['output'],runtime_controls_must_be_absent=[q['launch'][k] for k in ('authorization_path','runtime_path','single_attempt_log','resource_log','dispatch_log','exit_code_path')],session_must_be_absent=q['launch']['session_name'],resources=q['binding']['resources'],matrix_disk_budget_bytes=q['launch']['matrix_disk_budget_bytes'],
 readonly_path_evidence=rec(d/'server_actual_paths_v1/Native315_actual_path_readonly_receipt_v1.json'),P3=rec(p3),overwrite=False,remote_install_authorized=False,execution_authorized=False,
 policy='Before any write recheck current identity/GPU/resources, both upload files and exact seven-member inventory, all 167 reused file sizes/hashes, 105 partial-array hashes, safe parent directories, every installation/output/control target and fixed session absent. Exclusively create one named directory and seven named files, read back hashes. Do not overwrite/delete, materialize runtime controls, run tests, CUDA, prediction, scoring or training. Prior read-only snapshot is incomplete for some source assets: all 167 must pass a fresh recheck before installation.')
mp=t/'EJTC_RTJ_D_native315_h7vvrr_install_mapping_v2.json';write(mp,mapping)
with Path(str(mp)+'.sha256').open('x',encoding='ascii') as f:f.write(h(mp.read_bytes())+'  '+mp.name+'\n')
receipt=dict(status='EJTC_NATIVE315_V2_MINIMAL_TRANSPORT_FROZEN',request=rec(final),request_sha256=rid,bundle=rec(bp),mapping=rec(mp),P3=rec(p3),archive_members=7,directories_to_create=1,reused_asset_count=167,CPU_checks=28,path_regression_checks=6,actual_main_CPU_startup_pass=True,final_byte_authorize_CPU_pass=True,live_authorization_materialized=False,server_operations=0,installation_authorized=False,execution_authorized=False,prior_request_not_to_execute=q['supersedes_request_sha256'])
write(t/'transport_freeze_receipt_v2.json',receipt)
print(json.dumps(receipt,ensure_ascii=False))
