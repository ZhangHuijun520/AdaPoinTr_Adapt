"""Finish local sidecars in a new directory; request/source/test bytes unchanged."""
from pathlib import Path
import hashlib,json,shutil,tarfile
S=Path(__file__).resolve().parent;A=S/'pending_transport_v1';T=S/'pending_transport_v2'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rec(p):return dict(path=str(p.absolute()),bytes=p.stat().st_size,sha256=sha(p))
def emit(p,x):
    with Path(p).open('x',encoding='utf-8') as f:json.dump(x,f,indent=2,ensure_ascii=False)
def main():
    cpu=json.loads((S/'artificial_cpu_batch_v1/result.json').read_text(encoding='utf-8'))
    assert cpu['status']=='SPCG_ARTIFICIAL_CPU_PASS' and cpu['count']==32
    assert all(sha(S/n)==h for n,h in cpu['source_sha256'].items())
    oldq=A/'payload/SPCG_CUDA_execution_request_v1.json';oldhash=sha(oldq)
    emit(S/'transport_v1_encoding_failure_v1.json',dict(stage='CONTENTS_SIDECAR_ASCII_ENCODING',error='UnicodeEncodeError on Chinese protocol filename',CPU_batch_failed=False,CPU_reruns=0,request_sha256=oldhash,source_modified=False,failed_transport_preserved=str(A)))
    T.mkdir();shutil.copytree(A/'payload',T/'payload');shutil.copyfile(A/'installation_mapping_v1.json',T/'installation_mapping_v1.json')
    arc=T/'bcsp_spcg_cuda_pending_20261116_v2.tar.gz'
    shutil.copyfile(A/'bcsp_spcg_cuda_pending_20261116_v1.tar.gz',arc)
    mapping=json.loads((T/'installation_mapping_v1.json').read_text(encoding='utf-8'));assert mapping['request_sha256']==oldhash
    with tarfile.open(arc,'r:gz') as tar:
        members=tar.getmembers();expected={'installation_mapping_v1.json':T/'installation_mapping_v1.json',**{'payload/'+p.name:p for p in (T/'payload').iterdir()}}
        assert {m.name for m in members}==set(expected) and all(m.isfile() for m in members)
        lines=[]
        for m in members:
            blob=tar.extractfile(m).read();assert hashlib.sha256(blob).hexdigest()==sha(expected[m.name]);lines.append(hashlib.sha256(blob).hexdigest()+'  '+m.name+'\n')
    Path(str(arc)+'.sha256').write_text(sha(arc)+'  '+arc.name+'\n',encoding='ascii')
    Path(str(arc)+'.bytes').write_text(str(arc.stat().st_size)+'\n',encoding='ascii')
    Path(str(arc)+'.contents.sha256').write_text(''.join(lines),encoding='utf-8')
    assert sha(T/'payload/SPCG_CUDA_execution_request_v1.json')==oldhash
    q=json.loads(oldq.read_text(encoding='utf-8'))
    emit(S/'delivery_receipt_v2.json',dict(status='AWAITING_UPLOAD_READINESS_AND_SEPARATE_FULL_HASH_EXECUTION_AUTHORIZATION',request=rec(T/'payload/SPCG_CUDA_execution_request_v1.json'),archive=rec(arc),sidecars=[rec(Path(str(arc)+s)) for s in ['.sha256','.bytes','.contents.sha256']],contents_encoding='UTF-8',install_files=len(mapping['files']),archive_members=len(members),P3=rec(S/'implementation_P3_v1.json'),CPU_count=32,real_cases=[x['case_id'] for x in q['real_inputs']],authorization_materialized=False,runtime_materialized=False,launcher_materialized=False,server_calls=0,GPU_calls=0,training_request_created=False,source_or_request_changes=False,CPU_reruns=0))
    print(json.dumps(dict(status='PENDING_TRANSPORT_UTF8_V2_VERIFIED',request_SHA256=oldhash,archive_bytes=arc.stat().st_size,files=len(mapping['files']),real_cases=[x['case_id'] for x in q['real_inputs']]),ensure_ascii=False))
if __name__=='__main__':main()
