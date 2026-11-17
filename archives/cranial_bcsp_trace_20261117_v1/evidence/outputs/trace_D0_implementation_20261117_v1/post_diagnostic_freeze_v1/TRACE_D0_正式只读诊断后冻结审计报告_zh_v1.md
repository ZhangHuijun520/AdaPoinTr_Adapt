# TRACE D0正式只读诊断后冻结审计

日期：2026-11-17。结论：**FORMAL_TRACE_D0_POST_DIAGNOSTIC_FREEZE_PASS**，14项判据通过。

## 完整性与计数

- 独立重新读取退出码0；固定tmux会话与worker PID均已不存在。
- 80条逐次claim和80条trace清单与冻结病例顺序、输入、归一化及checkpoint身份一致；四模型各20次，40个预定病例，不替换或追加。
- loss、backward、optimizer step、warmup、retry、BNCal及训练计数均为0。
- 四模型参数／buffer状态及CPU/CUDA/Python/NumPy RNG运行前后证据一致。
- 授权回执、runtime、launcher新鲜哈希与本机已授权材料一致，单次claim绑定正确。

## 产物与归档

- 结果目录精确包含92个文件及`traces`、`tmp`两个目录，无额外或缺失文件、无路径链接。
- 80个NPZ逐文件SHA256与清单一致；逐一核验字段名、shape、FP32／int64 dtype、C顺序及ZIP CRC。
- G1只保存实际ALL256字段；G2包含实际`index[256,8]`和`native_d2[256,256]`，未伪造G1邻域。
- 归档84个普通成员全部流式回读并重算SHA256，与磁盘文件、内容清单及归档回执一致。
- 全目录总大小169710432 bytes，包含归档，未超过1GiB。

归档文件：

`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/TRACE_D0_memory_evidence_20261117_v1/development_predictions_v1.tar.gz`

大小：84179082 bytes。

SHA256：`509dde04102c49ab0de13f9e1d8821491a6371109cf5f1934d8cc585ad03feb9`。

对应三个校验文件位于同目录，名称为上述完整文件名后追加`.sha256`、`.bytes`、`.contents.sha256`。

## 资源证据

161条资源记录的顺序精确为80组before／after及1条complete。根据实际值独立复算所有阈值，与记录checks一致，全部通过：

| 指标 | 实测记录峰值／最低值 | 合同 |
|---|---:|---:|
| RSS峰值 | 2028949504 bytes，约1.89GiB | ≤8GiB |
| torch allocated峰值 | 241082368 bytes，约230MiB | ≤20GiB |
| torch reserved峰值 | 285212672 bytes，272MiB | ≤20GiB |
| SMI显存峰值 | 722MiB | ≤22528MiB |
| 最后资源记录耗时 | 43.824秒 | ≤900秒 |
| 记录中的最低磁盘空闲 | 7789871104 bytes，约7.25GiB | ≥4GiB |

耗时是运行监测器口径，不是CUDA端到端正式速度benchmark；最后资源记录位于压缩前，最终进程退出码为0。资源采样不等于硬隔离；SMI PID只作诊断，不宣称跨命名空间独占归属。

## 审计边界与下一步

本次不导入模型或包内源码，不调用forward、不读取GT、不重放评分或计算空间关联；服务器写入为0。有限值在冻结运行入口的实际断言中核验；本次独立复核字节、NPZ结构和CRC，没有再次数值遍历以计算科研结论。

14项机器可读判据见`formal_freeze_verification_v1.json`。审计源码、原始stdout/stderr及三部分远端结果均保存在本目录。

下一步下载归档及三个校验文件，完成本机大小／SHA256／成员核验后，再准备单独授权的CPU历史重放与空间证据分析。当前不能判断探针支撑假设是否成立，不授权G3或训练。
