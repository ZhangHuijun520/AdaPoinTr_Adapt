# P1 T0 Fold D：正式只读训练后冻结审计

日期：2026-11-06。结论：FORMAL_P1_T0_POST_TRAINING_FREEZE_AUDIT_PASS。4260项路径/绑定/顺序/数值/资源细项通过；训练成功，退出码0，进程和tmux已结束。请求SHA256：6a9e9bcdbfa60a6a9bc6b80c6d2d1374796aa02c919766c2fb70b3a0aa764f82。审计报告SHA256：02bd553e42f10098e16fd863c6716d664019735e705c20b3941b2b81d5672877。

## 完整计数与顺序

- optimizer updates、forward、backward、clip均为3900；LR/BN scheduler均100次。
- traversals100，病例曝光31200，drop300，metric3900条，resource3902条。
- 逐一比较全部3900个真实batch与原D冻结顺序，核验case/source ID、D训练来源allowlist、step/epoch/batch、实际LR与BN momentum、loss字段和有限梯度。
- 依据原计划重建逐病例/逐来源曝光与drop计数，与exposure.json完全一致，未漏病例或把D开发来源用于训练。
- 保存的order_plan与原冻结文件相同。原文件SHA256为4f68edd55912be0dccfb3d2a1cc72e499d3d499a36aa5f3788550145b3095720；canonical SHA256为2c9f3e9afb2cfe9ae46c0566bdbced465c64acc2a564654914d2163d74e5e838。
- completion中的BNCal/evaluation/resume均为false。

## 最终checkpoint

路径：`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p1/T0_foldD_seed0_train_20261106_v1/ckpt-last.pth`

大小：380368111 bytes。

本次实测SHA256：`ed901f18be2efb84f9b7b159cec2b71a3602e2e960087ac53d510881be9eba7c`

与completion及payload manifest一致。仅对原始字节做流式哈希，没有torch.load、反序列化或运行模型。本轮不创建本机权重副本；服务器权重与全部实验产物保持原样。

## 初始化、优化与资源

construction与已冻结的原生T0初始factory完全一致，共有状态指纹未变；persistent初始状态与历史原生GPU replay指纹相同。这里复核的是同一初始化身份，不把C历史replay改称D新GPU验证。parameter-only指纹只记录，未重建模型独立复算。

332个optimizer参数组与冻结T0定义一致，effective weight decay分别为0或0.0005。optimizer.defaults记录中的0.01是库默认值，各参数组已有显式覆盖，因此不代表实际weight decay变为0.01。betas/eps/amsgrad/foreach/fused及调度合同通过。

3902条资源记录的阶段/committed step顺序、原阈值与checks值均重新核对。RSS最大1266741248bytes，torch allocated峰值13206299648bytes，reserved峰值14248050688bytes，device最大14074MiB，记录耗时1193.760秒。均低于既定阈值；仍为采样监测，不是连续硬cgroup隔离。PID数值差异仅记录，不新增命名空间归属限制。

## 产物与只读边界

精确核验6个安装文件＋control、4个控制文件、15个训练结果文件＋空tmp目录，以及payload manifest的全部成员。请求、授权回执/runtime单向绑定、launcher渲染和单次claim均与原材料化哈希一致。所有被读文件内容哈希和权限/mtime/ctime/uid/gid在审计期间稳定，未将atime变化当作失败。

本次仅为内存执行的stdlib只读审计：服务器写入0、新forward/backward0、模型导入0、权重反序列化0、点集payload访问0。哈希累计780709764bytes，用时约0.688秒，处于原1GiB/45秒预算内。没有新增通用依赖库存扫描。

## 冻结材料与下一步

机器可读报告audit_report_v1.json保留全部检查与文件哈希，frozen_output_manifest_v1.json为结果清单，frozen_bound_asset_manifest_v1.json为相关绑定清单。frozen_T0_D_pairing_evidence_v1.json列出后续M0_D需要的request/construction/initialization/order/completion/run_identity/exposure精确绑定。正式审计报告目前仅保存在本机，后续M0_D运输准备需给它冻结服务器副本路径并上传核验；本轮不写服务器。

下一步可仅创建M0_D待授权request，复用已通过的D入口并绑定本次真实T0_D证据；无需再次修改模型、入口或重复GPU preflight。M0_D仍需单独执行授权。本轮没有创建M0_D request、启动训练、BNCal或development evaluation。训练loss不用于推断开发集效果。
