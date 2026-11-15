from pathlib import Path
import ast,hashlib,json
R=Path(__file__).resolve().parent.parent;S=R/'outputs/scq_rf_score_impl_20261115_v1'
s=(R/'outputs/scq_score_impl_20261114_v1/test_scq_BS_score_cpu_v1.py').read_text(encoding='utf-8')
s=s.replace('bcsp_scq_BS_two_arm_score_v1.py','bcsp_scq_rf_three_arm_score_v1.py').replace('outputs/scq_score_prep_20261114_v1','outputs/scq_rf_score_prep_20261115_v1').replace('SCQ_BS_score_case_index_candidate_v1.json','RF_three_arm_score_case_index_candidate_v1.json').replace('outputs/scq_pred_freeze_20261114_v2','outputs/scq_rf_pred_freeze_20261115_v2').replace('SCQ_BS_CD_input_index_v2.json','RF_sixmodel_input_index_v2.json')
s=s.replace('bcsp-scq-BS-local-scoring-request-v1','bcsp-scq-rf-local-scoring-request-v1').replace('bcsp-scq-BS-score-authorization-v1','bcsp-scq-rf-score-authorization-v1').replace('bcsp-scq-BS-twofold-score-index-candidate-v1','bcsp-scq-rf-three-arm-twofold-score-index-candidate-v1')
s=s.replace('model_rows=420,shared_control_rows=420,case_score_rows=840 if counts else 839,source_score_rows=168','model_rows=630,shared_control_rows=420,case_score_rows=1050 if counts else 1049,source_score_rows=210')
s=s.replace("arms=['B','S'],pairs=[['B','S']] if pair else [['S','B']]", "arms=s.ARMS,pairs=[list(p) for p in s.PAIRS] if pair else [['RF-Requery','RF-Static']]")
s=s.replace("limits=dict(wall_seconds=18000", "comparison_qualification=copy.deepcopy(s.QUALIFICATION),limits=dict(wall_seconds=18000")
s=s.replace("for arm,offset in [('B',.2),('S',.05)]:", "for arm,offset in [('S',.2),('RF-Static',.1),('RF-Requery',.05)]:")
s=s.replace("delta=np.full_like(co,.01) if arm=='S' else np.zeros_like(co);raw=co-delta;b=io.BytesIO();np.savez_compressed(b,prediction=pred,coarse=co,Qraw=raw,delta=delta)", "d0=np.full_like(co,.01);d1=np.full_like(co,.02) if arm!='S' else np.zeros_like(co);delta=d0+d1;raw=co-delta;q1=raw+d0;b=io.BytesIO();np.savez_compressed(b,prediction=pred,coarse=co,Qraw=raw,delta=delta,Q0=raw,Q1=q1 if arm!='S' else co,Q2=co,delta0=d0,delta1=d1)")
s=s.replace("bindings.append(dict(arm=arm", "bindings.append(dict(arm=s.ARM_BY_VARIANT[arm]")
s=s.replace("'SCQ'", "'SCQ_RF'")
s=s.replace('SCQ_BS_CD_420_NATIVE_FORWARD_COMPLETE','SCQ_RF_SIXMODEL_630_NATIVE_FORWARD_COMPLETE').replace('forwards=420','forwards=630').replace('forward_attempt_budget=420','forward_attempt_budget=630')
s=s.replace('len(lookup)==420','len(lookup)==630')
s=s.replace("for arm in ['B','S']:", "for arm in s.ARMS:").replace("{'prediction','coarse','Qraw','delta'}", "{'prediction','coarse','Qraw','delta','Q0','Q1','Q2','delta0','delta1'}")
s=s.replace("len(templates['C'])==len(templates['D'])==4", "len(templates['C'])==len(templates['D'])==5")
s=s.replace("templates['C'][0]['metrics']['CD_L1_mm']>templates['C'][1]['metrics']['CD_L1_mm']>0", "templates['C'][0]['metrics']['CD_L1_mm']>templates['C'][1]['metrics']['CD_L1_mm']>templates['C'][2]['metrics']['CD_L1_mm']>0")
s=s.replace("changed['models'][1]['construction']['scq']['variant']='B'", "changed['models'][1]['construction']['rf']['variant']='RF-Requery'")
s=s.replace("lookup['C','B',cases[0]['case_id']]", "lookup['C','S-ref',cases[0]['case_id']]")
start=s.index("   for name,arrays in [('22 missing delta'")
end=s.index('  baseline=[]',start)
s=s[:start]+'''   with np.load(io.BytesIO(blobs['S']),allow_pickle=False) as fixture:basearrays={k:fixture[k].copy() for k in fixture.files}
   bad1=copy.deepcopy(basearrays);bad1.pop('delta')
   bad2=copy.deepcopy(basearrays);bad2['GT']=gt
   bad3=copy.deepcopy(basearrays);bad3['Q1']+=.5
   bad4=copy.deepcopy(basearrays);bad4['Q1']=bad4['Q2']-.02;bad4['delta0']=bad4['Q1']-bad4['Q0'];bad4['delta1']=np.full_like(bad4['Q1'],.02)
   for name,arrays in [('22 missing delta',bad1),('23 extra GT key',bad2),('24 inconsistent Q1',bad3),('Sref false second stage',bad4)]:
    blob=io.BytesIO();np.savez_compressed(blob,**arrays);value=blob.getvalue();r=copy.deepcopy(lookup['C','S-ref',cases[0]['case_id']]);r['prediction'].update(bytes=len(value),sha256=hashlib.sha256(value).hexdigest())
    reject(name,lambda:s.load_prediction_arrays(View(tar,member=r['prediction']['name'],blob=value),r))
   reject('oversized verified member budget rejected',lambda:s.validate_archive(View(tar,lambda ms:setattr(ms[0],'size',s.ARCHIVE_MEMBER_BYTE_LIMIT+1)),index,'d'*64,None,'SCQ_RF'))
'''+s[end:]
s=s.replace("O/'full840'", "O/'full1050'").replace('len(rows)==840','len(rows)==1050').replace('len(s.aggregate_source(rows))==168','len(s.aggregate_source(rows))==210')
s=s.replace("['S_minus_B']", "['RF-Requery_minus_RF-Static']")
s=s.replace("complete['model_predictions']==complete['controls']==complete['frozen_baseline_rows_verified']==420", "complete['model_predictions']==630 and complete['controls']==complete['frozen_baseline_rows_verified']==420")
s=s.replace("complete['score_rows']==840 and complete['source_rows']==168", "complete['score_rows']==1050 and complete['source_rows']==210 and complete['comparison_qualification']==s.QUALIFICATION")
s=s.replace("row['arm']=='S'", "row['arm']=='RF-Requery'").replace("row['arm']=='B'", "row['arm']=='RF-Static'").replace("('B','S')", "('RF-Static','RF-Requery')")
s=s.replace('SCQ_BS_SCORING_CPU_CONTRACT_PASS','RF_THREE_ARM_SCORING_CPU_CONTRACT_PASS').replace('synthetic_actual_metric_rows=8','synthetic_actual_metric_rows=10').replace('synthetic_orchestrated_rows=840','synthetic_orchestrated_rows=1050')
s=s.replace("'8 metric rows use", "'10 metric rows use").replace("'840 orchestration rows", "'1050 orchestration rows").replace('not840 true metric','not1050 true metric')
needle="s.authorize(*chain());check('07 complete actual authorize840 contract')"
s=s.replace(needle,needle+"\n  qr,ar=chain();obj=json.loads(Path(qr['path']).read_bytes());obj['comparison_qualification']['strict_same_device_D_pair']=True;badq=emit('wrong_qualification_request.json',obj);bada=emit('wrong_qualification_authorization.json',dict(schema='bcsp-scq-rf-score-authorization-v1',request_sha256=badq['sha256'],explicit_user_authorization=True,user_authorization_text='ARTIFICIAL_ONLY'));reject('D confounding cannot be hidden',lambda:s.authorize(badq,bada))")
needle="comp=json.loads((out/'paired_comparison.json').read_bytes());"
s=s.replace(needle,needle+"check('three fixed comparisons and D qualification retained',comp['fixed_comparisons']==[b+'_minus_'+a for a,b in s.PAIRS] and comp['comparison_qualification']==s.QUALIFICATION and all(set(comp['comparison'][f])==set(comp['fixed_comparisons']) for f in ['C','D']));")
# Human check names reflect new shape; no metric computations changed.
for a,b in [('actual frozen metadata210 cases420 members','actual frozen metadata210 cases630 members'),('authorize840','authorize1050'),('synthetic210 cases420','synthetic210 cases630'),('actual426 member','actual636 member'),('actual four-key','actual nine-key'),('metric8 artificial','metric10 artificial'),('S closer than B','Requery closer than Static and Sref'),('actual840 orchestration','actual1050 orchestration'),('168 source groups','210 source groups'),('S minus B source-equal','Requery minus Static source-equal'),('exactly420 models420 controls840 rows168 sources','exactly630 models420 controls1050 rows210 sources')]:s=s.replace(a,b)
ast.parse(s);compile(s,'RF_score_tests','exec');p=S/'test_RF_three_arm_score_cpu_v1.py';p.open('x',encoding='utf-8',newline='\n').write(s)
entry=S/'bcsp_scq_rf_three_arm_score_v1.py'
with (S/'static_review_v1.json').open('x',encoding='utf-8') as f:json.dump(dict(status='STATIC_S0_S1_PASS',files=[dict(name=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in [entry,p]],checks=dict(syntax=True,frozen_metrics_untouched=True,CPU_only=True,real_scoring_not_invoked=True)),f,indent=2)
print(p)
