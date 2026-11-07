"""Write descriptive interpretation only after formal audit PASS."""
import hashlib,json
from pathlib import Path
S=Path(__file__).resolve().parent;F=S/'post_run_freeze_audit_20261107_v1'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def bind(p):return dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
a=read(F/'formal_audit_report_v1.json');assert a['status']=='FORMAL_POST_PROBE_FREEZE_AUDIT_PASS';values=read(F/'audited_values_v1.json')
lines=['# 冻结特征读出对照：正式冻结审计与科研解读 v1','','日期：2026-11-07。先完成正式只读审计，再解读。没有重跑模型、重新拟合、求解线性系统、调正则或计算正式gate。','','## 1. 审计结论与证据限度','',f"状态：`{a['status']}`，{len(a['checks'])}组检查通过。四模型各315训练＋105开发，共1680份特征；420行模型开发病例、84行模型开发来源；3372条资源记录；归档1692成员，服务器输出1700文件。",'', '服务器原件和归档成员逐一核验SHA256、大小及内容相关指纹；请求、入口、核心、index、授权／runtime／launcher绑定一致。独立核验保存的训练均值／标准差、ridge一阶最优性方程、保存系数计算出的预测与误差、每来源五缺损归约、分层汇总、均值／中位数及胜负计数。不重新训练或拟合。', '',f"最大ridge驻点残差：{a['max_ridge_stationarity_residual']:.3g}；用于确认保存系数符合固定平均损失＋lambda=1的合同，不是科研效果阈值。",'', '重要限度：worker保存的是模型／BN与RNG一致性的断言结果，没有持久化前后完整指纹，因此本次不能独立重哈希模型状态。Q只保存矩而非完整张量；原生Q一致性依赖已绑定代码在执行时的检查及保存矩核对。没有重新读取原始点集／权重或重算表面距离。','','## 2. 科研问题与对照','','目标不是生成新的骨块，而是判断固定输入几何或冻结encoder全局特征，能否被单配置线性读出更好地映射到G8192的经验质心和log半径。T0与M0均使用对应折的冻结模型，训练／开发来源分离；每来源五缺损，所有拟合／标准化只用训练。', '', '四对照为训练常数、已有coarse、18维D-only几何ridge、1024维冻结特征ridge。lambda固定为平均损失定义下1.0，无调参；较差线性探针不能证明信息不存在。以下为21来源等权均值，越小越好。半径误差是绝对log比，无量纲；不能把这四个参数称为完整骨片预测。','','## 3. 主要结果','','| 折／冻结模型 | 读出 | 质心误差mm | 质心误差/rGT | 绝对log半径误差 |','|---|---|---:|---:|---:|']
names={'constant':'训练常数','coarse':'已有coarse','geometry18':'输入几何ridge','feature1024':'冻结特征ridge'}
out={};allwins=[]
for label,s in values.items():
 out[label]={}
 for arm in names:
  z=s['source_equal'][arm];m=z['source_mean'];lines.append(f'| {label} | {names[arm]} | {m[0]:.4f} | {m[1]:.4f} | {m[2]:.5f} |');out[label][arm]=z
 z=s['source_equal']['feature1024'];d=z['mean_delta_vs_coarse'];allwins.append(d[0]<0 and d[2]<0)
lines+=['','## 4. 相对原coarse的来源级表现','','差值为读出−coarse，负值改善。以下同时列均值变化和改善／退化来源数，避免只挑平均值。','','| 折／模型 | 读出 | 质心差值mm | 质心改善／退化 | 半径差值 | 半径改善／退化 |','|---|---|---:|---:|---:|---:|']
for label,s in values.items():
 for arm in ['geometry18','feature1024']:
  z=s['source_equal'][arm];d=z['mean_delta_vs_coarse'];i=z['improved_sources'];w=z['worse_sources'];lines.append(f"| {label} | {names[arm]} | {d[0]:+.4f} | {i[0]}／{w[0]} | {d[2]:+.5f} | {i[2]}／{w[2]} |")
lines+=['','## 5. 分折解释','']
for label,s in values.items():
 z=s['source_equal']['feature1024'];m=z['source_mean'];c=s['source_equal']['coarse']['source_mean'];g=s['source_equal']['geometry18']['source_mean'];d=z['mean_delta_vs_coarse']
 center='改善' if d[0]<0 else '退化' if d[0]>0 else '相同';radius='改善' if d[2]<0 else '退化' if d[2]>0 else '相同'
 lines.append(f"- **{label}**：冻结特征读出质心{c[0]:.3f}→{m[0]:.3f}mm（{center}），半径误差{c[2]:.5f}→{m[2]:.5f}（{radius}）；对应几何读出为{g[0]:.3f}mm／{g[2]:.5f}。这只说明当前读出与坐标头的相对表现，不能把关联写成encoder或pooling的因果归因。")
lines+=['','## 6. 对H2的含义与下一步','']
if all(allwins):lines.append('四个冻结模型上，特征读出的质心与半径来源均值均优于原coarse，支持全局特征中存在可读出、而当前coarse头未充分利用的低阶几何信息。仍需结合多数来源和两模型的绝对水平解释，不能据此证明结构耦合一定改善完整表面。')
else:lines.append('并非四个冻结模型都同时获得质心与半径均值改善，不能宣称“条件利用不足已经被完整证明”。应按折／backbone分别解释：只改善半径不等于能定位缺损；只改善质心不保证范围或形状。')
lines+=['', '固定线性读出优于coarse时，支持相应目标的信息可以被简单映射利用；不能证明原坐标头完全忽略输入。若它不优于coarse，也只是否定本次固定线性／正则读出，不构成信息不可预测或必须增加定位器的证明。','', '是否继续一个H2，应依据本表中跨折稳定的具体目标提出唯一假设，并明确如何把D-only预测条件进入coarse、OFF恒等路径以及AUX／COUPLE公平对照。此次不自动设计／实现H2，不扫描lambda或增加训练；完整表面E／J覆盖、远端离群和新退化仍须由后续同协议模型实验检验。','', '当前是单seed、已多次使用的开发来源上的探索性结果。读出四维矩不构成高精度骨块、接口匹配、厚度／拓扑或临床可靠性证据；也不把GT对齐／Oracle结果混入正式性能。','','## 7. 文件','','- `formal_audit_report_v1.json`：正式审计、归档哈希、下载文件清单及限度。','- `audited_values_v1.json`：四模型全部已审计汇总，含每来源与五缺损分层。','- `downloads/development_predictions_v1.tar.gz`：本次特征／读出归档；沿用父打包函数文件名，内容不是新的dense预测。','- `remote_audit_report_v1.json`：服务器原件只读冻结核验。','- 首版审计传输超时与新版短行调用的记录均保留，不改科研执行记录。']
report=F/'冻结特征读出对照_正式冻结审计与科研解读_zh_v1.md'
with report.open('x',encoding='utf-8') as f:f.write('\n'.join(lines)+'\n')
with (F/'interpretation_summary_v1.json').open('x',encoding='utf-8') as f:json.dump(dict(status='DESCRIPTIVE_INTERPRETATION_AFTER_AUDIT_PASS',models=out,all_four_center_and_radius_mean_improve=all(allwins),H2_selected=False),f,indent=2)
files=[p for p in F.iterdir() if p.is_file()]
with (F/'final_delivery_manifest_v1.json').open('x',encoding='utf-8') as f:json.dump(dict(files=[bind(p) for p in files],audit_sources=[bind(S/n) for n in ['audit_remote_outputs_readonly_v1.py','invoke_readonly_run_audit_v1.py','invoke_readonly_run_audit_v2.py','audit_saved_probe_arithmetic_v1.py',Path(__file__).name]],no_refit=True,no_new_forward=True),f,indent=2)
print(json.dumps(dict(report=str(report),all_four_both_improve=all(allwins),metrics={k:{arm:v['source_mean'] for arm,v in z.items()} for k,z in out.items()})))
