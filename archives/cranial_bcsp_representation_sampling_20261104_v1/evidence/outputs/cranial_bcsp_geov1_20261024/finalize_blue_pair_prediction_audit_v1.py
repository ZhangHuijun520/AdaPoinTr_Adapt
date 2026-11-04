"""Save local audit report and exact manual download handoff, no server calls."""
import hashlib,json
from pathlib import Path
B=Path(__file__).resolve().parent;N=B/'blue_pair_eval_v1';F=N/'freeze_audit_v1'
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(n,text):
 with (F/n).open('x',encoding='utf-8',newline='\n') as f:f.write(text)
def main():
 r=json.loads((F/'audit_report.json').read_bytes());assert r['status']=='FORMAL_POST_PREDICTION_FREEZE_AUDIT_PASS' and r['forwards']==210 and r['exit_code']==0
 files=r['download_files'];path=str(Path(r['download_files'][0]['path']).parent).replace('\\','/')
 destination='E:\\ResearchBackups\\AdaPoinTr\\BCSP_BLUE_NOISE_AB_V1\\2026-11-04_paired_development_eval'
 lines=['# Fold C 欧氏／图距离：正式只读预测后冻结审计 v1','',
 '**结论：FORMAL_POST_PREDICTION_FREEZE_AUDIT_PASS。** 唯一一次预测已结束且退出码0；11组综合检查通过，210份预测及完整输出清单、213成员归档经独立只读重算核验。当前尚无补全精度或接口改善结论。', '',
 '## 身份、授权与权限边界','',
 f"审计记录UTC：`{r['UTC']}`。容器：`{r['hostname']}`，uid1000。外层request SHA256：`{r['outer_request_sha256']}`；内层request SHA256：`{r['inner_request_sha256']}`。",'',
 '本次单独授权仅用于只读冻结审计。使用既有WSL＋hpc5000短入口在内存执行stdlib审计，不写服务器，不导入模型／CUDA，不反序列化checkpoint，不运行forward、loss或评分。预测NPZ由stdlib读取NPY头和float32字节，检查有限性。没有运行任何新预测或训练。', '',
 '## 完整清单与身份核验','',
 '| 项目 | 核验结果 |','|---|---|',
 '| 退出码／进程 | 0；固定tmux已退出，worker不存活 |',
 '| 两臂病例 | C_Euclidean_elimination 105、C_surface_graph 105；共同105病例、21来源 |',
 '| 预测 | 210份逐个SHA256、大小、规范文件名、provenance核验；均finite float32、8192×3 |',
 '| 完整输出 | 精确221文件、predictions目录和空tmp目录；无多余／遗漏／失败产物 |',
 '| 安装／控制 | 213安装文件＋6控制文件的精确绑定、完整哈希和单向授权链通过 |',
 '| 权重／依赖 | 两份checkpoint SHA256重新流式计算；精确源码、provider和环境资产哈希核验 |',
 '| 配对证据 | 相同开发身份、来源排除、GT、D-only框架及固定共同点序元数据核验 |',
 '| 归档 | 213成员，精确顺序与集合，无重复；每个成员大小／哈希与原文件一致 |',
 '| sidecar | SHA256、bytes、contents SHA256文本精确匹配；四下载文件独立重算哈希 |',
 '| 稳定性 | 完整输出树和读取文件的内容相关指纹审计前后不变，排除atime |',
 '', '## 状态、RNG和资源','',
 '两个模型各105次native eval/inference_mode；参数及持久BN状态前后指纹相同。CPU／CUDA RNG前后指纹相同，Python／NumPy RNG不变断言为true；训练更新、BNCal、loss、backward计数均0。这是对保存证据及冻结实现的核验，不是独立重构模型状态或复跑CUDA。', '',
 '| 模型 | 参数／BN状态指纹（前后相同） |','|---|---|']
 for m in r['state_evidence']:lines.append(f"| {m['run']} | `{m['state_before']}` |")
 v=r['resource_maxima']
 lines+=['',f"完整扫描并重新计算423条资源记录的phase／forward序列及阈值。RSS峰值{v['RSS_bytes']:,} bytes，SMI峰值{v['device_MiB']} MiB，torch allocated峰值{v['peak_allocated']:,} bytes、reserved峰值{v['peak_reserved']:,} bytes，记录推理预算耗时{r['recorded_inference_budget_seconds']:.3f}秒，全部通过冻结阈值。PID按既定合同仅诊断，资源监测不代表专属硬隔离。",'',
 f"正式审计读取{r['read_bytes']:,} bytes，服务器核验耗时{r['seconds']:.3f}秒，位于2GiB读取／90秒预算内。输出总大小{r['actual_output_bytes']:,} bytes。",'',
 '## 已冻结下载文件','',f"服务器共同目录：`{path}`",'',
 '| 文件名 | bytes | 独立实测SHA256 |','|---|---:|---|']
 for f in files:lines.append(f"| {Path(f['path']).name} | {f['bytes']} | `{f['sha256']}` |")
 lines+=['', '## 下一步与结论限制','',
 f"建议手动下载上列四文件到本机 `{destination}`，随后只读核验大小、哈希及归档内容。此处仅建议目录，未创建目录、下载文件或声称已有本机备份。",'',
 '核验完成后，按既定协议单独授权必要的两臂评分入口适配和统一CPU评分：主指标为来源等权的未知表面E面积加权P95，关键次指标为J P95、J/E Cover@2mm及共同GT CD-L1。当前不直接运行旧四模型评分工具，不选择病例或改变阈值，不计算正式gate。单折单训练seed仅描述性研究，不能凭预测完成或本次审计通过宣布图距离优于欧氏，更不构成临床吻合认证或Mamba收益结论。', '',
 f"完整机器报告：`audit_report.json`，SHA256 `{h(F/'audit_report.json')}`。该报告包含221文件完整输出清单、210预测及3个归档元数据成员清单、219安装／控制文件哈希和状态证据。"]
 save('formal_freeze_audit_report_zh_v1.md','\n'.join(lines)+'\n')
 handoff=dict(status='SERVER_ARCHIVE_FORMALLY_VERIFIED_MANUAL_DOWNLOAD_PENDING',server_directory=path,files=files,suggested_local_directory=destination,downloaded_to_local=False,local_backup_verified=False,requires_local_hash_verification=True,scoring_executed=False,audit_report=dict(path=str((F/'audit_report.json').absolute()),sha256=h(F/'audit_report.json')))
 with (F/'manual_download_handoff_v1.json').open('x',encoding='utf-8') as f:json.dump(handoff,f,indent=2)
 delivery=[dict(name=p.name,bytes=p.stat().st_size,sha256=h(p)) for p in sorted(F.iterdir()) if p.is_file()]
 with (F/'audit_artifact_manifest_v1.json').open('x') as f:json.dump(dict(status=r['status'],files=delivery,server_writes=0,scoring=False),f,indent=2)
 print(json.dumps(dict(status=r['status'],checks=len(r['checks']),prediction_files=210,archive_members=213,output_manifest_files=len(r['output_manifest']),report_sha256=h(F/'formal_freeze_audit_report_zh_v1.md'),audit_sha256=h(F/'audit_report.json'))))
if __name__=='__main__':main()
