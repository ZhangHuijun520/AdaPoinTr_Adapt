# 四模型开发集预测：正式只读冻结审计与下载交接 v1

审计时间：2026-10-26T10:52:38.569313+00:00。结论：**FORMAL_POST_PREDICTION_FREEZE_AUDIT_PASS**。

本次为独立重算的只读审计，不是仅复述启动或完成回执。服务器写入、模型导入、checkpoint反序列化、CUDA及forward调用均为0。

## 已核验的科研证据

- 固定四模型，各105例，合计420条连续且无重复的预测记录；210个不同病例，42个out-of-fold来源，每来源五种缺损。
- 420个现场预测的文件大小与SHA256独立核验；NPZ仅读取prediction.npy，均为有限float32、8192×3。
- 四个训练最终checkpoint重新流式计算SHA256，与冻结身份一致；未加载checkpoint。
- 授权回执、runtime单向绑定和单次启动claim均与已材料化文件哈希一致。
- 四模型记录的完整model-state（参数及持久BN缓冲区）前后相等；已记录的CPU RNG前后相等。CUDA RNG未记录，不作相同断言。
- 845条资源日志的阶段／计数顺序精确一致，原阈值逐条重算通过；退出码0，无失败回执，训练更新／BNCal／loss／backward均为0。
- tar.gz恰有423个常规成员，成员顺序、大小及SHA与420个预测和3个推理元数据文件一致；归档不含checkpoint。
- 压缩包及三个sidecar的大小／SHA独立重算，内容清单423项严格匹配。

资源日志中的最大值：RSS 1499201536字节；设备显存 734 MiB；torch allocated 247680000字节；reserved 297795584字节。记录的推理预算阶段耗时 92.58206098712981秒，不作为经热身的正式性能benchmark。

## 手动下载的精确四文件

服务器共同目录：

```text
/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/development_four_models_seed0_v1
```

| 文件 | bytes | SHA256 |
|---|---:|---|
| development_predictions_v1.tar.gz | 37805756 | `c39b1d68aaf7dbc166d88dc57945187186ff01d753a5f20f8c69aa0dc49d9314` |
| development_predictions_v1.tar.gz.sha256 | 100 | `34deb10df2ea1f5db360f7d3ca69e4eae49ce876f0518403c9f6fff1bd0f3775` |
| development_predictions_v1.tar.gz.bytes | 9 | `ff85328580b19d672dae9b2d62ab218b14c5d4cd8a6851e08e7e3e42dfdae488` |
| development_predictions_v1.tar.gz.contents.sha256 | 48185 | `c624ad5b001852373ef96ca40f0b36781227e7facdc9eb33c822aa920a9543a0` |

建议本机放置目录（尚未创建或验证）：

```text
E:\ResearchBackups\AdaPoinTr\BCSP_INPUT_DENSITY_V1\2026-10-26_development_eval
```

由用户完成下载并确认本机位置。服务器和Windows不自动同步；本次服务器审计不等于本机备份核验。收到下载位置后，先按本清单核验四个文件，再执行已冻结的本机统一评分；本轮未计算任何模型误差、候选差值或bootstrap结果。

## 评分及解释边界

主终点保持A1未知原始表面E_G→预测点的面积加权P95（mm），并同时检查J切壁接口覆盖、逆向离群及固定控制。按source内五缺损等权汇总，再做16k−8k配对比较与固定10000次bootstrap、seed20261024。

此次通过证明预测产物满足已冻结执行与完整性合同，不证明16k更优、连续实体接触无缝、临床安全或Mamba收益。资源为采样监测，非专属cgroup硬限制。四模型仍是B0 AdaPoinTr、固定seed0、开发集两折比较。

审计报告SHA256：`09219c002b3e9018f3faf5f424c5750ed23f4507c7dcf897295a786f25644a52`。完整机器证据：audit_report.json；精确下载清单：download_manifest_v1.json；本机核验用哈希表：download_SHA256SUMS_v1.txt。
