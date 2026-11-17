# SPCG G1_D 入口适配、CPU验证、P3与待授权请求

日期：2026-11-17。本机限定implementation-only完成。唯一一批22项人工CPU检查、P3、最终request内存合同及运输包独立核验通过。未连接服务器、部署、训练或重复GPU准入。

## 科学合同与配对

G1_D继续使用固定Sobol256探针、全局256个Memory聚合、同结构共享H及直接Q生成；head、factory、U/H字节和母版源码均保持既有冻结身份。输入8192、输出8192、coarse256，原FC展开、loss、优化器和调度不变，不添加残差、clamp、额外监督或参数扫描。

绑定G0_D正式冻结证据，要求相同D折order、63来源315训练病例、3900更新、100轮、31200曝光、300drop。D折order原始SHA256为 `4f68edd55912be0dccfb3d2a1cc72e499d3d499a36aa5f3788550145b3095720`。使用共同scratch母版，不加载G0_D已训练checkpoint。

G0共同母版raw-state指纹为 `366e5a6c752270708d30a2459933812d92accb8bb24f84adb29a2c6a15053f46`；安装G1后完整初态绑定CUDA准入G1指纹 `3cfdbac9149b99e24ea6641fb9e00cf975754ad21c7a88fc6d34e17e01724ab9`。两种模型完整初态不同属于head替换的预期结果，不能混比其完整指纹。

## 实施

新增隔离 `bcsp_spcg_G1_D_training_entry_v1.py` 和 `bcsp_spcg_G1_D_training_bridge_v1.py`。entry将G1_C的折、schema、P3和配对前提限定到D，增加精确D数据根及order文件名核验；G0_D冻结证据按哈希读取并核对同折计数、顺序和共同scratch初态。原有G1构建、U/H加载、精确读取守卫及模型参数检查保持不变。

bridge相对G1_C仅改变fold守卫C→D，相对G0_D仅改变arm守卫G0→G1。继续复用原训练runtime和3900条同forward几何日志，指定step 1、39、390、1950、3900记录总loss Q梯度，不增加正式模型调用。

UTC-first、guard关闭前异常落盘与SystemExit(1)路径不变。原源码、G0/G1/G2科研模块、训练数据及资源阈值均未修改。新run为 `SPCG_G1_foldD_seed0_train_20261117_v1`。

## CPU与P3

唯一一批22项检查通过，权威记录为 `CPU_batch_v1/result.json` 中的count及完整checks列表。测试stdout保留了继承的旧短标签，不作为检查数量证据；未为修正显示标签重跑测试。

覆盖实际G1 factory/head及原母版forward/FC/loss接口、U/H冻结字节、旧head移除、Q梯度、完整authorize和真实D折元数据验证、错误折/数据根/order/arm/GPU/凭据哈希拒绝、单向授权合同、全局256聚合与直接Q公式、实际optimizer分组及SSM no-decay标记。

本轮还验证新bridge与G0_D已验证bridge的生命周期代码一致；G0_D的3900次人工forward/backward观察证据被继承，没有在本轮再次执行。实际Mamba、CUDA和生产cdist均未重跑。母版接口计算中的encoder/decoder和loss使用人工替身；完整authorize测试使用同哈希文件别名及人工auth/P3 fixture，不构成正式执行授权。生产初态身份仍由既有CUDA冻结和运行时断言约束。

P3状态为 `SPCG_G1D_TRAINING_LOCAL_P3_PASS`。真实授权回执、runtime、launcher及claim均未材料化。最终request通过独立validate和launcher内存合同，压缩包大小、SHA256、内容清单和9个安装文件再次独立核验。

## 待授权交付

request：`pending_transport_v1/payload/SPCG_G1_D_training_execution_request_v1.json`。

状态：`AWAITING_EXPLICIT_USER_AUTHORIZATION`。

完整request SHA256：

`3a19826c48c3d4f695c35eacb7e0238aa1c9c9479772fc97dc414c89421ed5a8`

运输包：`bcsp_spcg_G1_D_training_pending_20261117_v1.tar.gz`，19608 bytes。

压缩包SHA256：`9001fdb12f38fff185f86affbef8c9a7c5cbb136c7c1b70992c1756d4645a235`。

上传同目录压缩包及 `.sha256`、`.bytes`、`.contents.sha256` 四文件到 `/home/jovyan/`。包内9个拟安装文件及1份映射，包括G0_D正式冻结凭据；D数据、order、QC、provider、U/H等复用，执行前必须重新核验。

工具根：`/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_spcg_G1D_training_20261117_v1`。

资源合同保持3600秒、8GiB RSS、20GiB Torch、22528MiB SMI、1GiB输出及启动前8.5GiB余量。上一轮G0_D状态回传记录可用8983150592 bytes，约8.37GiB，低于8.5GiB阈值；该历史快照不代替当前实测，正式执行前应先重新核查容量并处理缺口，避免已知条件不满足时仍尝试启动。未授权任何删除。

上传后需对request完整SHA256单独执行授权，才可在条件满足后不覆盖安装并启动唯一一次G1_D训练。失败即停，不自动重试、resume、评价或BNCal。无需重复GPU准入；CPU通过不代表实际训练效果改善。
