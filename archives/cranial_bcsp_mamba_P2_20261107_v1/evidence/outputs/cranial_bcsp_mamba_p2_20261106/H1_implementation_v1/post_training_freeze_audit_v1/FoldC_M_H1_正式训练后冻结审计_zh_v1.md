# Fold C M-H1：正式只读训练后冻结审计

日期：2026-11-06。结论：**PASS**，23项汇总核验通过。

本次核验对应request SHA256：`e5fa766a408762a9a3bf3e2bd1dc993886b3422f7afaf69f9a994dc0ca20413d`。只读检查现有代码、控制材料、完整日志及产物；服务器写入0，新forward/backward/optimizer step均为0，未加载checkpoint或读取NPZ数组。

## 完成状态与权重

- 退出码0；固定tmux已退出，worker不存活；无失败产物。
- 3900次forward/backward/clip/optimizer step，100遍，31200曝光，300次drop-last。
- 精确15个文件和空tmp目录；完整清单/哈希匹配。文件均为jovyan所有、0600，无链接或硬链接替代。
- checkpoint大小：**407224375 bytes**。
- 本次独立流式实测并于审计末次复核的checkpoint SHA256：

```text
6839d694cdd8068085dceea1426aa9d55e71faeaff39a9032bf21af6b1e8b5b4
```

服务器权重：`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2_h1/M_H1_foldC_seed0_20261106_v1/ckpt-last.pth`。

## H1及训练合同

全部3900条记录有限、步数连续、更新已提交；H1始终启用。逐条核对 `H1_raw≈0.5*(H1_centroid+H1_radius)`、`H1_weighted≈0.1*H1_raw`，以及日志总loss的分量一致性；浮点一致性允许已冻结审计源码中的小量舍入误差。母版原始get_loss负责增加H1，runtime只做detach分量观察，没有重复增加loss。

H1 raw首条 `2.1469879150390625`，末条 `0.019380196928977966`；末条总训练loss `0.03770187869668007`。这些只是优化过程记录，不是开发集评价，不能证明覆盖或风险改善。

去噪仍为0；BNCal、development evaluation和resume均为false。

## 与冻结M0 Fold C基线的配对

- 参数初始化指纹一致：`d0ae62fe822af980e7e8d666d4137c2b086c435141ae642433a77c1f87a07f20`。
- 完整persistent-state初始指纹一致：`60c49927d3b51d1476312075b554343c448cac334f8e8b88fb80209358d0fe96`。
- factory构造证据完全一致，仍为真实M0、seed0；没有从最终checkpoint恢复。
- 3900个完整批次的case/source顺序、LR、BN momentum、clip和commit逐项一致。
- 原始order文件SHA256：`6ab424177d5227bd34585a710eedca578acdd2eeb226bec10cdfc86ee89cec9d`；canonical：`349189dcada4c41b9e6b0152fa24695b2c71ce5fce4144865247d03c445f795f`。
- 315例、63来源、每来源5缺损；训练/开发来源隔离；逐病例/逐来源曝光和drop计数与M0一致。
- optimizer defaults与362项参数组逐项一致；实际组weight decay仍为0或0.0005，SSM例外保留。不能把AdamW defaults中的0.01误认为实际参数组发生改变。
- 科研配置差量仅为事前确认的H1；新入口与分量日志是相应执行适配。训练后的权重应发生变化，不要求与M0最终权重相同。

## 资源与冻结稳定性

3902条资源记录（3900次step后＋保存前后）均通过原阈值。

| 资源 | 实测峰值 | 冻结上限 |
|---|---:|---:|
| RSS | 1694359552 bytes | 8589934592 bytes |
| torch allocated | 13388392960 bytes | 21474836480 bytes |
| torch reserved | 14388559872 bytes | 21474836480 bytes |
| SMI device used | 14210 MiB | 22528 MiB |

训练耗时 `1291.481` 秒。PID差异仍按已接受合同仅作诊断，3902条PID warning不改变原资源判定，也不构成同namespace进程所有权证明。空闲磁盘检查由冻结runtime及成功完成支撑，没有独立保存的逐步free-disk数值序列。

审计前后，15个产物的内容SHA256、大小、mtime、ctime、权限及归属完全一致。atime不参与比较，避免读取自身造成误判。

## 结论与下一步

本run可以作为已冻结的M-H1 Fold C训练产物，用于后续同协议比较。审计不认证临床准确性，也不代表H1已经通过全形状/风险资源门。

建议下一步**仅准备Fold D M-H1的待授权训练request**，保持相同H1、8k→8k、seed0、3900步和既定训练合同；不根据C折训练loss调参或筛病例。两折完成后再开展预定Native配对评价。

本次未创建Fold D request，未启动评价、BNCal或其他实验。全部原始回传、审计源码、冻结范围与机器可读结论保存于本目录。
