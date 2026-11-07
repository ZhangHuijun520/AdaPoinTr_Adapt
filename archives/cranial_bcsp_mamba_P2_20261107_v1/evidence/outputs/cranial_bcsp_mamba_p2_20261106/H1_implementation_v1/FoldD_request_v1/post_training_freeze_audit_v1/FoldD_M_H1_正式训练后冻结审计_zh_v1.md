# Fold D M-H1：正式只读训练后冻结审计与M0配对核验

结论：**PASS，23项汇总核验通过。**

对应request SHA256：`305ce3380ae7b951c7180907f63842abc51eae5d9dec817e2a5ad89718fdd390`。

## 实测产物

退出码0，tmux已退出，worker已结束。精确15个文件及空tmp目录，payload manifest完整匹配；权限0600、uid1000，拒绝链接替代。审计前后内容SHA256、大小、mtime/ctime和权限归属完全一致；不以读取会改变的atime判定漂移。

checkpoint大小：407224375 bytes。本次独立流式计算并复核的SHA256：

```text
6a76aa7dc156c0e2eeef29d4e03b253f624373ced8a48abebe1af4c99d7e789d
```

服务器文件：`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2_h1/M_H1_foldD_seed0_20261106_v1/ckpt-last.pth`。

## 完整计数与H1

3900 forward/backward/clip/optimizer steps，100 traversals，31200 exposures，300 drop-last。全部3900条日志步数连续、更新提交、H1启用、数值有限；逐条核对H1_raw与两项均值、0.1加权及总loss分量一致性。有限小数比较容差用于浮点日志舍入，不改变训练或科研晋级阈值。

首条H1 raw：2.1061348915100098；末条：0.02492707036435604；末条总训练loss：0.039386991411447525。这不是开发集性能，不能据此判定H1有效或调整参数。

H1唯一配置仍为centroid_radius、weight0.1、beta0.1、eps1e-6，无CVaR。BNCal/evaluation/resume均为false。

## M0 Fold D配对

初始参数指纹：`d0ae62fe822af980e7e8d666d4137c2b086c435141ae642433a77c1f87a07f20`。

初始persistent-state指纹：`60c49927d3b51d1476312075b554343c448cac334f8e8b88fb80209358d0fe96`。

两者与M0 D及冻结factory证据一致；未重建初始张量或加载checkpoint。362项optimizer参数组与defaults完全一致，实际weight decay仍为0或0.0005。完整3900个case/source批次、LR、BN momentum、clip和commit逐项匹配；315例/63来源、每来源5缺损、train/dev来源隔离。

原order文件SHA256：`4f68edd55912be0dccfb3d2a1cc72e499d3d499a36aa5f3788550145b3095720`；canonical：`2c9f3e9afb2cfe9ae46c0566bdbced465c64acc2a564654914d2163d74e5e838`。逐病例/逐来源曝光与丢弃计数和基线一致。

新增科研配置只有事前H1；入口和runtime复用C折原哈希。最终权重无需与M0相同。未依据C折loss调整D折合同。

## 资源与限制

3902条资源记录均通过冻结阈值：

| 资源 | 实测峰值 | 原上限 |
|---|---:|---:|
| RSS | 1694519296 bytes | 8589934592 bytes |
| torch allocated | 13388392960 bytes | 21474836480 bytes |
| torch reserved | 14388559872 bytes | 21474836480 bytes |
| SMI使用 | 14210 MiB | 22528 MiB |

训练耗时1288.258秒。3902条PID warning按已接受合同仅作诊断，不是新增资源失败，也不提供同namespace所有权证明。采样监测不等于硬隔离；空闲磁盘由冻结runtime及成功完成支撑，没有独立逐步free-disk序列。

本次服务器写入0，新增forward/backward/optimizer step均为0，未加载权重或读取真实NPZ数组。H1日志和已验证runtime提供一致性证据，不等于独立tensor重算loss。先前剩余调用因审批服务额度未执行，本次经正常审批续完；没有修改审计判据、重训或重试科学实验。

## 阶段结论

C/D两次M-H1训练现均已正式冻结，并分别与对应P1 M0基线配对通过。仍不知道Native完整骨块覆盖、接口或严重风险是否改善。

建议下一步仅准备两折H1开发集预测request：每折固定105例，共210次预测；保留原协议与共享参考，复用已冻结M0预测作对照。模型结构不变，但现有预测入口是否接受H1配置需先作限定兼容性核对，不能直接沿用P1 request。若最终要补做baseline预测或新增instrumentation，必须单独说明次数，不能隐含增加。

本次未创建预测request、未运行评价或BNCal、未追加训练。
