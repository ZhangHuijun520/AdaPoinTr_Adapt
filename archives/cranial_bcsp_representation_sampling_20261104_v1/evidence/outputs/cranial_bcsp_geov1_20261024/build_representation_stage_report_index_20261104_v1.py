"""Bind existing local reports; no experiment, decoding, inference or scoring."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
B = 'outputs/cranial_bcsp_geov1_20261024/'
REPORT = ROOT / 'docs/cranial_bcsp_geov1_20261024/骨组织完整边界点云_表示缺损采样与点数综合实验报告_20261104_zh_v1.md'
OUT = ROOT / B / 'representation_stage_report_20261104_v1'
SOURCES = [
('原始体素与旧点云六例配对诊断','outputs/cranial_geometry_diagnostic_20261023/raw_pairing_v1/raw_pairing_report_zh_v1.md'),
('MUG三例STL与九例综合诊断','outputs/cranial_geometry_diagnostic_20261023/mug_mesh_v1/mug_mesh_and_integrated_report_zh_v1.md'),
('六例与phantom表面提取、输入及目标密度CPU结果',B+'cpu_geometry_results_report_zh_v1.md'),
('SkullBreak真实数据QC',B+'real_data_qc_report_zh_v1.md'),
('SkullFix90例批量几何QC',B+'skullfix_batch_geometry_qc_20261102_v1/report_zh_v1.md'),
('SkullFix90例新V1点集',B+'skullfix_surface_points_20261103_v1/report_zh_v1.md'),
('MUG原固定三来源实体准入',B+'mug_solid_pilot_20261029_v1/results/mug_fixed3_solid_pilot_report_zh_v1.md'),
('MUG来源与坐标补证',B+'mug_solid_pilot_20261029_v1/source_completion_v1/source_completion_report_zh_v1.md'),
('A0221固定ROI实体切除小试',B+'mug_solid_pilot_20261029_v1/a0221_solid_pilot_20261102_v1/report_zh_v1.md'),
('MUG100来源批量实体构造',B+'mug_solid_defects_v2_20261102/report_zh_v1.md'),
('A0221前景审阅决定',B+'a0221_foreground_adjudication_20261102_v1/前景审阅决定_zh_v1.md'),
('输入密度四模型开发评分与解读',B+'development_eval_v1/local_scoring_v1/four_model_development_results_zh_v2.md'),
('D-only高曲率增强采样',B+'input_interface_sampling_20261102_v1/report_zh_v1.md'),
('既有预测与proxy证据初步诊断',B+'prediction_proxy_diagnosis_20261102_v1/report_zh_v1.md'),
('实际CUDA取点轨迹本机分析',B+'actual_proxy_trace_20261102_v1/local_analysis_v1/report_zh_v1.md'),
('三平面D-only接口定位阶段A',B+'interface_stageA_20261102_v1/report_zh_v1.md'),
('无定位PCA双组局部几何检查',B+'multisurface_CPU_20261102_v1/report_zh_v1.md'),
('Morton六例CPU小试',B+'spatial_stratified_pilot_20261103_v1/report_zh_v1.md'),
('Morton510例扩大几何核验',B+'spatial_stratified_expanded_20261103_v1/report_zh_v1.md'),
('V1与Morton正式评分审计及解读',B+'sampling_model_AB_foldC_seed0_20261103_v1/paired_development_eval_v1/post_scoring_freeze_audit_v1/formal_audit_and_scientific_interpretation_zh_v1.md'),
('固定点数欧氏样本消减小试',B+'blue_noise_pilot_20261103_v1/report_zh_v1.md'),
('保存点集切壁与邻面支持分解',B+'blue_noise_pilot_20261103_v1/cutwall_support_review_v2/report_zh_v1.md'),
('人工U形几何机制干预',B+'blue_noise_artificial_mechanism_20261103_v1/report_zh_v1.md'),
('六例原生表面图距离检查',B+'blue_noise_real_surface_graph_20261103_v1/report_zh_v1.md'),
('24来源表面图距离扩大检查',B+'blue_noise_surface_graph_expanded_20261103_v1/report_zh_v1.md'),
('SkullBreak五缺损类型适用性',B+'blue_noise_defect_types_20261103_v1/report_zh_v1.md'),
('欧氏训练后冻结审计',B+'blue_noise_model_pair_foldC_seed0_20261104_v1/first_training_request_v2/post_Euclidean_training_freeze_audit_v1/formal_freeze_audit_report_zh_v1.md'),
('欧氏与图距离评分审计及科研解读',B+'blue_pair_eval_v1/post_scoring_freeze_audit_v1/formal_audit_and_scientific_interpretation_zh_v1.md'),
('固定八病例几何可视化诊断',B+'blue_pair_eval_v1/geometry_review_8cases_v1/geometry_review_report_zh_v1.md'),
('当前采样方案固定与搜索收束决定','docs/cranial_bcsp_geov1_20261024/surface_sampling_freeze_and_search_closure_zh_v1_20261104.md'),
]

def identity(p):
    raw = p.read_bytes()
    return {'path': p.as_posix(), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}

def main():
    if OUT.exists():
        raise RuntimeError('New report binding directory must not already exist')
    records, lines = [], ['| 编号 | 精确版本 |','|---|---|']
    for n, (label, rel) in enumerate(SOURCES, 1):
        p = ROOT / rel
        item = identity(p)
        item.update(id=f'E{n:02d}', label=label)
        records.append(item)
        lines.append(f'| E{n:02d} | [{label}](<{p.as_posix()}>) |')
    raw = REPORT.read_text(encoding='utf-8')
    marker = '<!-- EVIDENCE_INDEX -->'
    if raw.count(marker) != 1:
        raise RuntimeError('Expected single unexpanded source index')
    raw = raw.replace(marker, '\n'.join(lines))
    foot = f'\n\n配套文件：[证据身份清单](<{(OUT / "evidence_manifest_v1.json").as_posix()}>)；[报告核查记录](<{(OUT / "report_verification_v1.json").as_posix()}>)。\n'
    REPORT.write_text(raw + foot, encoding='utf-8')
    OUT.mkdir()
    records_after = [identity(ROOT / rel) for _, rel in SOURCES]
    stable = all(a['sha256'] == b['sha256'] and a['bytes'] == b['bytes'] for a,b in zip(records,records_after))
    assert stable
    report_id = identity(REPORT)
    (OUT / 'evidence_manifest_v1.json').write_text(json.dumps({'version':1, 'date':'2026-11-04','scope':'Existing local reports only; no raw data, weights, model execution, geometry rescoring or server access','sources':records,'report':report_id},ensure_ascii=False,indent=2),encoding='utf-8')
    import re
    cited = set(re.findall(r'E\d{2}', raw))
    assert cited == {f'E{n:02d}' for n in range(1,31)}
    assert raw.count('```') % 2 == 0
    result = {'status':'REPORT_SOURCE_LINK_AND_IDENTITY_CHECK_PASS','source_reports':len(records),'source_bytes':sum(x['bytes'] for x in records),'all_source_paths_exist':True,'source_content_unchanged':stable,'all_30_evidence_labels_defined':True,'balanced_fenced_blocks':True,'report':report_id,'limitations':['Document/source binding verification, not independent recomputation of experimental metrics','Historical artifact and checkpoint identities are quoted from frozen records; no server revalidation','No claim of expert anatomical review or clinical validation']}
    (OUT / 'report_verification_v1.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))

if __name__ == '__main__':
    main()
