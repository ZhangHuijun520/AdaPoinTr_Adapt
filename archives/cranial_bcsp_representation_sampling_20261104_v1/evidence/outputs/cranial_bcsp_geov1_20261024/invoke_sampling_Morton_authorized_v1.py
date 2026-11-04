"""Existing short-wire driver, raw stdin bytes, one attempt per authorized phase."""
import base64,hashlib,json,re,subprocess,sys
from pathlib import Path
A=Path(__file__).resolve().parent/'sampling_model_AB_foldC_seed0_20261103_v1/Morton_training_request_v1/authorized_execution_v1'
BOOT="import sys,json,base64,io;d=json.load(sys.stdin);sys.stdin=io.TextIOWrapper(io.BytesIO(base64.b64decode(d['stdin'])));exec(compile(base64.b64decode(d['code']),'frozen_short_driver','exec'),{'__name__':'__main__'})"
def main():
 phase,mode=sys.argv[1:];assert phase in ['precheck','install','materialize'] and mode in ['inspect','execute_once']
 raw=(A/(phase+'_server_v1.py')).read_bytes();driver=(A/(phase+'_driver_v1.py')).read_bytes()
 plan=json.loads((A/'operation_plan_v1.json').read_text());assert hashlib.sha256(raw).hexdigest()==plan['payloads'][phase]
 data={'payload_base64':base64.b64encode(raw).decode(),'mode':mode}
 envelope=json.dumps({'code':base64.b64encode(driver).decode(),'stdin':base64.b64encode(json.dumps(data).encode()).decode()}).encode()
 prefix=phase+'_'+mode
 with (A/(prefix+'_started.json')).open('x') as f:json.dump({'scope_sha256':plan['scope_sha256'],'payload_sha256':hashlib.sha256(raw).hexdigest(),'driver_sha256':hashlib.sha256(driver).hexdigest(),'mode':mode,'no_retry':True},f,indent=2)
 timeout=340 if phase=='install' else 160
 try:
  p=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/usr/bin/python3','-I','-S','-B','-c',BOOT],input=envelope,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout)
  code,out,err,timed=p.returncode,p.stdout,p.stderr,False
 except subprocess.TimeoutExpired as e:code,out,err,timed=None,e.stdout or b'',e.stderr or b'',True
 stderr=re.sub(r'(?i)(bearer\s+|token[=:]\s*)\S+',r'\1[REDACTED]',err.decode('utf-8',errors='replace'))
 with (A/(prefix+'_capture.json')).open('x') as f:json.dump({'returncode':code,'timeout':timed,'stdout_base64':base64.b64encode(out).decode(),'stderr_redacted':stderr,'stderr_sha256':hashlib.sha256(err).hexdigest()},f,indent=2)
 text=out.decode('utf-8',errors='replace');print(text,flush=True)
 if code!=0:
  print(json.dumps({'returncode':code,'timeout':timed,'stderr_redacted':stderr}),flush=True);raise SystemExit(1)
 expected='LOCAL_SHORT_WIRE_STATIC_INSPECTION_PASS' if mode=='inspect' else {'precheck':'UPLOAD_AND_DESTINATION_READONLY_PASS','install':'INSTALLATION_3_HASH_PASS','materialize':'SINGLE_TMUX_LAUNCH_RETURNED_ZERO_NOT_TRAINING_PROOF'}[phase]
 values=[]
 for line in text.splitlines():
  try:v=json.loads(line)
  except json.JSONDecodeError:continue
  if isinstance(v,dict):values.append(v)
 matched=[v for v in values if v.get('status')==expected]
 if len(matched)!=1:raise RuntimeError('Missing unique positive remote phase receipt; stop without retry')
 with (A/(prefix+'_observation.json')).open('x') as f:json.dump(matched[0],f,indent=2)
 print('PHASE_CONFIRMED',phase,mode,flush=True)
if __name__=='__main__':main()
