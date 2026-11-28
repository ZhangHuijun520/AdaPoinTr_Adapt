"""Recheck all frozen conditions, then one explicitly authorized Native315 dispatch."""
from pathlib import Path
source=Path(__file__).with_name('install_native315_short_v2.py').read_text()
source=source.split('# Compile and enforce short-call budgets')[0].replace("e=d/'installation_evidence_v2'","e=d/'execution_evidence_v1'")
exec(compile(source,'<frozen-readiness-definitions>','exec'))
import importlib.util,shlex
audit=json.loads((d/'post_installation_freeze_audit_v2/formal_post_installation_freeze_audit_v2.json').read_bytes())
assert audit['status']=='FORMAL_READ_ONLY_EJTC_NATIVE315_V2_POST_INSTALLATION_FREEZE_AUDIT_PASS' and audit['request_sha256']==m['request_sha256']
rid=m['request_sha256'];assert rid=='4b9dc3dac44c4d547fb5c79826dc48346610a19ab828392c4fdbe1e98fcdec31'
# Existing installation is expected; only output/control/session must remain unused.
unused=[m['output_must_be_absent']]+m['runtime_controls_must_be_absent']
scan=scan.replace(repr(absent),repr(unused))
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
mat=load('authorization_materializer',Path(q['authorization_materializer']['local_path']))
assert h(Path(q['authorization_materializer']['local_path']).read_bytes())==q['authorization_materializer']['sha256']
auth,runtime=mat.materialize((b/'EJTC_RTJ_D_native315_execution_request_h7vvrr_v2.json').read_bytes(),
 'User separately authorized this exact installed v2 request: one 315 Native forward run, zero updates, recheck conditions, stop on failure, no automatic retry or resume. SHA256 '+rid,execution_authorized=True)
worker=load('native315_authorization_check',b/'ejtc_native_rtj315_v2.py')
assert h((b/'ejtc_native_rtj315_v2.py').read_bytes())==q['files']['worker']['sha256']
worker.authorize(q,rid,json.loads(auth),h(auth),json.loads(runtime))
p=q['launch'];cmd=[i['python_realpath'],'-I','-S','-B',p['launcher']['path']]
for key,val in [('request',p['request_path']),('request-sha256',rid),('authorization',p['authorization_path']),('authorization-sha256',h(auth)),('runtime',p['runtime_path']),('runtime-sha256',h(runtime))]:cmd+=['--'+key,val]
shell=shlex.join(cmd)+' > '+shlex.quote(p['dispatch_log'])+' 2>&1; rc=$?; (set -C; printf \'%s\\n\' "$rc" > '+shlex.quote(p['exit_code_path'])+')'
dispatch=f'''import subprocess
assert hashlib.sha256(Path({p['request_path']!r}).read_bytes()).hexdigest()=={rid!r}
for name in {unused!r}:assert not os.path.lexists(name)
assert subprocess.run(['tmux','has-session','-t','='+{p['session_name']!r}],capture_output=True).returncode==1
for name,raw in (({p['authorization_path']!r},{auth!r}),({p['runtime_path']!r},{runtime!r})):
 path=Path(name);assert path.parent.resolve(strict=True)==path.parent
 with path.open('xb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
subprocess.run(['tmux','new-session','-d','-s',{p['session_name']!r},{shell!r}],check=True,timeout=10)
print(json.dumps(dict(started=True,request_sha256={rid!r},session={p['session_name']!r},hostname=socket.gethostname())))
'''
inventory=f'''r=Path({m['new_install_root']!r});assert r.resolve(strict=True)==r and r.is_dir()
print(json.dumps([read(str(p)) for p in sorted(r.iterdir())]))
'''
# Render/compile every command before remote calls or authorization writes.
for code in [scan,inventory,package+'print(json.dumps(dict(members=7,fingerprint=sig(data))))',dispatch,*[j[0] for j in jobs]]:render(code)
run(scan,'identity_resources_unused_paths_before')
expected_installed=sorted([[r['target'],r['bytes'],r['sha256']] for r in m['files']])
assert run(read+inventory,'installed_inventory_before')==expected_installed
run(package+'print(json.dumps(dict(members=7,fingerprint=sig(data))))','upload_and_installed_material_recheck')
for j,(code,name,rows) in enumerate(jobs):
 assert run(code,name)==rows,'Prelaunch frozen asset/array mismatch'
 print('Prelaunch verified batch '+str(j+1)+'/'+str(len(jobs)),flush=True)
assert run(read+inventory,'installed_inventory_after')==expected_installed
resources=run(scan,'identity_resources_unused_paths_immediately_before')
for name,raw in [('explicit_user_authorization_v2.json',auth),('local_runtime_material_v2.json',runtime)]:
 with (e/name).open('xb') as f:f.write(raw)
receipt=dict(status='NATIVE315_EXECUTION_READINESS_PASS',request_sha256=rid,reused_files=167,partial_arrays=105,installed_files=7,resources=resources,actual_authorize_pass=True,counts=q['counts'])
with (e/'execution_readiness_receipt_v2.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,indent=2)
result=run(dispatch,'single_native315_dispatch_v2')
assert result['started'] is True and result['request_sha256']==rid
print(json.dumps(result))
