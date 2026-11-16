import pathlib,json,os,subprocess,sys
D=pathlib.Path(__file__).resolve().parent
r=json.loads((D/'CPU_invocation_v1.json').read_bytes());env=os.environ.copy();env['CUDA_VISIBLE_DEVICES']='';env['PYTHONDONTWRITEBYTECODE']='1'
try:
 p=subprocess.run(r['command'],env=env,capture_output=True,timeout=r['timeout_seconds']);rc=p.returncode;out=p.stdout;err=p.stderr;timeout=False
except subprocess.TimeoutExpired as e:
 rc=124;out=e.stdout or b'';err=e.stderr or b'';timeout=True
(D/'CPU_stdout_v1.bin').write_bytes(out);(D/'CPU_stderr_v1.bin').write_bytes(err);(D/'CPU_exit_v1.json').write_bytes((json.dumps(dict(returncode=rc,timeout=timeout,automatic_retry=False))+'\n').encode())
print(json.dumps(dict(returncode=rc,timeout=timeout,stdout_tail=out[-2000:].decode('utf-8',errors='replace'),stderr=err.decode('utf-8',errors='replace')),ensure_ascii=True));sys.exit(rc)
