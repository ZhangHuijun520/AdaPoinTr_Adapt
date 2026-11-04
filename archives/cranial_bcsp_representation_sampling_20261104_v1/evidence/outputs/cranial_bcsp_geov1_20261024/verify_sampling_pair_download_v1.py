"""Read-only verification of manually downloaded artifacts; never extract or score."""
import array,ast,hashlib,io,json,math,struct,sys,tarfile,time,zipfile
from pathlib import Path
B=Path(__file__).resolve().parent;N=B/'sampling_model_AB_foldC_seed0_20261103_v1/paired_development_eval_v1'
F=N/'freeze_audit_v1';V=N/'local_download_verification_v1'
LOCAL=Path('E:/ResearchBackups/AdaPoinTr/BCSP_SAMPLING_AB_V1/2026-11-03_paired_development_eval')
def need(ok,msg):
 if not ok:raise ValueError(msg)
def h(raw):return hashlib.sha256(raw).hexdigest()
def fingerprint(p):
 st=p.stat();return st.st_dev,st.st_ino,st.st_mode,st.st_size,st.st_mtime_ns
def sha(p):
 d=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):d.update(b)
 return d.hexdigest()
def main():
 start=time.monotonic();V.mkdir();checks=[];verified=[];stamps={};members=[]
 def check(name,ok):need(ok,name);checks.append(name)
 try:
  handoff_raw=(F/'manual_download_handoff_v1.json').read_bytes();handoff=json.loads(handoff_raw)
  report_raw=Path(handoff['audit_report']['path']).read_bytes();check('parent_formal_audit_hash',h(report_raw)==handoff['audit_report']['sha256'])
  report=json.loads(report_raw);check('parent_formal_audit_PASS',report['status']=='FORMAL_POST_PREDICTION_FREEZE_AUDIT_PASS')
  check('local_directory_regular_unlinked',LOCAL.is_dir() and not any(p.is_symlink() for p in [LOCAL,*LOCAL.parents]))
  expected_names={Path(r['path']).name for r in handoff['files']}
  check('exact_four_downloaded_files',{p.name for p in LOCAL.iterdir()}==expected_names)
  for r in handoff['files']:
   p=LOCAL/Path(r['path']).name;need(p.is_file() and not p.is_symlink(),'file type/link');stamps[str(p)]=fingerprint(p)
   actual=dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p));check('exact_size_SHA256_'+p.name,actual['bytes']==r['bytes'] and actual['sha256']==r['sha256']);verified.append(actual)
  archive=LOCAL/'development_predictions_v1.tar.gz';records=report['prediction_manifest'];lookup={r['name']:r for r in records}
  check('frozen_213_member_manifest_unique',len(records)==len(lookup)==213)
  content=''.join(r['sha256']+'  '+r['name']+'\n' for r in records)
  check('contents_sidecar_exact',Path(str(archive)+'.contents.sha256').read_text(encoding='ascii')==content)
  check('hash_sidecar_exact',Path(str(archive)+'.sha256').read_text(encoding='ascii')==verified[0]['sha256']+'  '+archive.name+'\n')
  check('bytes_sidecar_exact',Path(str(archive)+'.bytes').read_text(encoding='ascii')==str(archive.stat().st_size)+'\n')
  # Extract only the existing pure stdlib prediction-structure validator into memory.
  tree=ast.parse((F/'readonly_audit_source_v1.py').read_text(encoding='utf-8'))
  fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='array_contract')
  ns=dict(array=array,ast=ast,io=io,math=math,struct=struct,sys=sys,zipfile=zipfile,need=need)
  exec(compile(ast.Module(body=[fn],type_ignores=[]),'hash_bound_existing_array_validator','exec'),ns)
  expanded=0;predictions=0;metadata={}
  with tarfile.open(archive,'r:gz') as tf:
   entries=tf.getmembers();check('exact213_ordered_regular_archive_members',len(entries)==213 and [m.name for m in entries]==[r['name'] for r in records] and all(m.isfile() for m in entries))
   for m in entries:
    need(m.size==lookup[m.name]['bytes'] and 0<m.size<=4194304,'archive size budget')
    raw=tf.extractfile(m).read();expanded+=len(raw);need(expanded<=67108864 and time.monotonic()-start<=90,'verification budget')
    need(h(raw)==lookup[m.name]['sha256'],'member hash mismatch: '+m.name)
    if m.name.startswith('predictions/'):
     ns['array_contract'](raw);predictions+=1
    else:metadata[m.name]=raw
    members.append(dict(name=m.name,bytes=len(raw),sha256=h(raw)))
  check('all213_archive_member_hashes_match',len(members)==213)
  check('all210_predictions_finite_float32_8192x3',predictions==210)
  index=json.loads((N/'development_input_index_v1.json').read_bytes());observed=[json.loads(line) for line in metadata['inference_manifest.jsonl'].decode().splitlines()]
  check('same210_provenance_and_order',len(observed)==210 and [x['forward_index'] for x in observed]==list(range(1,211)) and all((a['run'],a['case_id'],a['source_id'],a['input_sha256'])==(b['run'],b['case_id'],b['source_id'],b['input']['sha256']) for a,b in zip(observed,index['inputs'])))
  done=json.loads(metadata['inference_complete.json'])
  check('completion_and_state_match_formal_audit',done['status']=='SAMPLING_PAIR_210_FORWARD_COMPLETE' and done['forwards']==210 and done['models']==report['state_evidence'] and all(done[k]==0 for k in ['training_updates','BNCal','loss','backward']))
  check('four_downloaded_files_stable_atime_excluded',all(fingerprint(Path(p))==v for p,v in stamps.items()))
  result=dict(status='LOCAL_DOWNLOADED_PREDICTION_ARCHIVE_VERIFIED',checks=checks,local_directory=str(LOCAL),downloaded_to_local=True,local_backup_verified=True,download_files=verified,archive_members=members,predictions=210,unique_cases=105,sources=21,formal_server_audit_sha256=h(report_raw),handoff_sha256=h(handoff_raw),expanded_bytes=expanded,seconds=time.monotonic()-start,archive_extracted=False,local_backup_directory_modified=False,server_operations=0,model_imports=0,forward_calls=0,scoring_executed=False,metrics_computed=False,limitations=['Local copy verification, not restoration of model weights; prediction archive contains no checkpoint','No reconstruction metrics or method comparisons calculated'])
 except BaseException as exc:
  result=dict(status='LOCAL_DOWNLOAD_VERIFICATION_FAILED_STOP_NO_RETRY',checks=checks,error=repr(exc),download_files=verified,scoring_executed=False,server_operations=0)
 with (V/'verification_result_v1.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
 print(json.dumps({k:v for k,v in result.items() if k!='archive_members'}))
 if result['status']!='LOCAL_DOWNLOADED_PREDICTION_ARCHIVE_VERIFIED':raise SystemExit(1)
 with (V/'verification_report_zh_v1.md').open('x',encoding='utf-8',newline='\n') as f:f.write('# V1／Morton配对预测：本机下载核验 v1\n\n核验通过。四个下载文件的大小与SHA256均与正式服务器冻结审计一致；213个归档成员哈希及完整顺序一致，210份预测均为finite float32、8192×3。105病例、21来源的身份、顺序和状态证据一致。读取前后四文件内容相关属性稳定。\n\n本机位置：`'+str(LOCAL)+'`。归档SHA256：`'+sha(archive)+'`。本次仅在项目目录新增核验回执，未解压、修改备份目录、连接服务器或计算评分。\n\n下一步需单独授权两臂评分入口的限定适配、人工CPU合同验证与P3，再冻结评分request；不得直接使用旧四模型评分工具或改动当前固定参考、主次指标和来源等权汇总。\n')
 with (V/'artifact_manifest_v1.json').open('x') as f:json.dump(dict(files=[dict(name=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(V.iterdir()) if p.is_file()]),f,indent=2)
if __name__=='__main__':main()
