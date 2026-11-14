# Fold C SCQ-S待授权训练

日期：2026-11-13。状态：**AWAITING_EXPLICIT_USER_AUTHORIZATION**。

B_C正式只读训练冻结审计24组检查通过，原始checkpoint实测SHA256为`9c4352355d001404e6e43a461244b6a2134884974cf8fba616ec0065c1001418`。本S_C request绑定该审计及B_C构造记录，仅准备、不执行。

请求文件：`pending_transport_v1/payload/SCQ_S_FoldC_training_execution_request_v1.json`。

完整SHA256：

`1aed46b99b11f83b6707b1a3fe81b7e90a971ec7419019327d3c224b2d2adc86`

保持同一`t6ibfm-0`、同GPU UUID/driver/软件合同。S_C从scratch使用原LQI私有初始化流及已冻结SCQ初始化字节，不加载B checkpoint；同315训练病例、63来源、8k→8k、seed0、batch8、100遍历、3900更新、31200曝光、300drop。原loss、optimizer分组、BN/LR schedule、数值设置、监测预算不变。不根据B训练loss修改配置，不重复GPU准入。

生产入口继续使用已通过UTC修正的`bcsp_scq_training_entry_v2.py`，无需新模型/入口适配或重跑人工测试。完整实际authorize路径已本机核对，基线冻结、设备、批次顺序和共有初始化均匹配；人工授权字典只存在内存，没有生成真实控制文件。

本次仅新增3个不覆盖安装目标：S_C request、本次B_C正式审计副本及B_C模型构造副本。既有29个安装payload复用、重新核验；不复用B_C claim或输出。所有新文件位于已有安装根，使用新`control_S_C_v1`与新运行目录。

新tmux：`bcsp_scq_S_foldC_20261113_v1`。

新输出：`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_S_foldC_seed0_train_20261113_v1`。

本机运输目录`pending_transport_v1/`内四文件：

- `bcsp_scq_S_foldC_training_pending_20261113_v1.tar.gz`
- 同名`.sha256`
- 同名`.bytes`
- 同名`.contents.sha256`

压缩包21138 bytes，SHA256：

`c04bcbe09c46815540f9c7b4b4f093e4768c85a45588798fdc4ae8e407413d51`

手动上传至`/home/jovyan/`，再单独授权request完整哈希。执行前重新核验当前身份、同GPU、上传、已安装资产、315训练文件及原资源阈值；3新目标/control/output必须不存在，不覆盖写入。失败即停，无自动重试/resume，不运行BNCal、评价或FoldD。

本轮服务器操作只有只读B_C审计；没有S_C安装、GPU运行或训练。详见`final_authorize_review_v1.json`及`delivery_receipt_v1.json`。
