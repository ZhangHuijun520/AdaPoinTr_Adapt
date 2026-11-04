"""Raw-stdin wrapper for the frozen one-shot install and prediction controller."""
import base64,hashlib,json,re,subprocess,sys
from pathlib import Path
B=Path(__file__).resolve().parent;A=B/'blue_pair_eval_v1/authorized_execution_v1'
BOOT="import sys,json,base64,io;d=json.load(sys.stdin);sys.stdin=io.TextIOWrapper(io.BytesIO(base64.b64decode(d['stdin'])));exec(compile(base64.b64decode(d['code']),'frozen_pair_driver','exec'),{'__name__':'__main__'})"
def main():
 sys.stdout.reconfigure(encoding='utf-8');mode=sys.argv[1];assert mode in ['inspect','execute_once']
 plan=json.loads((A/'operation_plan_v1.json').read_bytes());raw=(A/'materialize_and_start_once.py').read_bytes();driver=(A/'invoke_short_once.py').read_bytes()
 assert hashlib.sha256(raw).hexdigest()==plan['payload_sha256'] and hashlib.sha256(driver).hexdigest()==plan['driver_sha256']
 envelope=json.dumps(dict(code=base64.b64encode(driver).decode(),stdin=base64.b64encode(json.dumps(dict(mode=mode,payload_base64=base64.b64encode(raw).decode())).encode()).decode())).encode()
 with (A/(mode+'_started.json')).open('x') as f:json.dump(dict(request_sha256=plan['request_sha256'],payload_sha256=plan['payload_sha256'],mode=mode,no_retry=True),f,indent=2)
 try:
  p=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/usr/bin/python3','-I','-S','-B','-c',BOOT],input=envelope,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=160)
  code,out,err,timed=p.returncode,p.stdout,p.stderr,False
 except subprocess.TimeoutExpired as e:code,out,err,timed=None,e.stdout or b'',e.stderr or b'',True
 redacted=re.sub(r'(?i)(bearer\s+|token[=:]\s*)\S+',r'\1[REDACTED]',err.decode('utf-8',errors='replace'))
 with (A/(mode+'_capture.json')).open('x') as f:json.dump(dict(returncode=code,timeout=timed,stdout_base64=base64.b64encode(out).decode(),stderr_redacted=redacted,stderr_sha256=hashlib.sha256(err).hexdigest()),f,indent=2)
 text=out.decode('utf-16-le' if b'\x00' in out else 'utf-8',errors='replace');events=[]
 for line in text.splitlines():
  try:v=json.loads(line)
  except ValueError:continue
  if isinstance(v,dict):events.append(v)
 with (A/(mode+'_events.json')).open('x') as f:json.dump(events,f,indent=2)
 expected='LOCAL_SHORT_WIRE_STATIC_INSPECTION_PASS' if mode=='inspect' else 'EVALUATION_START_OBSERVED'
 matches=[v for v in events if v.get('status')==expected];failures=[v for v in events if v.get('status')=='FAILED_STOP_NO_RETRY']
 ok=code==0 and len(matches)==1 and not failures
 summary=dict(status='CONFIRMED' if ok else 'STOPPED_NO_RETRY',mode=mode,request_sha256=plan['request_sha256'],returncode=code,timeout=timed,observation=matches[0] if len(matches)==1 else None,failure=failures[-1] if failures else None,server_calls=0 if mode=='inspect' else 1,scoring=0,training=0,BNCal=0)
 with (A/(mode+'_result.json')).open('x') as f:json.dump(summary,f,indent=2)
 print(json.dumps(summary))
 if not ok:
  print(text[-10000:]);print(redacted);raise SystemExit(1)
if __name__=='__main__':main()
