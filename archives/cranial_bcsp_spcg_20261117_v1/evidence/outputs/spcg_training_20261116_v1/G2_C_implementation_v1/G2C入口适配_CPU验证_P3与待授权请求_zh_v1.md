# SPCG G2_C 入口适配、CPU验证、P3与待授权请求

2026-11-16。本机 implementation-only 完成，唯一一批24项人工 CPU 检查通过，P3通过。未连接服务器、部署、启动训练或重复GPU准入。

## 科学合同

G2使用固定Sobol256探针和每探针8个最近Memory，保留冻结head、factory、U、H和母版源码。输入8192、输出8192、coarse256，原FC展开及loss不变，不添加残差、clamp、额外监督或开发集选择。固定3900步、100次遍历、31200曝光、300drop，复用Fold C原315病例、63来源和完整批次顺序。

相同scratch母版与原H字节初始化，不加载G0/G1训练权重。G1/G2的完整初始状态指纹相同：`3cfdbac9149b99e24ea6641fb9e00cf975754ad21c7a88fc6d34e17e01724ab9`。arm选择本身不进入state_dict；相同参数字节不意味着两种聚合公式输出相同。

新run为 `SPCG_G2_foldC_seed0_train_20261116_v1`。资源阈值保持3600秒、8GiB RSS、20GiB Torch峰值、22528MiB SMI、1GiB输出及原磁盘余量合同。当前实时资源未在本轮核验。

## 实现与边界

新增隔离的 `bcsp_spcg_G2_C_training_entry_v1.py` 和 `bcsp_spcg_G2_C_training_bridge_v1.py`，原G0/G1文件及科研模块不变。entry只允许G2_C，通过原factory安装G2，并核验scratch母版、U/H、母版源码和准入初态；新增G1正式冻结凭据校验，要求同折、相同计数、相同顺序和相同完整head初态。保留G0冻结前提。

bridge相对G1仅改变arm守卫。原训练runtime、优化器、loss、调度和日志生命周期不变。保留UTC优先分派、guard关闭前保存异常及失败退出；沿用3900条几何日志及五个指定步骤的总loss Q梯度观测。

## 验证与P3

唯一一批24项CPU检查通过，记录见 `CPU_batch_v1/result.json`。覆盖实际G2 head/factory及原母版forward/FC接口、稳定k8选邻、直接Q生成、旧head移除、U/H字节、G1/G2同初态但不同输出、S/F/z梯度，以及完整authorize元数据验证、315病例与100轮顺序、错误arm/初态/GPU/授权拒绝、POSIX启动路径和实际optimizer分组函数。

完整authorize检查使用真实冻结元数据验证函数和同哈希本机文件别名；授权与P3仅使用人工fixture，不构成正式执行授权。encoder/decoder计算和loss使用人工替身；未重跑真实Mamba或生产cdist。导入链与异常策略部分验证继承既有CPU证据，没有把它们表述为本轮重新执行或训练效果证据。

静态准备中遇到Windows文件列表默认编码及不可访问长路径，已在测试启动前完成文件索引与精确别名处理；另补齐远端凭据名称与本机冻结结果名称的别名。本轮CPU批次仅执行一次，生产源码及守卫未因这些本机问题放宽。

`training_P3_v1.json` 汇总本轮验证、既有CUDA准入及原训练生命周期依据。最终request经过独立validate与launcher内存合同检查；真实授权回执、runtime、launcher和claim均未材料化。

## 待授权交付

request：`pending_transport_v1/payload/SPCG_G2_C_training_execution_request_v1.json`。

状态：`AWAITING_EXPLICIT_USER_AUTHORIZATION`。

完整SHA256：

`f55806333bf52eef358aa718a77b3e7bbc58f2dd59e5de341d56f8ab9df73322`

运输包：`pending_transport_v1/bcsp_spcg_G2_C_training_pending_20261116_v1.tar.gz`，20,390 bytes。

压缩包SHA256：`c5993b324c3fcd735bdcd64df1c4ccadfa36de97476a7326dc3788eac15cc3c3`。

同目录 `.sha256`、`.bytes`、`.contents.sha256` 组成四文件上传集；共10个拟安装文件与1份映射，包含G0和G1正式冻结凭据，不重新运输大数据或U/H。

上传后需对上述request完整SHA256单独执行授权。届时重验当前容器、GPU资源、上传哈希、复用资产、315训练输入、顺序、父凭据和全部新目标，才可不覆盖安装及单次训练。失败即停，不自动重试、resume、评价或BNCal；无需重复GPU准入。本次尚不能判断G2补全效果。
