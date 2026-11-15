from pathlib import Path
import ast,hashlib,json
R=Path(__file__).resolve().parent.parent;S=R/'outputs/scq_rf_score_impl_20261115_v1';S.mkdir()
parent=R/'outputs/scq_score_impl_20261114_v1/bcsp_scq_BS_two_arm_score_v1.py';src=parent.read_text(encoding='utf-8');tree=ast.parse(src)
prep=R/'outputs/scq_rf_score_prep_20261115_v1';scope=json.loads((prep/'RF_three_arm_unified_CPU_scoring_scope_v1.json').read_bytes());repl={}
for n in tree.body:
 if isinstance(n,ast.FunctionDef) and n.name in ['authorize','validate_index','validate_archive','load_prediction_arrays','run_scoring','main']:repl[n.name]=ast.get_source_segment(src,n)
v=repl['authorize'].replace('bcsp-scq-BS-local-scoring-request-v1','bcsp-scq-rf-local-scoring-request-v1').replace('bcsp-scq-BS-score-authorization-v1','bcsp-scq-rf-score-authorization-v1')
v=v.replace('model_rows=420,shared_control_rows=420,case_score_rows=840,source_score_rows=168','model_rows=630,shared_control_rows=420,case_score_rows=1050,source_score_rows=210')
v=v.replace(" return plan", " require(plan['comparison_qualification']==QUALIFICATION,'D device confound qualification')\n return plan")
repl['authorize']=v
v=repl['validate_index'].replace('bcsp-scq-fourmodel-native-index-v1','bcsp-scq-rf-sixmodel-native-index-v1').replace("['B_C','S_C','B_D','S_D']", "RUNS").replace('bcsp-scq-BS-twofold-score-index-candidate-v1','bcsp-scq-rf-three-arm-twofold-score-index-candidate-v1')
v=v.replace('==420','==630').replace("f=run['fold'];arm=run['variant'];", "f=run['fold'];arm=ARM_BY_VARIANT[run['variant']];").replace("run['label']==arm+'_'+f", "run['label']==PREFIX_BY_ARM[arm]+'_'+f")
v=v.replace("lookup[c['fold'],arm,c['case_id']]", "lookup[c['fold'],VARIANT_BY_ARM[arm],c['case_id']]")
repl['validate_index']=v
v=repl['validate_archive'].replace("kind=='SCQ'", "kind=='SCQ_RF'").replace('bcsp-scq-fourmodel-native-index-v1','bcsp-scq-rf-sixmodel-native-index-v1').replace("labels=['B_C','S_C','B_D','S_D']", "labels=RUNS").replace('==420','==630').replace('==426','==636').replace('len(done[\'models\'])==4','len(done[\'models\'])==6')
v=v.replace("sum(m.size for m in members)<=67108864", "sum(m.size for m in members)<=ARCHIVE_MEMBER_BYTE_LIMIT")
v=v.replace('SCQ_BS_CD_420_NATIVE_FORWARD_COMPLETE','SCQ_RF_SIXMODEL_630_NATIVE_FORWARD_COMPLETE')
v=v.replace("ev=m['construction'];v=ev['parent'];s=ev['scq'];arm=runs[m['run']]['variant']", "ev=m['construction'];arm=runs[m['run']]['variant'];is_rf='rf' in ev;require(is_rf is (arm!='S'),'RF module presence');scq=ev['parent'] if is_rf else ev;v=scq['parent'];s=scq['scq']")
v=v.replace("s['variant']==arm and arm in ARMS", "s['variant']=='S' and arm in ARM_BY_VARIANT").replace("s['new_parameters']==(0 if arm=='B' else 693507) and s['total_parameters']==(39903169 if arm=='B' else 40596676)", "s['new_parameters']==693507 and s['total_parameters']==40596676")
v=v.replace(" require(len(records)", "  require(s['initialization_sha256']==SCQ_INITIALIZER_SHA,'SCQ initializer identity')\n  if is_rf:\n   r=ev['rf'];require(r['variant']==arm and r['total_parameters']==40827847 and r['additional_parameters']==231171 and r['common_state_preserved'] and r['CPU_RNG_preserved'] and r['initialization_sha256']==RF_INITIALIZER_SHA,'RF construction identity')\n require(len(records)")
v=v.replace("i['variant'] in ARMS and i['run']==i['variant']+'_'+i['fold']", "i['variant'] in ARM_BY_VARIANT and i['run']==PREFIX_BY_ARM[ARM_BY_VARIANT[i['variant']]]+'_'+i['fold']")
v=v.replace("key=(r['fold'],r['variant'],r['case_id'])", "key=(r['fold'],ARM_BY_VARIANT[r['variant']],r['case_id'])").replace("archive_key='SCQ'", "archive_key='SCQ_RF'")
repl['validate_archive']=v
v=repl['load_prediction_arrays'].replace("keys=['prediction','coarse','Qraw','delta']", "keys=['prediction','coarse','Qraw','delta','Q0','Q1','Q2','delta0','delta1']").replace('exact four frozen prediction keys','exact nine frozen prediction keys').replace('rtol=2e-6,atol=2e-7','rtol=2e-5,atol=2e-6')
v=v.replace(" if record['variant']=='B':require(np.array_equal(arrays['Qraw'],arrays['coarse']) and np.count_nonzero(arrays['delta'])==0,'B zero residual')", " require(np.array_equal(arrays['Qraw'],arrays['Q0']) and np.array_equal(arrays['Q2'],arrays['coarse']) and np.allclose(arrays['Q0']+arrays['delta0'],arrays['Q1'],rtol=2e-5,atol=2e-6) and np.allclose(arrays['Q1']+arrays['delta1'],arrays['Q2'],rtol=2e-5,atol=2e-6),'native stage equations')\n if record['variant']=='S':require(np.array_equal(arrays['Q1'],arrays['Q2']) and np.array_equal(arrays['delta0'],arrays['delta']) and np.count_nonzero(arrays['delta1'])==0,'Sref no second stage')")
repl['load_prediction_arrays']=v
v=repl['run_scoring'].replace("'SCQ'", "'SCQ_RF'")
v=v.replace("pro['inference']['forward_attempt_budget']==420", "pro['inference']['forward_attempt_budget']==630").replace('len(lookup)==420','len(lookup)==630').replace('len(frozen)==len(prediction_bindings)==420','len(frozen)==len(prediction_bindings)==630')
v=v.replace('len(rows)==840','len(rows)==1050').replace('len(sources)==168','len(sources)==210').replace('len(selected)==420 and len(ss)==84','len(selected)==525 and len(ss)==105')
v=v.replace('SCQ_BS_TWOFOLD_SINGLE_SEED_DESCRIPTIVE_COMPARISONS','SCQ_RF_TWOFOLD_SINGLE_SEED_DESCRIPTIVE_COMPARISONS').replace("fixed_comparisons=['S_minus_B']", "fixed_comparisons=[b+'_minus_'+a for a,b in PAIRS],comparison_qualification=QUALIFICATION")
v=v.replace('model_predictions=420','model_predictions=630').replace('score_rows=840','score_rows=1050').replace('source_rows=168','source_rows=210').replace('LOCAL_SCQ_BS_TWO_ARM_TWOFOLD_CPU_SCORING_COMPLETE','LOCAL_SCQ_RF_THREE_ARM_TWOFOLD_CPU_SCORING_COMPLETE')
v=v.replace('bootstrap=0,formal_gate=False','bootstrap=0,formal_gate=False,comparison_qualification=QUALIFICATION')
repl['run_scoring']=v
repl['main']=repl['main'].replace('LOCAL_SCQ_BS_SCORING_P3_PASS','LOCAL_SCQ_RF_SCORING_P3_PASS').replace("{'SCQ'}", "{'SCQ_RF'}")
lines=src.splitlines(True)
for n in sorted(tree.body,key=lambda n:n.lineno,reverse=True):
 if isinstance(n,ast.FunctionDef) and n.name in repl:lines[n.lineno-1:n.end_lineno]=[repl[n.name]+'\n']
src=''.join(lines).replace("ARMS=['B','S']", "ARMS=['S-ref','RF-Static','RF-Requery']").replace("PAIRS=[('B','S')]", "PAIRS=[('RF-Static','RF-Requery'),('S-ref','RF-Static'),('S-ref','RF-Requery')]")
constants=dict(RUNS=['Sref_C','Static_C','Requery_C','Sref_D','Static_D','Requery_D'],ARM_BY_VARIANT={'S':'S-ref','RF-Static':'RF-Static','RF-Requery':'RF-Requery'},VARIANT_BY_ARM={'S-ref':'S','RF-Static':'RF-Static','RF-Requery':'RF-Requery'},PREFIX_BY_ARM={'S-ref':'Sref','RF-Static':'Static','RF-Requery':'Requery'},ARCHIVE_MEMBER_BYTE_LIMIT=scope['archive_binding']['uncompressed_member_bytes'],QUALIFICATION=scope['comparison_qualification'],SCQ_INITIALIZER_SHA='e7858ee3ae4c0bf6d68e447727c36514f5bbab42b95e1935f1686620ec089416',RF_INITIALIZER_SHA='a4024fbdb49feb41c609ae1171f04c2cb14ab794fc3663855d81395c6a1ea79e')
i=src.index('def require(');src=src[:i]+''.join(k+'='+repr(v)+'\n' for k,v in constants.items())+'\n'+src[i:]
ast.parse(src);compile(src,'RF_three_arm','exec')
ep=S/'bcsp_scq_rf_three_arm_score_v1.py';ep.open('x',encoding='utf-8',newline='\n').write(src)
def funcs(s):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(s).body if isinstance(n,ast.FunctionDef)}
a,b=funcs(parent.read_text(encoding='utf-8')),funcs(src);changed=[n for n in b if a[n]!=b[n]];assert set(changed)==set(repl)
with (S/'static_entry_review_v1.json').open('x',encoding='utf-8') as f:json.dump(dict(status='STATIC_ENTRY_S0_S1_PASS',entry_sha256=hashlib.sha256(ep.read_bytes()).hexdigest(),parent=dict(path=str(parent),sha256=hashlib.sha256(parent.read_bytes()).hexdigest()),changed_functions=changed,all_other_functions_AST_identical=True,metric_SHA_unchanged=True,archive_member_limit=constants['ARCHIVE_MEMBER_BYTE_LIMIT']),f,indent=2)
print(json.dumps(dict(status='RF_SCORE_ENTRY_STATIC_PASS',changed_functions=changed)))
