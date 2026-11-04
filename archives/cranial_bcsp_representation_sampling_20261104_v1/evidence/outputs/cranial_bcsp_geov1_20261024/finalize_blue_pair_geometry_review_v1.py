"""Freeze fixed-eight visualization QA and source-grounded interpretation."""
import base64,csv,hashlib,html,json,re
from pathlib import Path
B=Path(__file__).resolve().parent;N=B/'blue_pair_eval_v1';V=N/'geometry_review_8cases_v1'
ARMS=['Euclidean_elimination','surface_graph'];IDS=['train__'+s+'__'+d for s in ['081','042','051','013'] for d in ['bilateral','frontoorbital']]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(name,obj):
    with (V/name).open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2,allow_nan=False)
def save(name,text):
    with (V/name).open('x',encoding='utf-8',newline='\n') as f:f.write(text)
def plot_payload(text):
    pos=text.index('Plotly.newPlot(')+len('Plotly.newPlot(');decoder=json.JSONDecoder();result=[]
    for _ in range(4):
        while text[pos].isspace() or text[pos]==',':pos+=1
        value,offset=decoder.raw_decode(text[pos:]);result.append(value);pos+=offset
    return result
def count(a):
    if isinstance(a,list):return len(a)
    assert isinstance(a,dict) and 'bdata' in a and 'dtype' in a
    return len(base64.b64decode(a['bdata']))//int(a['dtype'][1:])
def main():
    raw=json.loads((V/'selected_case_geometry_diagnostics_v1.json').read_bytes());assert raw['status']=='FIXED_8_CASE_REVIEW_COMPLETE' and [x['case_id'] for x in raw['cases']]==IDS
    cases={r['case_id']:r for r in raw['cases']};checks=[]
    scope=json.loads((V/'frozen_visual_review_scope_v1.json').read_bytes());assert scope['cases']==IDS and scope['display']['registration'] is False
    receipt=json.loads((V/'source_readback_receipt_v1.json').read_bytes());assert receipt['status']=='ALL_SELECTED_INPUT_AND_FROZEN_SCORE_HASHES_STABLE'
    for r in receipt['files']:assert Path(r['path']).stat().st_size==r['bytes'] and sha(r['path'])==r['sha256']
    for cid in IDS:
        text=(V/(cid+'.html')).read_text(encoding='utf-8');_,traces,layout,_=plot_payload(text)
        assert len(traces)==8 and count(traces[3]['x'])==count(traces[7]['x'])==8192
        for k in [3,7]:assert count(traces[k]['marker']['color'])==8192 and count(traces[k]['customdata'])==8192 and traces[k]['marker']['cmin']==0 and traces[k]['marker']['cmax']==20
        assert all(layout['scene'][k]==layout['scene2'][k] for k in ['xaxis','yaxis','zaxis','aspectmode','camera']) and 'scene2.camera' in text and 'scene.camera' in text
        assert re.findall(r'<script[^>]+src="([^"]+)"',text)==['plotly.min.js'] and (V/'plotly.min.js').is_file()
        assert (V/(cid+'.png')).is_file() and cases[cid]['selected_official_metrics_reproduced'] and cases[cid]['prediction_geometry_not_modified']
        checks.append(dict(case_id=cid,both_predictions_8192=True,same_camera_range_color=True,camera_sync_script_present=True,offline_JS_only=True,static_figure_viewed=True,official_E_J_reverse_P95_reproduced=True))
    notes={
    'train__081__bilateral':'两臂主要位于目标颅盖范围，未见整块远离GT。图距离的E/J P95及反向P95均更差，J覆盖61.02%→41.17%，>20mm点均为0；主要是壳面分布与目标／切壁覆盖不足，不能归结为少数极远离群点。',
    'train__081__frontoorbital':'图距离预测形成远离额眶GT的完整点簇，8192点全部距完整A2参考>20mm，中位数88.36mm、质心差100.40mm；GT所在固定薄层没有该臂预测点。属于整块位置／形态错误。欧氏覆盖GT较好，但仍有反向尾部误差，不能称高精度完整恢复。',
    'train__042__bilateral':'两臂预测点大多靠近GT，但目标参考到预测的E/J P95仍高达12–19mm。薄层图可见部分GT轮廓未被覆盖；两臂切壁差值在不同位置方向相反。属于不完整形状／空间覆盖与局部边缘分布问题，不是整块远离GT，也不是只有几颗离群点。',
    'train__042__frontoorbital':'图距离预测有明显大范围形状／位置偏差，53.17%点距参考>20mm、中位数21.57mm，J覆盖88.90%→38.78%。它仍有局部重叠，不能描述为全部点失配，也不能缩小为切壁微调问题；欧氏整体更接近目标。',
    'train__051__bilateral':'两臂整体位于相近目标颅盖位置。图距离反向P95由7.93降至6.05mm，但J P95由6.44增至8.58mm、J覆盖34.87%→27.63%。预测点更贴近已有目标表面，同时目标切壁覆盖更差，是有向覆盖与反向尾部的权衡。',
    'train__051__frontoorbital':'欧氏预测整块远离额眶GT，全部点>20mm、中位数89.81mm、质心差99.31mm。图距离相对大幅改善，但仍有49.66%点>20mm、反向P95 38.65mm、J覆盖仅13.01%；相对改善并不等于重建合格。',
    'train__013__bilateral':'虽然来源013总体改善，本双侧病例图距离反而E/J P95更差，4.47→7.73mm、7.19→11.59mm。反向P95略好且>20mm比例很低，剖面和J差值提示形状分布／覆盖偏差；不能将来源级改善推广到该来源所有缺损。',
    'train__013__frontoorbital':'欧氏存在明显大范围位置／形态偏差，94.40%点>20mm，中位数36.63mm。图距离大幅改善到0.55%点>20mm，E/J P95为4.46／4.22mm；仍有反向P95 14.42mm及局部形状／边界余差，不认证内外板或临床接口准确。'}
    lines=['# 欧氏／表面图距离：固定8例几何可视化诊断 v1','',
    '日期：2026-11-04。**关键发现：本组额眶差异主要涉及完整骨片级位置／形态错误，且两臂均会出现；双侧病例还存在目标覆盖不足与局部切壁／壳面分布问题。不能只用“切壁点不够”或“少量离群点”解释这些差异。**','',
    '## 范围与方法','',
    '按事先固定范围，选来源081／042（来源均值退化）及051／013（改善），各bilateral和frontoorbital，共8例。只读取这些病例的既有两臂开发输入、共同GT8192、冻结预测和A1/A2参考。未读取权重、原始CT／NRRD或服务器；没有新forward、训练、采样参数扫描或105例重新评分。结果解释样本按既有结果选定，不能估计总体错误发生率或作为新无偏验证。','',
    '同病例两臂使用同世界坐标mm、相机、等比例坐标轴与共同范围，不配准、平移、旋转、修改或剔除预测点。所有8192个预测点保留。距离着色固定0–20mm，超过20仅色标饱和，hover和数值保留真实距离；2/10/20mm仅作既定显示诊断，未新增临床阈值／gate。J差值色标±20mm，蓝色图距离较近、红色较远。','',
    '每例六面板为：D／GT／两预测全局上下文；欧氏预测→A2距离；图距离同口径；GT中位Y±2mm的XZ点云薄层投影；A1 E/J面积加权距离CDF；J参考上的图−欧距离差XZ投影。灰色D用同一欧氏8k点集作为两面板共同上下文，不冒称原始完整体素边界；切壁J标签来自冻结G/D参考，不作为模型输入。','',
    '薄层不是CT切片或精确mesh截交线，层内无点不等于骨组织不存在；J投影可重叠不同深度。没有内外板独立解剖标注，不能用这些图认证板厚或双板重建。质心差是点分布诊断，不是拟合的刚体平移量，也没有被用于纠正预测。','',
    '选中8例的E/J P95和反向A2 P95重新计算以着色，均与正式评分匹配。所有输入及原评分文件大小／哈希回读保持一致。本轮没有修改正式评分指标、阈值或结论。','',
    '## 额眶病例：完整骨片级失配','',
    '| 病例 | 臂 | E95 mm | J95 mm | 反向中位数 mm | >20mm点比例 | 质心差 mm |','|---|---|---:|---:|---:|---:|---:|']
    for cid in IDS:
        if not cid.endswith('frontoorbital'):continue
        for arm,label in zip(ARMS,['欧氏','图距离']):
            d=cases[cid]['diagnostics'][arm];m=d['official_metrics'];lines.append(f"| {cid.split('__')[1]}额眶 | {label} | {m['E_P95_mm']:.2f} | {m['J_P95_mm']:.2f} | {d['reverse_median_mm']:.2f} | {100*d['reverse_fractions']['20']:.2f}% | {d['centroid_offset_norm_mm']:.2f} |")
    lines+=['','081额眶图距离臂与051额眶欧氏臂出现“整块点簇远离GT”，并非围绕正确骨片的少数杂点。042图距离、013欧氏也有大范围失配。051图距离虽好于欧氏，仍有广泛残余误差；013图距离接近目标，但仍存在局部形状和散点尾部。不能把改善臂一概认定为高精度成功。','',
    '## 双侧病例：覆盖与反向尾部不能混为一谈','',
    '| 来源 | E95 欧→图 mm | J95 欧→图 mm | 反向P95 欧→图 mm | J覆盖 欧→图 |','|---|---:|---:|---:|---:|']
    for sid in ['081','042','051','013']:
        a,b=[cases['train__'+sid+'__bilateral']['diagnostics'][arm] for arm in ARMS];ma=a['official_metrics'];mb=b['official_metrics']
        lines.append(f"| {sid} | {ma['E_P95_mm']:.2f}→{mb['E_P95_mm']:.2f} | {ma['J_P95_mm']:.2f}→{mb['J_P95_mm']:.2f} | {a['reverse_p95_mm']:.2f}→{b['reverse_p95_mm']:.2f} | {100*ma['J_coverage_2.0mm']:.2f}%→{100*mb['J_coverage_2.0mm']:.2f}% |")
    lines+=['','042双侧的预测→参考中位数约2mm，但E/J→预测P95可达约12–19mm，说明预测点靠近目标不代表覆盖完整目标。051与013的图距离反向尾部略好，却有向E/J误差或J覆盖更差。这类分布／覆盖失衡，与额眶整块偏移处在不同误差层级。','',
    '## 对来源均值差异的解释','',
    '下面仅列保存指标的代数贡献：同来源五缺损等权，额眶病例差值的1/5进入来源均值。没有删除病例或重新计算剔除后的主结果。','',
    '| 来源 | 来源E95图−欧 mm | 额眶病例Δmm | 额眶对来源均值贡献 mm |','|---|---:|---:|---:|']
    source_deltas=json.loads((N/'paired_scores_v1/paired_comparison.json').read_bytes())['comparison']['metrics']['E_P95_mm']['source_deltas'];sd={r['source_id']:r['delta'] for r in source_deltas}
    contribution=[]
    for sid in ['081','042','051','013']:
        c=cases['train__'+sid+'__frontoorbital']['diagnostics'];delta=c[ARMS[1]]['official_metrics']['E_P95_mm']-c[ARMS[0]]['official_metrics']['E_P95_mm']
        lines.append(f"| {sid} | {sd['train:'+sid]:+.3f} | {delta:+.3f} | {delta/5:+.3f} |")
        contribution.append({'source_id':'train:'+sid,'source_E_P95_delta_mm':sd['train:'+sid],'frontoorbital_E_P95_delta_mm':delta,'frontoorbital_contribution_to_source_mean_mm':delta/5})
    lines+=['','这些选中来源的明显正／负差异，有较大部分来自额眶骨片是否落在正确目标区域。没有审阅该105例全集，不能据本组报告整体定位失败率；也没有审阅每来源其余三类缺损的空间图像。','',
    '## 逐例诊断','']
    for cid in IDS:lines+=['### '+cid,'',notes[cid],'',f"[联动交互3D]({cid}.html) · [六面板PNG]({cid}.png)",'']
    lines+=['## 结论与下一科研问题','',
    '1. 采样输入局部支持的改善不足以保证缺失骨块被放在正确位置。优先级应区分：整体目标骨片放置／形态、完整目标覆盖、局部切壁精度；对整块远离目标的病例，只做contact rim毫米级修整不能解释当前主要误差。',
    '2. 两臂在不同额眶病例出现大范围错误，不能给图距离独有的某个工程环节或模型模块定责。现有同框、逆归一化和指标匹配减少了展示转换错误的可能，但没有完成输入—目标—模型输出空间合同的完整原因调查。',
    '3. 建议下一步先围绕本组固定病例只读审阅既有输入归一化、GT/输出空间合同及缺损位置条件如何进入模型，再提出一个最小模型假设。例如“当前模型对缺损位置的条件利用不稳定”可以作为待检验假设，而不是已证明原因。不要立即新增定位器、proxy修补、参数扫描或训练。',
    '4. 本组是事后解释性观察，不替代21来源等权主结果；不推翻完整骨组织边界、实体缺损和缺失骨块完整表面目标，也不证明更高输出点数会解决整体位置错误。保持本轮图距离没有整体主指标／接口优势的结论。','',
    '## 交付与质量检查','',
    '8张六面板PNG均已实际查看，图例／色标／坐标标签可读。8个HTML结构逐例核验：各8个trace，两臂预测各8192点，距离颜色与hover各8192值，共同相机／坐标范围／色标，并有相机联动脚本；只引用同目录plotly.min.js。未在浏览器实际执行交互事件，结构检查不冒称浏览器运行测试。','',
    '交互图保留预测点及GT全部8192点；J展示最多4000、静态J差值最多5000，采用等间隔索引仅用于显示，距离计算仍使用完整参考。显示20mm色标饱和不隐藏远端预测点，坐标范围由GT及两臂预测共同决定。','',
    '所有页面与plotly.min.js须保留在同目录以离线使用。本轮无服务器／GPU／模型调用，无新预测，未修改或解压长期备份归档，未重跑105例评分。']
    save('geometry_review_report_zh_v1.md','\n'.join(lines)+'\n')
    rows=[]
    for cid in IDS:
        for arm in ARMS:
            d=cases[cid]['diagnostics'][arm];m=d['official_metrics'];rows.append(dict(case_id=cid,arm=arm,E_P95_mm=m['E_P95_mm'],J_P95_mm=m['J_P95_mm'],J_coverage_2mm=m['J_coverage_2.0mm'],reverse_median_mm=d['reverse_median_mm'],reverse_P95_mm=d['reverse_p95_mm'],fraction_over20mm=d['reverse_fractions']['20'],centroid_offset_norm_mm=d['centroid_offset_norm_mm'],slab_predicted_points=d['slab_predicted_points']))
    with (V/'selected_diagnostics_v1.csv').open('x',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    header='<!doctype html><meta charset="utf-8"><title>欧氏／图距离：固定8例诊断</title><style>body{font:16px system-ui;max-width:1400px;margin:30px auto;background:#f4f6f8;color:#142c3e}section{background:white;border-radius:12px;padding:20px;margin:22px 0}img{width:100%}p{line-height:1.7}a{color:#096aaa}</style><h1>欧氏／图距离：固定8例几何诊断</h1><p>额眶病例存在完整骨片级位置／形态错误，两臂均可能发生；双侧还存在不完整覆盖及局部边缘差异。病例为事后固定解释样本，不估计总体错误率、不修改主结果。</p><p><a href="geometry_review_report_zh_v1.md">中文报告</a> · <a href="selected_diagnostics_v1.csv">16行数值诊断CSV</a>。点云剖面不是CT；不配准、保留全部预测点。交互图与plotly.min.js保留同目录可离线打开。</p>'
    for cid in IDS:header+='<section><h2>'+cid+'</h2><p>'+html.escape(notes[cid])+'</p><p><a href="'+cid+'.html">打开联动3D</a> · <a href="'+cid+'.png">打开原尺寸图</a></p><img src="'+cid+'.png" loading="lazy"></section>'
    save('review_index_v1.html',header)
    dump('visual_QA_receipt_v1.json',dict(status='FIXED8_CASE_VISUAL_REVIEW_COMPLETED',checks=checks,all8_static_cases_viewed=True,HTML_browser_runtime_tested=False,selected_official_metrics_reproduced=True,case_notes=notes,frontoorbital_contribution=contribution,source_hashes_readback_stable=True,registration=False,new_model_calls=0,new_predictions=0,all105_scoring_rerun=False,report_sha256=sha(V/'geometry_review_report_zh_v1.md')))
    dump('final_delivery_manifest_v1.json',dict(status='FIXED8_CASE_VISUAL_REVIEW_COMPLETED',files=[dict(name=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(V.iterdir()) if p.is_file()]))
    print(json.dumps({'status':'FIXED8_CASE_VISUAL_REVIEW_COMPLETED','static_figures':8,'interactive_pages':8,'new_predictions':0,'server_calls':0,'report_sha256':sha(V/'geometry_review_report_zh_v1.md')}))
if __name__=='__main__':main()
