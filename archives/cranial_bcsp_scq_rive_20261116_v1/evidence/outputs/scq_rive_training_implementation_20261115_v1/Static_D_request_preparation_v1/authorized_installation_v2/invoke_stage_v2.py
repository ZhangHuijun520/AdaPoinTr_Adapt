import hashlib,importlib.util,json,pathlib,sys
HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[1]
FIX=HERE.parent/'installation_exact_field_fix_v2'
p=FIX/'installation_call_plan_v2.json'
assert hashlib.sha256(p.read_bytes()).hexdigest()=='3d81da566ef3d885547dcdc5f8d6e750dc182cf3d61ffbf81f55275023eabd7d'
plan=json.loads(p.read_text(encoding='utf-8'))
stage=sys.argv[1]; assert stage in ('A','B','C')
i=('A','B','C').index(stage)
for previous in plan['calls'][:i]:
 r=json.loads((HERE/(previous['stage']+'.result.json')).read_text())
 assert r['returncode']==0 and not r['local_timeout']
 assert any(x.get('status')==previous['success_phase'] for x in r['rows'])
c=plan['calls'][i]
b=(FIX/c['source']).read_bytes()
assert hashlib.sha256(b).hexdigest()==c['source_sha256'] and len(b)==c['source_bytes']
spec=importlib.util.spec_from_file_location('remote_call',ROOT/'authorized_training_execution_v1'/'call_remote_v1.py')
t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t);t.HERE=HERE
rows=t.call(stage,b.decode('utf-8'),c['timeout_seconds'])
assert any(x.get('status')==c['success_phase'] for x in rows)
if stage=='C':
 row=next(x for x in rows if x.get('status')==c['success_phase'])
 assert len(row['files'])==1 and row['files'][0]['sha256']==plan['request_sha256']
 (HERE/'installation_completion_v2.json').write_text(json.dumps(dict(status='ONE_REQUEST_INSTALLED_IMMEDIATE_READBACK_PASS',files=row['files'],training_started=False,tests_run=False,formal_post_installation_audit=False),indent=2)+'\n')
