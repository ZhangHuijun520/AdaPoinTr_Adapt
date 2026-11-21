# Cranial-BCSP-FullMamba · BCSP-FCSP

[完整实验报告](evidence/outputs/fcsp_P5_preparation_20261121_v1/Cranial_BCSP_FullMamba_BCSP_FCSP_完整实验报告_zh_v1.md)

两折、两臂、seed0 的固定粗结构残差头对照。P5 有 630 行病例评分，P6 按 42 个来源作分折配对判定，结果为 `DO_NOT_ADVANCE`。

- `evidence/docs/` 保存协议与修订依据。
- `evidence/outputs/` 保存隔离实现、阶段审计、病例评分和 P6 来源 bootstrap 矩阵。
- `training/` 保存四组经冻结哈希核验的逐步训练指标及资源、初始化和完成记录。
- `checkpoint_identities.json` 保存四份残差头和两份继承的 G2 母版权重的核验信息。恢复时按折使用 G2 和对应的残差头。
- `public_files.sha256` 核对本文档及归档内容。运行脚本保留了原始路径和环境绑定，迁移执行需重新绑定。

预测数组、原始数据、特征缓存和权重使用本机存档。本归档用于阅读和核验实验，不是独立可运行的数据分发。
