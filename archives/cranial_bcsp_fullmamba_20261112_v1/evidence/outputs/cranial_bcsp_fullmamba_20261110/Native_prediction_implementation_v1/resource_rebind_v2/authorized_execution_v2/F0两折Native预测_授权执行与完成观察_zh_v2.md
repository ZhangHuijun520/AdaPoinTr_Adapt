# F0 两折 Native 预测：授权执行与完成观察 v2

日期：2026-11-11。状态：唯一一次获授权预测已结束；仅完成状态观察，尚未正式 post-prediction freeze audit。

用户上传v2运输包后明确授权request SHA256：`f1a222d9268adf33ffc32127bb62ad82c6b6cdf20748b0a68e8f2c1b97f13431`。

## 📋 执行与观察结果

| 项目 | 结果 |
| --- | --- |
| 当前容器 | shu-common-25721452-notebook-zv9bqd-0，UID1000 |
| GPU | RTX4090 D，UUID GPU-41b45aa3-f5e3-e609-53cb-9c48bc7716ed，驱动575.51.03 |
| 上传包 | 68663字节；SHA256 cb3c196c3620715dd068e23f4a002d032842fdde69da9dbfceb2e9df56d862a8，三个校验文件匹配 |
| 不覆盖安装 | 15目标全部新建并回读匹配；未覆盖原文件 |
| 启动前资产重验 | 源码、provider、依赖、配置、两份最终checkpoint和210个输入文件大小／SHA256匹配；未解码数组或反序列化权重 |
| 授权链 | 回执→SHA256→单向runtime→SHA256→launcher；独占claim后唯一一次tmux |
| 最终退出码 | 0 |
| 最终进程状态 | 固定tmux不存在，worker PID592已退出 |
| 预测／缓存文件观察 | 210份预测、20份context、10份8层trace |
| 日志行数观察 | 210条forward claim、210条inference manifest、423条resource记录 |
| 完成标志 | F0_CD_210_NATIVE_FORWARD_COMPLETE；PREDICTIONS_ARCHIVED_AWAITING_FREEZE_AUDIT |
| 运行失败标志 | 未发现failure.json |

操作stdout记录核验约1702831031字节，安装与材料化后仅启动一次。初次状态观察为初始化阶段，后续确认真实CUDA预测已进展到48例，再观察到210例及归档完成；最后确认退出码0和会话／worker均结束。未自动重试、追加forward或重复GPU preflight。

最后一条资源记录阶段为all_complete，报告耗时115.403秒，RSS1882226688字节、Torch峰值allocated241075712／reserved289406976字节；该条全部资源子条件通过。这些是末条值及其累计Torch峰值，不能代替全日志独立复核或声称RSS／SMI全过程峰值已经审计。

## 🔗 固定路径与执行凭据

安装根：`/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_f0_CD_native_prediction_20261111_v2`。

结果根：`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/F0_CD_native_development_20261111_v2`。

tmux：`bcsp_f0_CD_native_eval_20261111_v2`；主日志 `launch.log`，PID文件 `worker.pid`，退出码 `exit_code.txt`。

授权回执SHA256：`a15e2fcfdcd82374e91441a39664b0cf9458125aa7557619de669677993bbabc`。

runtime SHA256：`e5dff476fd07cc9a657803ece845735373a6e0f832b52933a783c670e8de53ff`。

launcher SHA256：`fb73080920dbbde589b48a0841b50f30c3a885a564f1681eb930e8ed6498b2a2`。

为执行此次已授权短调用，额外传输了原字节操作辅助脚本 `/home/jovyan/adapointr_work/PoinTr/third_party/f0_native_authorized_operation_20261111_v2.py`；它只负责固定包核验、映射安装、控制材料化和单次启动，不是模型或通用审计框架。控制目录保留安装核验与启动回执。未修改科研源码、provider、wheel或已有训练资产。

## ⚖️ 证据边界与下一步

本机保留原始传输stdout／stderr、单次本机操作claim、各阶段命令与返回码、启动观察和最终观察JSON。最终观察文件为 `final_status_observation_v2_result.json`；本次未独立重算服务器预测／归档的全量哈希，也未完整复核每模型状态／RNG指纹，因此不能将状态观察当作正式冻结审计。

运行日志存在timm导入弃用和Mamba缓存autotuning相关警告；未因此升级或安装任何依赖，任务实际退出码为0。沿用既有数值局限披露；本轮没有backward或optimizer step。

下一步需单独授权正式只读预测后冻结审计，核验210份预测、20份context、10份trace的完整清单及哈希、所有计数、两模型状态／RNG证据、全资源记录和压缩包／三个校验文件。通过后再下载、本机核验及准备统一CPU评分。本次没有执行评分、BNCal、训练或未来30次decoder干预，也不据此判断F0补全是否优于T0／M0。服务器归档尚未下载到本机长期备份目录。
