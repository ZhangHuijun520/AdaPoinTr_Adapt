"""Write local audit report from saved immutable remote observations; no server calls."""
import hashlib,json
from pathlib import Path
B=Path(__file__).resolve().parent;O=B/'sampling_model_AB_foldC_seed0_20261103_v1';F=O/'post_Morton_training_freeze_audit_v1'
def h(b):return hashlib.sha256(b).hexdigest()
def main():
 raw=(F/'audit_report_v1.json').read_bytes();r=json.loads(raw)
 assert r['status']=='FORMAL_POST_TRAINING_FREEZE_AUDIT_PASS' and all(r['checks'].values())
 c=r['counts'];p=r['checkpoint'];i=r['initialization'];resources=r['resource_summary']
 lines=['# Fold C Morton 8k：正式只读训练后冻结审计 v1','',
 '## 结论','',f"**通过，{len(r['checks'])}/{len(r['checks'])} 项检查全部为 true。** 候选臂与已审计 V1 组满足本次单折、单 seed 的训练配对合同；尚不能据此判断采样方案是否提高预测质量。",'',
 '## 授权与执行边界','',
 '用户单独授权正式只读训练后冻结审计。通过既有 WSL＋hpc5000 短入口执行一次 stdlib 只读核验，不修改服务器文件，不导入模型、不运行 forward，不加载 checkpoint／NPZ 内容为张量，不重训、不进入评价或 BNCal。',
 '',f"本次流式哈希共读取 {r['hashed_bytes']:,} bytes，服务器审计耗时 {r['elapsed_seconds']:.3f} 秒。保留既有 120 秒、768 MiB 总读取、512 MiB 单 checkpoint、512 文件上限与精确 Python 二进制大小／哈希例外，未放宽通用守卫。",'',
 '## 完成状态与计数','',
 '| 项目 | 核验值 |','|---|---|',
 '| 退出码／存活状态 | 0；固定 tmux 不存在，worker 已退出 |',
 f"| 更新／完整遍历 | {c['updates']}／{c['epochs']} |",
 f"| 病例曝光／drop_last 丢弃 | {c['case_exposures']}／{c['dropped_exposures']} |",
 f"| 实际 metric／resource 记录 | {c['metric_records']}／{c['resource_records']} |",
 '| forward／backward／clip／optimizer step | 各3900 |',
 '| LR scheduler／BN scheduler | 各100 |',
 '| BNCal／evaluation／resume | 均 false |',
 '',
 '完整扫描3900条记录，核对每条 epoch、batch、病例／来源顺序、更新提交、有限 loss／梯度、LR 及 BN momentum；重建并核对病例、来源及丢弃计数。3902条资源记录的顺序、阈值与通过状态均核验通过。',
 '', '## 实测 checkpoint 与产物清单','',
 f"路径：`{p['path']}`",'',f"大小：**{p['bytes']:,} bytes**。本次独立流式实测 SHA256，与 completion 一致：",'',f"`{p['sha256']}`",'',
 '输出目录精确为11个文件和一个空 tmp 目录，无 failure/startup_failure 标记；7个控制文件与授权材料化预期一致。授权／runtime 保持单向绑定。读取前后内容相关属性稳定，排除 atime 影响。', '',
 '| 输出文件 | bytes | SHA256 |','|---|---|']
 for a in r['output_manifest']:lines.append(f"| {Path(a['path']).name} | {a['bytes']} | {a['sha256']} |")
 lines+=['','## 与 V1 的配对一致性','',
 '重新哈希 V1 的训练日志、初始化、曝光、顺序、完成记录等非权重产物，并匹配其先前正式冻结审计。两个运行的模型／实现哈希、环境身份、配置、固定训练来源、GT／归一化框架／共同点顺序、完整批次顺序、LR／BN 序列、优化器默认参数、更新与曝光计数一致。候选315个NPZ逐文件哈希与冻结manifest一致。两臂允许的差异是输入采样方案；loss 与最终权重不要求相等。',
 '',f"初始参数指纹：`{i['parameter_sha256']}`",'',f"初始持久状态指纹：`{i['persistent_state_sha256']}`",'',
 f"两者均与 V1 初始化记录完全相同；seed为0。实际批次顺序 canonical SHA256：`{i['order_sha256']}`。",'',
 'V1 checkpoint 本次不重复流式哈希，使用此前正式审计的实测哈希，并只读确认当前文件大小、inode 与 mtime_ns 未改变；候选 checkpoint 已在本次完整流式实测。未反序列化或重建初始权重。', '',
 '## 资源与解释限制','',
 f"候选记录峰值：torch allocated {resources['peak_allocated']:,} bytes、reserved {resources['peak_reserved']:,} bytes，SMI {resources['device_peak_MiB']} MiB，RSS {resources['RSS_peak']:,} bytes；全部在冻结预算内。SMI PID 与容器 PID 的差异按既定合同仅诊断，不保证硬隔离或GPU独占。",'',
 '步骤及 forward/backward 等计数由冻结实现与保存记录交叉支持，未采集独立GPU trace。BNCal/evaluation未执行由冻结路径及记录支持，未开展全系统文件访问追踪。训练 loss 不是开发集指标，不用于宣布候选胜出。', '',
 '## 下一步','',
 '本次到此结束。下一科研步骤是对 V1 与 Morton 两臂进行同一 Fold C 开发集配对评价，使用共同 GT 和指标回答未知表面与接口吻合是否改善；先单独冻结评价合同并创建待授权 request，不自动启动预测、BNCal 或追加训练。', '',
 f"机器可读审计报告 SHA256：`{h(raw)}`。"]
 with (F/'formal_freeze_audit_report_zh_v1.md').open('x',encoding='utf-8',newline='\n') as f:f.write('\n'.join(lines)+'\n')
 files=[dict(name=p.name,bytes=p.stat().st_size,sha256=h(p.read_bytes())) for p in sorted(F.iterdir()) if p.is_file()]
 with (F/'audit_artifact_manifest_v1.json').open('x',encoding='utf-8') as f:json.dump(dict(status=r['status'],files=files,server_writes=0),f,indent=2)
 print(json.dumps(dict(status=r['status'],checks=len(r['checks']),report_sha256=h((F/'formal_freeze_audit_report_zh_v1.md').read_bytes()),audit_sha256=h(raw))))
if __name__=='__main__':main()
