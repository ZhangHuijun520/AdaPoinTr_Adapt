"""Fold D preparation: frozen scientific contract plus bounded read-only assets; no training."""
import ast,collections,copy,hashlib,json,shlex,subprocess,time
from pathlib import Path
S=Path(__file__).resolve().parent;R=S.parents[2];P1=R/'outputs/cranial_bcsp_mamba_p1_20261104';G=R/'outputs/cranial_bcsp_geov1_20261024'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def bind(p):return dict(path=str(p.absolute()),bytes=p.stat().st_size,sha256=sha(p))
def emit(n,v):
 with (S/n).open('x',encoding='utf-8') as f:json.dump(v,f,indent=2,ensure_ascii=False,allow_nan=False)
bp=P1/'M0_FoldD_request_v1/transport_payload/M0_foldD_seed0_training_execution_request_v1.json';ba=P1/'M0_FoldD_request_v1/post_training_freeze_audit_v1/audit_report_v1.json'
assert sha(bp)=='55793bca2fa9472d45b3cca0b9598154cdb12a84a3eb89633daa52b85a039d5f' and sha(ba)=='f65c3dd7d82814f705a09f11f5fa95f2583fba71380cdd29cd8b9f4f59e5bb61'
base=json.loads(bp.read_bytes());audit=json.loads(ba.read_bytes());assert audit['checks_passed']==len(audit['checks']) and all(audit['checks'].values())
CP=S.parent/'H2_COUPLE_foldC_initialization_readfix_v2';cq=json.loads((CP/'final_pending_request_v2/transport_payload/H2_COUPLE_foldC_seed0_training_execution_request_v2.json').read_bytes());ca=CP/'post_training_freeze_audit_v1/audit_report_v2.json'
assert sha(ca)=='5a040e5d5903264c3658e52fb00c50a17b531394efcb804fa17af2f76b7310de';c_audit=json.loads(ca.read_bytes());assert c_audit['checks_passed']==34 and all(c_audit['checks'].values())
fp=G/'consolidated_binding_v1/fold_binding.json';assert sha(fp)==base['QC']['fold_binding']['sha256'];fold=json.loads(fp.read_bytes())['folds']['D'];ids=fold['train_case_ids']
op=P1/'FoldD_pair_preparation_20261106_v1/shared_order_foldD_seed0_v1.json';assert sha(op)==base['order_plan']['sha256'];order=json.loads(op.read_bytes());assert order['case_ids']==ids and len(ids)==len(set(ids))==315 and len(order['epochs'])==100
assert len(fold['train_sources'])==63 and len(fold['dev_sources'])==21 and not set(fold['train_sources'])&set(fold['dev_sources'])
manifest=G/'real_data_qc_v1/manifest_8192.jsonl';assert sha(manifest)==base['QC']['manifests']['8192']['sha256'];rows=[json.loads(x) for x in manifest.read_text().splitlines()];selected={r['case_id']:r for r in rows if r['case_id'] in set(ids)}
assert len(selected)==315 and set(collections.Counter(r['source_id'] for r in selected.values()).values())=={5}
exposure,drop=collections.Counter(),collections.Counter()
for epoch,e in enumerate(order['epochs']):
 assert e['epoch']==epoch and len(e['batches'])==39 and len(e['dropped'])==3 and all(len(x)==8 for x in e['batches']);flat=sum(e['batches'],[])+e['dropped'];assert len(flat)==len(set(flat))==315 and set(flat)==set(ids)
 exposure.update(sum(e['batches'],[]));drop.update(e['dropped'])
assert sum(exposure.values())==31200 and sum(drop.values())==300
canonical=hashlib.sha256(json.dumps(order,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest();assert canonical==audit['order']['canonical_sha256']
static=json.loads((CP/'final_pending_request_v2/transport_payload/static_H2_COUPLE_training_config_v1.json').read_bytes());aux=copy.deepcopy(static);aux['H2']['mode']='AUX'
emit('static_H2_AUX_foldD_candidate_v1.json',aux);emit('static_H2_COUPLE_foldD_candidate_v1.json',static)
contract=dict(status='SCIENTIFIC_PAIR_CONTRACT_FROZEN_IMPLEMENTATION_PENDING',fold='D',arm_order=['AUX','COUPLE'],seed=0,n_input=8192,n_output=8192,counts=static['counts'],training=static['training'],resources=static['resources'],H2_common={k:v for k,v in static['H2'].items() if k!='mode'},H1=False,data_root=base['data_root'],QC=base['QC'],order_plan=base['order_plan'],canonical_order_sha256=canonical,M0_D_request=bind(bp),M0_D_formal_audit=bind(ba),FoldC_H2_formal_pair_audit=bind(ca),initialization_reference=base['initialization_reference'],initialization_policy='Both scratch from original M0 seed0 factory plus all-zero1025-parameter head; compare full H2 initial fingerprints within D. Never use C or AUX final checkpoint.',scientific_changes_from_C='Only preregistered D train/dev partition and its frozen batch order; no hyperparameter changes',prohibited=['Fold C loss/result-based tuning','New sampling or point count','Repeat GPU preflight','Training or inference in this preparation task','BNCal/evaluation/resume/automatic retry','Expansion of generic inventory/transport framework'],COUPLE_request_timing='Only after AUX_D completes and formal freeze provides exact AUX_D request/audit/initialization bindings',execution_request_created=False,training_started=False)
emit('FoldD_H2_paired_training_contract_v1.json',contract)
needed=[base['QC']['qualified_receipt'],base['order_plan'],base['QC']['fold_binding'],base['initialization_reference']]
planned=['/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p2_H2_foldD_20261107_v1','/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2/H2_AUX_foldD_seed0_20261107_v1','/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2/H2_COUPLE_foldD_seed0_20261107_v1']
emit('bounded_server_readiness_scope_v1.json',dict(identity=cq['identity'],metadata=needed,data_root=base['data_root'],payloads=[dict(path=base['data_root']+'/'+selected[c]['point_path'],sha256=selected[c]['sha256']) for c in ids],planned_targets=planned,wall_seconds=60,per_call_seconds=20,command_bytes=2048,maximum_metadata_bytes=2*1024**2,maximum_point_byte_reads=512*1024**2,NPZ_decoding=False,server_writes=0,model_calls=0))
B=['wsl.exe','-d','Ubuntu-20.04','--exec'];client='/home/zhj/.local/bin/hpc5000';start=time.monotonic()
def call(label,cmd):
 assert len(cmd.encode())<2048 and time.monotonic()-start<60
 p=subprocess.run(B+[client,'exec','--timeout','20','--',cmd],capture_output=True,timeout=30)
 for k,b in [('stdout',p.stdout),('stderr',p.stderr)]:
  with (S/(label+'_'+k+'.bin')).open('xb') as f:f.write(b)
 assert p.returncode==0,(label,p.returncode);return p.stdout.decode().replace('\r','')
def hashes(text):
 d={}
 for line in text.splitlines():
  h,p=line.split(None,1);p=p.strip();assert p not in d and len(h)==64;d[p]=h
 return d
try:
 I=cq['identity'];prefix='test "$(hostname)" = '+shlex.quote(I['hostname'])+' && test "$(id -u)" = 1000 && '
 state=call('identity_resources',prefix+'hostname && id -u && nvidia-smi --query-gpu=uuid,name,driver_version,memory.total,memory.used --format=csv,noheader,nounits && df -B1 --output=avail /home/jovyan && '+' && '.join('test ! -e '+p+' && test ! -L '+p for p in planned))
 lines=state.splitlines();gpu=[x.strip() for x in lines[2].split(',')];assert gpu[:4]==[I['gpu_uuid'],I['gpu_name'],I['driver_version'],str(I['nvidia_smi_memory_total_MiB'])] and int(gpu[4])<=256 and int(lines[-1])>=static['resources']['minimum_free_disk_bytes']
 mh=hashes(call('D_metadata_hashes','sha256sum '+' '.join(shlex.quote(r['path']) for r in needed)));assert mh=={r['path']:r['sha256'] for r in needed}
 for line in call('D_metadata_stat',"stat -c '%F|%s|%n' -- "+' '.join(shlex.quote(r['path']) for r in needed)).splitlines():
  typ,size,p=line.split('|',2);assert typ=='regular file' and int(size)==next(r['bytes'] for r in needed if r['path']==p)
 points=base['data_root']+'/points';text=call('D_point_inventory',prefix+'cd '+points+" && find . -mindepth 1 -maxdepth 1 -printf '%y|%s|%f\\n' | sort");inventory=[line.split('|',2) for line in text.splitlines()];expected={selected[c]['point_path'].removeprefix('points/'):selected[c]['sha256'] for c in ids}
 assert len(inventory)==315 and all(x[0]=='f' for x in inventory) and {x[2] for x in inventory}==set(expected) and sum(int(x[1]) for x in inventory)<=512*1024**2
 ph=hashes(call('D_315_point_hashes',prefix+'cd '+points+" && find . -maxdepth 1 -type f -print0 | sort -z | xargs -0 sha256sum"));assert ph=={'./'+p:h for p,h in expected.items()}
 emit('server_readiness_receipt_v1.json',dict(status='FOLDD_H2_NECESSARY_READONLY_READINESS_PASS',identity=I,GPU_used_MiB=int(gpu[4]),free_disk_bytes=int(lines[-1]),metadata_bindings_verified=needed,training_cases=315,sources=63,point_bytes=sum(int(x[1]) for x in inventory),point_SHA256=ph,planned_targets_absent=True,seconds=time.monotonic()-start,server_writes=0,NPZ_arrays_decoded=0,checkpoint_loads=0,model_calls=0,implementation_ready=False,execution_request_created=False,training_started=False))
 print(json.dumps(dict(status='FOLDD_H2_NECESSARY_READONLY_READINESS_PASS',GPU_used_MiB=int(gpu[4]),free_disk_bytes=int(lines[-1]),training_cases=315,metadata_files=4,implementation_ready=False)))
except BaseException as exc:
 emit('readiness_failure_v1.json',dict(status='FAILED_STOP_NO_RETRY',error=repr(exc)));raise
