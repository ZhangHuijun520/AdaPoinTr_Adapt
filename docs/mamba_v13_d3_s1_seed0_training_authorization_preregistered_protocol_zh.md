# Mamba v1.3 D3 S1 seed-0 训练授权预注册协议

> 本协议在四份 S1 配置完成 receipt-bound 物化后、任何 S1 optimizer step 前冻结。授权范围仅为 seed-0 fold A-D，禁止访问 locked holdout、S2 路径或启动模型选择。

## 授权对象

- 候选固定为 `S1`：dense 8192 点上的 2 mm contact-existence 与 GT-rim worst-10% tail objective；
- fold A-D 分别使用自身 training-only calibration receipt 中的完整精度权重；
- 顺序固定为 A、B、C、D，每 fold 100 epochs、epoch-100 checkpoint、完整 fold-train BNCal；
- 只在对应 development fold 上运行点指标与效率评估；
- 全过程使用 tmux，训练与评估保留 tqdm 进度。

## 授权前强制凭据

- Round-A 非运行模板锁与 MUG500+ M2 数据部署凭据；
- S0 seed-0 四 fold 冻结参考；
- S2 head-only feasibility 已冻结为负结果，S2 full route 继续关闭；
- S1 calibration completion、四份 fold receipt 和 tensor-hash hotfix 链；
- S1 materialization receipt、四份不可运行 YAML 及其 SHA256；
- 模型、数据集、loss、runner、评估、BNCal、run-record、completion 与 tmux 脚本哈希。

## 禁止事项

- 不得重新校准、平均、舍入、裁剪或人工修改 fold 权重；
- 不得根据 fold A-C 结果修改 fold D 或任何候选规则；
- 不得访问 locked holdout、旧 monitor、confirmation 或 official test；
- 不得自动启动 selection；
- 不得授权或训练 S2。

训练完成后只冻结 S1 seed-0 completion receipt；S1 相对 S0 的门控分析必须作为后续独立步骤执行。
