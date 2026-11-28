from pathlib import Path
source=Path(__file__).with_name('verify_upload_readonly_v2.py').read_text().split('archive=run(')[0].replace("e=d/'upload_readonly_v1'","e=d/'startup_status_readonly_v1'")
exec(compile(source,'<read-only-status-definitions>','exec'))
q=json.loads((d.parent/'EJTC_RTJ_D_native315_execution_request_h7vvrr_v2.json').read_bytes())
code=f'''import subprocess
root=Path({q['binding']['output']!r});paths={{{', '.join(repr(k)+':'+repr(q['launch'][k]) for k in ('dispatch_log','single_attempt_log','resource_log','exit_code_path'))}}}
result=dict(session_live=subprocess.run(['tmux','has-session','-t','='+{q['launch']['session_name']!r}],capture_output=True).returncode==0,output_exists=root.exists())
for key,name in paths.items():
 p=Path(name)
 if p.is_file():
  with p.open('rb') as f:f.seek(max(0,p.stat().st_size-5000));result[key]=f.read().decode('utf-8','replace')
for key in ('started.json','failure.json','completion.json'):
 p=root/key
 if p.is_file() and p.stat().st_size<=16384:result[key]=json.loads(p.read_bytes())
for key in ('attempts.jsonl','manifest.jsonl'):
 p=root/key
 if p.is_file() and p.stat().st_size<=2097152:result[key+'_records']=len(p.read_bytes().splitlines())
print(json.dumps(result))
'''
print(json.dumps(run(code,'initial_runtime_status')))
