"""Read-only byte comparison, not contract-test rerun or model import."""
from pathlib import Path
import json,os,hashlib,sys
V=Path(__file__).resolve().parent;O=V/'readonly_byte_diagnosis_v1';O.mkdir()
config=json.loads((V/'CPU_batch_v3/child_config.json').read_text(encoding='utf-8'))
def digest(b):return hashlib.sha256(b).hexdigest()
rows=[]
for key,r in config['q'].items():
 p=Path(r['path']);before=p.stat();raw=p.read_bytes()
 def fd_read(extra):
  fd=os.open(p,os.O_RDONLY|extra)
  try:return os.read(fd,r['bytes']+1)
  finally:os.close(fd)
 default=fd_read(0);binary=fd_read(os.O_BINARY)
 after=p.stat()
 row=dict(key=key,path=str(p),expected_bytes=r['bytes'],expected_sha256=r['sha256'],raw_bytes=len(raw),raw_sha256=digest(raw),raw_matches_frozen=len(raw)==r['bytes'] and digest(raw)==r['sha256'],CRLF_pairs=raw.count(b'\r\n'),LF_bytes=raw.count(b'\n'),control_Z_bytes=raw.count(b'\x1a'),default_fd_bytes=len(default),default_fd_sha256=digest(default),default_equals_raw=default==raw,default_equals_CRLF_to_LF=default==raw.replace(b'\r\n',b'\n'),binary_fd_bytes=len(binary),binary_fd_sha256=digest(binary),binary_equals_raw=binary==raw,first_default_difference_offset=next((i for i,(a,b) in enumerate(zip(default,raw)) if a!=b),None),size_mtime_ctime_inode_unchanged=all(getattr(before,k)==getattr(after,k) for k in ['st_size','st_mtime_ns','st_ctime_ns','st_ino']))
 rows.append(row)
result=dict(status='READONLY_BYTES_DIAGNOSIS_COMPLETE_NOT_TEST_EXECUTION',platform=sys.platform,python=sys.version,rows=rows,conclusion='Windows default text-mode os.open translates CRLF to LF; binary descriptor preserves frozen bytes',all_raw_frozen_match=all(x['raw_matches_frozen'] for x in rows),all_binary_frozen_match=all(x['binary_equals_raw'] for x in rows),default_translation_explains_all=all(x['default_equals_CRLF_to_LF'] for x in rows),production_code_changes=0,test_reruns=0,server_calls=0,models=0)
assert result['all_raw_frozen_match'] and result['all_binary_frozen_match'] and result['default_translation_explains_all']
(O/'byte_comparison_result_v1.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False))
