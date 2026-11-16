# RIVE Requery Fold D待授权训练request v1

状态：**AWAITING_EXPLICIT_USER_AUTHORIZATION**；execution_authorized=false。本轮仅本机制备和静态核对，无服务器调用。

## 冻结范围

- Requery_D、seed0、8192→8192、3900更新、100遍历、31200曝光、300丢弃，唯一一次从共同初态开始的训练，3600秒预算。
- 模型、既有entry/bridge/P3、依赖、D折315病例／63来源、D折完整批次顺序、优化器、loss和资源阈值不变。
- 绑定Static_D正式40项冻结审计，SHA256 `d1637699a9e1e6813920c5feeae014db72500ef71b15e21d447c2d2e479a86ea`。最终Static_D checkpoint仅作为完成证据，不用于warmstart；本臂仍使用共同原始初始化及冻结RF初始化。
- 新run ID：`SCQ_RIVE_Requery_foldD_seed0_train_20261115_v1`；新control/claim、tmux与output路径。未创建这些服务器路径，当前不存在性仍需后续只读核验。
- 47项本机静态检查通过；未重跑CPU测试、GPU准入或训练，静态核对不代表运行准入。

## request身份

本机文件：`E:\Codex\2026-06-06\mamba-ccf-c-1-high-resolution\outputs\scq_rive_training_implementation_20261115_v1\Requery_D_request_preparation_v1\SCQ_RIVE_Requery_foldD_seed0_train_20261115_v1_execution_request_v1.json`。

服务器计划路径：`/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rive_training_20261115_v1/SCQ_RIVE_Requery_foldD_seed0_train_20261115_v1_execution_request_v1.json`。

大小：15768字节。

完整SHA256：`c7519213883f5ffd7014576ab482beac4456ace3e4656606bcc40714672efba1`。

正式Static_D冻结凭据为逐字节复制，文件名 `Static_D_formal_training_freeze_v1.json`，大小20714字节；SHA256 `d1637699a9e1e6813920c5feeae014db72500ef71b15e21d447c2d2e479a86ea`。

## 未授权事项与下一步

没有材料化训练授权回执、runtime、launcher或claim；没有打包、上传、安装或启动。失败即停、不自动重试或resume，不运行评价或BNCal，不依据Static_D loss改变本臂设置。

当前资源未重新核对；原8,045,723,648字节空间观察发生于Static_D训练前，不能视为Requery_D当前可用空间。实际执行前仍需重验当前设备、冻结资产、315个D训练输入、至少6GiB空闲和所有新路径不存在。FIRST_SINGLE_RUN_ONLY表示仅准入本request，不声称其为矩阵首运行，完整矩阵容量不作认证。

下一步可单独冻结“本request＋Static_D正式冻结凭据”两文件补充运输包及不覆盖安装映射；entry/bridge/P3和点集均复用。之后分阶段只读上传核验、安装及正式冻结审计，再对完整request SHA256单独执行授权。
