# SCQ-RF十例实际Memory采集：安装、执行与完成观察

_2026-11-14｜已按完整request哈希授权执行一次｜本报告不是正式post-diagnostic冻结审计_

## 执行结果

唯一一次采集已结束，退出码0；固定tmux会话不再存在，worker已退出；生成十份Memory NPZ，C折7例、D折3例。没有loss、backward、optimizer step、BNCal、warmup、重试或训练。

执行request SHA256：

`51ee9e42bc29c93002b71c8449b59ed14453aeb6d57cda242857e045cd536945`

本request已消耗，不得再次执行。原请求文件保持冻结字节，其历史`AWAITING_EXPLICIT_USER_AUTHORIZATION`字段不代表仍可重复启动。

## 启动前与安装核验

重新核验了当前`shu-common-25721452-notebook-zbpgzu-0`、UID1000、RTX4090D GPU UUID／驱动、Python、空闲显存、磁盘和固定会话不存在。上传包及三个校验文件通过；精确复用源码、配置、provider／环境及父证据哈希通过；S_C／S_D最终checkpoint与十份输入哈希通过。

全部新目标及输出路径先确认不存在，再不覆盖安装17个文件。随后按单向顺序创建授权回执、runtime和launcher，核验已安装`authorize()`及冻结证据，通过后独占创建单次claim并提交一次tmux。没有修改模型、provider、数据或科研公式。

本机调用使用原始字节捕获、WSL `--exec`和有界短命令；28个远端步骤均在执行前完成静态检查，最长命令1953字节。所有阶段回执及stdout／stderr原字节保存在本目录。

## 完成观察

执行记录报告10次完整forward、10次额外Q1处KNN；两模型的参数／持久状态和CPU／CUDA／Python／NumPy RNG前后记录一致。Native一致性检查在运行过程中逐例执行；本次状态观察没有重新独立读取全部十例进行数值复算。

归档路径：

`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_ten_actual_memory_20261114_v1/development_predictions_v1.tar.gz`

记录大小：17,595,353字节。

记录SHA256：

`d3d7ce69ac6b6be70073ae593dd4f4416a58fc695a372c7e41375250552c311a`

本次没有下载该归档、重新核验所有归档成员或分析邻域变化；上述归档数值来自完成记录，不冒充正式审计实测结果。

## 下一步边界

下一步应单独进行**有界只读post-diagnostic freeze audit**：重新核验完整文件／目录清单、17个安装目标及控制链、十例输入／权重身份、原始采集与归档哈希、精确调用与额外KNN计数、Native一致性、状态／RNG及资源记录；不运行forward、不加载模型、不重试。

正式冻结通过后，再根据实际Memory讨论N0／N1与条件描述量是否有可区分信息。本次启动及完成观察不构成RF有效性、CUDA科研准入或训练授权。

机器可读记录：[execution_completion_observation_v1.json](execution_completion_observation_v1.json)。原始观察：[observation_0.json](observation_0.json)。
