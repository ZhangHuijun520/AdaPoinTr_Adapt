"""Local final archive and verified reuse of two existing checkpoints; no server/model calls."""
from pathlib import Path
import importlib.util,hashlib,json,re,shutil
R=Path(__file__).resolve().parent.parent
sp=importlib.util.spec_from_file_location('archive_util',R/'local_tools/archive_scq_BS_20261114_v1.py');u=importlib.util.module_from_spec(sp);sp.loader.exec_module(u)
D=R/'deliverables/scq_DAC_20261115_v1';BACK=Path('E:/ResearchBackups/AdaPoinTr/BCSP_FULLMAMBA_SCQ_DAC/2026-11-15_code_results_v1');CP=BACK.parent/'2026-11-15_reused_key_checkpoints_v1'
assert not BACK.exists() and not CP.exists()
if D.exists():assert not list(D.iterdir()),'refuse reuse nonempty archival attempt'
else:D.mkdir()
PUB=D/'public_payload';PRIV=D/'local_attachments'
B=R/'outputs/scq_dac_r01_preparation_20261115_v1';REPORT=R/'docs/cranial_bcsp_scq_dac_20261115_final'
assert u.sha(REPORT/'Cranial_BCSP_FullMamba_SCQ_DAC_完整实验报告_zh_2026-11-15_v1.md')==json.loads(u.read(REPORT/'stage_closure_receipt_v1.json'))['report']['sha256']
selected={};private={};excluded=[]
for root in [B,REPORT,R/'docs/cranial_bcsp_scq_dac_plan_20261115']:
 for p in u.inventory(root):
  if '__pycache__' in p.parts:continue
  name='evidence/'+p.relative_to(R).as_posix()
  if p.suffix=='.pth':excluded.append(dict(path=str(p),reason='artificial checkpoint fixture, regenerate from test; no new DAC trained weights'));continue
  if 'cpu_contract_batch_v1' in p.parts and 'ARTIFICIAL' in p.parts:
   if p.suffix not in ('.json','.md','.txt','.py'):excluded.append(dict(path=str(p),reason='regenerable artificial binary fixture'));continue
  is_private=p.suffix in ('.npz','.bin','.gz') or p.name=='metadata_result_v1.json'
  if is_private:private[name]=p
  else:
   assert p.suffix in ('.json','.jsonl','.md','.py','.txt','.csv','.sha256','.bytes','.sh','.log','.pid'),str(p)
   selected[name]=p
for p in (R/'local_tools').glob('*.py'):
 if 'dac' in p.name.lower():selected['archive_tools/'+p.name]=p
# Reuse a compact inherited source tree and exact small initializer bindings.
parent=R/'deliverables/scq_RF_20261115_v1/public_payload'
for p in u.inventory(parent):
 if p.suffix=='.py' or p.name=='LICENSE':selected['inherited_RF_sources/'+p.relative_to(parent).as_posix()]=p
mappingfile=R/'outputs/scq_rf_sixmodel_native_prediction_preparation_20261115_v1/implementation_v1/input_path_fix_v2/pending_request_v2/local_mirror_v2.json'
mirror=json.loads(u.read(mappingfile));q=json.loads(u.read(B/'pending_request_v1/SCQ_DAC_R1_execution_request_v1.json'));bindings=[]
for key in ['initialization','rf_initialization','static_config','preflight_scope','native_library','helper']:
 r=q[key]
 fallback={'preflight_scope':R/'outputs/cranial_bcsp_geov1_20261024/gpu_preflight_plotting_lazy_v3/artificial_gpu_zero_update_frozen_scope_v3.json','native_library':R/'outputs/scq_rf_sixmodel_native_prediction_preparation_20261115_v1/implementation_v1/input_path_fix_v2/bcsp_scq_rf_sixmodel_native_predict_v2.py','helper':R/'outputs/cranial_bcsp_geov1_20261024/gpu_preflight_plotting_lazy_v3/bcsp_artificial_gpu_preflight_v3.py'}
 p=Path(mirror[r['path']]) if r['path'] in mirror else fallback[key]
 assert u.sha(p)==r['sha256'];name='bound_sources/'+hashlib.sha256(r['path'].encode()).hexdigest()[:12]+'_'+p.name
 (private if p.suffix=='.bin' else selected)[name]=p;bindings.append(dict(role=key,remote=r['path'],member=('local_attachments/' if p.suffix=='.bin' else 'public_payload/')+name,bytes=r['bytes'],sha256=r['sha256']))
metric=R/'outputs/cranial_bcsp_geov1_20261024/blue_pair_eval_v1/bcsp_eval_metrics_v1.py';selected['bound_sources/'+metric.name]=metric
scorer=R/'outputs/scq_rf_score_impl_20261115_v1/bcsp_scq_rf_three_arm_score_v1.py';selected['bound_sources/'+scorer.name]=scorer
patterns=[rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',rb'(?:gh[pousr]_[A-Za-z0-9]{25,}|github_pat_[A-Za-z0-9_]{30,})',rb'Bearer\s+[A-Za-z0-9_.-]{30,}',rb'eyJ[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}',rb'https?://[^\s/\x22\x27]+:[^\s/@\x22\x27]+@']
manifest=[]
for n,p in sorted(selected.items()):
 b=u.read(p);assert len(b)<50*1024**2 and not any(re.search(pat,b) for pat in patterns),n
 u.put(PUB/n,b);manifest.append(dict(path=n,source=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
private_manifest=[]
for n,p in sorted(private.items()):
 dest=PRIV/n;u.lp(dest.parent).mkdir(parents=True,exist_ok=True);shutil.copyfile(u.lp(p),u.lp(dest));assert u.sha(dest)==u.sha(p);private_manifest.append(dict(path=dest.relative_to(D).as_posix(),bytes=u.lp(dest).stat().st_size,sha256=u.sha(dest)))
u.js(PUB/'source_manifest_v1.json',manifest);u.js(PUB/'local_only_manifest_v1.json',private_manifest);u.js(PUB/'excluded_regenerable_fixtures_v1.json',excluded);u.js(PUB/'inherited_source_bindings_v1.json',bindings)
weightsdir=Path('E:/ResearchBackups/AdaPoinTr/BCSP_FULLMAMBA_SCQ_RF/2026-11-15_key_checkpoints_v1');wr=json.loads(u.read(weightsdir/'local_verification_receipt_v1.json'));weights=[w for w in wr['weights'] if w['run'] in ('Requery_C','Requery_D')];assert len(weights)==2
CP.mkdir(parents=True);copy_rows=[]
for w in weights:
 source=Path(w['local_path']);assert source.stat().st_size==w['bytes'] and u.sha(source)==w['sha256'];dest=CP/source.name;shutil.copyfile(source,dest);assert dest.stat().st_size==w['bytes'] and u.sha(dest)==w['sha256'];copy_rows.append(dict(run=w['run'],source=str(source),local_path=str(dest),bytes=w['bytes'],sha256=w['sha256']))
u.js(CP/'checkpoint_verification_v1.json',dict(status='TWO_REUSED_RF_CHECKPOINTS_COPIED_AND_FRESH_HASH_VERIFIED',weights=copy_rows,no_new_DAC_checkpoint=True,checkpoint_deserialized=False,restore_execution=False,GitHub_weights=False,source_receipt=u.record(weightsdir/'local_verification_receipt_v1.json',weightsdir)))
u.js(PUB/'reused_checkpoint_identity_v1.json',dict(no_new_DAC_trained_weights=True,weights=[{k:w[k] for k in ('run','bytes','sha256')} for w in weights],local_backup_directory=str(CP),not_published=True))
report=next(REPORT.glob('*完整实验报告*.md'));u.put(PUB/'REPORT_zh.md',u.read(report))
u.put(PUB/'README.md',b'''# Cranial-BCSP-FullMamba: SCQ-DAC closed diagnostic stage

See [the complete report](REPORT_zh.md). This stage performed 36 artificial CPU contracts, one frozen-weight diagnostic (20 whole-model Native forwards +40 decoder-only calls), a formal read-only freeze audit, and 60 offline geometry scores on fixed20 development cases. No DAC model was trained. The current fixed agreement formula is closed without the planned six-run training matrix; its frozen-weight geometric evidence did not justify that investment. This is not proof that all end-to-end dual-neighborhood models fail.

Public: source code, configurations, scalar scores, audits, report and exact provenance. Local-only: prediction/Memory arrays, raw captures, binary initializers and diagnostic archive. Two reused RF-Requery checkpoints are separately copied and freshly hash-verified locally, never uploaded here. Raw skull datasets, GT arrays and compiled environments are excluded. Regenerable artificial checkpoint fixtures are excluded. Historical authorization/launcher records are inert provenance, not permission to rerun. The RNG audit limitation is retained: runtime equality was checked, but raw before/after RNG fingerprints were not saved.

The exact inherited source snapshot and identities preserve method context; absolute historical paths require explicit rebinding and do not make this a portable full runtime. Raw geometry references remain in the user's local dataset/reference bank. No new model/server/scoring work is performed by archival. Annotated tag: cranial-bcsp-scq-dac-20261115-v1.
''')
print(json.dumps(dict(stage='PUBLIC_AND_PRIVATE_SNAPSHOTS_READY',public=len(u.inventory(PUB)),private=len(private_manifest),weights_copied=2)),flush=True)
archive=u.pack(D,u.inventory(PUB)+u.inventory(PRIV),D/'scq_DAC_code_results_20261115_v1.tar.gz')
receipt=dict(status='SCQ_DAC_CODE_RESULTS_ALL_MEMBERS_VERIFIED',archive=archive,public_files=len(u.inventory(PUB)),private_files=len(private_manifest),weights_in_archive=False,checkpoints_backup=str(CP),secret_pattern_scan='PASS',server_calls=0,forward=0)
u.js(D/'archive_verification_v1.json',receipt);BACK.mkdir(parents=True)
for p in [D/'scq_DAC_code_results_20261115_v1.tar.gz',*(D/('scq_DAC_code_results_20261115_v1.tar.gz'+s) for s in ['.sha256','.bytes','.contents.sha256']),D/'archive_verification_v1.json']:
 dst=BACK/p.name;shutil.copyfile(p,dst);assert u.sha(dst)==u.sha(p)
expected={p.relative_to(D).as_posix():dict(bytes=u.lp(p).stat().st_size,sha256=u.sha(p)) for p in u.inventory(PUB)+u.inventory(PRIV)}
assert u.tar_verify(BACK/'scq_DAC_code_results_20261115_v1.tar.gz',expected)==archive['members']
u.js(D/'long_term_backup_receipt_v1.json',dict(status='LOCAL_BACKUP_AND_ALL_ARCHIVE_MEMBERS_READBACK_PASS',directory=str(BACK),archive=archive,checkpoint_directory=str(CP)));shutil.copyfile(D/'long_term_backup_receipt_v1.json',BACK/'long_term_backup_receipt_v1.json')
print(json.dumps(dict(status='DAC_ARCHIVE_AND_TWO_REUSED_CHECKPOINT_BACKUPS_COMPLETE',archive=archive,backup=str(BACK),checkpoint_backup=str(CP))),flush=True)
