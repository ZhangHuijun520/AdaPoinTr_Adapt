# -*- coding: utf-8 -*-
"""Summarize completed fixed QC records only; no NRRD payload or model reads."""
import collections
import hashlib
import json
from pathlib import Path
import numpy as np

BASE = Path(__file__).resolve().parent
OUT = BASE/'skullfix_batch_geometry_qc_20261102_v1'

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''): h.update(b)
    return h.hexdigest()

def save(name,obj):
    with (OUT/name).open('x',encoding='utf-8') as f:
        json.dump(obj,f,ensure_ascii=False,indent=2,allow_nan=False)

def main():
    summary=json.loads((OUT/'summary.json').read_text(encoding='utf-8'))
    process=json.loads((OUT/'process_result.json').read_text(encoding='utf-8'))
    scope=json.loads((OUT/'scope.json').read_text(encoding='utf-8'))
    visual=json.loads((OUT/'visual_review_v1.json').read_text(encoding='utf-8'))
    visual_more=json.loads((OUT/'visual_review_addendum_v1.json').read_text(encoding='utf-8'))
    visual_ids=sorted(set(visual['reviewed_case_ids']+visual_more['reviewed_case_ids']))
    if process['exit_code'] != 0 or summary['case_count'] != 90 or (OUT/'failure.json').exists():
        raise RuntimeError('batch did not finish successfully; no success report')
    rows=[json.loads(p.read_text(encoding='utf-8')) for p in sorted((OUT/'cases').glob('*.json'))]
    if len(rows)!=90 or [r['case_id'] for r in rows]!=scope['selected_ids']:
        raise ValueError('case record identity/count mismatch')
    if any(r['partition_overlap_voxels'] or r['partition_xor_voxels'] or not r['shared_J_pairing_exact']
           or not r['shared_J_opposite_physical_normals'] for r in rows):
        raise ValueError('geometric contract not satisfied')
    warning_counts=collections.Counter(w for r in rows for w in r['warnings'])
    ekey='FOV_contact_voxels_axis0low_high_axis1low_high_axis2low_high'
    g_fov=[r['case_id'] for r in rows if any(r[ekey]['G'])]
    c_fov=[r['case_id'] for r in rows if any(r[ekey]['C'])]
    multig=[{'case_id':r['case_id'],'components_6':r['G_components_6'],
             'largest_fraction':r['G_largest_component_fraction'],
             'nonlargest_voxels':int(round(r['voxels']['G']*(1-r['G_largest_component_fraction'])))}
             for r in rows if r['G_components_6']>1]
    ranges={}
    for k in ['shared_J_faces','shared_J_area_mm2','G_largest_component_fraction']:
        a=np.array([r[k] for r in rows])
        ranges[k]={'min':float(a.min()),'median':float(np.median(a)),'max':float(a.max())}
    gvol=np.array([r['voxels']['G']*r['voxel_volume_mm3'] for r in rows])
    ranges['G_volume_mm3']={'min':float(gvol.min()),'median':float(np.median(gvol)),'max':float(gvol.max())}
    selected_geometry_caveats=sorted(set(g_fov)|{r['case_id'] for r in rows if r['G_components_6']>1})
    result={'warning_counts':dict(warning_counts),'C_FOV_contact_cases':c_fov,
            'G_FOV_contact_cases':g_fov,'G_multicomponent_cases':multig,'ranges':ranges,
            'case_count_check':True,'input_scope_hash':sha(OUT/'scope.json'),
            'geometry_caveat_cases_not_excluded':selected_geometry_caveats,
            'figure_review_suggested_ids':sorted(set(['002','003','004']+selected_geometry_caveats[:3]))}
    save('descriptive_summary.json',result)
    warning_table='\n'.join(f'| {k} | {v} |' for k,v in sorted(warning_counts.items())) or '| 无 | 0 |'
    multitable='\n'.join(f"| {r['case_id']} | {r['components_6']} | {r['largest_fraction']:.8%} | {r['nonlargest_voxels']} |" for r in multig) or '| 无 | — | — | — |'
    r=ranges
    decision=('没有发现精确完整mask的跨训练/验证重复。' if not summary['cross_train_validation_duplicate_groups']
              else '存在精确完整mask的跨训练/验证重复，未来模型划分须先处理；本轮不改变划分。')
    text=f'''# SkullFix 拟使用来源：批量实体几何 QC 报告 v1

日期：2026-11-02。本机 CPU，原始数据只读；没有训练、GPU、服务器操作、缺损重造或点云重采样。

## 结论

在既有划分的80个训练病例和10个验证病例中，90组C/D/G均通过实体互补、同物理坐标和非空共享切壁逐面配对检查。270个NRRD前后SHA256一致，进程退出码0。10个保留测试病例的几何内容未读取。{decision}

因此，就本范围的**实体分割一致性**而言，没有发现必须通过重新制造缺损修复的问题。可以沿用原始体素实体缺损，并按已确定的新任务定义分别提取残颅完整边界及缺失骨块完整边界。不是把旧点云直接删除一片区域，也不把旧4096点监督自动当成本次完整边界目标。

这不是解剖真值、缺损临床真实性、全颅无截断、内外板独立覆盖或训练准入认证。警告没有被删除或修补；其中缺失骨块触及FOV、碎片连通性等会影响后续任务解释，应与下述逐例材料一起使用。

## 固定范围与方法

- 来源：`E:/dataset/SkullFix/extracted/training_set`，按`pointcloud_defective_norm/splits.json`和`manifest.jsonl`冻结。原摘要D盘路径未当成可执行路径；本机E盘实际路径逐项确认。
- 仅使用现有train/val身份，共90例；没有新增source/fold划分，也没有读取旧NPZ点云。test10例仅使用身份元数据作集合互斥检查。
- 解码前核对文件哈希；检查NRRD尺寸、方向矩阵、origin和space约定。仅接受显式二值标签，不将灰度CT自动阈值化。
- 逐体素检查`C = D ∪ G`、`D ∩ G = ∅`，并要求三实体非空。
- 在六邻接方向独立枚举D→G、G→D邻接；用轴编号、方向分组及二倍整数面中心建立精确共享切壁键，逐面配对。物理面面积由方向向量叉积获得，两侧物理法向相反。
- 统计D/G全部暴露体素面，包括FOV边界面；G按6邻接统计连通成分。切壁是实体相邻面，不是“距稀疏implant点2mm”的代理。
- 用完整C的形状及二值内容指纹检查已读取90例的精确重复。不能识别同患者不同裁剪、近似重复或重采样版本；不能证明与未读取test几何无重复。
- 全部90例按固定规则生成三轴剖面：位置为G体素包围盒中点。图像按各平面物理间距保持比例，轴是原生体素方向，不强行命名为统一解剖方向。剖面没有灰度CT信息。

## 实测结果

| 核验项 | 结果 |
|---|---|
| train / val / test payload | 80 / 10 / 0 |
| C/D/G互补及互斥 | 90/90通过，重叠与异或不一致体素均0 |
| C/D/G物理网格一致 | 90/90通过 |
| 非空共享切壁逐面配对及反向法向 | 90/90通过 |
| 原始文件哈希不变 | 270/270 |
| 已读取完整mask的精确重复组 | {len(summary['exact_duplicate_complete_groups'])} |
| 跨train/val精确重复组 | {len(summary['cross_train_validation_duplicate_groups'])} |
| 剖面图生成数 | {summary['sections_generated']} |

| 描述量 | 最小 | 中位数 | 最大 |
|---|---:|---:|---:|
| 共享切壁面数 | {r['shared_J_faces']['min']:.0f} | {r['shared_J_faces']['median']:.0f} | {r['shared_J_faces']['max']:.0f} |
| 共享切壁面积 mm² | {r['shared_J_area_mm2']['min']:.3f} | {r['shared_J_area_mm2']['median']:.3f} | {r['shared_J_area_mm2']['max']:.3f} |
| 缺失骨块体积 mm³ | {r['G_volume_mm3']['min']:.3f} | {r['G_volume_mm3']['median']:.3f} | {r['G_volume_mm3']['max']:.3f} |

面积基于暴露体素面的阶梯表面，不是平滑解剖曲面面积；连通性是6邻接定义，不把微小成分自动认定为错误组织。

## 视野与连通性警告

| 警告类型 | 病例数 |
|---|---:|
{warning_table}

完整C接触FOV的病例数为{len(c_fov)}，G接触FOV的病例数为{len(g_fov)}。前者说明记录中的骨组织碰到图像边界，不能自动称整颅完整；但不等于切除骨块也被截断。后者直接涉及缺失目标在原始视野之外是否还有结构，不能凭互补通过就忽略。任何FOV接触都只是几何事实，不能单凭本轮确定临床可用性。

G接触FOV的病例：{', '.join(g_fov) if g_fov else '无'}。

| G多成分病例 | 6邻接成分数 | 最大成分占G体素比例 | 其余成分合计体素数 |
|---|---:|---:|---:|
{multitable}

原始成分全部保留，无自动删点、去组件、填孔、平滑或重新采样。包围盒余量、每方向FOV接触量与原生剖面见逐例JSON及PNG。90张图的生成不等于90例独立解剖审阅。本轮实际视觉查看了{', '.join(visual_ids)}的三向剖面，观察范围与限制另见`visual_review_v1.json`及其addendum；不是专家影像标注。微小成分的数量来自体素连通性统计，不能声称在上述中点剖面上已逐个辨认。

## 对“是否修改缺损构造”的决定

本范围**不需要仅为实体一致性而重造SkullFix缺损，也不需要用大规模训练认证几何**。保留现有体素C/D/G及原始身份，后续表面表示以∂D为输入、∂G为目标，其中∂G包含原生面E和与D相接的新切壁J。

如需新训练，首先继承本轮完整警告清单并明确数据用途；本轮没有授权新训练、测试集开放或病例筛选。此决定不表示SkullFix与SkullBreak的切除分布已统一，也不表示MUG实体构造已完成。下一个独立科研问题仍是采样与有限点数是否充分表达这些边界，不能以几何互补替代覆盖证据。

## 验证、资源与产物

六项人工几何检查通过：实体互补、面键配对、各向异性面积、暴露面计数、重叠拒绝、旋转后的物理法向/面积。它们验证本批计算需要的有限合同，不是完整P3或临床认证。

批次耗时{summary['elapsed_seconds']:.2f}秒；RSS检查点最大读数{summary['sampled_RSS_max_bytes']:,} bytes，非连续真实峰值。预算45分钟、单例180秒、监测RSS8GiB、输出200MiB。失败即停，无自动修复或重跑。主体成功执行一次，stdout及独立退出码保留。

入口`skullfix_batch_geometry_qc_v1.py`；结果`scope.json`、`summary.json`、`descriptive_summary.json`、`case_summary.csv`、`cases/`、`sections/`、`synthetic_checks.json`、`process_result.json`。最终清单绑定本报告和相关脚本/日志。模型/optimizer/GPU调用0，原始数据写入0，新点集0。
'''
    with (OUT/'report_zh_v1.md').open('x',encoding='utf-8') as f: f.write(text)
    manifest={str(p.relative_to(OUT)):{'sha256':sha(p),'bytes':p.stat().st_size}
              for p in sorted(OUT.rglob('*')) if p.is_file()}
    external=[Path(__file__),BASE/'skullfix_batch_geometry_qc_v1.py',BASE/'skullfix_batch_geometry_qc_20261102_v1.stdout.log']
    save('artifact_manifest.json',{'files':manifest,'external_artifacts':{str(p):{'sha256':sha(p),'bytes':p.stat().st_size} for p in external}})
    print(json.dumps(result,ensure_ascii=True,indent=2))

if __name__=='__main__': main()
