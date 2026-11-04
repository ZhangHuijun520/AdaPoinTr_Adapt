"""One authorized read-only post-prediction audit through existing short wire."""
import base64,hashlib,json,subprocess,sys
from pathlib import Path
B=Path(__file__).resolve().parent;F=B/'sampling_model_AB_foldC_seed0_20261103_v1/paired_development_eval_v1/freeze_audit_v1'
BOOT="import sys,json,base64,io;d=json.load(sys.stdin);sys.stdin=io.TextIOWrapper(io.BytesIO(base64.b64decode(d['stdin'])));exec(compile(base64.b64decode(d['code']),'pair_readonly_freeze_audit','exec'),{'__name__':'__main__'})"
def main():
 sys.stdout.reconfigure(encoding='utf-8');raw=(F/'frozen_payload.py').read_bytes();driver=(F/'short_driver.py').read_bytes();review=json.loads((F/'static_review_v1.json').read_bytes())
 assert hashlib.sha256(raw).hexdigest()==review['payload_sha256'] and hashlib.sha256(driver).hexdigest()==review['driver_sha256']
 payload=json.dumps(dict(mode='execute_once',payload_base64=base64.b64encode(raw).decode())).encode();envelope=json.dumps(dict(code=base64.b64encode(driver).decode(),stdin=base64.b64encode(payload).decode())).encode()
 with (F/'attempt_started.json').open('x') as f:json.dump(dict(payload_sha256=review['payload_sha256'],server_writes=0,retries=0),f,indent=2)
 try:
  p=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/usr/bin/python3','-I','-S','-B','-c',BOOT],input=envelope,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=160)
  code,out,err,timed=p.returncode,p.stdout,p.stderr,False
 except subprocess.TimeoutExpired as e:code,out,err,timed=None,e.stdout or b'',e.stderr or b'',True
 with (F/'process_capture.json').open('x') as f:json.dump(dict(returncode=code,timeout=timed,stdout_base64=base64.b64encode(out).decode(),stderr_sha256=hashlib.sha256(err).hexdigest()),f,indent=2)
 text=out.decode('utf-16-le' if b'\x00' in out else 'utf-8',errors='replace');records=[]
 for line in text.splitlines():
  try:v=json.loads(line)
  except ValueError:continue
  if isinstance(v,dict) and v.get('status') in ['FORMAL_POST_PREDICTION_FREEZE_AUDIT_PASS','FORMAL_POST_PREDICTION_FREEZE_AUDIT_FAILED_STOP']:records.append(v)
 if len(records)!=1:print(text[-10000:]);raise RuntimeError('No unique audit report; stop no retry')
 r=records[0]
 with (F/'audit_report.json').open('x') as f:json.dump(r,f,indent=2)
 print(json.dumps({k:v for k,v in r.items() if k not in ['control_hashes','prediction_manifest','output_manifest','state_evidence','checkpoint_hashes']}))
 if code or r['status']!='FORMAL_POST_PREDICTION_FREEZE_AUDIT_PASS':raise SystemExit(1)
if __name__=='__main__':main()
