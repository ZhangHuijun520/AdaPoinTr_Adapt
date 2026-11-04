# Fold C 欧氏／图距离：正式只读预测后冻结审计 v1

**结论：FORMAL_POST_PREDICTION_FREEZE_AUDIT_PASS。** 唯一一次预测已结束且退出码0；11组综合检查通过，210份预测及完整输出清单、213成员归档经独立只读重算核验。当前尚无补全精度或接口改善结论。

## 身份、授权与权限边界

审计记录UTC：`2026-11-04T06:34:33.717240+00:00`。容器：`shu-common-25721452-notebook-v2iwsa-0`，uid1000。外层request SHA256：`4fd0d2736e58530326c37d77fdbd5e76242339c36ea0a7905290a58d0b31ab43`；内层request SHA256：`276dd6d316ec042d46f30b69e292a40cc9541d2daff416bac2cd15f6e6850f19`。

本次单独授权仅用于只读冻结审计。使用既有WSL＋hpc5000短入口在内存执行stdlib审计，不写服务器，不导入模型／CUDA，不反序列化checkpoint，不运行forward、loss或评分。预测NPZ由stdlib读取NPY头和float32字节，检查有限性。没有运行任何新预测或训练。

## 完整清单与身份核验

| 项目 | 核验结果 |
|---|---|
| 退出码／进程 | 0；固定tmux已退出，worker不存活 |
| 两臂病例 | C_Euclidean_elimination 105、C_surface_graph 105；共同105病例、21来源 |
| 预测 | 210份逐个SHA256、大小、规范文件名、provenance核验；均finite float32、8192×3 |
| 完整输出 | 精确221文件、predictions目录和空tmp目录；无多余／遗漏／失败产物 |
| 安装／控制 | 213安装文件＋6控制文件的精确绑定、完整哈希和单向授权链通过 |
| 权重／依赖 | 两份checkpoint SHA256重新流式计算；精确源码、provider和环境资产哈希核验 |
| 配对证据 | 相同开发身份、来源排除、GT、D-only框架及固定共同点序元数据核验 |
| 归档 | 213成员，精确顺序与集合，无重复；每个成员大小／哈希与原文件一致 |
| sidecar | SHA256、bytes、contents SHA256文本精确匹配；四下载文件独立重算哈希 |
| 稳定性 | 完整输出树和读取文件的内容相关指纹审计前后不变，排除atime |

## 状态、RNG和资源

两个模型各105次native eval/inference_mode；参数及持久BN状态前后指纹相同。CPU／CUDA RNG前后指纹相同，Python／NumPy RNG不变断言为true；训练更新、BNCal、loss、backward计数均0。这是对保存证据及冻结实现的核验，不是独立重构模型状态或复跑CUDA。

| 模型 | 参数／BN状态指纹（前后相同） |
|---|---|
| C_Euclidean_elimination | `e892431c528f0eb613feb83cdc69206045b4cc97db26e6da6be916a3648e7880` |
| C_surface_graph | `665df181115d0afe27d07453085c57fe1e4e5e869d26acf6bce2229f613cffee` |

完整扫描并重新计算423条资源记录的phase／forward序列及阈值。RSS峰值1,498,861,568 bytes，SMI峰值678 MiB，torch allocated峰值205,540,352 bytes、reserved峰值239,075,328 bytes，记录推理预算耗时41.760秒，全部通过冻结阈值。PID按既定合同仅诊断，资源监测不代表专属硬隔离。

正式审计读取889,842,781 bytes，服务器核验耗时1.376秒，位于2GiB读取／90秒预算内。输出总大小38,160,694 bytes。

## 已冻结下载文件

服务器共同目录：`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_blue_noise_ab_v1/bcsp_blue_pair_foldC_seed0_dev_v1`

| 文件名 | bytes | 独立实测SHA256 |
|---|---:|---|
| development_predictions_v1.tar.gz | 18915240 | `135102bb6af6d18e45735ed63041c9fecb471a3a75556d7d2b9ea07d5a2ea2a6` |
| development_predictions_v1.tar.gz.sha256 | 100 | `eb095027001957c2c522103c1d16d2664d32f088eae55a047cdc870d69846a2c` |
| development_predictions_v1.tar.gz.bytes | 9 | `ab48ea17100dfe5eb057d613e1d5555fdd108b3ba2c5ca1a8c237d67ddc31790` |
| development_predictions_v1.tar.gz.contents.sha256 | 26849 | `15b4d9b175a5362e4afbbda0ed197f4dd3a70f735436492d21db0e626d10df45` |

## 下一步与结论限制

建议手动下载上列四文件到本机 `E:\ResearchBackups\AdaPoinTr\BCSP_BLUE_NOISE_AB_V1\2026-11-04_paired_development_eval`，随后只读核验大小、哈希及归档内容。此处仅建议目录，未创建目录、下载文件或声称已有本机备份。

核验完成后，按既定协议单独授权必要的两臂评分入口适配和统一CPU评分：主指标为来源等权的未知表面E面积加权P95，关键次指标为J P95、J/E Cover@2mm及共同GT CD-L1。当前不直接运行旧四模型评分工具，不选择病例或改变阈值，不计算正式gate。单折单训练seed仅描述性研究，不能凭预测完成或本次审计通过宣布图距离优于欧氏，更不构成临床吻合认证或Mamba收益结论。

完整机器报告：`audit_report.json`，SHA256 `4d3ee27a6a7a7c403da0a30a0998711226d653e8089482b96e37649f44b6bbd2`。该报告包含221文件完整输出清单、210预测及3个归档元数据成员清单、219安装／控制文件哈希和状态证据。
