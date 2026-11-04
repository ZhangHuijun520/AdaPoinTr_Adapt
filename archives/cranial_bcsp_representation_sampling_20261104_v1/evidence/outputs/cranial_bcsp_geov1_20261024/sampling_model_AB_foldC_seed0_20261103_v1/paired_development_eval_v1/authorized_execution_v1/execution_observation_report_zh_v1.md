# Fold C V1／Morton两臂开发预测：授权执行与完成观察

## 结论

已按用户“已上传，单独授权上述完整哈希。”的执行授权，执行SHA256为 `76673ba94626253161dc70f0a33006d21c8094bced8148496c68c6c3490f0f4c` 的冻结范围。唯一一次预测任务已退出，退出码0，保存210条预测记录；V1与Morton各105例。此次完成观察不代替正式只读冻结审计，也不构成采样精度改善的结论。

## 安装与启动

使用冻结控制器原字节，经既有WSL＋hpc5000短入口调用。离线传输检查通过，最大行1068字节。控制器在任何写入前核验固定hostname／uid、上传包及四个sidecar、全部精确复用资产及两份checkpoint哈希、213个新文件目标与五个新数据目录／控制目录／输出目录不存在、GPU空闲及磁盘预算。

通过后独占创建冻结目录与213文件，逐文件读回核验；不修改原代码、训练数据、两份权重或历史产物。随后依次创建不可变execution scope、内层request、授权回执、单向runtime、单次launcher和claim。仅调用一次tmux启动。

- 当前容器：`shu-common-25721452-notebook-v2iwsa-0`
- 内层request SHA256：`2f6865ebc1a0557d8c1a3df589d8cca87df5312447eea1cab04cb6524c1c0414`
- tmux：`bcsp_sampling_pair_foldc_seed0_dev_v1`
- 输出：`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_sampling_ab_v1/bcsp_sampling_pair_foldC_seed0_dev_v1`

## 完成观察

两次只读观察分别记录196条和210条预测。最后一次观察：固定tmux已退出，worker PID33452已退出，退出码0，无failure记录。`inference_complete.json`标识为 `SAMPLING_PAIR_210_FORWARD_COMPLETE`；训练更新、BNCal、loss、backward均为0。

两模型各105次native eval／inference_mode，参数与持久BN状态的前后指纹相同，CPU／CUDA RNG指纹相同，Python／NumPy RNG不变断言通过。最后资源记录全部检查通过，记录elapsed44.006秒；RSS1,438,539,776 bytes，torch该模型峰值allocated205,540,352 bytes、reserved239,075,328 bytes。该值是最后一模型记录，不冒称整个任务的全局峰值。

归档已由执行器生成：

`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_sampling_ab_v1/bcsp_sampling_pair_foldC_seed0_dev_v1/development_predictions_v1.tar.gz`

完成记录报告大小18,902,839 bytes，SHA256：

`152a904ab7d5df856e1c8ea63320225f3c20c318c8c797127f5a89d869acc1dc`

以上归档哈希当前来自执行器completion记录，尚未经独立正式冻结审计重算；本机未下载或评分。

## 证据与后续边界

同目录 `explicit_grant.json`记录用户原文与唯一上下文哈希绑定；`execute_once_events.json`保留控制器实际材料化文件及哈希；`prediction_observation_02_result.json`保留完成观察。调用全过程保留原始stdout字节捕获及stderr哈希，没有读凭据文件。

当前尝试已消耗，不得重启或复用。下一步需单独授权正式只读预测后冻结审计，重新核验210预测、清单、归档与sidecar哈希、计数和状态／RNG证据。审计后再下载并单独授权统一CPU评分。本次未运行正式冻结审计、评分、训练或BNCal，也没有依据预测生成状态判断候选采样胜出。
