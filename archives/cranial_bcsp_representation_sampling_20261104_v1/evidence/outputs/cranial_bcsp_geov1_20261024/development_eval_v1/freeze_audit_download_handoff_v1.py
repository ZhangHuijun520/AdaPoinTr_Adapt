"""Write local audit summary and precise manual-download handoff. No server calls."""
from pathlib import Path,PureWindowsPath
import hashlib,json
N=Path(__file__).resolve().parent;A=N/'freeze_audit_v1';p=A/'audit_report.json'
raw=p.read_bytes();audit=json.loads(raw);assert audit['status']=='FORMAL_POST_PREDICTION_FREEZE_AUDIT_PASS'
digest=hashlib.sha256(raw).hexdigest()
backup=PureWindowsPath('E:/ResearchBackups/AdaPoinTr/BCSP_INPUT_DENSITY_V1/2026-10-26_development_eval')
items=[dict(server_path=r['path'],filename=Path(r['path']).name,bytes=r['bytes'],sha256=r['sha256'],suggested_local_path=str(backup/Path(r['path']).name)) for r in audit['download_files']]
manifest=dict(status='SERVER_FREEZE_VERIFIED_AWAITING_USER_MANUAL_DOWNLOAD',audit_report=dict(path=str(p),bytes=len(raw),sha256=digest),
 suggested_local_directory=str(backup),files=items,archive_includes_checkpoints=False,server_and_Windows_automatically_synced=False,
 Windows_backup_verified=False,CPU_scoring_started=False,server_files_deleted=False,
 next_action='User downloads exact4 files and confirms local location;verify their bytes/SHA256 before fixed local CPU scoring')
with (A/'download_manifest_v1.json').open('x') as f:json.dump(manifest,f,indent=2)
with (A/'download_SHA256SUMS_v1.txt').open('x') as f:
 for r in items:f.write(r['sha256']+'  '+r['filename']+'\n')
with (A/'audit_report.json.sha256').open('x') as f:f.write(digest+'  audit_report.json\n')
lines=['# 四模型开发集预测：正式只读冻结审计与下载交接 v1','',
 '审计时间：'+audit['UTC']+'。结论：**FORMAL_POST_PREDICTION_FREEZE_AUDIT_PASS**。','',
 '本次为独立重算的只读审计，不是仅复述启动或完成回执。服务器写入、模型导入、checkpoint反序列化、CUDA及forward调用均为0。','',
 '## 已核验的科研证据','',
 '- 固定四模型，各105例，合计420条连续且无重复的预测记录；210个不同病例，42个out-of-fold来源，每来源五种缺损。',
 '- 420个现场预测的文件大小与SHA256独立核验；NPZ仅读取prediction.npy，均为有限float32、8192×3。',
 '- 四个训练最终checkpoint重新流式计算SHA256，与冻结身份一致；未加载checkpoint。',
 '- 授权回执、runtime单向绑定和单次启动claim均与已材料化文件哈希一致。',
 '- 四模型记录的完整model-state（参数及持久BN缓冲区）前后相等；已记录的CPU RNG前后相等。CUDA RNG未记录，不作相同断言。',
 '- 845条资源日志的阶段／计数顺序精确一致，原阈值逐条重算通过；退出码0，无失败回执，训练更新／BNCal／loss／backward均为0。',
 '- tar.gz恰有423个常规成员，成员顺序、大小及SHA与420个预测和3个推理元数据文件一致；归档不含checkpoint。',
 '- 压缩包及三个sidecar的大小／SHA独立重算，内容清单423项严格匹配。','',
 '资源日志中的最大值：RSS '+str(audit['resource_maxima']['RSS_bytes'])+'字节；设备显存 '+str(audit['resource_maxima']['device_MiB'])+' MiB；torch allocated '+str(audit['resource_maxima']['peak_allocated'])+'字节；reserved '+str(audit['resource_maxima']['peak_reserved'])+'字节。记录的推理预算阶段耗时 '+str(audit['recorded_inference_budget_seconds'])+'秒，不作为经热身的正式性能benchmark。','',
 '## 手动下载的精确四文件','',
 '服务器共同目录：','',
 '```text',str(Path(items[0]['server_path']).parent).replace('\\','/'),'```','',
 '| 文件 | bytes | SHA256 |','|---|---:|---|']
for r in items:lines.append('| '+r['filename']+' | '+str(r['bytes'])+' | `'+r['sha256']+'` |')
lines+=['','建议本机放置目录（尚未创建或验证）：','','```text',str(backup),'```','',
 '由用户完成下载并确认本机位置。服务器和Windows不自动同步；本次服务器审计不等于本机备份核验。收到下载位置后，先按本清单核验四个文件，再执行已冻结的本机统一评分；本轮未计算任何模型误差、候选差值或bootstrap结果。','',
 '## 评分及解释边界','',
 '主终点保持A1未知原始表面E_G→预测点的面积加权P95（mm），并同时检查J切壁接口覆盖、逆向离群及固定控制。按source内五缺损等权汇总，再做16k−8k配对比较与固定10000次bootstrap、seed20261024。','',
 '此次通过证明预测产物满足已冻结执行与完整性合同，不证明16k更优、连续实体接触无缝、临床安全或Mamba收益。资源为采样监测，非专属cgroup硬限制。四模型仍是B0 AdaPoinTr、固定seed0、开发集两折比较。','',
 '审计报告SHA256：`'+digest+'`。完整机器证据：audit_report.json；精确下载清单：download_manifest_v1.json；本机核验用哈希表：download_SHA256SUMS_v1.txt。','']
with (A/'audit_and_download_handoff_zh_v1.md').open('x',encoding='utf-8') as f:f.write('\n'.join(lines))
print(json.dumps(dict(status=manifest['status'],audit_sha256=digest,downloads=items,CPU_scoring_started=False)))
