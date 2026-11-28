"""Separately authorized EJTC R/T/J scoring. Frozen geometry metrics, no gate decision."""
import argparse
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path,PurePosixPath
import sys
import tarfile
import time
from types import FunctionType
os.environ.update(CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',MKL_NUM_THREADS='2')
import numpy as np

ARMS=('R','T','J')
COUNTS=dict(model_rows=315,case_pairs=105,sources=21,comparisons=3,bootstrap_replicates=2000)
BOOTSTRAP_SEED=2026112807
def need(ok,why):
 if not ok:raise ValueError(why)
def digest(raw):return hashlib.sha256(raw).hexdigest()
def exact(rec):
 p=Path(rec['path']);a=p.stat()
 need(p.is_absolute() and p.resolve()==p and not p.is_symlink() and p.is_file() and a.st_size==rec['bytes'],'frozen path/size')
 raw=p.read_bytes();z=p.stat();need((a.st_ino,a.st_size,a.st_mtime_ns)==(z.st_ino,z.st_size,z.st_mtime_ns) and digest(raw)==rec['sha256'],'frozen file bytes')
 return raw
def module(rec):
 exact(rec);spec=importlib.util.spec_from_file_location(Path(rec['path']).stem,rec['path']);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def save(path,value):
 with path.open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,allow_nan=False);f.write('\n')
def authorize(q,sha,auth):
 need(q['schema']=='bcsp-ejtc-rtj-cpu-score-v1' and q['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION' and q['execution_authorized'] is False and q['counts']==COUNTS and q['arms']==list(ARMS) and q['bootstrap']==dict(generator='PCG64',seed=BOOTSTRAP_SEED,replicates=2000,source_count=21) and q['single_attempt'] is True and q['automatic_retry'] is False and q['formal_gate_executed_here'] is False,'exact scoring contract')
 need(set(auth)=={'schema','request_sha256','explicit_user_authorization','user_authorization_text'} and auth['schema']=='bcsp-development-authorization-v1' and auth['request_sha256']==sha and auth['explicit_user_authorization'] is True and sha in auth['user_authorization_text'],'separate exact-hash authorization')
def archive_members(q):
 audit=json.loads(exact(q['prediction_freeze']));local=json.loads(exact(q['local_download_verification']))
 need(audit['status']=='FORMAL_READ_ONLY_EJTC_NATIVE315_V2_POST_PREDICTION_FREEZE_AUDIT_PASS' and audit['request_sha256']==q['prediction_request_sha256'] and audit['predictions']==315 and audit['archive_members']==320 and audit['state_and_all_RNG_streams_unchanged'] is True,'formal prediction freeze')
 need(local['status']=='EJTC_NATIVE315_LOCAL_DOWNLOAD_AND_ALL_MEMBERS_VERIFIED' and local['formal_remote_audit_sha256']==q['prediction_freeze']['sha256'] and local['request_sha256']==q['prediction_request_sha256'] and local['all_local_member_hashes_match'] is True,'local download freeze')
 raw=exact(q['archive']);listing=json.loads(exact(q['member_listing']))
 need(digest(raw)==audit['archive']['sha256'] and len(raw)==audit['archive']['bytes'] and len(listing)==320 and q['member_listing']['sha256']==audit['listing_sha256'],'archive binding')
 for key,rec in [('archive_checksum',q['archive']),('listing_checksum',q['member_listing'])]:need(exact(q[key]).decode('ascii').split()==[rec['sha256'],Path(rec['path']).name],'checksum content')
 out={};observed=[]
 with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as t:
  for item in t:
   name=item.name;parts=PurePosixPath(name)
   need(item.isfile() and not parts.is_absolute() and '..' not in parts.parts and name not in out and len(out)<320 and 0<item.size<=2097152,'archive member safety')
   blob=t.extractfile(item).read();need(len(blob)==item.size,'member size');out[name]=blob;observed.append(dict(name=name,bytes=len(blob),sha256=digest(blob)))
 need(observed==listing,'full member inventory/hashes')
 return out
def index_cases(q,scope,index,manifest):
 rows=index['cases'];need(len(rows)==len(set(r['case_id'] for r in rows))==105 and [r['case_id'] for r in rows]==q['case_ids']==scope['case_ids'],'fixed 105 case order')
 need(sorted(set(r['source_id'] for r in rows))==q['source_ids'] and len(q['source_ids'])==21 and all(sum(r['source_id']==s for r in rows)==5 for s in q['source_ids']),'21 sources, five defects each')
 need(len(manifest)==315,'315 manifest rows');lookup={}
 for j,(arm,c) in enumerate(((a,c) for a in ARMS for c in rows),1):
  r=manifest[j-1];src=scope['inputs'][(j-1)%105];cid=c['case_id']
  need((r['index'],r['arm'],r['fold'],r['seed'],r['case_id'],r['source_id'])==(j,arm,'D',q['seeds'][0],cid,c['source_id']),'prediction arm/case identity')
  need(r['normalization']==c['normalization']==src['normalization'] and c['normalization_source']=='defective_bbox' and r['input_sha256']==c['point_file']['sha256']==src['input']['sha256'] and r['partial_array_sha256']==src['partial_array_sha256'] and r['checkpoint_sha256']==q['checkpoint_hashes'][arm] and r['member']==f'predictions/{arm}_D__{cid}.npz' and r['ssm_calls']==36 and r['native_fc_parent_major_verified'] is True,'prediction frame/weight/input binding')
  lookup[arm,cid]=r
 return rows,lookup
def verify_payload(raw):
 names={'coarse','prediction','S','delta','parent_index','token_index'}
 with np.load(io.BytesIO(raw),allow_pickle=False) as z:
  need(len(z.files)==6 and set(z.files)==names,'exact Native fields');v={k:z[k] for k in names}
 for k in ('S','delta','coarse','prediction'):
  a=v[k];need(a.dtype==np.float32 and a.shape==((8192 if k=='prediction' else 256),3) and np.isfinite(a).all(),'finite FP32 '+k)
 ids=np.arange(256,dtype=np.int64)
 need(v['parent_index'].dtype==v['token_index'].dtype==np.int64 and np.array_equal(v['parent_index'],np.repeat(ids,32)) and np.array_equal(v['token_index'],ids) and np.array_equal(v['S']+v['delta'],v['coarse']),'coarse and parent identities')
 return v
def bootstrap():return np.random.Generator(np.random.PCG64(BOOTSTRAP_SEED)).integers(0,21,size=(2000,21),dtype=np.int64)
def comparison(core,rows,sources,indices,first,second):
 aliases={first:'A',second:'B'};selected=[dict(r,arm=aliases[r['arm']]) for r in rows if r['arm'] in aliases]
 fn=core.summarize;fn=FunctionType(fn.__code__,dict(fn.__globals__,ARMS=('B','A')),fn.__name__)
 pairs,summary=fn(selected,sources,indices);summary.update(comparison=first+'_minus_'+second,arm_aliases={'A':first,'B':second})
 return dict(pairs=pairs,summary=summary)
def diagnostic(metric,ref,dist):
 j=ref['a_is_j'].astype(bool);w=ref['a_weights'][j];v=dist[j];need(len(v)>0 and np.isfinite(v).all() and np.all(w>0),'valid J diagnostic support')
 area=float(w.sum());band=(v>1.)&(v<=3.)
 return dict(J_Cover_at_1=float(np.average(v<=1.,weights=w)),J_Cover_at_3=float(np.average(v<=3.,weights=w)),J_area_1_to_3_mm2=float(w[band].sum()),J_fraction_1_to_3=float(w[band].sum()/area),J_area_mm2=area)
def score_one(core,metric,arr,ref,a2,gt,norm):
 captured=[]
 class ObserveMetric:
  def __getattr__(self,k):return getattr(metric,k)
  def nearest(self,query,points):
   v=metric.nearest(query,points)
   if query is ref['a_centers'] and len(points)==8192:captured.append(v)
   return v
 out=core.score_prediction(ObserveMetric(),arr,ref,a2,gt,norm)
 need(len(captured)==1,'one existing dense A1 distance reused for diagnostics')
 out['diagnostics']=diagnostic(metric,ref,captured[0]);return out
def resource_check(start,limits,process,result):
 need(time.monotonic()-start<=limits['wall_seconds'] and process.memory_info().rss<=limits['RSS_bytes'] and sum(p.stat().st_size for p in result.iterdir() if p.is_file())<=limits['output_bytes'],'scoring resource budget')
def score(q,result):
 import psutil,scipy
 from threadpoolctl import threadpool_limits
 need([np.__version__,scipy.__version__]==q['numeric_versions'],'numeric runtime')
 start=time.monotonic();process=psutil.Process();arc=archive_members(q)
 scope=json.loads(exact(q['prediction_scope']));index=json.loads(exact(q['case_index']))
 manifest=[json.loads(x) for x in arc['manifest.jsonl'].splitlines()];cases,lookup=index_cases(q,scope,index,manifest)
 core=module(q['scorer']);metric=module(q['metrics']);indices=bootstrap();scores=[]
 with threadpool_limits(limits=1),(result/'model_scores.jsonl').open('x',encoding='utf-8',newline='\n') as log:
  for c in cases:
   resource_check(start,q['limits'],process,result)
   with np.load(io.BytesIO(exact(c['reference'])),allow_pickle=False) as z:ref={k:z[k] for k in z.files}
   with np.load(io.BytesIO(exact(c['point_file'])),allow_pickle=False) as z:y=z['implant']
   need(y.shape==(8192,3) and y.dtype==np.float32 and np.isfinite(y).all() and digest(y.tobytes())==c['target_array_sha256'],'frozen scoring GT')
   gt=metric.world_points(y,c['normalization']);a2,_,_=metric.a2_reference(ref)
   for arm in ARMS:
    resource_check(start,q['limits'],process,result);r=lookup[arm,c['case_id']];raw=arc.pop(r['member'])
    need(len(raw)==r['bytes'] and digest(raw)==r['sha256'],'prediction manifest bytes')
    row=dict(arm=arm,fold='D',case_id=c['case_id'],source_id=c['source_id'],**score_one(core,metric,verify_payload(raw),ref,a2,gt,c['normalization']))
    scores.append(row);log.write(json.dumps(row,allow_nan=False)+'\n');log.flush()
 need(len(scores)==315 and len(arc)==5,'all model rows scored exactly once')
 save(result/'paired_summary.json',{a+'_minus_'+b:comparison(core,scores,q['source_ids'],indices,a,b) for a,b in (('J','R'),('J','T'),('T','R'))})
 save(result/'diagnostic_summary.json',dict(description='Preregistered descriptive dense J Cover@1/@3 and area (1,3]; no gate execution',source_equal_arm_means={arm:{k:float(np.mean([np.mean([r['diagnostics'][k] for r in scores if r['arm']==arm and r['source_id']==s]) for s in q['source_ids']])) for k in scores[0]['diagnostics']} for arm in ARMS}))
 with (result/'source_bootstrap_indices.npy').open('xb') as f:np.save(f,indices,allow_pickle=False)
 resource_check(start,q['limits'],process,result)
 save(result/'completion.json',dict(status='SCORED_AWAITING_READ_ONLY_FREEZE',counts=COUNTS,request_sha256=q['_request_sha256'],seconds=time.monotonic()-start,formal_gate_executed=False))
def main():
 parser=argparse.ArgumentParser()
 for k in ('request','request-sha256','authorization','authorization-sha256'):parser.add_argument('--'+k,required=True)
 a=parser.parse_args();q=json.loads(exact(dict(path=a.request,bytes=Path(a.request).stat().st_size,sha256=a.request_sha256)));auth=json.loads(exact(dict(path=a.authorization,bytes=Path(a.authorization).stat().st_size,sha256=a.authorization_sha256)))
 authorize(q,a.request_sha256,auth)
 need(Path(__file__).resolve()==Path(q['entry']['path']) and Path(sys.executable).resolve()==Path(q['interpreter']['path']) and sys.flags.isolated and sys.dont_write_bytecode,'bound isolated CPU runtime')
 exact(q['entry']);exact(q['interpreter']);out=Path(q['output']);need(out.is_absolute() and out.resolve()==out and out.parent.is_dir() and not os.path.lexists(out),'fresh output');out.mkdir()
 q['_request_sha256']=a.request_sha256
 try:score(q,out)
 except BaseException as error:
  save(out/'failure.json',dict(status='FAILED_STOP_NO_RETRY',error=repr(error)));raise
if __name__=='__main__':main()
