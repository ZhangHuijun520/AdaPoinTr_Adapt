# S-ref_C runtime精确读取修订与v2待授权说明

2026-11-14。本轮只在新入口的已有精确只读守卫中追加`implementation.runtime`一条文件记录。一般读取根不变，旧目录没有整目录放行。旧入口、bridge、runtime、模型、初始化、数据、顺序、loss、优化器、3900步与资源阈值保持不变。

## CPU与P3

唯一一次新版CPU批次36项全部通过；其中实际文件策略子进程成功在安装audit hook之后，用`source_module`读取、编译并加载原runtime。其依赖使用精确既有adapter和contract预加载，optimizer、loader和训练生命周期均未执行。

同一策略还拒绝runtime写入、错误SHA256和未绑定邻文件读取，并保留模型源码／初始化、训练专属NPZ、最终checkpoint及整数fd合同。测试仍包含人工S-ref一次forward／backward的接入检查，没有真实训练或更新。

新P3与最终request实际authorize路径通过；旧失败及其正式审计保留，旧request已消耗，不得复用。CPU通过不证明训练一定能启动或科研效果通过；进一步启动问题仍可能存在。

证据：[新P3](training_entry_P3_v2.json)、[静态一条绑定差量](static_review_v2.json)、[最终授权路径核对](final_authorize_review_v2.json)。完整CPU结果保存在上一层`cpu_runtime_read_batch_v3/result_v1.json`及`policy_stdout.bin`。

## v2待授权训练request

[SCQ_RF_Sref_C_training_execution_request_v2.json](pending_transport_v2/payload/SCQ_RF_Sref_C_training_execution_request_v2.json)

完整SHA256：

```text
b387a08bd2de575723d8f89a6f0c7fb1665590108eed0ef62c00d28b8394d4f1
```

状态保持`AWAITING_EXPLICIT_USER_AUTHORIZATION`。仍仅首个S-ref Fold C、8k→8k、seed0、3900更新、31,200曝光、300丢弃；从头初始化，不加载历史checkpoint，不执行评价或BNCal，不resume／自动重试，无需重复GPU准入。

新安装根为`/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v2`，7个新文件不覆盖安装；复用原metadata、bridge、runtime及已冻结GPU准入证据。

新输出为`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_Sref_foldC_seed0_train_20261114_v2`，tmux为`bcsp_scq_rf_Sref_C_train_20261114_v2`，授权回执／runtime／launcher／claim均使用新路径。

## 上传与执行边界

本机目录：`E:\Codex\2026-06-06\mamba-ccf-c-1-high-resolution\outputs\scq_rf_Sref_C_training_implementation_20261114_v1\runtime_read_hotfix_v2\pending_transport_v2`。

上传以下四文件到`/home/jovyan/`：

1. `bcsp_scq_rf_Sref_C_runtime_read_pending_20261114_v2.tar.gz`
2. `bcsp_scq_rf_Sref_C_runtime_read_pending_20261114_v2.tar.gz.sha256`
3. `bcsp_scq_rf_Sref_C_runtime_read_pending_20261114_v2.tar.gz.bytes`
4. `bcsp_scq_rf_Sref_C_runtime_read_pending_20261114_v2.tar.gz.contents.sha256`

压缩包28,322字节，SHA256为`22d98e9da7873cfe9c3ec5fa9ee6281fdfdfbebbc3fddab77ab868ba83a1d904`，8成员含7个payload及安装映射。

上传后须单独授权新request完整哈希，才可重新核验当前身份、复用资产和315训练文件、不覆盖安装并启动唯一一次新尝试。本轮未操作服务器、部署、创建真实执行控制文件、GPU准入或训练。
