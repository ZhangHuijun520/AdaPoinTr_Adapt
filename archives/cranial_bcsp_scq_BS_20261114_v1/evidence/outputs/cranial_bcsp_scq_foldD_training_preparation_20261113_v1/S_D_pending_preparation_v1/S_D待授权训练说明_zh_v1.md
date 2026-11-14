# Fold D SCQ-S待授权训练

日期：2026-11-13。状态：**AWAITING_EXPLICIT_USER_AUTHORIZATION**。

B_D正式只读训练冻结审计27组检查通过。S_D绑定实测B_D权重身份、正式audit及construction，使用已通过27项CPU检查和P3的D入口，不重复GPU准入或新增模型适配。

request：`pending_transport_v1/payload/SCQ_S_FoldD_training_execution_request_v1.json`。

完整SHA256：

`6c1e09d3366874f4f775061d9a957e1b5048dba0f295ff1127194bb798a90072`

## 1. 既定配对合同

相同`t6ibfm-0`、GPU UUID/driver/软件，原FoldD 63来源315病例，8k→8k、seed0、batch8、100遍历、3900更新、31200曝光、300drop。模型从scratch按原私有随机流构造，再加载既定SCQ初始化字节；不加载B_D checkpoint。原loss/optimizer参数分组、LR/BN schedule、clip、数值合同和全部资源预算不变。

B_D实测checkpoint SHA256为：

`f4bdd386c78eb3ebd7e764e9166761d18c3381acf0b0dc2ac91472533f5faf82`

此哈希只绑定配对证据，不将该checkpoint作为S训练输入。S_D与B_D的原始批次顺序及共有初始化必须匹配，不能根据此前训练loss调整数据、参数或步数。

最终实际authorize全路径已本机语义复核，315病例、native准入、D折基线、同设备及order均通过；授权字典仅在内存中用于静态检查，未生成真实执行控制文件。

## 2. 上传与新路径

四文件位于`pending_transport_v1/`：

- `bcsp_scq_S_foldD_training_pending_20261113_v1.tar.gz`
- 同名`.sha256`
- 同名`.bytes`
- 同名`.contents.sha256`

包大小 **22101 bytes**，SHA256：

`d370c964b8e785de1a6d57e2ff1836ac3479876a4ad1de8c5ee6fb37bdde3b89`

包内3个新目标（S_D request、B_D audit、B_D construction）与1份安装映射。复用原36个已安装payload及D入口，不重传模型、provider、权重或点集。

新目标仍在已存在安装根`/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1`，该根名称不决定所用数据折。新增文件、`control_S_D_v1`及输出必须全新、不覆盖。

tmux：`bcsp_scq_S_foldD_20261113_v1`。

输出：`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_S_foldD_seed0_train_20261113_v1`。

手动上传四文件到`/home/jovyan/`后，单独授权request完整SHA256，才可新鲜核验当前同设备资源、上传包、复用资产及315个D训练文件哈希，再安装并启动一次。失败即停，无自动重试/resume，不评价、BNCal或追加实验。

本轮未修改生产模型、部署、运行GPU或启动训练；材料只保存本机项目目录，未自动归档或推送GitHub。完整证据见`final_authorize_review_v1.json`和`delivery_receipt_v1.json`。
