# -*- coding: utf-8 -*-
"""Summarize frozen JSON evidence for reporting; no arrays, scoring, model or server."""
import hashlib,json,statistics
from pathlib import Path
from collections import Counter

R=Path(__file__).resolve().parents[2];D=Path(__file__).resolve().parent
V=R/'outputs/trace_D0_implementation_20261117_v1'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def rec(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(4194304),b''):h.update(b)
    return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=h.hexdigest())
def emit(n,x):
    with (D/n).open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
audit=read(V/'CPU_analysis_freeze_v1/formal_freeze_verification_v1.json');gpu=read(V/'post_diagnostic_freeze_v1/formal_freeze_verification_v1.json');closure=read(R/'outputs/trace_scientific_closure_20261117_v1/scientific_closure_record_v1.json')
assert all(audit['checks'].values()) and all(gpu['checks'].values())
for b in audit['output_bindings']:assert rec(Path(b['path']))==b
rows=read(V/'CPU_history_replay_analysis_v1/case_evidence.json');summary=read(V/'CPU_history_replay_analysis_v1/summary.json')
assert len(rows)==80 and summary['status']==audit['decision']=='NO_SUPPORT_OR_INCONCLUSIVE'
roles={}
keys=['R_case','T_case','nu_case','memory_union_fraction','memory_hit_entropy','unique_neighborhoods','F_mean_channel_variance','f_mean_channel_variance']
for role in ['G1_C','G2_C','G1_D','G2_D']:
    part=[r for r in rows if r['run']==role]
    roles[role]=dict(records=len(part),unique_sources=len({r['source_id'] for r in part}),geometry={k:dict(min=min(r['spatial'][k] for r in part),median=statistics.median(r['spatial'][k] for r in part),max=max(r['spatial'][k] for r in part)) for k in keys})
fixed=[dict(run=r['run'],case_id=r['case_id'],delta_E_mm=r['delta_E'],**{k:r['spatial'][k] for k in ['R_case','T_case','nu_case','memory_union_fraction']}) for r in rows if r['run'].startswith('G2') and r['selection_stratum']=='PREVIOUSLY_EXPOSED_FIXED_CASE']
facts=dict(status='FROZEN_JSON_REPORT_DESCRIPTIVE_SUMMARIES_ONLY',report_date='2026-11-17',core_result=summary,closure_status=closure['status'],roles=roles,fixed_cases=fixed,exact_QP_records=sum(all(r['replay'][k]['exact_bytes'] for k in ['Q','P']) for r in rows),Memory_unique_counts=sorted({r['spatial']['S_unique'] for r in rows}),counts=gpu['counts'],GPU_resource=gpu['resource_summary'],CPU_resource=audit['resource_summary'],GPU_resource_records=gpu['resource_records'],CPU_resource_records=audit['resource_records'],archive=gpu['archive'],GPU_audit_checks=len(gpu['checks']),CPU_audit_checks=len(audit['checks']),CPU_test_checks=read(V/'CPU_batch_v2/result.json')['count'],source_defect_counts={fold:dict(Counter(r['defect_type'] for r in rows if r['run']=='G2_'+fold)) for fold in ['C','D']},new_score_or_association_computation=False)
emit('report_facts_v1.json',facts)
paths=[R/'docs/cranial_bcsp_trace_20261117_v2/Cranial_BCSP_FullMamba_BCSP_TRACE_正式实验计划书_审阅修订v2_2026-11-17.md',R/'outputs/trace_plan_review_20261117_v1/TRACE_D0_proposed_cases_v2.json',R/'outputs/trace_P0_readiness_20261117_v1/P0_verification_v1.json',R/'outputs/trace_P0_readiness_20261117_v1/TRACE_D0_preparation_scope_v1.json',V/'TRACE_D0_P3_v1.json',V/'CPU_batch_v1/failure.json',V/'CPU_batch_v2/result.json',V/'test_bcsp_trace_D0_CPU_v2.py',V/'bcsp_trace_D0_observer_v1.py',V/'bcsp_trace_D0_entry_v1.py',V/'bcsp_trace_D0_analysis_v1.py',V/'TRACE_D0_execution_request_v1.json',V/'installation_attempt_v1/installation_receipt_v1.json',V/'post_installation_freeze_v1/formal_freeze_verification_v1.json',V/'post_diagnostic_freeze_v1/formal_freeze_verification_v1.json',V/'authorized_execution_v1/completion_observation_v1.json',V/'CPU_analysis_preparation_v1/TRACE_D0_CPU_analysis_execution_request_v1.json',V/'CPU_analysis_preparation_v1/authorized_execution_v1/execution_exit_v1.json',V/'CPU_analysis_freeze_v1/formal_freeze_verification_v1.json',V/'CPU_history_replay_analysis_v1/case_evidence.json',V/'CPU_history_replay_analysis_v1/summary.json',R/'outputs/trace_scientific_closure_20261117_v1/scientific_closure_record_v1.json',R/'outputs/spcg_score_freeze_20261117_v1/frozen_research_summary_v1.json',R/'outputs/spcg_scientific_decision_20261117_v1/scientific_decision_record_v1.json',R/'outputs/spcg_implementation_20261116_v1/bcsp_spcg_head_v1.py',R/'outputs/spcg_implementation_20261116_v1/bcsp_spcg_factory_v1.py',R/'outputs/trace_plan_review_20261117_v1/TRACE_primary_literature_ledger_v1.json',Path('E:/ResearchBackups/AdaPoinTr/BCSP_FULLMAMBA_TRACE/2026-11-17_D0_memory_evidence/local_verification_receipt_v1.json')]
emit('report_evidence_manifest_v1.json',dict(status='LOCAL_EXISTING_EVIDENCE_BINDINGS_VERIFIED',sources=[rec(p) for p in paths],report_facts=rec(D/'report_facts_v1.json'),scientific_arrays_opened=False,new_experiments=False,server_operations=0))
print(json.dumps(dict(status=facts['status'],evidence_files=len(paths),fixed_cases=len(fixed))))
