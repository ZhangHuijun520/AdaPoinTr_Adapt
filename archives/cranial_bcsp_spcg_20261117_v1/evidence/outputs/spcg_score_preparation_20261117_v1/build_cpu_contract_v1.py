"""Static creation of SPCG-specific artificial contract batch; no test execution."""
from pathlib import Path
import ast
R=Path(__file__).resolve().parents[2];O=R/'outputs/spcg_score_implementation_20261117_v1'
s=(R/'outputs/scq_rf_score_impl_20261115_v1/test_RF_three_arm_score_cpu_v1.py').read_text(encoding='utf-8')
a=s.index("  prep=R/");b=s.index("  check('01",a)
s=s[:a]+'''  prep=R/'outputs/spcg_score_preparation_20261117_v1';real=json.loads((S/'SPCG_score_case_index_v1.json').read_bytes());idx=json.loads(Path(real['archive_inputs']['SPCG']['prediction_index']['path']).read_bytes());oldq=json.loads((R/'outputs/scq_rf_score_impl_20261115_v1/local_scoring_execution_request_v1.json').read_bytes());refs=json.loads(Path(oldq['reference_manifest']['path']).read_bytes())
'''+s[b:]
s=s.replace("bad['inputs'][0]['save_Qraw']=False","bad['inputs'][0]['save_Qraw']=True")
s=s.replace("comparison_qualification=copy.deepcopy(s.QUALIFICATION),limits=","statistics=copy.deepcopy(s.BOOTSTRAP),comparison_qualification=copy.deepcopy(s.QUALIFICATION),limits=")
s=s.replace("obj['comparison_qualification']['strict_same_device_D_pair']=True","obj['comparison_qualification']['D_G0_cross_device_reference']=False")
a=s.index('  saved=json.loads');b=s.index("  for m in modelmeta:m.update(state_before",a)
s=s[:a]+'''  # Read only frozen inference metadata, never real prediction arrays.
  with tarfile.open(real['archive_inputs']['SPCG']['archive']['path']) as realtar:saved=json.loads(realtar.extractfile('inference_complete.json').read())
  modelmeta=copy.deepcopy(saved['models'])
'''+s[b:]
a=s.index("  for arm,offset in");b=s.index('  items=[];',a)
s=s[:a]+'''  for arm,offset in [('G0',.2),('G1',.1),('G2',.05)]:
   pred=gt+offset;co=pred[:256].copy();b=io.BytesIO();np.savez_compressed(b,prediction=pred,coarse=co);blobs[arm]=b.getvalue()
   off=pred.astype(float).reshape(256,32,3)-co.astype(float)[:,None,:];geoms[arm]=dict(frame='native_D_only_normalized_no_GT',coarse=stats(co),dense=stats(pred),mean_dense_minus_coarse=off.mean((0,1)).tolist(),offset_mean_squared_radius=float((off**2).sum(2).mean()))
'''+s[b:]
s=s.replace(",('cache_manifest.jsonl',[])",'')
s=s.replace("dict(inference=dict(forward_attempt_budget=630))","dict(counts=dict(forward_attempts=630))")
s=s.replace("set(ar)=={'prediction','coarse','Qraw','delta','Q0','Q1','Q2','delta0','delta1'}","set(ar)=={'prediction','coarse'}")
s=s.replace("lambda ms:setattr(next(m for m in ms if m.name=='cache_manifest.jsonl'),'size',1)","lambda ms:setattr(next(m for m in ms if m.name=='resources.jsonl'),'size',0)")
s=s.replace("changed['models'][1]['construction']['rf']['variant']='RF-Requery'","changed['models'][1]['construction']['change']['arm']='G2'")
a=s.index("   bad1=copy.deepcopy(basearrays)");b=s.index("   reject('oversized",a)
s=s[:a]+'''   bad1=copy.deepcopy(basearrays);bad1.pop('coarse')
   bad2=copy.deepcopy(basearrays);bad2['GT']=gt
   bad3=copy.deepcopy(basearrays);bad3['coarse'][0,0]=np.nan
   bad4=copy.deepcopy(basearrays);bad4['coarse']=bad4['coarse'].astype(np.float64)
   for name,arrays in [('22 missing coarse',bad1),('23 extra GT key',bad2),('24 nonfinite coarse',bad3),('FP64 coarse rejected',bad4)]:
    blob=io.BytesIO();np.savez_compressed(blob,**arrays);value=blob.getvalue();r=copy.deepcopy(lookup['C','G0',cases[0]['case_id']]);r['prediction'].update(bytes=len(value),sha256=hashlib.sha256(value).hexdigest())
    reject(name,lambda:s.load_prediction_arrays(View(tar,member=r['prediction']['name'],blob=value),r))
'''+s[b:]
s=s.replace("complete['bootstrap']==complete['forward_calls']==0","complete['bootstrap']['replicates_per_fold']==2000 and complete['bootstrap']['folds']==2 and complete['forward_calls']==0")
s=s.replace("'paired_summary',",'')
# Standardize all symbols; only fixture-specific schemas differ from original RF.
s=s.replace('bcsp_scq_rf_three_arm_score_v1.py','bcsp_spcg_three_arm_score_v1.py').replace('bcsp-scq-rf','bcsp-spcg').replace('SCQ_RF','SPCG').replace('RF_THREE_ARM','SPCG_THREE_ARM')
s=s.replace('RF-Requery','G2').replace('RF-Static','G1').replace('S-ref','G0')
s=s.replace("blobs['S']","blobs['G0']").replace("schema='bcsp-spcg-three-arm-twofold-score-index-candidate-v1'","schema='bcsp-spcg-three-arm-twofold-score-index-v1'")
a=s.index("  emit('result_v1.json'")
extra='''  ids=['source:%03d'%i for i in range(21)];ic=s.make_bootstrap_indices(ids,'C');idd=s.make_bootstrap_indices(ids,'D')
  check('43 exact C PCG64 matrix',np.array_equal(ic,np.random.Generator(np.random.PCG64(2026111601)).integers(0,21,size=(2000,21),dtype=np.int64)))
  check('44 exact D PCG64 matrix',np.array_equal(idd,np.random.Generator(np.random.PCG64(2026111602)).integers(0,21,size=(2000,21),dtype=np.int64)) and not np.array_equal(ic,idd))
  reject('45 unsorted source IDs rejected',lambda:s.make_bootstrap_indices(ids[::-1],'C'))
  reject('46 duplicate source IDs rejected',lambda:s.make_bootstrap_indices([ids[0]]*21,'C'))
  delta=list(range(-10,11));expect=np.quantile(np.asarray(delta)[ic].mean(1),[.025,.975],method='linear')
  check('47 linear percentile oracle',np.array_equal(s.bootstrap_ci(delta,ic)['CI95'],expect))
  check('48 constant delta exact interval',s.bootstrap_ci([3.]*21,ic)['CI95']==[3.,3.])
  check('49 undefined sources retained',s.bootstrap_ci([None]+[0.]*20,ic)['status']=='UNDEFINED_NONFINITE_PAIRS_RETAINED')
  reject('50 wrong matrix shape rejected',lambda:s.bootstrap_ci(delta,ic[:100]))
  reject('51 out of range draw rejected',lambda:s.bootstrap_ci(delta,np.full((2000,21),21,dtype=np.int64)))
  for fold in ['C','D']:
   ix=np.load(out/('bootstrap_indices_'+fold+'.npy'),allow_pickle=False);br=json.loads((out/('bootstrap_index_record_'+fold+'.json')).read_bytes())
   check('52 '+fold+' saved matrix and source order SHA',br['sha256']==s.digest(out/('bootstrap_indices_'+fold+'.npy')) and br['sources']==sorted(br['sources']) and np.array_equal(ix,s.make_bootstrap_indices(br['sources'],fold)))
   for pair in s.PAIRS:
    name=pair[1]+'_minus_'+pair[0]
    for value in comp['comparison'][fold][name]['metrics'].values():
     oracle=s.bootstrap_ci([v['delta'] for v in value['source_deltas']],ix)
     assert value['bootstrap']==oracle
  check('53 all metrics and comparisons reuse same fold draws')
  check('54 CPU only no model import',s.os.environ['CUDA_VISIBLE_DEVICES']=='' and 'torch' not in sys.modules)
'''
s=s[:a]+extra+s[a:]
ast.parse(s)
(O/'test_SPCG_three_arm_score_cpu_v1.py').write_text(s,encoding='utf-8',newline='\n')
print('CPU test source created; batch not executed')
