"""Summarize observed source failure; never relabel it successful solid validation."""
from pathlib import Path
import csv,hashlib,json
N=Path(__file__).resolve().parent;R=N/'results'
data=json.loads((R/'results.json').read_bytes());scope=json.loads((N/'scope_v1.json').read_bytes())
assert data['source_count']==3 and data['admitted']==0 and data['defects_generated']==data['point_pairs_generated']==0
tests=json.loads((N/'artificial_CPU_tests_v1.json').read_bytes());assert tests['status']=='PASS' and tests['tests']==8
rows=[]
for r in data['cases']:
 n=r['nrrd'];s=n['scalar_statistics'];rows.append(dict(source_id=r['source_id'],status=r['status'],shape='x'.join(map(str,n['shape'])),minimum=s['minimum'],maximum=s['maximum'],unique_values=s['unique_values'],
  axis0_center_span_mm=n['physical_bounds']['axis_center_lengths_mm'][0],axis1_center_span_mm=n['physical_bounds']['axis_center_lengths_mm'][1],axis2_center_span_mm=n['physical_bounds']['axis_center_lengths_mm'][2],
  NRRD_SHA256=n['sha256'],clear_STL_SHA256=r['clear_stl']['sha256'],defects_generated=0,point_pairs_generated=0))
with (R/'source_summary_v1.csv').open('x',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
lines=['# MUG500+固定三来源实体缺损pilot：源准入结果报告 v1','',
 '日期：2026-10-29。固定来源：A0136、A0137、A0138。执行位置：本机CPU；不连接服务器、不使用GPU、不训练。','',
 '## 结论与实际完成程度','',
 '**三例源数据核查已完成，但没有一例通过“可直接切除的可信完整骨实体”准入，因此实体缺损生成及8k采样验证尚未执行。** 本轮不是成功生成三例新缺损，也不把源检查完成等同于构造验证成功。','',
 '已完成：三个精确NRRD成员的解码、体素值全量分布、affine及范围检查；三个clear STL的绑定哈希与包围盒核对；原始标量中心剖面；8项人工CPU测试。实际生成D/G实体0组、点云配对0组。','',
 '## 范围与方法','',
 '- 仅从既定A0136-A0140.zip读取A0136、A0137、A0138的同名NRRD内容，不解压整个数据包，不读取A0139／A0140几何。三份NRRD首次完整读取后固定成员SHA256，并在本轮再次读取核验不变；未冒称已匹配历史NRRD哈希。',
 '- NRRD按明确signed int16、gzip、NRRD第一轴最快顺序解析，严格核验声明形状／解码字节数／affine，不调用旧的values>0或values>0.5骨mask转换。',
 '- 全量统计65536个可能int16值的直方图，未按观察结果调阈值；二值取值本身也不被视为骨组织语义证明。',
 '- 三个现有clear STL按二进制记录流式读取；SHA与2026-10-23 scope一致。只比较顶点包围盒，不做ICP、轴翻转、缩放、平移、填洞或自动删组件。STL本身没有可信坐标系声明，包围盒比较不能替代配准或同源认证。',
 '- 保留原ellipsoid_medium的center／frame／radii，但未将其直接套在未认证的NRRD上；未重新选切除中心、病例或缺损参数。','',
 '```mermaid','flowchart LR',
 '    accTitle: MUG fixed three source admission',
 '    accDescr: Exact source files are checked before solid removal. All three currently stop at bone-mask and physical-correspondence admission.',
 '    src["固定三来源 NRRD 与 STL"] --> gate{"完整骨mask及物理对应可信？"}',
 '    gate -->|"本轮三例未通过"| stop["保留源证据；不生成D/G"]',
 '    gate -. "未来通过后" .-> cut["固定实体切除"]',
 '    cut -.-> qc["互补／切壁／8k采样QC"]','```','',
 '## 三来源实测','',
 '| 来源 | NRRD形状 | 标量范围 | 不同取值数 | 体素轴中心跨度mm | 准入 |','|---|---|---|---:|---|---|']
for row in rows:lines.append('| '+row['source_id']+' | '+row['shape']+' | '+str(row['minimum'])+'～'+str(row['maximum'])+' | '+str(row['unique_values'])+' | '+ ' / '.join(f'{row[k]:.3f}' for k in ['axis0_center_span_mm','axis1_center_span_mm','axis2_center_span_mm'])+' | 未通过 |')
lines+=['',
 'A0136、A0138为多值标量体积，不能直接当骨前景；A0137只有两层，第三体素轴中心跨度1 mm，不能充当完整三维颅骨实体。三者都没有本轮可核验的骨标签映射。值域及剖面与灰度影像一致，但这里不认证HU校准、具体影像类型或解剖诊断。','',
 '按未经变换的坐标比较，三个NRRD的中心坐标包围盒均不能包含对应clear STL的顶点包围盒。该结果只说明“直接按同一世界坐标套用历史切除”未获支持，不能据此认定文件损坏，也不能通过自由配准把它调到相似。','',
 '原clear STL已在既有诊断中发现开放／非流形边：A0136为2601／172、A0137为1868／262、A0138为561／158。本轮只重验相同文件SHA，不重算这些拓扑指标；不能因为NRRD未准入，就未经验证把旧网格当闭合实体体素化。','',
 '## 原始数据剖面','',
 '![三个固定NRRD的体素轴中心剖面](source_volume_sections_v1.png)','',
 '图中为原始标量图像，不是C／D／G mask，也没有模拟缺损。各面板采用体素轴距离的等毫米比例；1～99百分位仅为显示窗，不是分割阈值。A0137前两面板呈极薄条带来自实际两层数据，未人为补层；第三面板的投影样外观不作为影像类型认证。已逐图检查标题、比例和图注。','',
 '## 仍未执行的验证','',
 '| 任务 | 状态 | 原因 |','|---|---|---|',
 '| 固定ellipsoid_medium实体切除 | 未执行 | 缺乏可信完整骨mask及物理对应 |',
 '| C=D并G、D与G互斥及同affine验证 | 未执行 | 未生成C/D/G实体 |',
 '| 共享J面位置、相反法向及面积配对 | 未执行 | 没有实体切壁真值 |',
 '| 内／外表面及切壁采样覆盖 | 未执行 | 没有合法边界与点集；不伪造覆盖率0% |',
 '| 8192输入→8192完整骨块边界目标 | 未执行 | 没有合法实体配对 |','',
 '## 下一步需要补齐的具体条件','',
 '优先补齐这三个同编号来源的完整骨组织分割mask，带spacing／方向／origin及组织标签含义，并提供与用于历史切除的clear STL的可追溯坐标关系。只有灰度CT时，需要另行明确分割方法，不能以values>0或随意选HU阈值代替本计划的骨实体。',
 '',
 '本轮对E:/dataset/MUG500plus的文件名搜索未发现这三个编号的额外已解压NRRD／NIfTI／MHA／MHD／seg文件；指定ZIP三来源目录也未列出单独骨mask成员。这不是证明其他存储位置一定没有相应分割。',
 '',
 '如果只能使用现有STL，应另行确定可信实体化／拓扑修复和验证方案，保留几何修改记录及坐标依据；该路线没有在本轮自动执行。三来源仍保留，不换容易病例，也不把旧删面点云当作新的实体切除结果。','',
 '## 资源与证据','',
 '总耗时 '+f"{data['seconds']:.3f}"+' 秒；守卫采样中最大RSS '+str(data['monitored_peak_RSS_bytes'])+' 字节。预算：总60分钟、单例15分钟、监测RSS8GiB、输出1GiB、线程2；不是持续峰值或硬cgroup保证。8项人工CPU检查通过。源文件未写入，未改变旧MUG数据。','',
 '本轮NRRD成员SHA256：','', '| 来源 | SHA256 |','|---|---|']
for row in rows:lines.append('| '+row['source_id']+' | `'+row['NRRD_SHA256']+'` |')
lines+=['','精确机器结果：results.json、三份*_source_admission.json、source_summary_v1.csv及*_scalar_histogram.npz。范围和代码绑定见上级scope_v1.json及artificial_CPU_tests_v1.json。','',
 '本报告严格区分“源检查完成”和“实体构造验证通过”。当前科学状态为UNRESOLVED_SOURCE，不宣称新MUG缺损构造已完成。','']
report=R/'mug_fixed3_solid_pilot_report_zh_v1.md'
with report.open('x',encoding='utf-8') as f:f.write('\n'.join(lines))
def bind(p):return dict(path=str(p.absolute()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
files=[p for p in R.iterdir() if p.is_file()]+[N/'scope_v1.json',N/'artificial_CPU_tests_v1.json',N/'source_admission_v1.py',Path(__file__)]
with (N/'artifact_manifest_v1.json').open('x') as f:json.dump(dict(status='SOURCE_CHECK_COMPLETE_SOLID_VALIDATION_UNRESOLVED',files=[bind(p) for p in files],source_count=3,admitted=0,defects_generated=0,point_pairs_generated=0,server_calls=0,GPU_calls=0,training=0),f,indent=2)
print(json.dumps(dict(status='SOURCE_CHECK_COMPLETE_SOLID_VALIDATION_UNRESOLVED',report=str(report),sources=rows),ensure_ascii=True))
