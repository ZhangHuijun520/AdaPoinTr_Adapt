# RIVE Requery Fold C待授权训练request

状态：**AWAITING_EXPLICIT_USER_AUTHORIZATION**。仅完成本机制备与静态绑定核对，未操作服务器。

## 冻结范围

- Requery_C、seed0、8192→8192、3900更新、100 traversals、31200曝光、300drop，唯一一次scratch训练，3600秒。
- 复用已经安装/验证的同一RIVE entry与双臂bridge，模型、数据、初始化、C折完整顺序、优化器、loss、资源阈值及P3均不变。
- 绑定Static_C正式39项冻结审计，SHA256 `37c4c51ba73b28fbc43de7b37aeb00d898d63792655f1de81b29e9bc083990b5`。Static_C最终权重仅是证据，不用于warmstart；Requery仍从共同原始初始化开始。
- 全新run ID、控制/claim、tmux和结果路径。失败即停，不自动重试、resume、BNCal或评价。
- 37项静态绑定检查通过；没有重跑CPU验证或GPU preflight，也没有新增模型实现。

request完整SHA256：

```text
45d37fc024dd4e97a82cd08c93ad25cebfcbd4a4f74ae8b2be9d22e4536392de
```

request大小15777字节。服务器计划路径：`/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rive_training_20261115_v1/SCQ_RIVE_Requery_foldC_seed0_train_20261115_v1_execution_request_v1.json`，本轮尚未上传或写入。状态为待授权，execution_authorized=false；没有材料化生产授权回执、runtime、launcher或claim。

## 资源与下一步

不沿用Static_C之前8.49GiB作为Requery当前可用空间；request明确当前空间未重查，执行前必须重新核对同设备、复用哈希、315训练输入、至少6GiB空间和新路径不存在。capacity字段FIRST_SINGLE_RUN_ONLY沿用既有入口schema，含义为仅此一个request的空间准入，不是声称Requery是矩阵首运行。完整矩阵空间仍未认证。

下一步可单独冻结**两文件补充运输包与不覆盖安装映射**：本request及Static_C正式冻结凭据。entry、bridge、P3和点集均复用，不重复运输；完成上传核验后，仍需对request完整SHA单独执行授权。不要直接授权未知当前资源的新设备迁移，也不要依据Static_C训练loss调整Requery配置。
