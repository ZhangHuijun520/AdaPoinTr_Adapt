# SPCG G2_D 入口适配、CPU验证、P3与待授权请求

2026-11-17。本机限定implementation-only完成。唯一一批32项CPU检查、P3及最终运输包独立核验通过；未连接服务器、部署、训练或重复GPU准入。

## 科学与设备合同

G2_D复用冻结的局部k=8 Memory摘要、固定Sobol256探针与共享H、1416维读出和直接Q生成公式，不修改head、factory、U/H、loss或decoder。8192输入／8192输出、256 coarse，固定3900步、100轮、31200曝光、300drop。

与G1_D保持同一GPU `GPU-4b19574a-832d-b4fe-e655-a57462954d6a`、当前hostname `shu-common-25721452-notebook-yxwd3w-0`，相同D折order、完整初态及训练合同。共同完整初态指纹为 `3cfdbac9149b99e24ea6641fb9e00cf975754ad21c7a88fc6d34e17e01724ab9`。从scratch构建，不加载G0/G1最终权重。

启动6GiB、运行期间4GiB、单次输出1GiB及原CPU/GPU内存和3600秒预算保持不变。G0_D仍为跨设备参照，不能声称与G1_D/G2_D严格同设备。新设备状态和存储余量仍需执行前重新核验。

## 隔离实现

新增G2_D专用entry和bridge。entry复用已验证的新设备及6GiB守卫，切换到既有G2构建，增加G1_D正式冻结凭据的精确读取与检查，要求相同完整初态、D折order、GPU UUID及对应G1_D request哈希；保留G0_D共同scratch母版和计数核验。

bridge相对G1_D仅改变arm守卫，原训练runtime、3900条几何日志、五个总loss Q梯度观测步骤、UTC-first及异常收尾保持不变。模型、数据、采样、初始化字节及既有科研源码未改动，不根据训练loss调参。

## CPU与P3

唯一一批32项CPU检查通过，记录位于 `CPU_batch_v1/result.json`。覆盖实际G2 factory/head及母版forward/FC/loss接口、稳定k8选邻和局部聚合、直接Q、S/F/z有限非零梯度、U/H字节、完整authorize与D折元数据、跨折/身份/阈值/反向授权拒绝、G1_D凭据哈希及不同设备拒绝、优化器no-decay、共同初态和bridge差量。

母版计算中encoder/decoder与loss为人工替身，未重新运行实际Mamba、CUDA或生产cdist。真实D元数据通过同哈希文件别名核验，未读取真实NPZ payload。auth/P3 fixture不构成实际执行授权。G0_D的人工3900观测生命周期和原导入链证据继承，未冒充本轮重新执行。

P3状态 `SPCG_G2D_TRAINING_LOCAL_P3_PASS`。最终request独立validate和launcher内存合同、11个payload文件、压缩包SHA256、bytes和内容清单均通过。真实授权回执、runtime、launcher和claim均未材料化。

## 交付

request：`pending_transport_v1/payload/SPCG_G2_D_training_execution_request_v1.json`，状态 `AWAITING_EXPLICIT_USER_AUTHORIZATION`。

完整request SHA256：

`2885c64fca8717e16a57bdaac2ad5bbf6290b36539d893893d4ef161a0e807b9`

运输包：`bcsp_spcg_G2_D_training_pending_20261117_v1.tar.gz`，22774 bytes。

压缩包SHA256：`a9809c831ab1fa3aba196d533f1e80057ed4b3be505f7c32e0a1986e200c8f48`。

包内11个拟安装文件和1份映射，包括G0_D及G1_D冻结凭据。上传压缩包与.sha256、.bytes、.contents.sha256四文件到/home/jovyan/。新工具根为 `/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_spcg_G2D_training_20261117_v1`，新run为 `SPCG_G2_foldD_seed0_train_20261117_v1`。

上传后需单独授权上述完整request哈希；重验当前身份、同GPU、6GiB余量、复用资产/D315输入/order和全部新目标后，才能不覆盖安装并单次启动。失败即停，不自动重试或resume，不运行评价或BNCal。无需重复GPU准入。训练完成并正式冻结后，才准备预定矩阵的统一Native预测；本轮尚不能判断补全效果。
