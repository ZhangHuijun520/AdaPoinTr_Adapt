"""Read-only CIUA audit. No model imports, solves, fits or source mutation."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
for k in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS'):os.environ[k]='2'
from pathlib import Path
import hashlib,io,json,tarfile,time
import numpy as np

O=Path(__file__).resolve().parent
R=O.parents[1];P=R/'outputs/ciua_CPU_analysis_preparation_20261118_v1';D=P/'analysis_results_v1'
SHA='41eceb1fab6866314b467f2cef5217bca1986b8c0639ee94857cce51e2406657'
checks={};seen={};start=time.monotonic();maxdiff={}
def read(p):return json.loads(Path(p).read_bytes())
def digest(b):return hashlib.sha256(b).hexdigest()
def exact(r):
 p=Path(r['path']);assert p.is_file() and not any(x.is_symlink() for x in (p,*p.parents)),str(p)
 b=p.read_bytes();assert len(b)==r['bytes'] and digest(b)==r['sha256'],str(p);seen[str(p)]=r;return b
def record(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=digest(b))
def save(n,v):
 with (O/n).open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def check(k,v=True):assert v,k;checks[k]=True
def close(k,a,b,tol=2e-9):
 a=np.asarray(a);b=np.asarray(b);assert a.shape==b.shape,k
 d=float(np.max(np.abs(a-b))) if a.size else 0.;assert np.isfinite(a).all() and np.isfinite(b).all() and d<=tol,(k,d)
 maxdiff[k]=max(d,maxdiff.get(k,0.))
def geometry(p):
 p=p.astype('f8');c=p-p.mean(0)
 return np.r_[p.mean(0),(c.T@c/len(p))[np.triu_indices(3)],np.quantile(p,[.1,.5,.9],axis=0,method='linear').T.ravel()]
def target(G,D):
 G=G.astype('f8');c=G.mean(0);b=(D.min(0).astype('f8')+D.max(0).astype('f8'))/2
 return np.r_[c,np.log(np.sqrt(((G-c)**2).sum(1).mean())),np.bincount((G>=b).astype('i8')@np.array([1,2,4]),minlength=8)/len(G)]
def errors(pred,y,scales):
 u=np.sort(pred[:,4:],axis=1)[:,::-1];cs=np.cumsum(u,1)-1;rho=(u-cs/np.arange(1,9)>0).sum(1)-1
 prob=np.maximum(pred[:,4:]-cs[np.arange(len(pred)),rho,None]/(rho[:,None]+1),0)
 return np.c_[np.linalg.norm(pred[:,:3]-y[:,:3],axis=1)*scales,np.abs(pred[:,3]-y[:,3]),.5*np.abs(prob-y[:,4:]).sum(1)]
def gate(a,b,mm):
 d=a-b
 return bool(d[:,0].mean()<=-mm+1e-12 and d[:,2].mean()<=-.03+1e-12 and (d[:,0]<-1e-12).sum()>=14 and (d[:,2]<-1e-12).sum()>=14)

def main():
 check('request_SHA256',digest((P/'CIUA_CPU_analysis_execution_request_v1.json').read_bytes())==SHA)
 q=read(P/'CIUA_CPU_analysis_execution_request_v1.json');a=read(q['launch_contract']['authorization']);r=read(q['launch_contract']['runtime']);m=read(P/'execution_materialization_receipt_v1.json')
 check('authorization_and_one_way_runtime',a['request_sha256']==SHA and a['explicit_user_authorization'] is True and r==dict(schema='ciua-runtime-v1',request_sha256=SHA,authorization_sha256=digest(Path(q['launch_contract']['authorization']).read_bytes())) and r['authorization_sha256']==m['authorization_sha256'] and digest(Path(q['launch_contract']['runtime']).read_bytes())==m['runtime_sha256'])
 check('launcher_frozen_bytes',digest(Path(q['launch_contract']['launcher']).read_bytes())==m['launcher_sha256'])
 check('exit0_no_timeout',read(q['launch_contract']['exit_code'])['exit_code']==0 and read(q['launch_contract']['exit_code'])['timed_out'] is False)
 check('single_attempt_claim',(Path(q['attempt_claim']).read_text().strip()==SHA))
 check('empty_stdout_stderr',all(Path(q['launch_contract'][k]).stat().st_size==0 for k in ('stdout','stderr')))
 expected={'analysis_full.json','completion.json','output_manifest.json','resources.jsonl','stages.jsonl','archive_receipt.json','ciua_results_v1.tar.gz','ciua_results_v1.tar.gz.sha256','ciua_results_v1.tar.gz.bytes','ciua_results_v1.tar.gz.contents.sha256'}
 check('exact_output_file_directory_sets',{p.name for p in D.iterdir() if p.is_file()}==expected and {p.name for p in D.iterdir() if p.is_dir()}=={'features'} and not list((D/'features').iterdir()))
 manifest=read(D/'output_manifest.json');check('manifest_request',manifest['request_sha256']==SHA)
 for x in manifest['files']:exact(dict(x,path=str(D/x['path'])))
 check('four_manifested_files',len(manifest['files'])==4)
 ar=read(D/'archive_receipt.json');blob=exact(ar);members={x['name']:x for x in ar['members']};found=set()
 with tarfile.open(fileobj=io.BytesIO(blob),mode='r:gz') as tf:
  for t in tf:
   assert t.isfile() and t.name in members and t.name not in found
   b=tf.extractfile(t).read();x=members[t.name];assert len(b)==t.size==x['bytes'] and digest(b)==x['sha256'] and b==(D/t.name).read_bytes();found.add(t.name)
 check('archive_exact_five_members',found==set(members) and len(found)==5)
 check('three_archive_sidecars',(D/'ciua_results_v1.tar.gz.bytes').read_text().strip()==str(ar['bytes']) and (D/'ciua_results_v1.tar.gz.sha256').read_text().split()==[ar['sha256'],'ciua_results_v1.tar.gz'] and (D/'ciua_results_v1.tar.gz.contents.sha256').read_text().splitlines()==[x['sha256']+'  '+x['name'] for x in ar['members']])
 def recurse(x):
  if isinstance(x,dict):
   if {'path','bytes','sha256'}<=x.keys():exact(x)
   for v in x.values():recurse(v)
  elif isinstance(x,list):
   for v in x:recurse(v)
 recurse(q)
 check('frozen_source_inputs_environment_hashes')
 rows=q['rows'];canon=read(q['all_manifest']['path'])['records'];assert len(rows)==840
 check('canonical840',len({(x['run'],x['case_id']) for x in rows})==840 and all(all(x[k]==y[k] for k in ('run','fold','role','case_id','source_id','normalization')) and x['input']['sha256']==y['input_sha256'] for x,y in zip(rows,canon)))
 fresh=read(q['fresh_feature_index']['path'])['records'];cache=read(q['reuse_manifest']['path'])['records'];fresh={(x['run'],x['case_id']):x for x in fresh};cache={(x['run'],x['case_id']):x for x in cache}
 check('partition800_40',len(fresh)==800 and len(cache)==40 and not fresh.keys()&cache.keys() and fresh.keys()|cache.keys()=={(x['run'],x['case_id']) for x in rows})
 Y=[];Q=[];F={k:[] for k in ('D18','z','zF','zf')}
 with tarfile.open(q['trace_archive']['path'],'r:gz') as tf:
  for row in rows:
   with np.load(io.BytesIO(exact(row['input'])),allow_pickle=False) as z:Dp=z['partial'];Gp=z['implant']
   assert Dp.shape==Gp.shape==(8192,3) and Dp.dtype==Gp.dtype==np.float32
   key=row['run'],row['case_id'];g=geometry(Dp)
   if key in fresh:
    with np.load(io.BytesIO(exact(fresh[key]['feature'])),allow_pickle=False) as z:v={k:z[k].copy() for k in z.files}
    close('D18',g,v['D18'],0)
   else:
    cr=cache[key];b=tf.extractfile(cr['member']).read();assert digest(b)==cr['trace']['sha256']
    with np.load(io.BytesIO(b),allow_pickle=False) as z:
     assert np.array_equal(z['x'][:,1024:1408],z['f']) and np.array_equal(z['x'][:,:1024],np.broadcast_to(z['z'],(256,1024)))
     raw=z['F'].astype('f8');cc=raw-raw.mean(1,keepdims=True);ln=cc/np.sqrt((cc*cc).mean(1,keepdims=True)+1e-5)
     v=dict(z=z['z'].copy(),mF=ln.mean(0).astype('f4'),mf=z['f'].astype('f8').mean(0).astype('f4'),Q=z['Q'].copy(),D18=g)
   Y.append(target(Gp,Dp));Q.append(target(v['Q'],Dp));F['D18'].append(g);F['z'].append(v['z']);F['zF'].append(np.r_[v['z'],v['mF']]);F['zf'].append(np.r_[v['z'],v['mf']])
 Y=np.array(Y);Q=np.array(Q);F={k:np.array(v) for k,v in F.items()};result=read(D/'analysis_full.json');completion=read(D/'completion.json');folds=result['folds'];summary={};fit_count=0;case_count=0
 for fold,fr in folds.items():
  it=[i for i,x in enumerate(rows) if x['fold']==fold and x['role']=='train'];iv=[i for i,x in enumerate(rows) if x['fold']==fold and x['role']=='development'];tr=[rows[i] for i in it];dv=[rows[i] for i in iv]
  sources=sorted({x['source_id'] for x in tr});vs=sorted({x['source_id'] for x in dv});assert len(it)==315 and len(iv)==105 and len(sources)==63 and len(vs)==21 and not set(sources)&set(vs) and fr['rows']==dv and fr['source_order']==vs
  for sr in (tr,dv):
   for sid in {x['source_id'] for x in sr}:assert {x['case_id'].split('__',2)[2] for x in sr if x['source_id']==sid}=={'bilateral','frontoorbital','parietotemporal','random_1','random_2'}
  bp=np.random.Generator(np.random.PCG64(2026111801 if fold=='C' else 2026111802)).integers(0,21,(2000,21));assert np.array_equal(bp,fr['bootstrap_indices'])
  perm=np.random.Generator(np.random.PCG64(2026111803 if fold=='C' else 2026111804)).permutation(63);mapping=dict(zip(sources,[sources[j] for j in perm]));assert mapping==fr['permutation']['mapping'] and fr['permutation']['fixed_points']==sum(k==v for k,v in mapping.items())
  lookup={(x['source_id'],x['case_id'].split('__',2)[2]):i for i,x in enumerate(tr)};pi=[lookup[mapping[x['source_id']],x['case_id'].split('__',2)[2]] for x in tr]
  w=np.array([1/(63*sum(x['source_id']==r['source_id'] for x in tr)) for r in tr]);yt=Y[it];yv=Y[iv];sc=np.array([x['normalization']['scale'] for x in dv]);ts=np.array([x['normalization']['scale'] for x in tr]);se={}
  for name,pred in fr['predictions'].items():
   pred=np.array(pred);assert pred.shape==(105,12)
   if name=='constant':close('constant',pred,np.broadcast_to(w@yt,pred.shape))
   elif name=='Q':close('native_Q',pred,Q[iv],0)
   else:
    fit_count+=1;key=name.replace('_permuted','');fit=fr['fits'][name];x=F[key][it];y=yt[pi] if name.endswith('_permuted') else yt
    xm=w@x;ym=w@y;xs=np.sqrt(w@((x-xm)**2));ys=np.sqrt(w@((y-ym)**2));cx=xs==0;cy=ys==0;xs=np.where(cx,1.,xs);ys=np.where(cy,1.,ys)
    for k,v in [('x_mean',xm),('y_mean',ym),('x_scale',xs),('y_scale',ys)]:close('train_only_'+k,fit[k],v)
    assert np.array_equal(cx,fit['constant_x']) and np.array_equal(cy,fit['constant_y']) and fit['train_sources']==sources and fit['dimension']==x.shape[1] and fit['lambda_mean_objective']==1.
    X=(x-xm)/xs;Z=(y-ym)/ys;X[:,cx]=0;Z[:,cy]=0;W=np.array(fit['coefficient']);res=float(np.abs((X*w[:,None]).T@(X@W-Z)+W).max());assert res<=1e-8;close('stationarity',res,fit['stationarity'],1e-10)
    def predict(vals):
     xx=(vals-xm)/xs;xx[:,cx]=0;pred=xx@W*ys+ym;pred[:,cy]=ym[cy];return pred
    close('saved_coefficient_predictions',pred,predict(F[key][iv]));close('train_errors',fr['train_errors'][name],errors(predict(x),yt,ts))
    sv=np.array(fit['singular_values']);assert len(sv)==min(x.shape) and (sv>=0).all() and fit['rank']<=min(x.shape);close('effective_df',fit['effective_df'],np.sum(sv*sv/(sv*sv+1)))
   err=errors(pred,yv,sc);close('case_errors',err,fr['case_errors'][name]);case_count+=len(err)
   se[name]=np.stack([err[[i for i,x in enumerate(dv) if x['source_id']==sid]].mean(0) for sid in vs]);close('source_errors',se[name],fr['source_errors'][name])
   for typ in fr['type_means']:close('type_means',fr['type_means'][typ][name],err[[i for i,x in enumerate(dv) if x['case_id'].endswith('__'+typ)]].mean(0))
  for key,c in fr['comparisons'].items():
   ka,kb=key.split('_minus_');d=se[ka]-se[kb]
   vals=dict(mean=d.mean(0),median=np.median(d,axis=0),improved=(d < -1e-12).sum(0),worse=(d>1e-12).sum(0),tied=(np.abs(d)<=1e-12).sum(0),CI95=np.quantile(d[bp].mean(1),[.025,.975],axis=0,method='linear'),source_differences=d)
   for k,v in vals.items():close('comparisons_'+k,c[k],v)
  op=yt[:,4:];entropy=-(np.where(op>0,op,1)*np.log(np.where(op>0,op,1))).sum(1);assert fr['octant_informative']==bool(np.max(np.abs(op-op[0]))>1e-12)
  for k,v in dict(variance=op.var(0),entropy_mean=entropy.mean(),nonzero_bins=(op>0).sum(1),dominant_fraction=op.max(1)).items():close('octant_'+k,fr['octant_train_stats'][k],v)
  summary[fold]=dict(source_means={k:v.mean(0).tolist() for k,v in se.items()},comparisons=fr['comparisons'],fits={k:{kk:v[kk] for kk in ['dimension','rank','effective_df','stationarity']} for k,v in fr['fits'].items()},permutation=fr['permutation'],octant_informative=fr['octant_informative'],gate_details={k:dict(versus_D18=gate(se[k],se['D18'],2.),versus_Q=gate(se[k],se['Q'],1.),versus_z=gate(se[k],se['z'],1.),log_radius_delta_Q=float((se[k]-se['Q'])[:,1].mean())) for k in ['z','zF','zf']})
  fr['_audited_se']=se
 decisions={}
 for k in ('z','zF','zf'):
  I=all(fr['octant_informative'] and gate(fr['_audited_se'][k],fr['_audited_se']['D18'],2.) for fr in folds.values());trade=any((fr['_audited_se'][k]-fr['_audited_se']['Q'])[:,1].mean()>.01+1e-12 for fr in folds.values());U=I and all(gate(fr['_audited_se'][k],fr['_audited_se']['Q'],1.) for fr in folds.values())
  extra=k!='z' and all(gate(fr['_audited_se'][k],fr['_audited_se']['z'],1.) and (fr['_audited_se'][k]-fr['_audited_se']['z'])[:,1].mean()<=.01+1e-12 for fr in folds.values())
  decisions[k]=dict(I_PASS=bool(I),U_PASS=bool(U and not trade),TRADEOFF=bool(trade),aggregation_increment=bool(extra),training_authorized=False)
 check('independent_targets_predictions_errors_aggregation_bootstrap_decisions',decisions==result['decisions']==completion['decisions'])
 check('exact16_saved_fits2100_case_method_rows',fit_count==16 and case_count==2100 and result['solves']==completion['solves']==16 and result['case_model_rows']==210 and result['feature_methods']==10 and completion['records']==840 and completion['new_forward']==0 and completion['status']=='CIUA_CPU_ANALYSIS_COMPLETE_PENDING_FREEZE')
 resources=[json.loads(x) for x in (D/'resources.jsonl').read_text().splitlines()];check('842_resource_record_sequence',len(resources)==842 and [(x['phase'],x['count']) for x in resources]==[('before_record',i) for i in range(840)]+[('complete_analysis',840),('before_manifest',840)])
 for x in resources:
  v=x['values'];cc=dict(RSS=v['RSS_bytes']<=q['limits']['RSS_bytes'],output=v['output_bytes']<=q['limits']['output_bytes'],wall=v['wall_seconds']<=q['limits']['wall_seconds']);assert cc==x['checks'] and all(cc.values())
 check('resource_values_and_final_output_budget',sum(p.stat().st_size for p in D.rglob('*') if p.is_file())<=q['limits']['output_bytes'])
 check('no_torch_or_model_import','torch' not in __import__('sys').modules)
 # Recheck audited output bytes after all numeric reads. atime is intentionally excluded.
 inventory=[record(p) for p in sorted(D.rglob('*')) if p.is_file()]
 for x in manifest['files']:exact(dict(x,path=str(D/x['path'])))
 save('independent_numeric_summary_v1.json',dict(folds=summary,decisions=decisions,maximum_recompute_differences=maxdiff))
 save('formal_freeze_receipt_v1.json',dict(status='CIUA_CPU_ANALYSIS_FORMAL_READ_ONLY_FREEZE_PASS',checks=checks,request_sha256=SHA,inventory=inventory,records=840,fits_verified=16,new_fits=0,case_method_rows=2100,new_forward=0,resource_records=len(resources),resource_peaks={k:max(x['values'][k] for x in resources) for k in ['RSS_bytes','output_bytes','wall_seconds']},input_files_rehashed=len(seen),archive_sha256=ar['sha256'],seconds=time.monotonic()-start,limitations=['resource records are sampled, not a continuous peak measurement','saved singular values/rank not recomputed by new SVD; stationary equation independently checked','I/U are low-dimensional diagnostic gates, not model-performance or causal gates']))
 print(json.dumps(dict(status='CIUA_CPU_ANALYSIS_FORMAL_READ_ONLY_FREEZE_PASS',checks=len(checks),fits_verified=fit_count,new_fits=0,case_rows=case_count,seconds=time.monotonic()-start)))

if __name__=='__main__':
 try:main()
 except BaseException as e:
  save('audit_failure_v1.json',dict(status='AUDIT_FAILED_STOP',error=repr(e),passed_checks=checks));raise
