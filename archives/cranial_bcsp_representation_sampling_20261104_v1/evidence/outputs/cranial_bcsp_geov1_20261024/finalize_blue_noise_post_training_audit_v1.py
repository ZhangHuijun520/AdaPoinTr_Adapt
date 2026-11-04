"""Save local report/manifests from the completed immutable read-only audit."""
import hashlib,json
from pathlib import Path
B=Path(__file__).resolve().parent
F=B/'blue_noise_model_pair_foldC_seed0_20261104_v1/first_training_request_v2/post_Euclidean_training_freeze_audit_v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
def main():
    p=F/'audit_report_v1.json';r=json.loads(p.read_bytes())
    assert r['status']=='FORMAL_POST_TRAINING_FREEZE_AUDIT_PASS' and all(r['checks'].values())
    c=r['counts'];ck=r['checkpoint'];i=r['initialization'];res=r['resource_summary']
    dump(F/'frozen_output_file_manifest_v1.json',{'status':r['status'],'files':r['output_manifest'],'audit_report_sha256':sha(p)})
    dump(F/'frozen_bound_asset_manifest_v1.json',{'files':r['all_bound_files'],'active_training_data':r['active_training_data'],'graph_payloads_read':False})
    report=f'''# Fold C 欧氏距离采样臂：正式只读训练后冻结审计 v1

日期：2026-11-04。结论：**FORMAL_POST_TRAINING_FREEZE_AUDIT_PASS，{len(r['checks'])}/{len(r['checks'])}项全部通过。**

本次使用既有WSL＋hpc5000短入口进行一次独立只读审计。没有写服务器、反序列化checkpoint、重建模型、读取NPZ为张量、运行forward、重训、BNCal或开发评价。审计流式哈希读取共{r['hashed_bytes']:,} bytes；保留120秒、768MiB总读取、512MiB checkpoint、512文件上限。精确Python二进制仅按原冻结17,331,920 bytes及既有SHA256例外校验，未扩大普通文件上限。

## 计数、顺序及执行状态

| 项目 | 实测／核对结果 |
|---|---|
| 退出码、tmux、worker | 0；会话及worker均已退出 |
| 更新／遍历 | {c['updates']}／{c['epochs']} |
| 病例曝光／drop_last丢弃 | {c['case_exposures']}／{c['dropped_exposures']} |
| 完整metrics／resources记录 | {c['metric_records']}／{c['resource_records']} |
| forward／backward／clip／optimizer step | 各3900，completion与冻结runtime交叉支持 |
| LR scheduler／BN scheduler | 各100 |
| BNCal／evaluation／resume | 均false |

逐条核对3900条实际日志中的step、epoch、batch、病例与来源顺序、optimizer提交、有限loss和梯度、LR与BN momentum；从实际批次重建case/source/drop曝光计数并匹配exposure.json。运行order_plan与冻结文件逐字节相同，canonical哈希与初始化、曝光及completion一致。

## Checkpoint及冻结清单

路径：`{ck['path']}`。

大小：**{ck['bytes']:,} bytes**。本次独立流式实测SHA256，匹配completion：

```text
{ck['sha256']}
```

结果目录精确包含11个文件和一个空tmp目录，无failure/startup_failure。5个控制文件与授权材料化预期大小／哈希一致，授权→runtime保持单向绑定，single-attempt marker匹配完整scope及inner request。全部读取文件及结果树的内容相关属性前后稳定，atime不参与判定。

| 输出文件 | bytes | SHA256 |
|---|---:|---|
'''
    for row in r['output_manifest']:report+=f"| {Path(row['path']).name} | {row['bytes']} | {row['sha256']} |\n"
    report+=f'''
## 初始化与训练来源

Scratch seed0；参数指纹 `{i['parameter_sha256']}`，持久状态指纹 `{i['persistent_state_sha256']}`。记录与同源码、同配置、同seed0的既有已冻结参考一致，当前请求没有父权重。顺序canonical SHA256为 `{i['order_sha256']}`。

本次验证的是绑定runtime保存的初始化记录及其一致性，没有通过重新构造模型独立恢复初始权重。后续图距离臂仍须在其首更新前比较同一参数／buffer指纹，不能把本次通过当作未来配对已经完成。

315个欧氏臂训练NPZ逐文件流式哈希与冻结manifest一致，未解码payload；63训练来源与21开发来源互斥。图距离臂仅核对既有配对元数据中的目标、归一化和共同点序，不读取该臂NPZ、不创建其执行内容。30个固定模型／provider／环境资产重新核验通过。优化器默认值按记录核验，实际分组weight_decay仍由已绑定runtime及合同支持；defaults中的0.01不代表各分组最终采用值。

## 资源与解释范围

3902条资源记录均符合顺序、阈值及停止合同。记录峰值：Torch allocated {res['peak_allocated']/1024**3:.2f}GiB、reserved {res['peak_reserved']/1024**3:.2f}GiB；SMI {res['device_peak_MiB']}MiB；RSS {res['RSS_peak']/1024**3:.2f}GiB。SMI PID与容器PID差异继续仅作诊断，不保证硬隔离或GPU独占。

训练loss：首批{r['loss_summary']['first']:.6f}，末批{r['loss_summary']['last']:.6f}，最后一遍历39批均值{r['loss_summary']['last_epoch_mean']:.6f}。这些是训练指标，不能据此判断采样方法的开发集收益。forward/backward等计数由冻结路径与日志交叉支持，没有独立GPU trace；BNCal/evaluation=false亦不等于进行了全系统文件访问追踪。

## 后续边界

本次仅冻结欧氏臂训练结果，不创建或启动图距离臂request。下一科研步骤可单独准备图距离臂的待授权request，复用既有点集，绑定本次初始化、同一环境、同一顺序与3900步合同；待两臂训练及独立审计完成后，再按阶段进行开发集配对评价。

机器可读审计报告SHA256：`{sha(p)}`。
'''
    with (F/'formal_freeze_audit_report_zh_v1.md').open('x',encoding='utf-8') as f:f.write(report)
    files={p.name:{'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(F.iterdir()) if p.is_file()}
    dump(F/'audit_artifact_manifest_v1.json',{'status':r['status'],'files':files,'server_writes':0,'model_calls':0})
    print(json.dumps({'status':r['status'],'checks':len(r['checks']),'checkpoint_SHA256':ck['sha256'],'report_SHA256':sha(F/'formal_freeze_audit_report_zh_v1.md')}))
if __name__=='__main__':main()
