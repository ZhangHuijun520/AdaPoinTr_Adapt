# -*- coding: utf-8 -*-
"""Read saved products, verify bindings, and write the batch completion report."""
import csv,hashlib,json,sys
from pathlib import Path
import numpy as np

B=Path(__file__).resolve().parent
R=B/'skullfix_surface_points_20261103_v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,obj):
    with p.open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2,allow_nan=False)
def main():
    summary=json.loads((R/'summary.json').read_text(encoding='utf-8'))
    assert summary['cases']==90 and not (R/'failure.json').exists()
    scope=json.loads((R/'scope.json').read_text(encoding='utf-8'))
    records=[json.loads(s) for s in (R/'manifest_8192.jsonl').read_text(encoding='utf-8').splitlines()]
    assert len(records)==90 and len({r['source_id'] for r in records})==90
    assert {r['case_id'] for r in records}==set(scope['source_ids'])
    assert not ({r['case_id'] for r in records}&set(scope['excluded_internal_test_ids']))
    assert len(list((R/'points').glob('*.npz')))==90
    assert len(list((R/'diagnostics').glob('*.npz')))==90
    rows=[]
    for r in records:
        p=R/r['point_path'];d=R/r['diagnostic_provenance_path']
        assert sha(p)==r['sha256'] and sha(d)==r['diagnostic_provenance_sha256']
        with np.load(p,allow_pickle=False) as z:
            assert set(z.files)=={'partial','implant'}
            for name in z.files:assert z[name].shape==(8192,3) and z[name].dtype==np.float32 and np.isfinite(z[name]).all()
            assert hashlib.sha256(z['implant'].tobytes()).hexdigest()==r['target_array_sha256']
            with np.load(d,allow_pickle=False) as q:
                A=q['directions'];o=q['origin'];center=q['normalization_center'];scale=q['normalization_scale']
                assert np.array_equal(center,np.array(r['normalization']['center'])) and scale==r['normalization']['scale']
                for prefix,name in [('D','partial'),('G','implant')]:
                    local=(z[name].astype(float)*scale+center-o)@np.linalg.inv(A)-q[prefix+'_sample_voxel_indices']
                    axis=q[prefix+'_sample_axis'];sign=q[prefix+'_sample_sign']
                    assert np.abs(local[np.arange(8192),axis]-.5*sign).max()<1e-3
                    assert np.abs(local).max()<.501
                    assert q[prefix+'_sample_is_J'].shape==(8192,)
                assert not q['G_sample_is_FOV'].any()
        row=json.loads((R/'cases'/f"{r['case_id']}.json").read_text(encoding='utf-8'))
        assert row['shared_J_pairing_verified'] and row['input_completed_before_C_G_decode']
        rows.append(row)
    for split,filename in [('train','train_manifest_8192.jsonl'),('val','validation_manifest_8192.jsonl')]:
        sub=[json.loads(s) for s in (R/filename).read_text(encoding='utf-8').splitlines()]
        assert sub==[r for r in records if r['split']==split]
    for p,digest in scope['implementation_and_metadata_sha256'].items():assert sha(Path(p))==digest
    def stat(vals):
        a=np.array(vals,float)
        return {'mean':float(a.mean()),'median':float(np.median(a)),'min':float(a.min()),'max':float(a.max())}
    agg={}
    for group in ['D','G']:
        agg[group]={k:stat([r[group][k] for r in rows]) for k in ['sample_J_points','sample_FOV_points','FOV_area_fraction']}
        for region in ['all_boundary_metric','J_metric']+(['original_boundary_E_metric'] if group=='G' else []):
            agg[group][region]={k:stat([r[group][region][k] for r in rows]) for k in ['cover_1mm','cover_2mm','p95_mm']}
    agg['maximum_roundtrip_mm']=max(r['roundtrip_world_max_mm'][g] for r in rows for g in ['D','G'])
    agg['inherited_warning_cases']=[{'case_id':r['case_id'],'warnings':r['prior_geometry_warnings']} for r in rows if len(r['prior_geometry_warnings'])>1]
    save(R/'aggregate_geometry.json',agg)
    with (R/'case_metrics.csv').open('x',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(['case_id','split','D_J_points','D_J_cover2','D_J_p95_mm','G_J_points','G_J_cover2','G_J_p95_mm','G_E_cover2','G_E_p95_mm','D_FOV_points','D_FOV_area_fraction'])
        for r in rows:
            d,g=r['D'],r['G'];w.writerow([r['case_id'],r['split'],d['sample_J_points'],d['J_metric']['cover_2mm'],d['J_metric']['p95_mm'],g['sample_J_points'],g['J_metric']['cover_2mm'],g['J_metric']['p95_mm'],g['original_boundary_E_metric']['cover_2mm'],g['original_boundary_E_metric']['p95_mm'],d['sample_FOV_points'],d['FOV_area_fraction']])
    def mean(g,r,k,percent=False):return f"{agg[g][r][k]['mean']*(100 if percent else 1):.4f}"
    report=f'''# SkullFix 已开放90例新表示点集：完成报告 v1

日期：2026-11-03。状态：本机CPU生成及产物回读核验完成；未运行模型、训练、GPU或服务器任务。

## 范围与数据身份

沿用已经开放并通过批量几何QC的90例：80例训练、10例验证。另10例内部留出不解码、不参与点集生成。这里的80/10/10为本项目既有划分，不是官方挑战测试划分。原始270个NRRD在生成前后均核对SHA256，保持不变。

不新增缺损，不清理连通成分，不平滑、补洞或改变坐标。018与062既有微小植入物成分保留；原始几何问题不能通过点云采样自动消除。

## 表示、目标与可重复性

- 输入为残缺骨实体D的全部暴露体素面∂D；目标为缺失骨块G的完整边界∂G，包括原始边界E和共享切壁J。既有骨组织的内侧、外侧及孔腔边界均不按语义筛除；没有额外的解剖内外板标签。
- 复用不变的V1采样器：按面片物理面积有放回抽面，再在面内均匀取点；不是体积采样，也不是平滑等值面采样。体素尺度阶梯特征仍然存在。
- 每例输入8192点、目标8192点，float32，数组键仅为`partial/implant`。输入先以seed 0抽16384点后取前8192点，保持与既有SkullBreak输入前缀合同一致；目标独立seed 0抽8192点。
- 输入采样和归一化参数在解码C/G前完成。仅以D的前景体素中心世界包围盒中心及半对角线归一化，目标使用相同变换；没有用GT指导输入点选取。
- 逐例验证C=D∪G、D∩G=∅，D/G两侧J面的位置一致且方向相反，并与既有QC身份绑定一致。
- 切壁、FOV及原始面归属单独存放在`diagnostics/`，仅供几何检查，不是模型输入特征。

## 产物与核验

生成90个点集、90个独立来源标签文件和90个逐例几何记录；总清单90条，训练清单80条，验证清单10条。全部NPZ重新加载，验证键、形状、类型、有限值、哈希、坐标与来源面一致性。最大世界坐标float32归一化回读误差为{agg['maximum_roundtrip_mm']:.9f} mm。

固定人工几何检查8项通过，覆盖各向异性面面积、面内采样、刚体变换、共享切壁、FOV标记与归一化。它们不是模型加载或GPU训练准入测试。

批次耗时{summary['elapsed_seconds']/60:.2f}分钟；检查点采样到的最大RSS为{summary['sampled_RSS_max_bytes']/1024**3:.3f} GiB，并非连续监测的绝对峰值或硬隔离上限。

## 描述性几何结果

以下为90例等权均值；覆盖率以原始暴露体素面中心为参考、按物理面积加权，距离使用同侧完整采样点集最近邻。它们不是连续解剖真值误差，也不是模型预测性能。

| 测量区域 | 1 mm覆盖率 | 2 mm覆盖率 | P95距离（mm） |
|---|---:|---:|---:|
| 输入D全部边界 | {mean('D','all_boundary_metric','cover_1mm',True)}% | {mean('D','all_boundary_metric','cover_2mm',True)}% | {mean('D','all_boundary_metric','p95_mm')} |
| 输入D切壁J | {mean('D','J_metric','cover_1mm',True)}% | {mean('D','J_metric','cover_2mm',True)}% | {mean('D','J_metric','p95_mm')} |
| 目标G全部边界 | {mean('G','all_boundary_metric','cover_1mm',True)}% | {mean('G','all_boundary_metric','cover_2mm',True)}% | {mean('G','all_boundary_metric','p95_mm')} |
| 目标G切壁J | {mean('G','J_metric','cover_1mm',True)}% | {mean('G','J_metric','cover_2mm',True)}% | {mean('G','J_metric','p95_mm')} |
| 目标G原始边界E | {mean('G','original_boundary_E_metric','cover_1mm',True)}% | {mean('G','original_boundary_E_metric','cover_2mm',True)}% | {mean('G','original_boundary_E_metric','p95_mm')} |

输入切壁点数均值{agg['D']['sample_J_points']['mean']:.2f}（范围{agg['D']['sample_J_points']['min']:.0f}–{agg['D']['sample_J_points']['max']:.0f}）；目标切壁点数均值{agg['G']['sample_J_points']['mean']:.2f}（范围{agg['G']['sample_J_points']['min']:.0f}–{agg['G']['sample_J_points']['max']:.0f}）。每例的范围、中位数及细分指标见`aggregate_geometry.json`与`case_metrics.csv`。

## FOV与结论边界

当前V1把体积外视为背景，因此包含扫描截断面；这不是天然解剖边界。本批沿用该规则并显式标记，没有偷偷修改采样器。输入FOV面积占比均值{agg['D']['FOV_area_fraction']['mean']*100:.4f}%，范围{agg['D']['FOV_area_fraction']['min']*100:.4f}–{agg['D']['FOV_area_fraction']['max']*100:.4f}%；{summary['cases_with_sampled_D_FOV']}例采到FOV点，共{summary['D_FOV_sample_points_total']}点。目标G均不触FOV。

本批补齐了SkullFix既定90例的新表示数据资产，可作为后续采样研究和模型接入的固定工作基线。均匀采样不保证稀薄局部结构充分覆盖；保留多表面几何不等于认证每个内外板都采足。8192/8192是当前工作设置，本批没有证明它最优，也没有证明V1优于其他方法。使用新点集训练尚未发生；与既有SkullBreak模型比较时仍需固定训练、评价及划分合同。

## 文件入口

- `manifest_8192.jsonl`：全90例点集、原始来源、归一化与哈希。
- `train_manifest_8192.jsonl`、`validation_manifest_8192.jsonl`：固定80/10划分。
- `points/`：模型点数组；`diagnostics/`：仅供分析的来源标签。
- `cases/`、`case_metrics.csv`、`aggregate_geometry.json`：逐例及汇总结果。
- `scope.json`、`synthetic_checks.json`、`summary.json`、`completion_verification.json`、`artifact_manifest.json`：本批范围与核验材料。
'''
    with (R/'report_zh_v1.md').open('x',encoding='utf-8') as f:f.write(report)
    save(R/'completion_verification.json',{'status':'PASS','point_files_verified':90,'diagnostic_files_verified':90,'case_records':90,'train':80,'validation':10,'point_shapes':[8192,3],'all_bindings_and_readback_pass':True,'excluded_internal_test_payload_reads':0,'forward_calls':0,'training_calls':0,'verifier_sha256':sha(Path(__file__))})
    files={str(p.relative_to(R)).replace('\\','/'):{'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(R.rglob('*')) if p.is_file()}
    save(R/'artifact_manifest.json',{'status':'FROZEN_COMPLETED_LOCAL_POINT_PREPARATION','files':files,'manifest_excludes_itself':True})
    print(json.dumps({'status':'PASS','files':len(files),'bytes':sum(v['bytes'] for v in files.values()),'aggregate':agg},ensure_ascii=True))
if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');main()
