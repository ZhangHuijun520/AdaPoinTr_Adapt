"""Execute the one frozen read-only audit through the existing short-wire driver."""
import base64,hashlib,json,subprocess,sys
from pathlib import Path
B=Path(__file__).resolve().parent;F=B/'blue_noise_model_pair_foldC_seed0_20261104_v1/first_training_request_v2/graph_request_v2/post_training_audit_v1'
BOOT="import sys,json,base64,io;d=json.load(sys.stdin);sys.stdin=io.TextIOWrapper(io.BytesIO(base64.b64decode(d['stdin'])));exec(compile(base64.b64decode(d['code']),'sampling_readonly_audit_driver','exec'),{'__name__':'__main__'})"
def main():
 sys.stdout.reconfigure(encoding='utf-8');raw=(F/'readonly_audit_server_v1.py').read_bytes();driver=(F/'audit_short_driver_v1.py').read_bytes()
 scope=json.loads((F/'frozen_readonly_scope_v1.json').read_text());assert hashlib.sha256(raw).hexdigest()==scope['audit_source_sha256']
 payload=json.dumps({'payload_base64':base64.b64encode(raw).decode(),'mode':'execute_once'}).encode()
 envelope=json.dumps({'code':base64.b64encode(driver).decode(),'stdin':base64.b64encode(payload).decode()}).encode()
 with (F/'audit_attempt_started_v1.json').open('x') as f:json.dump({'read_only':True,'audit_payload_sha256':scope['audit_source_sha256'],'server_writes':0,'retry':False},f,indent=2)
 p=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/usr/bin/python3','-I','-S','-B','-c',BOOT],input=envelope,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=180)
 with (F/'audit_capture_v1.json').open('x') as f:json.dump({'returncode':p.returncode,'stdout_base64':base64.b64encode(p.stdout).decode(),'stderr_sha256':hashlib.sha256(p.stderr).hexdigest()},f,indent=2)
 text=p.stdout.decode('utf-16-le' if b'\x00' in p.stdout else 'utf-8',errors='replace')
 records=[]
 for line in text.splitlines():
  try:v=json.loads(line)
  except ValueError:continue
  if isinstance(v,dict) and v.get('status') in ['FORMAL_POST_TRAINING_FREEZE_AUDIT_PASS','AUDIT_FAILED_STOP_NO_RETRY']:records.append(v)
 if len(records)!=1:
  print(text);raise RuntimeError('No unique audit result; do not retry or create candidate request')
 result=records[0]
 with (F/'audit_report_v1.json').open('x') as f:json.dump(result,f,indent=2)
 print(json.dumps({'status':result['status'],'transport_returncode':p.returncode,'checks':result.get('checks'),'checkpoint':result.get('checkpoint'),'initialization':result.get('initialization'),'counts':result.get('counts'),'error':result.get('error'),'hashed_bytes':result.get('hashed_bytes'),'seconds':result.get('elapsed_seconds')},ensure_ascii=True))
 if p.returncode or result['status']!='FORMAL_POST_TRAINING_FREEZE_AUDIT_PASS':raise SystemExit(1)
if __name__=='__main__':main()
