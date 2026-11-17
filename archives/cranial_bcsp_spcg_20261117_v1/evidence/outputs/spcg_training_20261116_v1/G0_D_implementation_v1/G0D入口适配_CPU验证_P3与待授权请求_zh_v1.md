# SPCG G0_D 入口适配、CPU验证、P3与待授权请求

日期：2026-11-16。本机限定implementation-only完成，唯一一批20项人工CPU检查通过，P3通过，最终运输包独立核验通过。本轮未连接服务器、部署、运行训练或重复GPU准入。

## 科研合同

G0_D为预定矩阵第四组，沿用本轮G0_C的FullMamba-LQI基线、原始learned coarse head及FC展开，不安装G1/G2空间探针头。8192输入、8192输出、256 coarse，loss、优化器、调度、精度及资源阈值不变。

使用已冻结的Fold D：63训练来源、315病例，21开发来源、105病例；本轮仅读取既有QC、manifest与order元数据，未读取真实NPZ payload或开发预测。正式训练固定3900更新、100轮、31200曝光、300drop；不按C折训练loss调参，不做BNCal、评价、resume或自动重试。

D折顺序文件原始SHA256：`4f68edd55912be0dccfb3d2a1cc72e499d3d499a36aa5f3788550145b3095720`。

数据根：`/home/jovyan/adapointr_work/PoinTr/data/bcsp_geov1_foldd_8192_seed0_v1`。

G0 scratch初态仍绑定既有CUDA准入G0指纹：`366e5a6c752270708d30a2459933812d92accb8bb24f84adb29a2c6a15053f46`。不加载C折已训练checkpoint。D折三臂后续需保持同设备及共同初始化、批次顺序的配对块。

## 最小接入

新增隔离entry和bridge；原G0_C、G1_C、G2_C代码和科研模块保持不变。entry只接受G0_D，绑定D折数据根和order，使用实际D折QC及完整100轮order验证；三份C折正式冻结凭据作为顺序前提，并核验G0共同scratch初态。

bridge相对已验证G0_C仅改变折守卫C→D。继续复用原训练runtime及全部同forward观察逻辑，不新增正式forward/backward。UTC-first、源码及数据读取守卫、完整异常在guard关闭前保存和失败退出逻辑不变。

新run：`SPCG_G0_foldD_seed0_train_20261116_v1`。

新工具根：`/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_spcg_G0D_training_20261116_v1`。

资源合同继续为3600秒、8GiB RSS、20GiB Torch峰值、22528MiB SMI、1GiB输出；启动前至少8.5GiB可用空间。实际当前容量未在本轮重新核验，不因此前清理推断下一次启动必然满足。

## CPU验证与P3

唯一一批20项检查通过，结果见 `CPU_batch_v1/result.json`。覆盖：

- 实际G0母版forward、原coarse head、FC输出及coarse+dense loss梯度路径；骨干和loss计算使用人工替身。
- 完整authorize调用使用真实冻结D折元数据验证器和本机精确哈希别名，核验315病例、63来源及100轮顺序；授权/P3仅为人工fixture，不产生执行权限。
- C折、错误数据根、C折order、错误arm、缺失或伪造C冻结凭据、GPU选择器不一致及反向授权绑定均被拒绝。
- 直接运行新bridge，人工小模型完成3900次forward/backward观测，无optimizer更新，验证3900条几何记录、五个梯度观测步骤、loss组件和D折case顺序；这不是正式模型训练。
- 实际optimizer分组函数保留原coarse矩阵与bias权重衰减口径；UTC分派及异常处理与原实现一致，原导入链证据继承。

CPU验证未重跑实际Mamba、CUDA或生产cdist，不证明训练效果。生产模型初始化身份来自冻结CUDA/G0证据，未用人工模型冒充生产初态。

P3状态：`SPCG_G0D_TRAINING_LOCAL_P3_PASS`。最终request再次通过独立validate与launcher内存合同检查，运输包文件集合、内容哈希、压缩包哈希和bytes独立通过。未材料化真实授权回执、runtime、launcher或claim。

## 交付与下一步

最终request：`pending_transport_v1/payload/SPCG_G0_D_training_execution_request_v1.json`，状态 `AWAITING_EXPLICIT_USER_AUTHORIZATION`。

完整request SHA256：

`a877093becfd3e9763da36565c9401275e2f5ddd4f6d4f223fb4964ddf1d7fea`

运输包：`bcsp_spcg_G0_D_training_pending_20261116_v1.tar.gz`，20279 bytes。

压缩包SHA256：`fa101a7488b5e928d0eddaea6e4b4d330b9ba45776552164ae1434e67e63df60`。

上传同目录压缩包及 `.sha256`、`.bytes`、`.contents.sha256` 四文件至 `/home/jovyan/`。包内11个拟安装文件和1份映射，包括C折三份冻结凭据；D折QC、order、数据及provider为复用范围，执行前必须重新核验其实际存在及哈希。

之后需对request完整SHA256单独执行授权，才可重新核验当前容器、GPU、资源、全部复用资产、D折315输入及新目标，不覆盖安装并启动唯一一次G0_D训练。失败即停，不自动重试或resume，不运行评价或BNCal，无需重复GPU准入。训练后仍须独立正式只读冻结审计，再准备G1_D。
