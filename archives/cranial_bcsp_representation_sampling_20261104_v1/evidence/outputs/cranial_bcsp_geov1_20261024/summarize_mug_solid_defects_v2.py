# -*- coding: utf-8 -*-
"""Finalize already-computed MUG solid-cut results. Does not read raw geometry."""
import collections
import csv
import hashlib
import html
import json
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

BASE=Path(__file__).resolve().parent
OUT=BASE/'mug_solid_defects_v2_20261102'

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()

def dump(name,obj):
    with (OUT/name).open('x',encoding='utf-8') as f:
        json.dump(obj,f,indent=2,ensure_ascii=False,allow_nan=False)

def main():
    s=json.loads((OUT/'summary.json').read_text(encoding='utf-8'))
    p=json.loads((OUT/'process_result.json').read_text(encoding='utf-8'))
    scope=json.loads((OUT/'scope.json').read_text(encoding='utf-8'))
    if p['exit_code']!=0 or (OUT/'failure.json').exists():raise RuntimeError('batch failed; no success report')
    rows=[json.loads(q.read_text(encoding='utf-8')) for q in sorted((OUT/'cases').glob('*.json'))]
    if len(rows)!=100 or {r['source_id'] for r in rows}!={e['source_id'] for e in scope['entries']}:
        raise ValueError('source set/count mismatch')
    solids=[r for r in rows if 'solid_path' in r]
    eligible=[r for r in solids if r['research_geometry_eligible']]
    folds={f:{'intended_sources':sum(r['fold']==f for r in rows),
              'solids':sum(r['fold']==f for r in solids),
              'geometry_candidates':sum(r['fold']==f for r in eligible)} for f in 'ABCD'}
    diagnostics=[]
    boundary_margin_crossings=[]
    for r in solids:
        q=OUT/r['solid_path']
        if q.stat().st_size!=r['solid_bytes'] or sha(q)!=r['solid_sha256']:
            raise ValueError('solid artifact hash mismatch')
        with np.load(q,allow_pickle=False) as n:
            if not np.array_equal(n['C_bits'],n['D_bits']|n['G_bits']) or np.any(n['D_bits']&n['G_bits']):
                raise ValueError('saved C/D/G Boolean contract')
            bits=int(np.prod(n['shape']))
            counts={role:int(np.unpackbits(n[role+'_bits'],bitorder='little',count=bits).sum()) for role in ['C','D','G']}
            if counts!=r['voxels']:raise ValueError('saved voxel counts mismatch')
            plane_spacing=1/np.linalg.norm(np.linalg.inv(n['directions']),axis=0)
            # Stored bbox bounds are voxel centers. The union-of-voxels boundary
            # extends another half voxel toward each FOV plane.
            boundary_margin=float(np.min(np.array(r['G_FOV_margin_mm'])-.5*plane_spacing[:,None]))
        if r['research_geometry_eligible'] and boundary_margin<5:
            boundary_margin_crossings.append(r['source_id'])
        diagnostics.append({'source_id':r['source_id'],'solid_hash_verified':True,'saved_counts_verified':True,
                            'minimum_G_voxel_boundary_FOV_margin_mm':boundary_margin})
    exact_groups=collections.defaultdict(list)
    for r in solids:exact_groups[r['raw_C_fingerprint']].append({'source_id':r['source_id'],'fold':r['fold']})
    duplicates=[v for v in exact_groups.values() if len(v)>1]
    warnings=collections.Counter(w for r in solids for w in r['warnings'])
    ranges={}
    for name in ['J_faces','J_area_mm2','G_volume_mm3','G_to_C_volume_fraction','minimum_G_FOV_margin_mm']:
        a=np.array([r[name] for r in solids])
        ranges[name]=None if not len(a) else {'min':float(a.min()),'median':float(np.median(a)),'max':float(a.max())}
    component_stats={}
    for group in ['raw_foreground_components','G_components']:
        component_stats[group]={}
        for name in ['count_6','largest_fraction']:
            a=np.array([r[group][name] for r in solids])
            component_stats[group][name]=(None if not len(a) else
                {'min':float(a.min()),'median':float(np.median(a)),'max':float(a.max())})
    analysis={'source_status_counts':s['status_counts'],'fold_counts':folds,
              'source_rejection_reasons':s['source_rejection_reasons'],'warnings':dict(warnings),
              'constructed_solid_ranges':ranges,'exact_C_duplicate_groups_among_constructed_sources':duplicates,
              'component_statistics_not_noise_accuracy':component_stats,
              'every_saved_solid_hash_count_and_partition_verified':True,'verification':diagnostics,
              'center_based_5mm_gate_but_boundary_margin_below_5mm':boundary_margin_crossings,
              'formal_high_precision_training_ready':False,
              'remaining_scientific_limits':['raw foreground bone anatomy / artifacts',
                'historical geometric cutter is not a calvarial anatomical label',
                'explicit original-STL frame is not independent whole-mask/clear-STL registration certification',
                'geometry-selected subset differs from original100; no balanced fourfold assertion']}
    dump('batch_verification_and_analysis.json',analysis)
    fields=['source_id','fold','status','research_geometry_eligible','formal_training_eligible','reason',
            'C_voxels','D_voxels','G_voxels','J_faces','J_area_mm2','G_E_faces','G_component_count6',
            'G_largest_component_fraction','minimum_G_FOV_margin_mm','solid_path','solid_sha256']
    with (OUT/'source_disposition.csv').open('x',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for r in rows:
            d={k:r.get(k,'') for k in fields}
            for role in ['C','D','G']:d[role+'_voxels']=r.get('voxels',{}).get(role,'')
            d['G_component_count6']=r.get('G_components',{}).get('count_6','')
            d['G_largest_component_fraction']=r.get('G_components',{}).get('largest_fraction','')
            w.writerow(d)
    # A minimal review gallery, no server, scripts, controls, or source modification.
    cards=[]
    (OUT/'review_sections').mkdir(exist_ok=False)
    caption_fixes=[]
    for r in rows:
        image=r.get('section',{}).get('path')
        if image:
            original=OUT/image
            corrected=OUT/'review_sections'/original.name
            # The shared SkullFix plotting helper has a dataset-specific title.
            # Correct only the title in separate copies; never rerun or edit geometry.
            im=Image.open(original).convert('RGB')
            draw=ImageDraw.Draw(im)
            draw.rectangle((0,0,im.width,31),fill='white')
            font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',17)
            draw.text((12,10),f"MUG500+ {r['source_id']}: raw-C solid cut, native-grid sections at G bbox midpoints",fill='black',font=font)
            im.save(corrected)
            caption_fixes.append({'source_id':r['source_id'],'original':image,
                                 'corrected':str(corrected.relative_to(OUT)),
                                 'correction':'dataset title only; geometry pixels below y=31 unchanged'})
            image=str(corrected.relative_to(OUT))
        detail=(f"J area={r['J_area_mm2']:.2f} mm²; G components={r['G_components']['count_6']}; "
                f"largest={r['G_components']['largest_fraction']:.3%}; FOV margin={r['minimum_G_FOV_margin_mm']:.2f} mm"
                if 'solid_path' in r else r.get('reason',''))
        cards.append('<article><h2>'+html.escape(r['source_id']+' | '+r['status'])+'</h2><p>'+html.escape(detail)+
                     '</p>'+('<img loading="lazy" src="'+html.escape(image)+'">' if image else '')+'</article>')
    dump('figure_caption_correction.json',{'reason':'reused plotting helper had literal SkullFix title; original case IDs/data were MUG',
                                         'corrections':caption_fixes,'geometry_recomputed':False})
    with (OUT/'review_gallery.html').open('x',encoding='utf-8') as f:
        f.write('<!doctype html><meta charset="utf-8"><title>MUG solid-cut review</title><style>body{font-family:sans-serif;max-width:1550px;margin:24px auto;padding:0 16px;background:#f5f6f8}article{background:white;padding:16px;margin:18px 0;border:1px solid #ddd}img{width:100%}h2{font-size:18px}</style><h1>MUG v2: 100-source disposition and solid-cut sections</h1><p>Raw binary foreground retained. Geometric cutters are not anatomical region labels. No expert GT certification. All rejection records retained.</p>'+''.join(cards))
    rejects='\n'.join(f'| {reason} | {count} |' for reason,count in sorted(s['source_rejection_reasons'].items())) or '| 无 | 0 |'
    status='\n'.join(f'| {name} | {count} |' for name,count in sorted(s['status_counts'].items()))
    foldtable='\n'.join(f"| {k} | {v['intended_sources']} | {v['solids']} | {v['geometry_candidates']} |" for k,v in folds.items())
    warningtable='\n'.join(f'| {name} | {count} |' for name,count in sorted(warnings.items())) or '| 无 | 0 |'
    candidates=', '.join(r['source_id'] for r in eligible) or '无'
    text=f'''# MUG500+ 实体缺损构造 v2：完整实施与批量结果

日期：2026-11-02。范围为既定D6 development100；不读取封存确认来源，不训练。

## 当前完成程度

**实体切除算法、原生物理坐标、完整C/D/G保存及共享切壁核验已实现，并完成100个固定开发来源的一次性处理。**生成{s['solids_written']}组实体；其中{s['research_geometry_eligible']}组通过本版5mm骨块周边FOV余量条件。每个来源都有通过或不准入记录，没有替换病例、调整切除参数、补洞、清理前景或重复尝试。

**这不等于已经建立经解剖验证的正式高精度训练集。**本批形式上的高精度GT训练准入数为0；原始二值前景含非骨伪影的风险、旧几何切除位置未必位于颅盖、坐标声明与独立全几何配准的区别仍明确保留。几何算法完成与上游GT可靠性是两件事，不能用程序运行成功替代后者。

## 1. 确定下来的缺损构造方法

以原始二值骨前景C为母版，原生体素中心在物理LPS空间中的位置为`x = index @ directions + origin`。令R为固定物理椭球，则：

`D = C & ~R`；`G = C & R`。

严格保留`C=D∪G`和`D∩G=∅`。完整骨组织边界依赖原始分割，不从外轮廓填成实心，不通过STL孔洞自动封口来猜测骨组织。

输入表面应从∂D提取，目标从∂G提取。∂G包括原生未知表面E及新形成的厚度方向接触切壁J。J由D/G相邻体素的共享物理面定义，两侧位置、面积相等，实体外法向相反。它不是旧稀疏implant点云附近的距离带，也不是仅一条外侧边线。

本批不做点云采样，避免把第三个问题“采样方法与点数”混入第二个问题“实体缺损”。后续可从保存实体一致地提取全部暴露边界及面来源。

## 2. 与旧流程和A0221 pilot的关系

旧MUG流程只按三角形质心删除原面片，没有新增连接内外层的切壁。v2在体素实体中进行Boolean切除，切壁来自真实D/G邻接，因此纠正了旧目标仅为缺失原面片的结构性差异。

每个来源只使用旧历史`ellipsoid_medium`的center/frame/radii，固定一次，不重新搜索部位。原STL须明确声明RAS/LPS，继而将旧切除参数变换到统一LPS；当前NRRD自己的affine和space用于体素世界坐标。无声明者不靠较小距离选择坐标。

这是一项可追溯的“相同历史几何切除参数、不同实体构造”的新版本；NRRD分割与clear STL并不保证逐面一致，因此它不是严格相同母版的单因素因果实验。历史参数可能位于颅底、面骨等区域；`medium`不是“颅盖”的解剖标签。

A0221旧pilot使用另一个固定ROI且比较raw与最大成分。本批A0221继承历史medium参数、保留raw全部前景，是不同实验，不能拿来直接覆盖旧pilot或声称前景已修好。原三例A0136/137/138的失败记录同样保留。

## 3. 固定范围、数据边界与前景处理

来源身份来自本机D6 development100锁；source级A/B/C/D身份继承，不重分折、不读取确认25、不扩展到500例或其他封存集合。读取ZIP中央目录确定精确NRRD成员，不解压整个归档。源文件只读；结果位于本机项目的新目录。

仅读取显式二值体（0/1或0/255，所有值均检查）；不把灰度NRRD按经验阈值分割为骨。二值分布只是格式证据，不是组织学准确性证明。

**全部原始前景保留。**没有最大成分过滤、组件删除、形态学开闭、填腔、平滑、自动封孔或ICP拟合。非最大成分可能是噪声、孤立骨、对角连接或其他结构，不能自动按噪声删除；相应风险在目标中原样存在并有数量记录。

## 4. 批量实测结果

| 状态 | 来源数 |
|---|---:|
{status}

| 不生成实体的来源原因 | 数量 |
|---|---:|
{rejects}

原始来源不合格按冻结规则记录一次，继续下一个独立来源；这是批处理的数据分流，不是失败后修复或重试。意外执行异常必须停止，不自动重跑。

通过FOV余量的几何候选来源：{candidates}。

| 继承fold | 原计划来源 | 已保存实体 | 通过本版FOV余量的候选 |
|---|---:|---:|---:|
{foldtable}

不能将减少后的来源数继续描述成旧100来源／四折各25来源的完整矩阵。没有为了平衡或结果更好重新分配fold。完整100条身份、来源原因、哈希、实体路径和指标在`source_disposition.csv`、`cases/`及`scope.json`。

## 5. 几何合同、视野余量与质量警告

所有已写实体均核验同网格的C/D/G互补及互斥，共享J的二倍整数面中心键逐项一致、物理法向相反。方向向量叉积给出面积；不能将各向异性体素或旋转仿射当作单位网格。保存后重新加载打包数组核对；汇总又独立核对每份实体SHA256、体素计数和Boolean关系。

冻结代码中的5mm余量精确定义为G体素中心包围盒到原图像六个体素面平面的最小物理距离，不要求整个椭球及其空气部分都在图像内。实体体素并集的最外面还比这些中心向外延伸半个体素；汇总已从保存affine独立计算扣除半体素后的真实体素边界余量。通过原中心余量条件但边界余量不足5mm的病例：{', '.join(boundary_margin_crossings) if boundary_margin_crossings else '无'}。原冻结判定未被事后改写。这是几何支持条件，不是临床安全阈值，也不证明该区域无分割缺失。未满足原冻结条件者保留实体用于审查，但不列入本版几何候选。

| 原始实体警告 | 已构造来源数 |
|---|---:|
{warningtable}

完整C触及FOV和G周边不足不是同一个问题。多成分数量也不是噪声率。所有生成病例均有局部统计和固定三轴剖面（非正交网格则明确跳过，避免错误比例）。图库`review_gallery.html`包含全部通过和失败病例，不按预测表现挑选。复用绘图函数的原图标题含固定SkullFix字样，已在独立`review_sections/`副本更正为MUG500+；原图及实体未改，未重算几何，标题更正记录见`figure_caption_correction.json`。

实际视觉查看了A0207、A0221、A0234三份原生剖面，范围与选择原因见`visual_review_v1.json`，不是100例全面专家审阅。A0207/A0234显示的切除部位并非单纯颅盖；A0221可见颅腔内大量分离前景。成分比例较高也不能自动替代分割准确性或颅盖位置确认。

## 6. 文件布局与复用

每份`solids/Axxxx__ellipsoid_medium__raw_CDG.npz`含：`C_bits,D_bits,G_bits,shape,directions,origin,cut_center_LPS,cut_frame_columns_LPS,cut_radii_mm`。

三个实体为C-order展开、`numpy.packbits(bitorder='little')`，尾部padding不属于体素。读取方式：

```python
with np.load(path, allow_pickle=False) as n:
    shape = tuple(n['shape'])
    count = int(np.prod(shape))
    C = np.unpackbits(n['C_bits'], bitorder='little', count=count).reshape(shape).astype(bool)
    D = np.unpackbits(n['D_bits'], bitorder='little', count=count).reshape(shape).astype(bool)
    G = np.unpackbits(n['G_bits'], bitorder='little', count=count).reshape(shape).astype(bool)
```

每个来源的J方向、面积、面数、法向及规范面键SHA256记录在同名JSON；需要完整J时，可按同一六邻接规则从D/G无歧义重建，不依赖点云近邻猜测。没有创建STL或将离散体素边界称作光滑连续解剖曲面。

## 7. 哪些问题已解决，哪些不能由生成器解决

| 问题 | 本轮决定 |
|---|---|
| 先删面还是先切实体 | 确定先在骨组织体中切除，再分别提取D/G完整边界 |
| 新暴露厚度方向壁面是否存在 | 已在生成实体中以非空共享体素面逐项核验 |
| 颅腔／已有孔道是否填实 | 不填，保留原始前景和背景 |
| 输出是什么 | ∂G完整边界，即E＋J；不是只有旧原生面片 |
| 是否有可恢复的批量实体资产 | 有，{s['solids_written']}组，含完整affine、切除参数及哈希 |
| 是否所有100例都成功 | 否；按表逐例保留原因，未补换来源 |
| 是否为经确认的颅盖缺损 | 尚未；历史几何方向不等于解剖区域标签 |
| 是否为高精度解剖GT训练集 | 尚未；不能用原始二值前景或互补通过替代分割质量确认 |

若下一阶段仅进行**明确披露原始分割局限的受控表示研究**，这些保存实体提供了可复用基础；但不得把当前原始前景目标误称为临床骨真值。若论文核心主张是高精度颅盖接口吻合，应先对拟用区域作有依据的前景及解剖区域确认，或获取同源可信分割。不能继续靠换阈值、换最大成分或扫描切除位置使结果看起来合格。

本轮不直接开展上述训练，也不自动冻结新的病例排除或四折训练合同。MUG未决质量问题不要求回滚已经通过的SkullFix／SkullBreak实体定义。

## 8. 执行、完整性与限制

主体一次执行，退出码{p['exit_code']}，耗时{s['elapsed_seconds']:.2f}秒；RSS检查点最大值{s['sampled_RSS_max_bytes']:,} bytes，非连续峰值。8项人工检查通过：实体互补、球壳切壁、颅腔不填、孤立前景不删、旋转各向异性坐标与独立公式一致、RAS/LPS等价、保存位运算及roundtrip。

构造来源的NRRD成员SHA256读取前后核对；ZIP大小/mtime按冻结元数据核对。没有重新计算约50GB全部ZIP的容器哈希，不能声称做过该验证。失败来源保留已读取成员的指纹证据。原数据写入、封存payload访问、模型/GPU、训练、新点云均为0。

脚本`mug_solid_defects_v2.py`和其精确几何依赖在`scope.json`绑定；汇总脚本及所有产物在最终`artifact_manifest.json`绑定。`batch_verification_and_analysis.json`记录保存数组独立复核、fold计数和精确内容重复检查；后者只覆盖已构造来源，不能认定与封存来源不存在近似重复。
'''
    with (OUT/'report_zh_v1.md').open('x',encoding='utf-8') as f:f.write(text)
    artifacts={str(q.relative_to(OUT)):{'bytes':q.stat().st_size,'sha256':sha(q)}
               for q in sorted(OUT.rglob('*')) if q.is_file()}
    external=[Path(__file__),BASE/'mug_solid_defects_v2.py',BASE/'mug_solid_defects_v2_20261102.stdout.log']
    dump('artifact_manifest.json',{'files':artifacts,'external_files':{str(q):{'bytes':q.stat().st_size,'sha256':sha(q)} for q in external}})
    print(json.dumps({'source_status_counts':s['status_counts'],'fold_counts':folds,'warnings':dict(warnings),
                      'formal_high_precision_training_ready':False},ensure_ascii=True,indent=2))

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');main()
