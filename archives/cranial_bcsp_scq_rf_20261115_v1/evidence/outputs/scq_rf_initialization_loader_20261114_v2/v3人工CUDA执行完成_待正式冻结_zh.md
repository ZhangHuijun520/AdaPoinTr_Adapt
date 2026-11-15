# SCQ-RF v3人工CUDA执行完成观察

2026-11-14。对应request SHA256：`8a3d0173fa3cec9e737e384c9af99f37e996c79ef3e60bb5e99b14dc275f2cac`。

## 当前状态

唯一一次已授权v3任务已结束，退出码0；worker PID9235及固定tmux均已退出。服务器完成状态为`RF_NATIVE_CUDA_COMPLETE_PENDING_FORMAL_FREEZE`，**尚待正式只读post-CUDA冻结审计，不是训练准入或科研效果结论**。

安装前核验冻结容器`shu-common-25721452-notebook-zbpgzu-0`、GPU／资源、上传包及3个校验文件、55项复用资产大小与哈希均通过；8个新文件不覆盖安装及回读哈希核验完成。随后单向材料化授权回执／runtime／launcher，提交唯一一次tmux启动，没有自动重试。

## 完成记录中的计数与检查

| 阶段 | batch | forward | full loss | backward | optimizer step |
|---|---:|---:|---:|---:|---:|
| S-ref eval参考 | 1 | 1 | 0 | 0 | 0 |
| RF-Static eval | 1 | 1 | 1 | 1 | 0 |
| RF-Requery eval | 1 | 1 | 1 | 1 | 0 |
| RF-Static train模式 | 8 | 1 | 1 | 1 | 0 |
| RF-Requery train模式 | 8 | 1 | 1 | 1 | 0 |
| 合计 | — | **5** | **4** | **4** | **0** |

完成记录包含180次原生Mamba模块forward调用；这对应5次完整模型forward，不能算作180次病例预测。共有初始状态及RF两臂与同会话S-ref的初态输出一致性检查通过，各阶段实际Q2消费者合同检查通过。

四个RF阶段中，两头全部参数的梯度均存在且有限。原SCQ的W2与新增RF的V2权重／bias梯度有效；W1／V1梯度为零，符合输出层零初始化的预期。非零诊断头的上游可导性沿用先前CPU证据，本次没有追加GPU干预、optimizer或训练。

人工eval两臂loss均为0.4480944276，人工train模式两臂均为0.3931327462。它们仅是固定人工输入上的执行记录；零初始化时两臂预测一致是预期现象，不能据此判断重查询机制无效、有效或改善真实颅骨补全。

目前观察到的末期资源记录中，torch峰值allocated13,601,458,176字节、reserved14,852,030,464字节；对应记录的SMI占用14,651MiB，均在冻结阈值内。它们来自本次状态回读，完整资源样本及峰值仍应在正式审计中重新核算，不视为benchmark。

## 证据与下一步

- [启动回执](authorized_execution_v3/launch_receipt_v1.json)
- [结束状态观察](authorized_execution_v3/observation_1.json)
- 原始传输输出及安装／哈希核验记录保存在`authorized_execution_v3`。
- 服务器输出：`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_artificial_cuda_20261114_v3`。
- 服务器日志：上述目录下`launch.log`；完整记录位于`completion.json`、`events.jsonl`、`construction.json`、`resources.jsonl`及`payload_manifest.json`。

下一步应单独进行**正式只读post-CUDA freeze audit**，重新核验完整文件清单、哈希、精确计数、两种初始化绑定、同会话初态一致性、逐消费者、梯度、状态／RNG恢复及资源证据。本轮没有执行该正式审计、创建训练request或运行训练／BNCal／真实开发集评价。
