from pathlib import Path
import json,hashlib,tarfile,os,socket
assert socket.gethostname()=='shu-common-25721452-notebook-lwwgl9-0' and os.getuid()==1000
p=Path('/home/jovyan/adapointr_work/PoinTr');a=Path('/home/jovyan/bcsp_spcg_cuda_pending_20261116_v2.tar.gz')
assert hashlib.sha256(a.read_bytes()).hexdigest()=='ac9dbd1007db1ec5d3824684361ce55691bb36aaa41b8f484b5b9b4f37a6a5e4'
t=tarfile.open(a);qraw=t.extractfile('payload/SPCG_CUDA_execution_request_v1.json').read();assert hashlib.sha256(qraw).hexdigest()=='00a69c5cc3d42e04f4caa3c21650dd58db5d8c1b446741a1b42caf6730213d0f'
q=json.loads(qraw);mapping=json.load(t.extractfile('installation_mapping_v1.json'));root=Path(mapping['remote_root'])
def exact(r):
 v=Path(r['path']);assert not any(x.is_symlink() for x in (v,*v.parents));assert v.stat().st_size==r['bytes'] and hashlib.sha256(v.read_bytes()).hexdigest()==r['sha256'],str(v)
rows=list(q['implementation'].values())[:4]+q['dependencies']+[q[k] for k in ['helper','parent_helper','timezone_implementation','preflight_scope','static_config','mother_source']]
for r in rows:exact(r)
s=json.loads(Path(q['preflight_scope']['path']).read_bytes())
for r in s['bindings']['provider']+s['bindings']['environment_metadata']:exact(r)
sources=[dict(path=str(Path(q['model_root'])/r.get('relative_target',r.get('relative_path'))),bytes=r['bytes'],sha256=r['sha256']) for r in s['bindings']['candidate']+s['bindings']['isolated_model_project_sources']]
for r in sources:exact(r)
for r in q['real_inputs']:exact(r)
print(json.dumps(dict(status='ALL_REUSED_AND_FIVE_INPUT_FILE_HASHES_PASS',sources=len(sources),dependencies=len(rows))))
