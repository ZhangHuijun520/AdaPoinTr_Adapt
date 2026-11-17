# -*- coding: utf-8 -*-
"""Assemble planning documents and existing JSON metadata only; no model/data payload access."""
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(r'E:\Codex\2026-06-06\mamba-ccf-c-1-high-resolution')
OUT = ROOT / 'outputs/trace_plan_review_20261117_v1'
PLAN = ROOT / 'docs/cranial_bcsp_trace_20261117_v2/Cranial_BCSP_FullMamba_BCSP_TRACE_正式实验计划书_审阅修订v2_2026-11-17.md'
ORIGINAL = Path(r'C:\Users\zhj\Desktop\Cranial_BCSP_FullMamba_BCSP-TRACE_探针Memory空间证据与锚点条件验证_正式实验计划书_2026-11-17.md')

def dump(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def binding(path):
    blob = path.read_bytes()
    return {'path': str(path), 'bytes': len(blob), 'sha256': hashlib.sha256(blob).hexdigest()}

def readj(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

original_copy = OUT / 'user_TRACE_draft_20261117_v1_original.md'
assert not original_copy.exists(), 'do not overwrite original evidence'
original_copy.write_bytes(ORIGINAL.read_bytes())
caseindex = ROOT / 'outputs/spcg_score_implementation_20261117_v1/SPCG_score_case_index_v1.json'
cases = readj(caseindex)['cases']
types = ['bilateral', 'frontoorbital', 'parietotemporal', 'random_1', 'random_2']
mandatory = {
    'C': ['train__051__random_1', 'train__072__random_1', 'train__012__parietotemporal'],
    'D': ['train__008__random_2', 'train__046__parietotemporal'],
}
selected = []
for fold in ('C', 'D'):
    pool = [c for c in cases if c['fold'] == fold]
    assert len(pool) == 105 and len({c['source_id'] for c in pool}) == 21
    chosen = [c for name in mandatory[fold] for c in pool if c['case_id'] == name]
    assert len(chosen) == len(mandatory[fold])
    seen = {c['source_id'] for c in chosen}
    for defect in types:
        count = sum(c['case_id'].split('__', 2)[2] == defect for c in chosen)
        candidates = [c for c in pool if c['case_id'].split('__', 2)[2] == defect]
        candidates.sort(key=lambda c: hashlib.sha256(('BCSP_TRACE_D0_v2|' + fold + '|' + c['case_id']).encode('utf-8')).hexdigest())
        for candidate in candidates:
            if count == 4:
                break
            if candidate['source_id'] in seen:
                continue
            chosen.append(candidate)
            seen.add(candidate['source_id'])
            count += 1
        assert count == 4
    assert len(chosen) == 20 and len(seen) == 20
    for c in chosen:
        row = dict(c)
        row['defect_type'] = c['case_id'].split('__', 2)[2]
        row['selection_stratum'] = 'PREVIOUSLY_EXPOSED_FIXED_CASE' if c['case_id'] in mandatory[fold] else 'HASH_SELECTED_NONPRESSURE'
        row['selection_hash'] = hashlib.sha256(('BCSP_TRACE_D0_v2|' + fold + '|' + c['case_id']).encode('utf-8')).hexdigest()
        row['forward_arms'] = ['G1', 'G2']
        selected.append(row)
    assert Counter(c['case_id'].split('__', 2)[2] for c in chosen) == Counter({t: 4 for t in types})

assert len(selected) == 40 and len({c['source_id'] for c in selected}) == 40
dump(OUT / 'TRACE_D0_proposed_cases_v2.json', {
    'status': 'PROPOSED_METADATA_ONLY_NOT_AN_EXECUTION_REQUEST',
    'date': '2026-11-17', 'execution_authorized': False,
    'source_index': binding(caseindex),
    'rule': 'reserve mandatory source IDs first; fixed type order; SHA256(BCSP_TRACE_D0_v2|fold|case_id) ascending; skip used sources; four cases per type',
    'type_order': types, 'case_count': 40, 'unique_sources': 40,
    'full_forward_count_if_separately_authorized': 80,
    'counts': {fold: {'cases': 20, 'unique_sources': 20, 'previously_exposed': len(mandatory[fold]), 'primary_association_cases': 20-len(mandatory[fold])} for fold in ('C', 'D')},
    'payload_read': False, 'model_loaded': False, 'server_connected': False,
    'cases': selected,
})
lines = ['# TRACE D0拟用40例（仅元数据冻结建议）', '', '尚未读取点云payload或运行模型；不是执行请求。', '', '| Fold | 病例 | 来源 | 层次 |', '|---|---|---|---|']
for c in selected:
    lines.append('| {} | {} | {} | {} |'.format(c['fold'], c['case_id'], c['source_id'], '既有固定案例' if c['selection_stratum'].startswith('PREVIOUSLY') else '哈希补充'))
(OUT / 'TRACE_D0_proposed_cases_v2.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')

ledger = [
 ('3DMambaComplete', 'arXiv:2404.07106v2, 2026-05-19; TOMM DOI 10.1145/3774887', 'https://arxiv.org/html/2404.07106v2', '全文方法部分核对', 'HyperPoint Generation含Cross-Attention；不属完全无注意力。锚点名称不足以构成创新。'),
 ('CompletionMamba: Taming State Space Model for Point Cloud Completion', 'IEEE TIP 34, 5473–5485, 2025; 10.1109/TIP.2025.3597041', 'https://pubmed.ncbi.nlm.nih.gov/40853794/', '官方收录摘要', '坐标重排与局部SSM提供相关性；未据摘要认定具体公式等价。'),
 ('DAPointMamba: Domain Adaptive Point Mamba for Point Cloud Completion', 'AAAI 2026; 10.1609/aaai.v40i8.37596', 'https://ojs.aaai.org/index.php/AAAI/article/view/37596', '官方检索摘要；后续直接重访反爬拒绝', '域适应背景，不是颅骨同协议效果证据。'),
 ('FusionMamba: Efficient 3D Point Cloud Completion via Spatially-Aware State Space Models and Multi-Scale Information Fusion', 'Information Fusion 134:104378, 2026; 10.1016/j.inffus.2026.104378', 'https://www.sciencedirect.com/science/article/pii/S1566253526002575', '出版社检索摘要/Highlights；直接重访403', '涉及几何校正与局部全局融合，不能据摘要声称已复现或证明TRACE不同。'),
 ('GDPNet: A Geometry Aware Dual-Path Network for Point Cloud Completion', 'Computers & Graphics, 2026；DOI需进一步原页核验', 'https://www.sciencedirect.com/science/article/pii/S0097849326001810', '出版社检索预览；直接访问403', '仅作关键节点与结构几何线索；不以同名语义分割GDPNet代替。'),
 ('Hyper-PCN: Hypergraph-Based Point Cloud Completion via High-Order Correlation Modeling', 'CVPR 2026, 39121–39130', 'https://openaccess.thecvf.com/content/CVPR2026/html/Li_Hyper-PCN_Hypergraph-Based_Point_Cloud_Completion_via_High-Order_Correlation_Modeling_CVPR_2026_paper.html', '官方论文页摘要，补充材料检索', 'Anchor协作高阶关系的相关工作；不迁移其邻域参数。'),
 ('PPC-MT: A Mamba-Transformer Hybrid for Point Cloud Completion', 'arXiv:2603.00870v1, 2026-03', 'https://arxiv.org/html/2603.00870v1', '全文入口/标题核对', '明确混合架构，仅用于架构归类，不作无注意力依据。'),
 ('MedPCFM: Improving Medical Point Cloud Completion by Integrating Point Transformers and Flow Matching', 'arXiv:2606.24433v1, 2026-06-23；预印本', 'https://arxiv.org/html/2606.24433v1', '全文方法与实验设置核对', 'SkullFix/Break直接相关；采样、点数、归一化和训练预算不同，不能直接排名。'),
 ('MedPCFM-TED: One-Step Point Cloud Flow Matching for Implant Generation via Teacher-Guided Endpoint Distillation', 'MICCAI 2026 SASHIMI卫星研讨会；官方DOI/页码待公布', 'https://papers.miccai.org/miccai-2026-sat/SASHIMI_017.html', '官方论文页摘要与作者核对', '区分卫星研讨会与主会；不虚构DOI，不直接比较时间。'),
 ('High-Resolution Cranial Defect Reconstruction by Iterative, Low-Resolution, Point Cloud Completion Transformers', 'MICCAI 2023; 10.1007/978-3-031-43996-4_32', 'https://arxiv.org/abs/2308.03813', '原始预印本入口与作者机构PDF', '迭代低分辨率至高分辨率任务背景，不直接移植其结果。'),
 ('Point Cloud Diffusion Models for Automatic Implant Generation', 'arXiv:2303.08061, 2023', 'https://pfriedri.github.io/pcdiff-implant-io/', '作者项目页与机构研究页', '完整形状重建、曲面重建及取差集链路与直接缺失骨块边界预测应分开。'),
 ('CDRMamba: A Framework for Automated Craniomaxillofacial Defect Reconstruction Using Mamba-Based Modeling', 'Biomedical Signal Processing and Control; 10.1016/j.bspc.2024.107376', 'https://www.sciencedirect.com/science/article/pii/S1746809424014344', '出版社摘要', '3D影像/UNet-Mamba路线，不是直接点云同协议基线。'),
 ('SkullBreak / SkullFix – Dataset for Automatic Cranial Implant Design and a Benchmark for Volumetric Shape Learning Tasks', 'Data in Brief 35:106902, 2021', 'https://pmc.ncbi.nlm.nih.gov/articles/PMC8100897/', '官方全文数据库', '原始数据来源和合成缺损背景；本项目84来源不是全部官方数据。'),
 ('Thickness and Design Features of Clinical Cranial Implants—What Should Automated Methods Strive to Replicate?', 'IJCARS 19(4):747–756, 2024; 10.1007/s11548-024-03068-4', 'https://pubmed.ncbi.nlm.nih.gov/38430381/', '官方收录摘要', '临床厚度/边缘设计与合成切壁指标有差别，不把2mm支持解释为临床标准。'),
 ('Revisiting Point Cloud Completion: Are We Ready for the Real-World?', 'ICCV 2025, 25388–25398', 'https://openaccess.thecvf.com/content/ICCV2025/html/Pathak_Revisiting_Point_Cloud_Completion_Are_We_Ready_For_The_Real-World_ICCV_2025_paper.html', '官方论文页与PDF检索', '现实数据分布和拓扑背景；不将训练完整GT骨架采样当作D-only推理方法。'),
]
dump(OUT / 'TRACE_primary_literature_ledger_v1.json', {
    'cutoff_date': '2026-11-17',
    'method': 'targeted primary-source web verification; not a systematic review; full text/abstract/preview access explicitly distinguished',
    'unavailable_channel': 'No academic database MCP tools were available in this session; no tools or packages installed.',
    'coverage_limits': 'User historical title lists are research leads, not a claim that all 82 papers, formulas and implementations were read.',
    'entries': [dict(title=t, bibliographic_status=b, url=u, evidence_level=e, relevance_limit=n) for t,b,u,e,n in ledger],
    'excluded_or_not_promoted': [
        '同名GDPNet图网络/Transformer语义分割论文不替代本条点云补全论文。',
        '2026年11月Mamba语义场景补全预印本不作为颅骨对象级同协议基线。',
        '此前题录中未核全文/公式/代码的其他条目不用于原创性保证。',
    ],
})
litmd = ['# TRACE文献核验表', '', '截止2026-11-17；定向核验，不是系统综述。全文、摘要与检索预览分开标注；未核代码不声称复现。', '']
for t,b,u,e,n in ledger:
    litmd += ['## '+t, '', b, '', '- 来源：[原始访问入口]('+u+')。', '- 证据层级：'+e+'。', '- 对本计划的作用与限制：'+n, '']
(OUT / 'TRACE_primary_literature_ledger_v1.md').write_text('\n'.join(litmd), encoding='utf-8')

receiptpath = Path(r'E:\ResearchBackups\AdaPoinTr\BCSP_FULLMAMBA_SPCG\SPCG_final_archival_receipt_20261117_v1.json')
receipt = readj(receiptpath)
dump(OUT / 'TRACE_inherited_checkpoint_locations_v1.json', {
    'status': 'INHERITED_VERIFIED_BACKUP_RECEIPT_NOT_A_FRESH_WEIGHT_REHASH_OR_LOAD',
    'receipt_binding': binding(receiptpath),
    'receipt_status': receipt['status'],
    'D0_weights': [w for w in receipt['weights'] if w['run'] in ('G1_C','G2_C','G1_D','G2_D')],
    'restore_execution': 'NOT_TESTED_IN_TRACE', 'checkpoint_payload_read_this_review': False,
})
evidencepaths = [
    ROOT / 'outputs/spcg_experiment_report_20261117_v1/Cranial_BCSP_FullMamba_BCSP_SPCG_完整实验报告_zh_v1.md',
    ROOT / 'outputs/spcg_score_freeze_20261117_v1/frozen_research_summary_v1.json',
    ROOT / 'outputs/spcg_score_freeze_20261117_v1/audit_verification_v1.json',
    ROOT / 'outputs/spcg_scientific_decision_20261117_v1/scientific_decision_record_v1.json',
    ROOT / 'outputs/spcg_visualization_freeze_20261117_v2/audit_verification_v1.json',
    ROOT / 'outputs/spcg_implementation_20261116_v1/bcsp_spcg_head_v1.py',
    ROOT / 'outputs/cranial_bcsp_geov1_20261024/blue_pair_eval_v1/bcsp_eval_metrics_v1.py',
    ROOT / 'outputs/spcg_native_prediction_preparation_20261117_v1/implementation_v1/SPCG_native_scope_v1.json',
    caseindex, receiptpath,
]
dump(OUT / 'TRACE_review_evidence_manifest_v1.json', {
    'status': 'PLANNING_ONLY_NO_EXECUTION', 'original': binding(ORIGINAL),
    'original_preserved_copy': binding(original_copy),
    'reviewed_local_sources': [binding(p) for p in evidencepaths],
    'prohibited_actions_not_taken': ['server connection','checkpoint load','NPZ payload read','forward','training','production edits','execution request creation'],
})

# Documentary consistency checks, not scientific/CPU model contract tests.
summary = readj(ROOT / 'outputs/spcg_score_freeze_20261117_v1/frozen_research_summary_v1.json')
for fold, expected in [('C',1.5270355316275281), ('D',1.872022882855)]:
    val = summary['folds'][fold]['comparisons']['G2_minus_G1']['metrics']['E_P95_mm']['mean_delta_b_minus_a']
    assert abs(val-expected) < 1e-8
docs = [PLAN] + list(OUT.glob('*.md'))
for doc in docs:
    s = doc.read_text(encoding='utf-8-sig')
    assert not any(ord(c) < 32 and c not in '\n\r\t' for c in s), str(doc)
    assert s.count('```') % 2 == 0
    lines = s.splitlines()
    for i,line in enumerate(lines):
        if line.startswith('|') and i+1 < len(lines) and lines[i+1].startswith('|'):
            assert line.count('|') == lines[i+1].count('|'), (doc, i)
qa = {
    'status': 'DOCUMENT_AND_METADATA_QA_PASS_NOT_IMPLEMENTATION_P3',
    'checks': {'original_copy_exact': original_copy.read_bytes()==ORIGINAL.read_bytes(),
               'forty_cases_forty_sources': True, 'twenty_per_fold': True,
               'four_per_type_per_fold': True, 'five_mandatory_preserved': True,
               'primary_association_count_C17_D18': True,
               'historical_E_delta_matches_formal_freeze': True,
               'markdown_control_characters_tables': True,
               'no_runtime_or_request_created': True},
    'plan': binding(PLAN),
    'artifacts': [binding(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name != 'document_qa_and_delivery_manifest_v1.json'],
}
dump(OUT / 'document_qa_and_delivery_manifest_v1.json', qa)
print(json.dumps({'status': qa['status'], 'plan': qa['plan'], 'cases': 40, 'primary_cases': {'C':17,'D':18}},ensure_ascii=False))
