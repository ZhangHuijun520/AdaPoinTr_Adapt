"""Freeze the8case visual interpretation and offline payload checks; no new model calls."""
import base64,hashlib,html,json,math,re
from pathlib import Path
B=Path(__file__).resolve().parent;N=B/'sampling_model_AB_foldC_seed0_20261103_v1/paired_development_eval_v1';V=N/'geometry_review_8cases_v1'
ARMS=['V1','Morton_area_stratified8k'];IDS=['train__'+s+'__'+d for s in ['051','053','013','041'] for d in ['bilateral','frontoorbital']]
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(n,text):
 with (V/n).open('x',encoding='utf-8',newline='\n') as f:f.write(text)
def payload(text):
 pos=text.index('Plotly.newPlot(')+len('Plotly.newPlot(');decoder=json.JSONDecoder();result=[]
 for k in range(4):
  while text[pos].isspace() or text[pos]==',':pos+=1
  value,offset=decoder.raw_decode(text[pos:]);result.append(value);pos+=offset
 return result
def count(a):
 if isinstance(a,list):return len(a)
 assert isinstance(a,dict) and 'bdata' in a and 'dtype' in a
 return len(base64.b64decode(a['bdata']))//int(a['dtype'][1:])
def main():
 raw=json.loads((V/'selected_case_geometry_diagnostics_v1.json').read_bytes());revision=json.loads((V/'static_layout_v2/selected_case_geometry_diagnostics_v1.json').read_bytes())
 assert [r['case_id'] for r in raw['cases']]==IDS and raw['cases']==revision['cases'];cases={r['case_id']:r for r in raw['cases']}
 checks=[]
 for cid in IDS:
  page=(V/(cid+'.html')).read_text(encoding='utf-8');pid,traces,layout,config=payload(page)
  assert len(traces)==8 and count(traces[3]['x'])==count(traces[7]['x'])==8192
  for index in [3,7]:assert count(traces[index]['marker']['color'])==8192 and traces[index]['marker']['cmin']==0 and traces[index]['marker']['cmax']==20
  # Plotly scene domains must differ for side-by-side placement; compare geometry only.
  assert all(layout['scene'][k]==layout['scene2'][k] for k in ['xaxis','yaxis','zaxis','aspectmode','camera']) and 'scene2.camera' in page and 'scene.camera' in page
  srcs=re.findall(r'<script[^>]+src="([^"]+)"',page);assert srcs==['plotly.min.js'] and (V/srcs[0]).is_file()
  assert (V/'static_layout_v2'/(cid+'.png')).is_file()
  checks.append(dict(case_id=cid,interactive_8_traces=True,both_predictions_8192=True,same_camera_range_color=True,local_JS_only=True,PNG_layout_v2_exists=True))
 scope=json.loads((V/'frozen_visual_review_scope_v1.json').read_bytes());assert scope['cases']==IDS
 bysource=json.loads((N/'paired_scores_v1/paired_comparison.json').read_bytes())['comparison']['metrics']['E_P95_mm']['source_deltas'];source_delta={r['source_id']:r['delta'] for r in bysource}
 notes={
 'train__051__bilateral':'两臂整体落在颅盖目标区域。Morton壳面内部偏离／散点尾部更多：反向中位数3.36 mm，P95 11.88 mm；>20 mm仅0.85%，不是整块远离GT。E/J均略退化。',
 'train__051__frontoorbital':'Morton整块骨片落在远离额眶GT的位置，8192点全部距参考>20 mm；反向中位数120.93 mm、质心差132.96 mm。主要是大范围位置／形态错误，不能解释为少数离群或仅切壁误差。V1大体定位正确，但仍有局部壳面及尾部误差。',
 'train__053__bilateral':'两臂整体位置合理，Morton的E和J指标均改善，远端尾部略减；说明来源053并非所有缺损都失败。仍能看到预测分布偏离真实薄壳及边缘，不能按单视角认定内外板已正确重建。',
 'train__053__frontoorbital':'Morton再次形成远离目标的完整点簇，全部预测点>20 mm；反向中位数103.48 mm、质心差121.54 mm。是整块位置／形态错误；V1相对定位正确，局部与尾部误差仍存在。',
 'train__013__bilateral':'两臂主要处于正确颅盖位置。Morton的E/J和反向距离略差，>20mm比例0.27%；属于局部壳面／边缘和有限散点差异，不是整块大范围定位错误。',
 'train__013__frontoorbital':'V1整块远离目标，全部点>20 mm；Morton明显更接近但仍有67.85%点>20 mm、反向中位数25.70 mm。相对改善不等于重建成功，Morton仍有大范围位置／形态偏差。',
 'train__041__bilateral':'两臂整体位于目标颅盖。Morton的E/J覆盖尾部改善明显，J P95 7.42→2.84 mm，但反向P95 3.80→7.18 mm变差，>20mm约0.17%。是接口覆盖与少量散点／局部形态间的权衡，不是所有几何指标同时改善。',
 'train__041__frontoorbital':'V1整块严重偏离，全部点>20 mm；Morton大幅改善，但仍有约10.35%点>20 mm，E/J P95仍为13.85／17.44 mm。残余是较大范围位置／形态及尾部误差，尚不属于只差毫米级切壁微调。'}
 lines=['# V1／Morton固定8例：几何可视化审阅报告 v1','',
 '**最重要发现：本次严重回退／改善主要涉及骨块整体位置与形态错误，而不是单纯contact rim采样不足。该错误在两臂都出现。** Morton在051／053的frontoorbital失败，V1在013／041的frontoorbital失败；双侧缺损则主要呈现较局部的壳面、接口覆盖及散点权衡。', '',
 '## 固定范围与实际操作','',
 '按此前报告预先固定4来源051／053（来源均值退化）与013／041（来源均值改善），各看bilateral与frontoorbital，共8例。不根据本轮图像换病例、位置、视角或阈值。读取各例既有8k输入、共同GT8192、两个已冻结预测和A1/A2参考；没有服务器操作、模型加载、新forward或训练，没有解压或写入长期备份目录。', '',
 '两模型在物理mm同框比较，未配准、平移、旋转、重采样或剔除预测点。3D范围由GT与两预测共同确定，保留所有8192个预测点，包括远端失败点。误差色标固定0–20 mm，超过20只饱和显示，原始距离和hover保留；20mm是展示尺度，不新增临床阈值或正式gate。切壁差值色标固定±20mm。', '',
 '新增诊断只计算这8例的既有预测到完整A2参考距离、A1 E/J距离、质心差与薄层点云投影。E/J P95与反向P95已与正式评分逐例对照一致。没有重跑105例统一评分或修改其结果。静态图v2仅修正共享色标布局，v1与v2的8例数值诊断逐项相同。', '',
 '## 图如何读','',
 '六面板依次为：全颅上下文D／GT／两预测；V1预测点→A2距离；Morton同口径距离；GT中位Y±2mm薄层的XZ点投影；E/J面积加权距离CDF；GT切壁J上Morton−V1的有向距离差。蓝色差值是Morton较近，红色较远。3D交互双面板共享初始坐标范围、相机和色标，并提供联动旋转与点距离hover。灰色上下文用共同V1采样的D，不冒称原始完整体素或STL。', '',
 '薄层图不是CT切片，也不是精确mesh截交线；离散点有限，不在层内不表示几何不存在。未给内外板独立解剖标签，因此不能由这些图认证板厚或内外板分别重建正确。质心差只作点分布诊断，不是估计出的刚体平移，也没有用它纠正结果。', '',
 '## 四例额眶缺损：大范围错误','',
 '| 病例 | 模型 | E P95 mm | J P95 mm | 预测→参考中位数 mm | >20mm点比例 | 质心差 mm |','|---|---|---:|---:|---:|---:|---:|']
 for cid in IDS:
  if not cid.endswith('frontoorbital'):continue
  for arm,label in zip(ARMS,['V1','Morton']):
   d=cases[cid]['diagnostics'][arm];v=d['official_metrics'];lines.append(f"| {cid.split('__')[1]}额眶 | {label} | {v['E_P95_mm']:.2f} | {v['J_P95_mm']:.2f} | {d['reverse_median_mm']:.2f} | {100*d['reverse_fractions']['20']:.2f}% | {d['centroid_offset_norm_mm']:.2f} |")
 lines+=['',
 '051和053的Morton失败点并非围绕正确骨块附带的少量杂点，而是整个预测点簇远离GT。013和041的V1同样如此，说明不能归因于Morton独有的某个工程失败。Morton在013／041虽相对大幅改善，仍有明显整体或分布尾部偏差，不应称“高精度接口恢复”。', '',
 '## 每例审阅结论','']
 for cid in IDS:
  lines+=['### '+cid,'',notes[cid],'',f"[离线双面板3D]({cid}.html) · [修正布局的六面板图](static_layout_v2/{cid}.png)",'']
 lines+=['## 双侧缺损：局部壳面、接口及尾部差异','',
 '| 来源（bilateral） | E P95 V1→Morton mm | J P95 V1→Morton mm | 反向P95 V1→Morton mm |','|---|---:|---:|---:|']
 for sid in ['051','053','013','041']:
  d=cases['train__'+sid+'__bilateral']['diagnostics'];a=d['V1'];b=d[ARMS[1]]
  lines.append(f"| {sid} | {a['official_metrics']['E_P95_mm']:.2f}→{b['official_metrics']['E_P95_mm']:.2f} | {a['official_metrics']['J_P95_mm']:.2f}→{b['official_metrics']['J_P95_mm']:.2f} | {a['reverse_p95_mm']:.2f}→{b['reverse_p95_mm']:.2f} |")
 lines+=['',
 '这些双侧病例没有呈现整块远离目标的模式；主要差异位于壳面分布、接口覆盖和预测散点尾部。051／013的Morton局部退化，053的Morton较好，041则E/J改善但反向尾部变差。因而本组既不是“全由几个离群点造成”，也不是“全由切壁密度造成”，必须分开读有向覆盖与反向离群。', '',
 '## 这些额眶错误对来源均值的贡献','',
 '以下仅按已冻结来源均值和已选择的额眶病例计算代数贡献，不删除病例、不修改主结果。每来源五缺损等权，因此额眶病例差值的1/5进入该来源均值。', '',
 '| 来源 | 来源E P95差值 mm | 额眶病例差值 mm | 额眶对来源均值贡献 mm |','|---|---:|---:|---:|']
 for sid in ['051','053','013','041']:
  cid='train__'+sid+'__frontoorbital';d=cases[cid]['diagnostics'];delta=d[ARMS[1]]['official_metrics']['E_P95_mm']-d['V1']['official_metrics']['E_P95_mm']
  lines.append(f"| {sid} | {source_delta['train:'+sid]:+.3f} | {delta:+.3f} | {delta/5:+.3f} |")
 lines+=['',
 '这说明本次选中来源的明显正／负差异，很大程度上由额眶骨块是否被放在正确区域驱动。它不能用来估计105例中此类错误的总体发生率；8例本来就是按先前结果挑选的解释性病例，且尚未审阅这4来源的其余缺损形态。', '',
 '## 可以和不可以下的结论','',
 '可以确认：当前模型端存在与精细切壁吻合不同层级的大范围目标骨块定位／形态错误；仅增加输入接口点支持，不足以保证在不同缺损位置正确补出骨块。输入几何改善未稳定转化为模型收益的判断仍成立，且现在知道部分均值差异来自完整骨片级错误。', '',
 '仍不能确认：错误具体发生在FPS、proxy、编码器、查询中心、decoder或训练优化哪一步。不同病例在相同冻结数据/权重链下错误模式不同，不能凭图像直接诊断某个模块，更不能据此擅自做配准修正或删病例。单位和D-only逆归一化按冻结记录一致；这降低了统一缩放/平移错误的解释力，但本次不替代对科研输入—目标—输出空间合同的完整原因调查。', '',
 '下一科研问题应优先转为“模型是否可靠利用缺损位置条件，正确放置缺失骨块”，随后才是局部contact rim的毫米级修整。建议先围绕这8例审阅既有模型的空间输出合同与缺损位置条件化机制，形成一个最小科研假设；不继续扫描采样参数，不直接新增训练、定位器或通用审计框架。V1仍为当前默认，但不应被理解为已达到可靠高精度定位。', '',
 '## 交付与验证限制','',
 '交付8张六面板PNG（推荐static_layout_v2）、8个离线Plotly双面板HTML、共享本地plotly.min.js、数值诊断JSON及源文件哈希回读凭据。已实际查看8例静态图，并检查修正色标布局的代表图；HTML逐例核验8trace、两模型各8192点、共享相机/坐标/色标、联动脚本及本地JS依赖。未自动启动浏览器执行交互事件，因此结构核验不冒称全浏览器兼容性测试。', '',
 '全部输入及原评分文件哈希回读保持一致；本轮无新预测、无权重读取、无服务器或GPU操作。']
 save('geometry_review_report_zh_v1.md','\n'.join(lines)+'\n')
 header='<!doctype html><meta charset="utf-8"><title>固定8例几何审阅</title><style>body{font:16px system-ui;max-width:1400px;margin:30px auto;background:#f4f6f8;color:#142c3e}section{background:white;border-radius:12px;padding:20px;margin:22px 0}img{width:100%}p{line-height:1.7}a{color:#096aaa}</style><h1>固定8例几何审阅：整体骨片错误与局部接口误差</h1><p>重要：两臂在不同额眶病例都存在整块位置错误。本组按先前结果选定，只作解释，不估计总体错误率、不剔除病例。图中剖面为点云薄层投影，不是CT；所有预测点保留，无配准。</p><p><a href="geometry_review_report_zh_v1.md">中文审阅报告</a> · 交互HTML与plotly.min.js须保留同目录，完全离线可用。</p>'
 for cid in IDS:header+='<section><h2>'+cid+'</h2><p>'+html.escape(notes[cid])+'</p><p><a href="'+cid+'.html">打开联动双面板3D</a> · <a href="static_layout_v2/'+cid+'.png">打开原尺寸六面板图</a></p><img src="static_layout_v2/'+cid+'.png" loading="lazy"></section>'
 save('review_index_v2.html',header)
 receipt=dict(status='FIXED8_CASE_VISUAL_REVIEW_COMPLETED',checks=checks,all8_static_cases_viewed=True,representative_layout_v2_viewed=True,layout_v1_v2_diagnostics_equal=True,HTML_runtime_browser_tested=False,selected_official_metrics_reproduced=True,unmodified_prediction_geometry=True,server_calls=0,model_calls=0,new_forward_calls=0,all105_scoring_rerun=False,QA_checker_revision='First metadata check incorrectly compared Plotly scene domains,which differ by panel placement; corrected to compare camera/axis ranges/aspect only. Figures and diagnostic data unchanged.',case_notes=notes,report_sha256=h(V/'geometry_review_report_zh_v1.md'))
 with (V/'visual_QA_receipt_v1.json').open('x') as f:json.dump(receipt,f,indent=2,ensure_ascii=True)
 files=[dict(name=str(p.relative_to(V)).replace('\\','/'),bytes=p.stat().st_size,sha256=h(p)) for p in sorted(V.rglob('*')) if p.is_file()]
 with (V/'final_delivery_manifest_v1.json').open('x') as f:json.dump(dict(status=receipt['status'],files=files),f,indent=2)
 print(json.dumps(dict(status=receipt['status'],case_count=8,interactive_HTML=8,primary_finding='Whole-fragment placement/shape errors in selected frontoorbital cases, present in both arms',report_sha256=receipt['report_sha256'],new_model_calls=0)))
if __name__=='__main__':main()
