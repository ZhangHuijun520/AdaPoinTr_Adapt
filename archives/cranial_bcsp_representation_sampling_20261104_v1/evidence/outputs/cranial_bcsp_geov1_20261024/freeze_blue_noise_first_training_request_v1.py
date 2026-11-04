"""Finalize identity constants and freeze one pending training scope, locally only."""
import ast,base64,copy,gzip,hashlib,importlib.util,io,json,tarfile,time
from pathlib import Path
B=Path(__file__).resolve().parent;O=B/'blue_noise_model_pair_foldC_seed0_20261104_v1'
F=O/'first_training_request_v1';I=F/'implementation';E=F/'evidence';R=O/'server_readiness_v1'
PROJECT='/home/jovyan/adapointr_work/PoinTr';ROOT=PROJECT+'/third_party/bcsp_blue_noise_ab_foldc_seed0_v1';DATA=PROJECT+'/data/bcsp_blue_noise_ab_foldc_seed0_v1'
RUN='bcsp_blue_noise_foldC_Euclidean_elimination_in8192_out8192_seed0_train_v1'
OUT=PROJECT+'/logs/cranial_bcsp_blue_noise_ab_v1/'+RUN;CONTROL=ROOT+'/control_Euclidean_v1'
STAGE='BCSP_BLUE_NOISE_AB_V1';ARMS=['Euclidean_elimination','surface_graph']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def shab(b):return hashlib.sha256(b).hexdigest()
def dump(p,v):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,indent=2,ensure_ascii=False,allow_nan=False)
def write(p,s):
    with p.open('x',encoding='utf-8',newline='') as f:f.write(s)
def module(name,p):
    spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def main():
    start=time.monotonic()
    prep=json.loads((O/'local_preparation_review_v1.json').read_bytes());assert all(prep['checks'].values())
    tests=json.loads((O/'cpu_contract_attempt_v1/result.json').read_bytes());assert tests['status']=='PASS' and tests['checks']==20
    obs=json.loads((R/'identity_v2_observation_v1.json').read_bytes());assetsobs=json.loads((R/'assets_observation_v1.json').read_bytes())
    for mode in ('identity_v2','assets'):assert json.loads((R/(mode+'_capture_v1.json')).read_bytes())['returncode']==0
    assert obs['hostname']=='shu-common-25721452-notebook-v2iwsa-0' and obs['uid']==1000 and obs['project']==PROJECT
    assert obs['disk_free']>4*1024**3 and not obs['compute'] and not obs['tmux_sessions']
    assert len(obs['new_roots_absent'])==3 and all(p['is_directory'] and p['writable'] for p in obs['parents'].values())
    assert assetsobs['status']=='SELECTED30_HASH_PASS' and len(assetsobs['assets'])==30
    old=B/'sampling_model_AB_foldC_seed0_20261103_v1';base=json.loads((old/'V1_training_entry_request_v1.json').read_bytes())
    identity=copy.deepcopy(base['identity']);g=[v.strip() for v in obs['gpu'].split(',')]
    assert g[:4]==[identity['gpu_uuid'],identity['gpu_name'],identity['driver_version'],str(identity['nvidia_smi_memory_total_MiB'])+' MiB'] and int(g[4].split()[0])<=256
    assert obs['python_realpath']==identity['python_realpath'] and obs['python_version']=='Python '+identity['python_version']
    assert assetsobs['assets']==json.loads((old/'server_assets_observation_v1.json').read_bytes())['assets']
    assert not F.exists();I.mkdir(parents=True);E.mkdir()
    files=[]
    def add(local,member,dest):
        p=Path(local);assert p.is_file() and not p.is_symlink()
        r={'path':dest,'bytes':p.stat().st_size,'sha256':sha(p)}
        files.append({'local_path':str(p),'member':member,'destination':dest,'bytes':r['bytes'],'sha256':r['sha256']});return r
    def evidence(p,name=None):
        name=name or Path(p).name;return add(p,'evidence/'+name,ROOT+'/evidence/'+name)
    observed=evidence(R/'identity_v2_observation_v1.json','server_readonly_observation_v1.json')
    selected=evidence(R/'assets_observation_v1.json','server_assets_observation_v1.json')
    resource={'schema':'bcsp-blue-noise-resource-v1','stage':STAGE,'new_identity':identity,'old_scope_sha256':base['preflight_scope']['sha256'],'historical_GPU_audit_sha256':base['GPU_audit']['sha256'],'readonly_identity':observed,'readonly_assets':selected,'historical_GPU_only':True,
      'limitations':['Read-only match does not certify present CUDA execution; no preflight repeated','Monitor thresholds retained; no strict dedicated cgroup or PID-ownership claim','Server is not a Git checkout; model/provider source identity uses exact30 SHA256 records','Both arms require the same environment and initial parameter/buffer fingerprints; candidate requires later separate authorization']}
    dump(E/'resource_binding_v1.json',resource);rr=evidence(E/'resource_binding_v1.json')
    # Only the two previously reserved hash constants change; preserve old source snapshots.
    oldcontract=(O/'implementation/bcsp_blue_noise_training_contract_v1.py').read_text(encoding='utf-8')
    assert oldcontract.count('UNBOUND_PENDING_CURRENT_SERVER_READINESS')==1
    contract=oldcontract.replace('UNBOUND_PENDING_CURRENT_SERVER_READINESS',rr['sha256'])
    write(I/'bcsp_blue_noise_training_contract_v1.py',contract)
    entry=(O/'implementation/bcsp_blue_noise_training_entry_v1.py').read_text(encoding='utf-8')
    oldhash=sha(O/'implementation/bcsp_blue_noise_training_contract_v1.py');assert entry.count(oldhash)==1
    entry=entry.replace(oldhash,sha(I/'bcsp_blue_noise_training_contract_v1.py'));write(I/'bcsp_blue_noise_training_entry_v1.py',entry)
    with (I/'bcsp_blue_noise_training_runtime_v1.py').open('xb') as f:f.write((O/'implementation/bcsp_blue_noise_training_runtime_v1.py').read_bytes())
    for p in I.glob('*.py'):ast.parse(p.read_text(encoding='utf-8'))
    assert contract.replace(rr['sha256'],'UNBOUND_PENDING_CURRENT_SERVER_READINESS')==oldcontract
    assert entry.replace(sha(I/'bcsp_blue_noise_training_contract_v1.py'),oldhash)==(O/'implementation/bcsp_blue_noise_training_entry_v1.py').read_text(encoding='utf-8')
    assert sha(I/'bcsp_blue_noise_training_runtime_v1.py')==sha(O/'implementation/bcsp_blue_noise_training_runtime_v1.py')
    # Freeze train-only payload selection. Development and diagnostic point sets stay local.
    static=evidence(O/'static_training_config_v1.json');order=evidence(O/'shared_order_foldC_seed0_v1.json')
    verification=evidence(O/'paired_train_data_receipt.json');foldrec=evidence(B/'consolidated_binding_v1/fold_binding.json')
    manifests={}
    for arm in ARMS:
        manifests[arm]=evidence(O/arm/'train_manifest_8192.jsonl',arm+'_train_manifest_8192.jsonl')
        records=[json.loads(s) for s in (O/arm/'train_manifest_8192.jsonl').read_text(encoding='utf-8').splitlines()];assert len(records)==315
        for row in records:
            assert row['comparison_split']=='train' and row['sampler_arm']==arm and row['comparison_stage']==STAGE
            p=O/arm/row['point_path'];assert sha(p)==row['sha256']
            add(p,'data/'+arm+'/'+row['point_path'],DATA+'/'+arm+'/'+row['point_path'])
    c=module('final_blue_noise_bound_contract',I/'bcsp_blue_noise_training_contract_v1.py')
    folds=json.loads((B/'consolidated_binding_v1/fold_binding.json').read_bytes());fold=folds['folds']['C']
    qualified={'schema':'bcsp-blue-noise-qualified-v1','stage':STAGE,'arm':ARMS[0],'verification':verification,'manifests':manifests,'fold_binding':foldrec,'fold':'C','n_input':8192,'train_allowlist_sha256':fold['train_allowlist_sha256'],'limitations':list(c.LIMITS)}
    dump(E/'qualified_Euclidean_training_receipt_v1.json',qualified);qualifiedrec=evidence(E/'qualified_Euclidean_training_receipt_v1.json')
    q=copy.deepcopy(base);q.update(schema='bcsp-blue-noise-training-request-v1',stage=STAGE,status='AWAITING_EXPLICIT_USER_AUTHORIZATION',run_id=RUN,arm=ARMS[0],paired_initialization=None,static_config=static,order_plan=order,resource_rebind=rr,identity=identity,data_root=DATA+'/'+ARMS[0],output=OUT,launch_attempt=CONTROL+'/launch_attempt_v1.json')
    q['QC']={'qualified_receipt':qualifiedrec,'verification':verification,'manifests':manifests,'fold_binding':foldrec}
    q['implementation']={role:add(I/('bcsp_blue_noise_training_'+role+'_v1.py'),'implementation/bcsp_blue_noise_training_'+role+'_v1.py',ROOT+'/implementation/bcsp_blue_noise_training_'+role+'_v1.py') for role in ('entry','contract','runtime')}
    q['implementation']['preflight_helper']=base['implementation']['preflight_helper']
    # Exercise final hashes through the actual authorize/rebind/metadata functions in RAM.
    mapping={a['destination']:Path(a['local_path']) for a in files}
    mapping[base['preflight_scope']['path']]=B/'gpu_preflight_plotting_lazy_v3/artificial_gpu_zero_update_frozen_scope_v3.json'
    # The old GPU report has already passed exact30? Bind its separately verified local frozen copy.
    oldgpu=next(p for p in B.rglob('post_preflight_freeze_audit_report_v1.json') if sha(p)==base['GPU_audit']['sha256'])
    mapping[base['GPU_audit']['path']]=oldgpu
    ram={'RAM:request':q,'RAM:authorization':{'schema':'bcsp-training-authorization-v1','request_sha256':'1'*64,'explicit_user_authorization':True,'user_authorization_text':'ARTIFICIAL RAM CONTRACT CHECK ONLY'},'RAM:runtime':{'schema':'bcsp-training-runtime-v1','request_sha256':'1'*64,'authorization_sha256':'2'*64}}
    original=c.json_bound
    def resolve(r):
        if r['path'] in ram:return copy.deepcopy(ram[r['path']])
        p=mapping[r['path']];assert p.stat().st_size==r['bytes'] and sha(p)==r['sha256'];return json.loads(p.read_bytes())
    c.json_bound=resolve
    checks={}
    try:
        assert c.validate_rebind(rr,q['preflight_scope'],q['GPU_audit'])==resource;checks['actual_resource_evidence_rebind']=True
        got,config=c.authorize({'path':'RAM:request','sha256':'1'*64},{'path':'RAM:authorization','sha256':'2'*64},{'path':'RAM:runtime','sha256':'3'*64});assert got==q;checks['final_full_authorize_RAM_only']=True
        rows,spec=c.verify_qualified_receipt(qualified,verification,manifests,foldrec,'C',8192,ARMS[0]);assert len(rows)==315;checks['final_train_metadata315_and_qualified']=True
        assert c.validate_order(resolve(order),fold['train_case_ids']);checks['exact3900_order']=True
        ram['RAM:authorization']['explicit_user_authorization']=False
        try:c.authorize({'path':'RAM:request','sha256':'1'*64},{'path':'RAM:authorization','sha256':'2'*64},{'path':'RAM:runtime','sha256':'3'*64})
        except ValueError:checks['false_authorization_rejected']=True
        else:raise AssertionError('false authorization accepted')
    finally:c.json_bound=original
    # Bootstrap the final sibling without model/dependency imports.
    e=module('final_blue_noise_entry',I/'bcsp_blue_noise_training_entry_v1.py');e.install_contract();checks['final_entry_pinned_bootstrap']=True
    assert all(checks.values()) and len(checks)==6
    dump(E/'final_binding_verification_v1.json',{'status':'FINAL_BINDING_SIX_CHECKS_PASS','checks':checks,'CPU20':{'sha256':sha(O/'cpu_contract_attempt_v1/result.json'),'checks':20},'delta':'resource sentinel replaced with exact current evidence hash; entry sibling contract hash updated only; runtime bytes identical','RAM_only_authorization':True,'model_CUDA_calls':0,'server_writes':0})
    evidence(E/'final_binding_verification_v1.json')
    for p in [O/'cpu_contract_attempt_v1/result.json',O/'actual_reader_verification_v1.json',O/'local_preparation_review_v1.json'] :evidence(p)
    protocol={'stage':STAGE,'arms':ARMS,'fold':'C','seed':0,'sampling_seed':0,'input':8192,'target':8192,'common_candidate_pool':32768,'fixed_rule':'unchanged compact-kernel weighted elimination; Euclidean versus conservative surface-graph path approximation; no radius/weight tuning','initialization':'fresh matched scratch seed0; same parameter and buffer fingerprints required before second arm','scientific_contract':'B0 AdaPoinTr Transformer; existing cdist Chamfer/native PointNet2; batch8,100 traversals,3900 updates,31200 exposures,300 drops; no model/optimizer/order changes','historical_V1_role':'context only; not the matched Euclidean comparator','scope_limits':['SkullBreak only; 63 training and21 development sources','one fold, one seed pilot; no confirmation/gate claim','source-mean native unknown G surface P95 primary; contact J metrics and outliers secondary; dev evaluation separately authorized','graph path is not exact continuous geodesic; separate inner/outer plate anatomical coverage not certified']}
    dump(E/'comparison_protocol_v1.json',protocol);evidence(E/'comparison_protocol_v1.json')
    dump(E/'local_P3_v1.json',{'status':'LIMITED_FINAL_BINDING_P3_PASS','tests':checks,'implementation':{p.name:sha(p) for p in I.glob('*.py')},'prior_CPU20':sha(O/'cpu_contract_attempt_v1/result.json'),'prior_all840_reader':sha(O/'actual_reader_verification_v1.json'),'limits':['No CUDA/model initialization executed','RAM-only authorization; no real auth/runtime/launcher materialized','Git unavailable on server; fixed source hashes match','Training resource peaks still require monitoring at real execution']});p3=evidence(E/'local_P3_v1.json')
    dump(F/'Euclidean_training_entry_request_v1.json',q);inner=add(F/'Euclidean_training_entry_request_v1.json','control_Euclidean_v1/training_entry_request_v1.json',CONTROL+'/training_entry_request_v1.json')
    assert len({a['member'] for a in files})==len({a['destination'] for a in files})==len(files)
    assert sum(a['member'].startswith('data/') for a in files)==630
    required=[ROOT,DATA,PROJECT+'/logs/cranial_bcsp_blue_noise_ab_v1'];assert obs['new_roots_absent']==required
    mappingfile=F/'non_overwrite_installation_mapping_v1.json'
    dump(mappingfile,{'status':'FROZEN_NOT_INSTALLED','assets':files,'required_new_roots':required,'scope':'two arms train315 each plus exact minimal code/evidence; no development NPZ, raw volumes, source_selections or weights','install_contract':'Immediately before any server write recheck hostname/uid/GPU, archive hashes, every target and ancestor; all files absent and unlinked; exclusive creation only; postwrite size/SHA256; any exception stops without automatic retry'})
    T=F/'transport_v1';T.mkdir();name='bcsp_blue_noise_ab_foldc_seed0_v1';archive=T/(name+'.tar.gz')
    with archive.open('xb') as stream:
        with gzip.GzipFile(fileobj=stream,mode='wb',mtime=0,filename='',compresslevel=6) as z:
            with tarfile.open(fileobj=z,mode='w',format=tarfile.USTAR_FORMAT) as tar:
                for a in files:
                    raw=Path(a['local_path']).read_bytes();assert shab(raw)==a['sha256']
                    info=tarfile.TarInfo(a['member']);info.size=len(raw);info.mode=0o644;info.mtime=0;tar.addfile(info,io.BytesIO(raw))
    with tarfile.open(archive,'r:gz') as tar:
        members=tar.getmembers();assert len(members)==len(files)
        for m,a in zip(members,files):assert m.isfile() and m.name==a['member'] and m.size==a['bytes'] and shab(tar.extractfile(m).read())==a['sha256']
    transports=[archive]
    for suffix,text in [('.tar.gz.sha256',sha(archive)+'  '+archive.name+'\n'),('.bytes',str(archive.stat().st_size)+'\n'),('.contents.sha256',''.join(a['sha256']+'  '+a['member']+'\n' for a in files))]:
        p=T/(name+suffix);write(p,text);transports.append(p)
    p=T/(name+'.contents.sha256.sha256');write(p,sha(T/(name+'.contents.sha256'))+'  '+name+'.contents.sha256\n');transports.append(p)
    env=c.expected_environment(json.loads(mapping[base['preflight_scope']['path']].read_bytes()),identity,OUT);env['TMPDIR']=OUT+'/tmp'
    request={'schema':'bcsp-blue-noise-first-model-execution-scope-v1','status':'AWAITING_EXPLICIT_USER_AUTHORIZATION','execution_authorized':False,'stage':STAGE,'run_id':RUN,
      'scope':'after manual upload and explicit complete-hash authorization: fixed non-overwrite installation, then exactly one fresh Euclidean FoldC seed0 training; graph arm data installed only, no graph training authorized','training_runs_authorized_by_this_pending_scope':1,'planned_pair_total_runs':2,'candidate_training_authorized':False,
      'identity':identity,'inner_request':inner,'scientific_config':static,'order_plan':order,'resource_rebind':rr,'local_P3':p3,'training_counts':{'sources':63,'cases':315,'input':8192,'target':8192,'batch':8,'traversals':100,'updates':3900,'exposures':31200,'dropped_exposures':300},'resources_per_run':config['resources'],
      'transport':{'files':[{'path':str(p),'filename':p.name,'bytes':p.stat().st_size,'sha256':sha(p),'upload_directory':'/home/jovyan'} for p in transports],'archive_sha256':sha(archive),'members':len(files),'installation_mapping':{'path':str(mappingfile),'sha256':sha(mappingfile)}},
      'future_paths':{'control':CONTROL,'authorization':CONTROL+'/authorization_v1.json','runtime':CONTROL+'/runtime_v1.json','launcher':CONTROL+'/launch_once_v1.sh','launch_attempt':q['launch_attempt'],'output':OUT,'log':OUT+'/launch.log','PID':OUT+'/worker.pid','exit_code':OUT+'/exit_code.txt','checkpoint':OUT+'/ckpt-last.pth','completion':OUT+'/completion.json','tmux':'bcsp_blue_noise_foldc_euclidean_seed0_train_v1'},
      'launcher_contract':{'environment':env,'python':identity['python_realpath'],'flags':['-I','-S','-B'],'entry':q['implementation']['entry']['path'],'entry_sha256':q['implementation']['entry']['sha256'],'external_timeout_seconds':86400,'kill_after_seconds':5,'transport':'original file bytes Base64 with byte/SHA256 verification; raw stdout/stderr capture; use WSL --exec; PowerShell propagates LASTEXITCODE','order':'recheck upload/source/resource/absence gates; validate and create log parents before redirection; one-way authorization then runtime; claim exclusive attempt before exactly one fixed tmux launch','one_way_materialization':'inner/full request hashes -> explicit authorization -> authorization SHA256 -> runtime -> launcher; no reverse runtime hash in authorization'},
      'scientific_risk_disclosure':['Read-only source match is not current CUDA certification; prior GPU evidence retained without repeated preflight','CPU metadata and RAM grant checks do not execute actual model initialization/optimizer','Resource monitoring with unchanged thresholds; no dedicated cgroup or strict SMI-PID ownership','Server is not a Git checkout; all30 exact selected source/provider/environment assets matched','Sampling has exploratory geometry evidence only; no model accuracy benefit claimed'],
      'completion_boundary':'Stop after the one Euclidean attempt. Independent post-training freeze audit and baseline initialization evidence required before a separately authorized graph request.',
      'forbidden':['no graph or extra training','no development payload/evaluation','no BNCal','no FoldD/SkullFix/MUG/Mamba changes','no resume or automatic retry','no dependency download/build/install or environment upgrade; no frozen model/provider source changes','no old-file overwrite/delete','no use of provenance Windows paths in server commands']}
    req=F/'Euclidean_training_execution_request_v1.json';dump(req,request);write(F/(req.name+'.sha256'),sha(req)+'  '+req.name+'\n')
    dump(F/'freeze_receipt_v1.json',{'status':'TRANSPORT_AND_PENDING_REQUEST_FROZEN','request_sha256':sha(req),'archive_sha256':sha(archive),'archive_bytes':archive.stat().st_size,'members':len(files),'train_NPZ':630,'server_writes':0,'training_calls':0,'real_authorization_runtime_launcher_created':0,'seconds':time.monotonic()-start})
    report=f'''# 欧氏／图距离 Fold C：服务器就绪核对与首运行待授权范围\n\n日期：2026-11-04。状态：AWAITING_EXPLICIT_USER_AUTHORIZATION。\n\n当前容器 {identity['hostname']}，UID1000，RTX4090D，GPU UUID {identity['gpu_uuid']}，驱动 {identity['driver_version']}。SMI显存1MiB、无计算进程；磁盘可用{obs['disk_free']/1024**3:.2f}GiB。30个固定资产共{assetsobs['hashed_bytes']}字节全部大小及SHA256匹配。三个新根目录不存在，父目录可写且无链接。Git查询返回128，原因是服务器副本不是Git仓库；保留失败查询及成功补证原文，以固定文件哈希绑定源码身份。第二版服务器查询返回0且完整观察落盘，本机随后摘要打印因字段分支产生KeyError；不影响已落盘的只读证据，未因此再发起查询。\n\n保留原本机implementation目录。最终部署候选只替换contract的资源占位哈希及entry的contract哈希，runtime逐字节不变。既有20项CPU检查及840文件读取结果继续保留；最终绑定另做6项限定检查，包括实际rebind、完整authorize、训练元数据、批次、拒绝未授权和入口哈希启动。授权仅在RAM中模拟，没有真实授权文件。以上不是CUDA或模型训练验证。\n\n运输包含两臂各315份训练点集，合计630份NPZ及固定代码/证据，共{len(files)}个文件；不运输开发点集、原始体素、诊断选点或权重。安装映射使用精确Linux绝对路径，manifest内Windows路径只作溯源，不执行或猜测转换。\n\n首个request仅覆盖一次Euclidean_elimination，FoldC、seed0、8k→8k、batch8、100遍历、3900更新、31200曝光及300丢弃。第二臂必须等待首臂训练后审计并绑定相同初始化指纹，再单独授权。资源合同保持24h、RSS8GiB、设备显存22528MiB、Torch峰值20GiB、输出2GiB及启动前可用磁盘4GiB。失败即停，不自动重试或resume。\n\nrequest SHA256：`{sha(req)}`。压缩包：`{archive.name}`，{archive.stat().st_size} bytes，SHA256 `{sha(archive)}`。\n\n运输文件位于本目录transport_v1；上传到/home/jovyan后，仍须先核验上传与目标不存在性。当前未上传、安装、材料化真实授权/runtime/launcher或启动训练。需另行明确授权完整request SHA256。\n'''
    write(F/'readiness_and_pending_request_report_zh_v1.md',report)
    print(json.dumps({'status':'PENDING_REQUEST_FROZEN','request_sha256':sha(req),'archive_sha256':sha(archive),'archive_bytes':archive.stat().st_size,'members':len(files),'transport_directory':str(T)}))
if __name__=='__main__':main()
