# LQI 两折 Native 预测：正式只读冻结审计报告 v1

日期：2026-11-11。结论：**FORMAL_LQI_CD_POST_PREDICTION_FREEZE_AUDIT_PASS，45/45 项检查通过。**

## 1. 范围和授权

本轮依据用户单独授权进行正式只读预测后审计。服务器写入、新 forward、backward、optimizer step、GT 数组读取、checkpoint 反序列化、GPU 计算、BNCal 和评分均为 0。审计只读取冻结资产的字节、已生成预测数组及日志；在本机保存证据副本。未下载预测压缩包，不声称已有长期本机备份。

request SHA256：`cab2831f27913766d7009101ec86d9a6e642a40b9330359dbfc8ff5928610fb6`。

容器：`shu-common-25721452-notebook-zv9bqd-0`，UID 1000。输出根：

`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/LQI_CD_native_development_20261111_v1`

## 2. 完整集合、计数与稳定性

- 退出码为 0；worker 及固定 tmux 均已退出，无 failure 或未知执行产物。
- 两折各 105 例，各 21 个固定开发来源；全部病例、顺序、输入 SHA256、checkpoint、归一化和输出文件绑定与冻结索引一致。
- 210 次唯一 pre-forward claim、210 条预测清单、210 条几何摘要；无额外调用、无旧 context／全层 trace 缓存。
- 全部 210 份预测仅含 `prediction[8192,3]` 和 `coarse[256,3]`，均为 FP32 且所有坐标有限。
- 输出精确为 224 个文件、5 个目录；安装为 14 个冻结文件、6 个控制文件，无未知文件或符号链接。
- 审计前后两次完整输出哈希相同，安装／输出内容相关属性指纹相同；指纹不含 atime，避免正常读取造成误报。
- 267 个冻结资产重新核验大小、SHA256 及读取期间稳定性，覆盖两个最终 checkpoint、210 个输入、复用代码／provider／配置／元数据及准入文件；不反序列化权重或输入 GT。

## 3. 执行合同、模型身份及状态／RNG

授权回执、request、runtime、单次 claim、launcher 渲染字节和启动回执的单向哈希链匹配；安装回执确认零覆盖。CPU 46 项及本机 P3 的源码绑定保持一致。

两个模型的保存 construction evidence 均确认真实 LQI：`F0-LQI-implementation-v1`、`F0-LQI-v1`、`query_aligned_local_memory_interleaving`、交错条件 query 出口语义、零新增学习参数，母版 M0 身份和共有初始化不变。记录中未注册禁止的 attention 模块。这里不将该模块清单扩展为对所有底层 CUDA kernel 的普遍证明。

两折分别满足：参数及持久 BN 状态 SHA256 前后相等；CPU／CUDA RNG 哈希以及 Python／NumPy 完整 RNG 序列前后相等，格式有效；eval/inference_mode；每模型 105 次 forward，BNCal／optimizer／backward 均为 0。状态核验依赖绑定实现和保存的前后指纹，不重新构建模型或加载 checkpoint。

| 模型 | 状态指纹（前后相同） | RNG整体记录摘要（前后相同） |

|---|---|---|
| C_LQI | `cff10568bf08bfb2b9f9ee81910e5f6fe1a8b59945545752550d7a888cb3a4f6` | `3f618f32120aecdc57eb0e00a1c311be176549bcea4e5f3a55e8496fc89d0a6b` |
| D_LQI | `ab4187f4d1892ed567e26e468aac94b1d06f29356a08425324e4198771f00eb8` | `3f618f32120aecdc57eb0e00a1c311be176549bcea4e5f3a55e8496fc89d0a6b` |

## 4. 资源与几何日志一致性

423 条资源记录的阶段／调用序列完整；全部阈值子条件依据实测值独立重算通过，时间单调，资源日志无失败子条件。

| 实测采样量 | 数值 |

|---|---|
| RSS 峰值 | 1946484736 字节（约 1.813 GiB） |
| Torch allocated 峰值 | 241075712 字节 |
| Torch reserved 峰值 | 281018368 字节 |
| SMI 设备显存采样峰值 | 717 MiB |
| 最后资源采样时长 | 58.487 秒 |
| 当前输出总大小（含压缩包） | 40017931 字节 |

这些是运行资源观测，不是独占资源硬隔离或标准性能 benchmark；PID 信息只作诊断。

全部 210 份已存点集的无 GT 几何摘要经独立 NumPy 重算通过，最大统计绝对差为 0.0。该检查证明日志与数组一致，不证明预测形状或接口准确。

## 5. 归档与下载清单

归档精确包含 216 个成员：210 份 coarse+dense 预测及 6 个日志／完成证据。全部成员的名称、大小、哈希与当前服务器文件逐一一致，无服务器解压写入；归档及三个 sidecar 与 completion 和新哈希结果一致。

同一服务器目录下待下载四文件：

| 文件名 | 字节数 | SHA256 |

|---|---:|---|
| `development_predictions_v1.tar.gz` | 19642001 | `fbb06d406a4fd705df3c30463b32dc31f4b728a33546fed01dd142458f6f876e` |
| `development_predictions_v1.tar.gz.sha256` | 100 | `c3f88f8e7a29953e457d1b20576a044aba6da7a69bc9e6a17f618d47a29ffcc9` |
| `development_predictions_v1.tar.gz.bytes` | 9 | `cb0d3dca5a67e470d175ef0fa257054fea16fb40733b1c0a27a99f90a33ce23c` |
| `development_predictions_v1.tar.gz.contents.sha256` | 24174 | `4a92ee27809ccfd470cde92f4b096aa8004328cb5c4e775a4a3f72a4d5e04e67` |

建议本机长期保存目录：

`E:\ResearchBackups\AdaPoinTr\BCSP_FULLMAMBA_LQI\2026-11-11_native_development_eval`

机器可读清单：`download_four_files_manifest_v1.json`，其中给出服务器精确路径、大小和 SHA256。当前 `local_archive_verified=false`，不能据本轮审计删除服务器归档或原始结果。

## 6. 结论与下一步

本次两折 210 次 Native 预测的执行合同、计数、身份、完整文件集合、状态／RNG、数组和归档冻结证据通过。尚未进行 GT 评分，因此仍不能判断 LQI 相对 F0 的补全精度和接口吻合是否改善。

下一步下载上述四文件，在本机核验压缩包、sidecar、精确成员集合和逐成员哈希；之后再准备与已冻结 F0 的统一 CPU 评分入口和待授权 request。保持原指标、阈值、归一化、病例及来源等权统计，不追加训练、调参、筛选病例、F0 再预测或 GPU preflight。
