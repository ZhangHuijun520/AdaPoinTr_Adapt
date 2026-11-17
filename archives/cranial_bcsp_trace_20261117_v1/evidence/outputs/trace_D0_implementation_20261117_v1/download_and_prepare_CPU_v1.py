# -*- coding: utf-8 -*-
"""Download four frozen files and verify bytes/members only; never run analysis."""
import hashlib,json,os,shutil,subprocess,tarfile,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
V=Path(__file__).resolve().parent
B=Path('E:/ResearchBackups/AdaPoinTr/BCSP_FULLMAMBA_TRACE/2026-11-17_D0_memory_evidence')

def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(4194304),b''):h.update(b)
    return h.hexdigest()
def record(p):return dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))
def save(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')

def main():
    freeze=read(V/'post_diagnostic_freeze_v1/formal_freeze_verification_v1.json')
    assert freeze['status']=='FORMAL_TRACE_D0_POST_DIAGNOSTIC_FREEZE_PASS' and all(freeze['checks'].values())
    ar=freeze['archive'];expected=read(V/'post_diagnostic_freeze_v1/archive_result_v1.json')['file_records']
    assert not B.exists(),'no overwrite/retry';assert shutil.disk_usage(B.parent.parent).free>3*ar['bytes']
    B.mkdir(parents=True);M=B/'verification';M.mkdir()
    save(M/'download_scope_v1.json',dict(status='FOUR_FILE_DOWNLOAD_ONLY_NO_ANALYSIS',archive=ar,expected_members=expected,server_writes=0,model_loads=0,analysis=False))
    base=Path(ar['path']).name;downloads=[]
    try:
        for suffix in ('','.sha256','.bytes','.contents.sha256'):
            remote=ar['path']+suffix;dest=B/(base+suffix)
            assert not dest.exists()
            wsl='/mnt/e/'+dest.as_posix()[3:]
            print(json.dumps(dict(stage='download_started',file=dest.name)),flush=True)
            with (M/(dest.name+'_stdout.bin')).open('xb') as out,(M/(dest.name+'_stderr.bin')).open('xb') as err:
                p=subprocess.run(['wsl.exe','--exec','/home/zhj/.local/bin/hpc5000','get',remote,wsl,'--timeout','180'],stdout=out,stderr=err,timeout=200)
            save(M/(dest.name+'_exit.json'),dict(returncode=p.returncode))
            assert p.returncode==0,'download failed stop no retry'
            downloads.append(record(dest))
        archive=B/base
        assert archive.stat().st_size==ar['bytes'] and sha(archive)==ar['sha256']
        assert int((B/(base+'.bytes')).read_text())==ar['bytes']
        assert (B/(base+'.sha256')).read_text().split()==[ar['sha256'],base]
        assert (B/(base+'.contents.sha256')).read_text().splitlines()==[r['sha256']+'  '+r['name'] for r in expected]
        lookup={r['name']:r for r in expected};seen=set()
        with tarfile.open(archive,'r|gz') as tf:
            for m in tf:
                assert m.isfile() and m.name in lookup and m.name not in seen and '..' not in Path(m.name).parts and not m.name.startswith('/')
                h=hashlib.sha256();count=0
                with tf.extractfile(m) as f:
                    for b in iter(lambda:f.read(1048576),b''):h.update(b);count+=len(b)
                assert count==m.size==lookup[m.name]['bytes'] and h.hexdigest()==lookup[m.name]['sha256']
                seen.add(m.name)
        assert len(seen)==84 and seen==set(lookup)
        result=dict(status='TRACE_D0_LOCAL_FOUR_FILES_AND_ALL84_MEMBERS_VERIFIED',directory=str(B),archive=record(archive),downloads=downloads,members=84,trace_files=80,archive_extracted=False,NPZ_decoded=False,GT_read=False,model_loads=0,forward=0,analysis_executed=False,server_writes=0,server_deletions=0,formal_freeze=record(V/'post_diagnostic_freeze_v1/formal_freeze_verification_v1.json'))
        save(B/'local_verification_receipt_v1.json',result)
        print(json.dumps(dict(status=result['status'],archive=result['archive'],members=84)),flush=True)
    except BaseException as exc:
        save(M/'failure_v1.json',dict(status='FAILED_STOP_NO_RETRY',error=repr(exc),downloaded=downloads));raise

if __name__=='__main__':main()
