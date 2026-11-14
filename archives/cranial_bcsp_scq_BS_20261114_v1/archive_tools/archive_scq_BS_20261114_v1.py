"""Local archival only. No model imports, replay, server writes or deletion."""
from pathlib import Path
import base64, collections, hashlib, json, os, re, shutil, subprocess, sys, tarfile

R=Path(__file__).resolve().parent.parent
D=R/'deliverables/scq_BS_20261114_v1'
BACK=Path('E:/ResearchBackups/AdaPoinTr/BCSP_FULLMAMBA_SCQ')
WEIGHTS=BACK/'2026-11-14_key_checkpoints_v1'
PUB=D/'public_payload'
PRIVATE=D/'local_attachments'

def lp(p):
    s=str(p.absolute());return Path('\\\\?\\'+s) if os.name=='nt' and not s.startswith('\\\\?\\') else p
def read(p):return lp(p).read_bytes()
def sha(p):
    h=hashlib.sha256()
    with lp(p).open('rb') as f:
        for b in iter(lambda:f.read(4194304),b''):h.update(b)
    return h.hexdigest()
def put(p,b):
    lp(p.parent).mkdir(parents=True,exist_ok=True)
    with lp(p).open('xb') as f:f.write(b)
def js(p,x):put(p,(json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode())
def emit(**x):print(json.dumps(x,ensure_ascii=True),flush=True)
def inventory(root):
    return sorted((Path(str(Path(d)/n).removeprefix('\\\\?\\')) for d,_,names in os.walk(lp(root)) for n in names),key=str)
def record(p,root):return dict(path=p.relative_to(root).as_posix(),bytes=lp(p).stat().st_size,sha256=sha(p))
def tar_verify(p,expected):
    seen=set()
    with tarfile.open(lp(p),'r|gz') as t:
        for m in t:
            assert m.isfile() and m.name in expected and m.name not in seen,m.name
            h=hashlib.sha256();size=0
            with t.extractfile(m) as f:
                for b in iter(lambda:f.read(4194304),b''):size+=len(b);h.update(b)
            assert h.hexdigest()==expected[m.name]['sha256'] and size==expected[m.name]['bytes'],m.name
            seen.add(m.name)
    assert seen==set(expected)
    return len(seen)
def pack(root,files,dest):
    entries=[record(p,root) for p in files]
    with tarfile.open(lp(dest),'x:gz',compresslevel=1,format=tarfile.PAX_FORMAT) as t:
        for p in files:t.add(lp(p),arcname=p.relative_to(root).as_posix(),recursive=False)
    count=tar_verify(dest,{v['path']:v for v in entries})
    result=dict(path=str(dest),bytes=lp(dest).stat().st_size,sha256=sha(dest),members=count)
    put(dest.with_name(dest.name+'.sha256'),(result['sha256']+'  '+dest.name+'\n').encode())
    put(dest.with_name(dest.name+'.bytes'),(str(result['bytes'])+'\n').encode())
    put(dest.with_name(dest.name+'.contents.sha256'),''.join(v['sha256']+'  '+v['path']+'\n' for v in entries).encode())
    return result

def checkpoints():
    assert not WEIGHTS.exists(),'no overwrite or automatic transfer retry'
    audit=json.loads(read(R/'outputs/scq_pred_freeze_20261114_v2/post_prediction_freeze_audit_result_v1.json'))
    assert audit['status'].endswith('PASS')
    rows=[dict(run=x['run'],**x['checkpoint']) for x in audit['models']]
    assert [x['run'] for x in rows]==['B_C','S_C','B_D','S_D']
    assert shutil.disk_usage(BACK).free>3*sum(x['bytes'] for x in rows)
    WEIGHTS.mkdir();meta=WEIGHTS/'metadata';meta.mkdir()
    js(meta/'frozen_download_scope_v1.json',dict(hostname='shu-common-25721452-notebook-zbpgzu-0',weights=rows,server_writes=0,model_loads=0))
    code="import pathlib,hashlib,json,socket,os;assert socket.gethostname()=='shu-common-25721452-notebook-zbpgzu-0' and os.getuid()==1000;r=[]\n"
    code+='for s in '+repr([x['path'] for x in rows])+":\n p=pathlib.Path(s);assert p.is_file() and not any(x.is_symlink() for x in (p,*p.parents));a=p.stat();h=hashlib.sha256()\n with p.open('rb') as f:\n  for b in iter(lambda:f.read(4194304),b''):h.update(b)\n z=p.stat();assert (a.st_ino,a.st_size,a.st_mtime_ns,a.st_ctime_ns)==(z.st_ino,z.st_size,z.st_mtime_ns,z.st_ctime_ns);r.append(dict(path=s,bytes=a.st_size,sha256=h.hexdigest()))\n"
    code+="print(json.dumps(dict(hostname=socket.gethostname(),uid=os.getuid(),files=r)))"
    command="/opt/conda/bin/python -I -S -B -c \"exec(__import__('base64').b64decode('"+base64.b64encode(code.encode()).decode()+"'))\""
    args=['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000']
    p=subprocess.run(args+['exec','--timeout','120','--',command],capture_output=True,timeout=145)
    put(meta/'readonly_probe_stdout.bin',p.stdout);put(meta/'readonly_probe_stderr.bin',p.stderr)
    assert p.returncode==0,('REMOTE_PROBE_FAILED_STOP',p.returncode)
    remote=json.loads(p.stdout.decode('utf-8').strip())
    assert remote['hostname']=='shu-common-25721452-notebook-zbpgzu-0' and remote['uid']==1000
    assert remote['files']==[{k:x[k] for k in ['path','bytes','sha256']} for x in rows]
    js(meta/'fresh_server_hash_verification_v1.json',remote)
    for row in rows:
        dest=WEIGHTS/'weights'/(row['run']+'_epoch99_step3900.pth');dest.parent.mkdir(exist_ok=True)
        wsl='/mnt/e/'+dest.as_posix()[3:]
        emit(stage='checkpoint_download_started',run=row['run'],bytes=row['bytes'])
        with (meta/(row['run']+'_transfer_stdout.bin')).open('xb') as out,(meta/(row['run']+'_transfer_stderr.bin')).open('xb') as err:
            p=subprocess.run(args+['get',row['path'],wsl,'--timeout','1200'],stdout=out,stderr=err,timeout=1230)
        assert p.returncode==0,('TRANSFER_FAILED_STOP_NO_RETRY',row['run'],p.returncode)
        assert dest.stat().st_size==row['bytes'] and sha(dest)==row['sha256']
        emit(stage='checkpoint_local_hash_matches',run=row['run'])
    for x in audit['models']:js(meta/(x['run']+'_prediction_checkpoint_binding.json'),x)
    put(meta/'prediction_freeze_audit.json',read(R/'outputs/scq_pred_freeze_20261114_v2/post_prediction_freeze_audit_result_v1.json'))
    for label,rel in [('B_C','cranial_bcsp_scq_foldC_training_preparation_20261113_v1/UTC_order_hotfix_v2/post_training_freeze_v2/freeze_verification_v2.json'),('S_C','cranial_bcsp_scq_foldC_training_preparation_20261113_v1/S_C_pending_preparation_v1/post_training_freeze_v1/freeze_verification_v1.json'),('B_D','cranial_bcsp_scq_foldD_training_preparation_20261113_v1/post_training_freeze_v1/freeze_verification_v1.json'),('S_D','cranial_bcsp_scq_foldD_training_preparation_20261113_v1/S_D_pending_preparation_v1/post_training_freeze_v1/freeze_verification_v1.json')]:
        put(meta/(label+'_training_freeze.json'),read(R/'outputs'/rel))
    put(meta/'README.md',b'# SCQ B/S final checkpoints\n\nExact final epoch99/step3900 B_C, S_C, B_D, S_D checkpoint bytes. All four arms are necessary paired baselines/candidates; no best-case selection. Fresh server hashes and local downloaded bytes match the formal freeze evidence. No torch.load, inference, resume, conversion or restore execution. Code/data/provider dependencies remain separate. Never upload these files to GitHub. No server writes or deletions.\n')
    emit(stage='checkpoint_archive_compression_started')
    archive=pack(WEIGHTS,inventory(WEIGHTS),WEIGHTS/'scq_BS_key_checkpoints_20261114_v1.tar.gz')
    receipt=dict(status='FOUR_SCQ_BS_CHECKPOINTS_LOCAL_AND_ARCHIVE_MEMBERS_VERIFIED',weights=rows,archive=archive,checkpoint_deserialized=False,restore_test=False,server_writes=0,server_deletions=0,GitHub_weights=False)
    js(WEIGHTS/'local_verification_receipt_v1.json',receipt);emit(**receipt)

def code_results():
    assert not D.exists(),'no overwriting archival attempts'
    destination=BACK/'2026-11-14_code_results_v1';assert not destination.exists()
    selected={};private={};excluded=[]
    text={'.py','.json','.jsonl','.csv','.tsv','.md','.txt','.yaml','.yml','.sh','.ps1','.log','.pid','.patch','.diff','.sha256','.bytes','.png','.svg'}
    roots=[p for p in (R/'outputs').iterdir() if p.is_dir() and (p.name.startswith('cranial_bcsp_scq_') or p.name.startswith('scq_') or p.name.startswith('cranial_bcsp_fullmamba_n0'))]
    roots += [R/'docs/cranial_bcsp_scq_BS_20261114',R/'docs/cranial_bcsp_fullmamba_spatial_coarse_20261113']
    for root in roots:
        for p in inventory(root):
            if '__pycache__' in p.parts or '.pytest_cache' in p.parts:continue
            assert not lp(p).is_symlink()
            target='evidence/'+p.relative_to(R).as_posix()
            if p.suffix in text:selected[target]=p
            elif p.suffix in {'.bin','.npz','.html'} or p.name.endswith('.tar.gz'):private[target]=p
            else:excluded.append(dict(path=p.relative_to(R).as_posix(),bytes=p.stat().st_size,reason='not public code/result; fixture weight or unsupported binary'))
    parent=R/'deliverables/cranial_bcsp_fullmamba_20261112_v1/public_payload'
    for folder in [parent/'parent_source_snapshot',parent/'evidence/outputs']:
        for p in inventory(folder):
            if p.suffix=='.py' or p.name=='LICENSE':selected['inherited_fullmamba/'+p.relative_to(parent).as_posix()]=p
    metric=R/'outputs/cranial_bcsp_geov1_20261024/blue_pair_eval_v1/bcsp_eval_metrics_v1.py'
    selected['evidence/'+metric.relative_to(R).as_posix()]=metric
    selected['archive_tools/'+Path(__file__).name]=Path(__file__)
    # Real-looking credential patterns are checked before anything is published.
    patterns=[rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',rb'(?:gh[pousr]_[A-Za-z0-9]{25,}|github_pat_[A-Za-z0-9_]{30,})',rb'Bearer\s+[A-Za-z0-9_.-]{30,}',rb'eyJ[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}',rb'https?://[^\s/\x22\x27]+:[^\s/@\x22\x27]+@',rb'https?://[^\s\x22\x27]+[?&](?:access_token|auth_token|token)=[A-Za-z0-9_.%-]{20,}']
    manifest=[]
    for target,p in sorted(selected.items()):
        b=read(p);assert len(b)<50*1024**2,('public file size',target)
        assert not any(re.search(pat,b) for pat in patterns),('SECRET_PATTERN_STOP',target)
        put(PUB/target,b);manifest.append(dict(path=target,source=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
    js(PUB/'source_file_manifest_v1.json',manifest);js(PUB/'excluded_inventory_v1.json',excluded)
    emit(stage='public_source_identity_and_secret_scan_pass',files=len(manifest))
    priv=[]
    for target,p in sorted(private.items()):
        dest=PRIVATE/target;lp(dest.parent).mkdir(parents=True,exist_ok=True);assert not lp(dest).exists()
        shutil.copyfile(lp(p),lp(dest));assert sha(dest)==sha(p)
        priv.append(dict(path=dest.relative_to(D).as_posix(),bytes=p.stat().st_size,sha256=sha(dest),source=str(p)))
    # Copy and independently stream-verify the already downloaded Native archive.
    source=BACK/'2026-11-14_native_development_eval/development_predictions_v1.tar.gz'
    assert sha(source)=='57e7c761510bd8fb0f4758a49eb38354231ba8b0893eab16513f1b478350838d'
    checks={line.split('  ',1)[1]:dict(sha256=line.split('  ',1)[0]) for line in read(source.with_name(source.name+'.contents.sha256')).decode().splitlines() if line}
    with tarfile.open(source,'r|gz') as t:
        for m in t:
            assert m.isfile() and m.name in checks
            checks[m.name]['bytes']=m.size
    assert tar_verify(source,checks)==426
    for suffix in ['','.sha256','.bytes','.contents.sha256']:
        p=source.with_name(source.name+suffix);dest=PRIVATE/'native_predictions'/p.name
        lp(dest.parent).mkdir(parents=True,exist_ok=True);shutil.copyfile(lp(p),lp(dest));assert sha(dest)==sha(p)
        priv.append(dict(path=dest.relative_to(D).as_posix(),source=str(p),bytes=p.stat().st_size,sha256=sha(dest)))
    js(PUB/'local_only_reference_manifest_v1.json',priv)
    report=R/'docs/cranial_bcsp_scq_BS_20261114/SCQ_BS_阶段正式实验报告_zh_v1.md'
    portable=read(report).decode()
    def link_replace(m):
        link=m.group(1)
        if link.startswith(('http:','https:','#')):return m.group(0)
        p=(report.parent/link).resolve();target='evidence/'+p.relative_to(R).as_posix()
        return ']('+target+')' if target in selected else '](LOCAL_ONLY_RESULTS.md)'
    portable=re.sub(r'\]\(([^)]+)\)',link_replace,portable)
    put(PUB/'REPORT_zh.md',portable.encode())
    put(PUB/'LOCAL_ONLY_RESULTS.md',b'# Local-only artifacts\n\nPoint arrays, native predictions, binary initializer/readbacks and interactive HTML are in local_attachments/ of the complete local archive. Public manifests preserve their paths and hashes. Original evidence files retain historical links and statuses. REPORT_zh.md changes navigation only. Checkpoints are archived separately and never published.\n')
    put(PUB/'README.md',b'# SCQ B/S closed research stage, 2026-11-14\n\nRead [the detailed Chinese report](REPORT_zh.md). This snapshot preserves SCQ-v2 source, native LQI parent dependencies, artificial tests, P3/CUDA evidence, four 3900-step training logs and formal freezes, 420 Native prediction identities, 840 scoring rows, risk transitions, static figures and all210-case Qraw diagnostics. B is freshly trained LQI; S adds local Memory feature and relative-geometry residuals. Mean E/J improves on both development folds, but Fold C introduces two severe failures. Qraw displacement is common in improved cases too. F capacity training, multi-seed confirmation, bootstrap and formal G1 were not performed.\n\nPublic evidence retains original bytes and absolute historical bindings; it is not automatically replayable or an execution authorization. Files named authorizations/requests are historical evidence, not credentials. Frozen initializer binaries, interactive point-bearing HTML, diagnostic arrays and complete Native predictions are local-only. Raw datasets, compiled providers/environments and checkpoints are excluded from public Git. Four final B/S C/D checkpoints are separately saved locally. No model execution, rescoring, server writes or deletion is part of this archive.\n\nParent FullMamba snapshot: annotated tag cranial-bcsp-fullmamba-20261112-final, commit 979e997ea844d3b157a2aefe821575c819d5df08 in ZhangHuijun520/AdaPoinTr_Adapt. Inherited code snapshots preserve provenance; they are not new scientific changes. source_file_manifest_v1.json binds original sources, public_files.sha256 binds this public payload, and local_only_reference_manifest_v1.json locates local attachments. The local tar archive is verified member-by-member and copied to E:/ResearchBackups/AdaPoinTr/BCSP_FULLMAMBA_SCQ/2026-11-14_code_results_v1.\n')
    files=inventory(PUB)
    put(PUB/'public_files.sha256',''.join(sha(p)+'  '+p.relative_to(PUB).as_posix()+'\n' for p in files).encode())
    emit(stage='local_code_result_archive_compression_started',public_files=len(files)+1,private_files=len(priv))
    result=pack(D,inventory(PUB)+inventory(PRIVATE),D/'scq_BS_code_results_20261114_v1.tar.gz')
    receipt=dict(status='SCQ_BS_LOCAL_CODE_RESULT_ARCHIVE_ALL_MEMBERS_VERIFIED',archive=result,public_files=len(inventory(PUB)),private_files=len(priv),checkpoint_included=False,secret_scan='NO_PATTERN_MATCHES',server_writes=0,server_deletions=0)
    js(D/'archive_verification_v1.json',receipt)
    destination.mkdir(parents=True)
    copies=[]
    for p in [D/'scq_BS_code_results_20261114_v1.tar.gz',*(D/('scq_BS_code_results_20261114_v1.tar.gz'+s) for s in ['.sha256','.bytes','.contents.sha256']),D/'archive_verification_v1.json']:
        q=destination/p.name;shutil.copyfile(lp(p),lp(q));assert sha(p)==sha(q);copies.append(record(q,destination))
    receipt=dict(status='SCQ_BS_LONG_TERM_COPY_HASH_VERIFIED',directory=str(destination),files=copies)
    js(D/'long_term_backup_receipt_v1.json',receipt);js(destination/'long_term_backup_receipt_v1.json',receipt);emit(**receipt)

if __name__=='__main__':
    if sys.argv[1]=='checkpoints':checkpoints()
    elif sys.argv[1]=='code_results':code_results()
    else:raise ValueError('exact phase required')
