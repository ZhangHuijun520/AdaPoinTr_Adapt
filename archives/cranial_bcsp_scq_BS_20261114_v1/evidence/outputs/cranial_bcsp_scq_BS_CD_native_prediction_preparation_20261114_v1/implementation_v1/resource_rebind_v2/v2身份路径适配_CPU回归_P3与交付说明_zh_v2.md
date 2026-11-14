# v2身份／路径适配、CPU回归与待授权交付

## 本轮结果

仅在既有两个点集目录检查固定210个开发病例，共420个候选物理路径。210例均找到与原冻结大小和SHA256完全一致的文件，读取32936706字节进行哈希核验，未读取NPZ数组。

实际路径映射：

| 开发fold | 实际点集目录 |
|---|---|
| C | `/home/jovyan/adapointr_work/PoinTr/data/bcsp_geov1_foldd_8192_seed0_v1/points` |
| D | `/home/jovyan/adapointr_work/PoinTr/data/bcsp_geov1_foldc_8192_seed0_v1/points` |

目录名不作为病例分折依据。病例、来源、fold、输入大小及哈希、D-only归一化和同折配对均未改变；只纠正210条唯一输入的物理路径，420条模型输入记录对应更新。此前从训练根目录推导开发路径的判断错误已纠正，不归因于数据损坏或模型失败。

## 最小实现差量

新增v2专用入口，不覆盖v1。仅`authorize()`与`validate_evidence()`函数改变：

- 四份历史训练audit仍精确绑定原`t6ibfm-0`训练身份；不能将其改写为当前容器。
- 实际预测进程绑定`zbpgzu-0`，GPU UUID为`GPU-dabcc897-ac69-efac-4438-a6186dea9aaa`，驱动575.51.03，并检查CUDA_VISIBLE_DEVICES一致。
- 对精确输入index、当前身份及重绑定证据增加不可变哈希绑定。

其他函数／类AST均与原42项CPU验证版本一致，包括模型builder、SCQ模块、严格checkpoint加载、forward、420计数、状态／RNG、读取策略、资源监测、归档及launcher。未改变模型、权重、loss、资源阈值或采样规则。

所有四个模型将在同一当前设备／驱动上执行预测，但不能声称其与历史设备／驱动的预测位级等价。不重复已通过的GPU preflight。

## CPU验证及P3

唯一一批22项针对性CPU回归通过；未重跑旧42项。覆盖完整v2授权路径、新旧身份区分、旧GPU环境拒绝、210条路径仅发生物理映射变化、错误fold与原错误根目录拒绝、四份历史audit与新身份补充证据验证、错误哈希／交换audit拒绝、原预测函数AST保留、POSIX参数和新路径。

新P3通过，继承原42项实际人工模型／420接口验证，并明确本次22项仅覆盖身份与路径差量。没有真实forward、真实checkpoint加载或GPU调用；不宣称CUDA或科研效果通过。

## 待授权request与运输包

request：`pending_request_v2/payload/SCQ_BS_CD_native_prediction_execution_request_v2.json`。

完整SHA256：

`ce4b4b672a299934721d0b0f1fb22ea23de1bc41fd998ff94e10368fe1ebee5a`

运输包：`pending_request_v2/bcsp_scq_BS_CD_native_prediction_pending_20261114_v2.tar.gz`，79701字节。

SHA256：

`5f1330046c557551fb6ca5af130b30386d37d643dcc10bfc7b1c162dad2bae06`

包含18个不覆盖安装文件及安装映射，19个归档成员已逐一核验。三个配套校验文件为`.sha256`、`.bytes`、`.contents.sha256`。

v2状态保持`AWAITING_EXPLICIT_USER_AUTHORIZATION`。未材料化真实授权回执、runtime、launcher、claim或tmux。旧v1保留为身份不匹配停止、未安装未预测的历史尝试，不得沿用其执行授权。

上传v2四文件后，需单独授权上述v2完整request哈希，才可重新核验当前资源、上传包、复用资产、四权重及210输入，按新映射不覆盖安装，并唯一一次执行B_C／S_C／B_D／S_D各105例、共420次Native预测。失败即停，不自动重试或resume，不训练、BNCal或评分。
