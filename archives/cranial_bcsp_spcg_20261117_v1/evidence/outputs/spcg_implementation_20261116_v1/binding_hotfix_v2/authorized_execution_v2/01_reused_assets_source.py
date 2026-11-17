from pathlib import Path
import json,hashlib,tarfile,os,socket
assert socket.gethostname()=='shu-common-25721452-notebook-lwwgl9-0' and os.getuid()==1000
p=Path('/home/jovyan/adapointr_work/PoinTr');a=Path('/home/jovyan/bcsp_spcg_binding_hotfix_pending_20261116_v2.tar.gz')
assert hashlib.sha256(a.read_bytes()).hexdigest()=='0a6adcb5b8ad0da94b64e6d54fe63d0d1c8609296011cfb7f2a1ee7ffa337154'
t=tarfile.open(a);qraw=t.extractfile('payload/SPCG_CUDA_execution_request_v2.json').read();assert hashlib.sha256(qraw).hexdigest()=='a2b1961158b58199e212130654ddd274ce617c90e24448f22ba70a0062c2343e'
q=json.loads(qraw);assert q['environment']['CUDA_VISIBLE_DEVICES']==q['identity']['gpu_uuid'];mapping=json.load(t.extractfile('installation_mapping_v2.json'));root=Path(mapping['remote_root'])
def exact(r):
 v=Path(r['path']);assert not any(x.is_symlink() for x in (v,*v.parents));assert v.stat().st_size==r['bytes'] and hashlib.sha256(v.read_bytes()).hexdigest()==r['sha256'],str(v)
rows=list(q['implementation'].values())+q['dependencies']+[q[k] for k in ['helper','parent_helper','timezone_implementation','preflight_scope','static_config','mother_source','probe_asset','head_initialization']]
for r in rows:exact(r)
s=json.loads(Path(q['preflight_scope']['path']).read_bytes())
for r in s['bindings']['provider']+s['bindings']['environment_metadata']:exact(r)
sources=[dict(path=str(Path(q['model_root'])/r.get('relative_target',r.get('relative_path'))),bytes=r['bytes'],sha256=r['sha256']) for r in s['bindings']['candidate']+s['bindings']['isolated_model_project_sources']]
for r in sources:exact(r)
for r in q['real_inputs']:exact(r)
print(json.dumps(dict(status='ALL_REUSED_AND_FIVE_INPUT_FILE_HASHES_PASS',sources=len(sources),dependencies=len(rows))))
