"""Local report from the completed graph/paired audit; no server calls."""
import hashlib,json
from pathlib import Path
B=Path(__file__).resolve().parent;O=B/'blue_noise_model_pair_foldC_seed0_20261104_v1/first_training_request_v2';F=O/'graph_request_v2/post_training_audit_v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
def main():
    file=F/'audit_report_v1.json';r=json.loads(file.read_bytes());basefile=O/'post_Euclidean_training_freeze_audit_v1/audit_report_v1.json';base=json.loads(basefile.read_bytes())
    assert r['status']=='FORMAL_POST_TRAINING_FREEZE_AUDIT_PASS' and all(r['checks'].values())
    assert r['paired_comparison']['baseline_audit_sha256']==sha(basefile)
    c=r['counts'];p=r['checkpoint'];i=r['initialization'];res=r['resource_summary']
    dump(F/'frozen_output_manifest_v1.json',{'status':r['status'],'files':r['output_manifest']})
    dump(F/'frozen_bound_asset_manifest_v1.json',{'files':r['all_bound_files'],'active_training_data':r['active_training_data'],'paired_comparison':r['paired_comparison']})
    report=f'''# 欧氏／图距离 Fold C：图距离臂正式冻结审计与两臂配对核验

日期：2026-11-04。结论：**FORMAL_POST_TRAINING_FREEZE_AUDIT_PASS，{len(r['checks'])}/{len(r['checks'])}项全部通过。** 两个既定运行已完成训练及各自正式冻结审计；尚未进行本对照的开发集预测或评分。

## 执行范围

本次仅通过WSL＋hpc5000执行一次有界stdlib只读审计，服务器写入0，模型导入0，forward0；未反序列化checkpoint或NPZ、未恢复模型、未重训、未进入BNCal或开发评价。总流式哈希读取{r['hashed_bytes']:,} bytes。继续采用120秒、768MiB总读取、512MiB单checkpoint、512文件预算，以及既定Python二进制精确17,331,920 bytes／SHA256例外。

## 完成计数及执行证据

| 项目 | 图距离臂核验结果 | 与欧氏臂关系 |
|---|---|---|
| 退出码及存活状态 | 0，固定tmux与worker已退出 | 两臂均正常退出 |
| 输入／输出 | 8192／8192 | 一致 |
| 来源／训练病例 | 63／315 | 一致，开发来源互斥 |
| optimizer更新／遍历 | {c['updates']}／{c['epochs']} | 一致 |
| 曝光／丢弃 | {c['case_exposures']}／{c['dropped_exposures']} | 逐病例、逐来源及drop集合一致 |
| metrics记录 | {c['metric_records']} | 全部step、epoch、batch、病例／来源顺序、LR、BN momentum、clip与提交标记一致 |
| resources记录 | {c['resource_records']} | 各自原阈值与顺序全部通过 |
| forward／backward／clip／step | 各3900 | completion与冻结runtime交叉支持 |
| LR／BN调度调用 | 各100 | 一致 |
| BNCal／evaluation／resume | 均false | 一致 |

逐条读取3900个metric事件，检查有限loss／梯度、loss分项求和、学习率和BN momentum公式；重建曝光及丢弃计数并对照exposure.json。两臂的loss、梯度和最终权重允许不同，不将其要求相等。

## 实测checkpoint与产物清单

图距离臂路径：`{p['path']}`。

大小：**{p['bytes']:,} bytes**。本次独立流式实测SHA256，与completion一致：

```text
{p['sha256']}
```

欧氏臂沿用此前正式实测SHA256 `{base['checkpoint']['sha256']}`，本次确认大小、inode和mtime_ns仍匹配此前冻结记录，并检查审计期间属性稳定；没有再次读取整份欧氏权重或声称重算了该哈希。欧氏臂所有非权重输出重新读取／哈希并与此前正式冻结清单匹配。

图距离结果目录精确为11个文件及一个空tmp目录，无failure／startup_failure。7个控制文件与冻结材料化预期大小／SHA256匹配，授权→runtime单向绑定和唯一attempt标记均通过。所有哈希文件与结果树内容相关属性前后稳定，排除atime干扰。

| 图距离臂输出文件 | bytes | SHA256 |
|---|---:|---|
'''
    for row in r['output_manifest']:report+=f"| {Path(row['path']).name} | {row['bytes']} | {row['sha256']} |\n"
    report+=f'''
## 配对一致性

两个运行的模型、entry／contract／runtime／helper、环境身份、PointNet2 provider、cdist后端、静态配置、固定fold来源、order文件和资源预算绑定一致。30个固定模型／provider／环境资产重新按大小与SHA256核验通过。实际optimizer默认记录一致；分组衰减等行为依赖同一冻结runtime，不把defaults中的weight_decay=0.01误认为所有参数组最终值。

初始化seed0，参数指纹 `{i['parameter_sha256']}`，持久buffer指纹 `{i['persistent_state_sha256']}`；两臂记录完全相同，并匹配图距离请求中的欧氏冻结证据。顺序canonical SHA256 `{i['order_sha256']}`。初始化由冻结运行入口在首更新前比较，本次复核保存记录；未独立重建初始模型权重。

全部3900条实际批次序列与LR／BN／clip／提交标记一致；case、source及dropped_case计数完全一致。配对目标数组哈希、D-only归一化及共同点序元数据一致。315份图距离训练NPZ重新逐文件流式哈希，与冻结manifest一致；未解码这些NPZ或再次计算其中的目标数组哈希，目标一致性依赖此前实际数据QC及本次文件身份与元数据绑定。

## 资源与科研解释

记录峰值：allocated {res['peak_allocated']/1024**3:.2f}GiB，reserved {res['peak_reserved']/1024**3:.2f}GiB，设备SMI {res['device_peak_MiB']}MiB，RSS {res['RSS_peak']/1024**3:.2f}GiB，均在原预算内。PID命名空间差异继续仅诊断，不代表专属GPU或cgroup硬隔离。

图距离臂训练loss首批 {r['loss_summary']['first']:.6f}，末批 {r['loss_summary']['last']:.6f}，最后一遍历均值 {r['loss_summary']['last_epoch_mean']:.6f}。这些是训练量，不据此判断欧氏或图距离采样胜负。计数由固定runtime、completion和日志交叉支持，没有独立GPU trace；BNCal/evaluation未执行同样不是全系统文件访问追踪结论。

## 下一阶段

训练配对核验通过后，可单独准备两臂Fold C开发集配对评价request：每臂105病例、共210次预测，同一GT和指标，使用最终native权重，不自动BNCal／TTA或追加训练。主要回答未知表面补全与接口吻合是否改善，按来源等权汇总；单fold、单seed探索对照不构成最终泛化或显著性结论。本次没有创建或执行评价内容。

图距离机器可读审计SHA256：`{sha(file)}`。欧氏父审计SHA256：`{sha(basefile)}`。
'''
    with (F/'formal_freeze_and_pairing_report_zh_v1.md').open('x',encoding='utf-8') as out:out.write(report)
    dump(F/'audit_artifact_manifest_v1.json',{'status':r['status'],'files':{p.name:{'bytes':p.stat().st_size,'sha256':sha(p)} for p in F.iterdir() if p.is_file()},'server_writes':0,'model_calls':0})
    print(json.dumps({'status':r['status'],'checks':len(r['checks']),'graph_checkpoint_sha256':p['sha256'],'paired_checks_passed':True,'audit_report_sha256':sha(file)}))
if __name__=='__main__':main()
