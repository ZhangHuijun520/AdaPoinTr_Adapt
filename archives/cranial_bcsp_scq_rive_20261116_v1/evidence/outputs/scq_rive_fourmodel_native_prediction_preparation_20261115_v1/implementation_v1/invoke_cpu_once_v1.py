import pathlib,json,os,subprocess,sys
D=pathlib.Path(__file__).resolve().parent
r=json.loads((D/'cpu_invocation_v1.json').read_text());env=os.environ.copy();env['CUDA_VISIBLE_DEVICES']='';env['PYTHONDONTWRITEBYTECODE']='1'
try:
 p=subprocess.run(r['command'],env=env,capture_output=True,timeout=r['timeout_seconds']);rc=p.returncode;out=p.stdout;err=p.stderr;timed_out=False
except subprocess.TimeoutExpired as e:
 rc=124;out=e.stdout or b'';err=e.stderr or b'';timed_out=True
(D/'cpu_stdout_v1.bin').write_bytes(out);(D/'cpu_stderr_v1.bin').write_bytes(err)
(D/'cpu_exit_v1.json').write_text(json.dumps(dict(returncode=rc,timeout=timed_out,automatic_retry=False))+'\n')
print(json.dumps(dict(returncode=rc,timeout=timed_out,stdout=out.decode('utf-8',errors='replace'),stderr=err.decode('utf-8',errors='replace')),ensure_ascii=True));sys.exit(rc)
