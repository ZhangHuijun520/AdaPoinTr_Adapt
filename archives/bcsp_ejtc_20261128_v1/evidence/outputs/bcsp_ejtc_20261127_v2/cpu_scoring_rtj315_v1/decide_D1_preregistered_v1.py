"""Frozen original G0-G5 decision; no tuning, training, inference or scoring."""
from pathlib import Path
import hashlib,json
d=Path(__file__).resolve().parent;base=d.parent;load=lambda p:json.loads(p.read_bytes());h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
auditpath=d/'post_score_freeze_audit_v1/formal_score_freeze_audit_v1.json';audit=load(auditpath);assert audit['status']=='FORMAL_READ_ONLY_EJTC_SCORE315_POST_SCORING_FREEZE_AUDIT_PASS'
q=load(d/'EJTC_RTJ_D_CPU_scoring_execution_request_v1.json');protocol=Path(q['protocol']['path']);assert h(protocol)==q['protocol']['sha256']
summary=load(d/'cpu_scored_once_v1/paired_summary.json');scope=load(base/'native_rtj315_preparation_v1/EJTC_RTJ_D_native315_scope_v2.json')
g0stats=summary['J_minus_R']['summary'];rmean=g0stats['metrics']['dense'];rsevere=g0stats['severe_case_ids']['B']
g0=dict(E_P95_mm=dict(actual=rmean['E_P95_mm']['arm_mean']['B'],maximum=8.087807971901558),severe=dict(actual=len(rsevere),maximum=6),J_Cover_at_2_pp=dict(actual=rmean['J_Cover_at_2']['arm_mean']['B'],minimum=44.427812447446904))
g0pass=g0['E_P95_mm']['actual']<=g0['E_P95_mm']['maximum'] and len(rsevere)<=6 and g0['J_Cover_at_2_pp']['actual']>=g0['J_Cover_at_2_pp']['minimum']
def criterion(actual,op,threshold):return dict(actual=actual,comparison=op,threshold=threshold,passed=(actual<=threshold if op=='<=' else actual>=threshold if op=='>=' else actual>threshold))
gates={}
for comparison,minimum in [('J_minus_R',2.),('J_minus_T',1.)]:
 s=summary[comparison]['summary'];c=s['metrics']['coarse'];v=s['metrics']['dense'];delta=lambda table,k:table[k]['delta_A_minus_B']
 checks={
 'G1':{**{k:criterion(delta(c,k),'<=',.25) for k in ('E_P95_mm','J_P95_mm')},**{k:criterion(delta(c,k),'>=',-.5) for k in ('E_Cover_at_2','J_Cover_at_2')},'reverse_A2_P95_mm':criterion(delta(c,'reverse_A2_P95_mm'),'<=',.5),'far20_pp':criterion(delta(c,'far20'),'<=',.25)},
 'G2':dict(J_Cover_at_2_pp=criterion(delta(v,'J_Cover_at_2'),'>=',minimum),improved_sources=criterion(v['J_Cover_at_2']['improved_sources'],'>=',14),CI95_lower=criterion(v['J_Cover_at_2']['CI95'][0],'>',0),leave_one_minimum=criterion(v['J_Cover_at_2']['leave_one_source_range'][0],'>',0)),
 'G3':{**{k:criterion(delta(v,k),'<=',.25) for k in ('E_P95_mm','J_P95_mm','CD_L1_mm')},'E_Cover_at_2_pp':criterion(delta(v,'E_Cover_at_2'),'>=',-.5)},
 'G4':dict(reverse_A2_P95_mm=criterion(delta(v,'reverse_A2_P95_mm'),'<=',.5),far20_pp=criterion(delta(v,'far20'),'<=',.25)),
 'G5':dict(total_severe=criterion(len(s['severe_case_ids']['A']),'<=',len(s['severe_case_ids']['B'])),new_severe=criterion(len(s['severe_case_ids']['new']),'<=',1))}
 gates[comparison]={g:dict(passed=all(x['passed'] for x in r.values()),criteria=r) for g,r in checks.items()}
training={}
for arm,record in scope['training_freeze_receipts'].items():
 path=Path(record['local_path']);assert h(path)==record['sha256'];r=load(path)
 assert r['checkpoint']['sha256']==scope['checkpoints'][arm]['sha256'] and r['counts']['steps']==3900
 training[arm]=dict(path=str(path),sha256=h(path),status=r['status'])
failed=[dict(pair=comp,gate=g,criterion=k,**v) for comp,groups in gates.items() for g,group in groups.items() for k,v in group['criteria'].items() if not v['passed']]
assert g0pass and len(failed)==2
record=dict(status='D1_FAIL_STOP',score_audit_sha256=h(auditpath),protocol=q['protocol'],scoring_request_sha256=audit['request_sha256'],G0=dict(passed=g0pass,criteria=g0),comparisons=gates,failed_criteria=failed,
 training_freeze_evidence=training,G6=dict(status='INHERITED_FORMAL_TRAINING_FREEZE_EVIDENCE',note='Three formally frozen training identities and 3900-step paired contracts linked; no new training recomputation in this gate script'),
 G7=dict(status='DEPLOYMENT_HOLD_NOT_FULLY_ADJUDICATED',note='Native state/RNG/operator-count/resource contract frozen. Dedicated preregistered deployment timing not executed; no new forward or timing authorized. Does not reverse G1/G3 FAIL_STOP.'),
 uncertainty='Single Fold D training seed; source-bootstrap intervals are conditional on these weights, not cross-seed or cross-fold evidence',
 interpretation='J improves the primary shared-wall coverage against both R and T, but fails J-T coarse far20 and dense E coverage protection; this exact candidate does not qualify for C1/D2/SkullFix continuation under the original gates.',
 next_boundary='Freeze current D1 as FAIL_STOP; no automatic replication, parameter change, new training or timing. Optional bounded existing-prediction review and final report/archiving require their own scope.')
dest=d/'EJTC_D1_preregistered_gate_decision_v1.json'
with dest.open('x',encoding='utf-8') as f:json.dump(record,f,ensure_ascii=False,indent=2)
print(json.dumps(dict(status=record['status'],G0_pass=g0pass,failed_criteria=failed,gate_pass={c:{g:v['passed'] for g,v in groups.items()} for c,groups in gates.items()}),ensure_ascii=False))
