# Mamba v1.4 D4 候选、训练预算与门控预注册协议

> 本协议在 D4 M2 `100 source / 400 case` 独立生成审计通过后冻结。它定义 D4-A feasibility 与 T0/T1/T2 Round-A，但不授权训练、不选择候选，也不访问任何保护数据。

## 1. 顺序修订

现有总体路线合理，但 proposal feasibility 与 full training 之间必须避免循环依赖。本协议采用独立、仅依赖 partial geometry 的 13 维 high-resolution descriptor，不加载 completion checkpoint。D4-A 因而可以在任何 T0/T1/T2 full training 之前完成。

D4-A 每折只用 75 个 train source 训练 proposal head，对 25 个未参与训练的 dev source 做一次性评分。若 400 个 out-of-fold case 不是全部命中，则 T0/T1/T2 Round-A 全部禁止开始，防止在已知 proposal 不可靠时消耗新的 development。

## 2. 唯一的 high-resolution proposal

候选集合固定为 8192 个 partial 点，保持冻结 NPZ 中的原始顺序。每点 descriptor 固定为：

- normalized xyz：3 维；
- 到 16-NN centroid 的偏移：3 维；
- 16-NN 距离 mean/std/max：3 维；
- 协方差特征值除以 trace，升序：3 维；
- radial norm：1 维。

总计 13 维。kNN 排除自身，不做数据增强，不加入 defect type、GT mask、implant 或完整 skull 信息。

Proposal head 固定为 `13 -> 128 -> 64 -> 1` 的 GELU MLP，无 dropout，使用 case-balanced BCE。训练固定 50 epochs、batch 8、AdamW、`lr=1e-3`、`weight_decay=1e-4`、cosine decay 到 `1e-5`，只保留 final-epoch checkpoint。

## 3. 固定 selector

Rim budget 继续固定为 32，不扫描 query 数。selector 同时针对 P-D3 的 ranking 与 FPS 丢失，但参数由本协议一次性冻结：

1. 对 8192 个候选按 score 降序、候选索引升序排序；
2. 无条件保留 top-score 8 点；
3. 固定 ranked pool 为 top-256；
4. 在已保留 8 点的条件下，用 deterministic Euclidean FPS 补足 24 点；
5. FPS 距离并列时按 score rank、候选索引依次决胜。

这不是在旧 D3 上选择的最优参数；P-D3 只提供“ranking 与 selector 都需处理”的机制类别。

## 4. D4-A hard gate

全部 400 个 out-of-fold case 必须同时满足：候选 oracle 存在 positive、最终 32 anchors 至少保留一个 positive、必要输出有限、病例配对完整且未访问保护数据。任一病例失败，D4-A 冻结为 negative，Round-A 不启动。

通过后，四个 final proposal-head checkpoint 按 fold 冻结。T1/T2 只加载同折 head 且保持冻结；full training 不再用 GT rim supervision，也不重新训练 proposal head。

## 5. Round-A 候选

| 候选 | 冻结定义 |
|---|---|
| T0 | O0-xyz reference，256 global learned queries |
| T1 | 224 global + 32 high-resolution rim queries；加载同折冻结 D4-A head |
| T2 | T1 + 32 bounded support points；每个 rim query 的第 0 个 offspring 被 support point 替换 |

T2 offset 为 normalized-space `0.02 * tanh(raw_offset)`。总输出严格保持 `32 support + 8160 generated = 8192`。generated-only 指标必须排除 32 个 replacement support points。

Round-A 不加入 S1 dense contact objective。proposal head 也不在 T1/T2 内继续优化，从而把主要变量限制为 query allocation 与 support preservation。

## 6. 训练预算与四折执行

若 D4-A 通过，Round-A 上限为 `3 candidates x 4 folds x seed0 = 12 trainings`。每个 full run 固定：

- 100 epochs，total batch size 8；
- AdamW，`lr=1e-4`、`weight_decay=5e-4`；
- 沿用冻结 LambdaLR 和 BN scheduler；
- 不 early stop；
- 训练期间不评估 dev；
- 仅使用 final epoch checkpoint，并只用同折训练病例重校准 BatchNorm；
- 每个 candidate/fold 只做一次 dev evaluation；
- 禁止根据 dev 选择 epoch、checkpoint 或重新训练。

执行顺序固定为 T0 A-D、T1 A-D、T2 A-D。若中途出现实现错误，只能在证明尚未消费相应 dev 结果后做语义不变修复。

## 7. 安全门控

实验候选按以下顺序逐项通过：完整配对、全部必要指标有限、dense 2 mm zero-contact 为零、T2 generated-only zero-contact 为零、灾难数不高于 T0、induced 不多于 rescued、双向 contact relevance 事件向量逐项不高于 T0、Final 非劣、效率门。

灾难定义为任一必要指标非有限，或 `rim_contact_hd95_mm > 50`。Contact relevance 使用 `2/5/10/20/50 mm` 固定阈值；非有限值记为超限事件，不做数值填补。

Final 容忍量为 CD `+0.10 mm`、HD95 `+0.50 mm`、NSD@1 `-0.01`。效率上限为参数 `1.10x`、峰值显存 `1.10x`、中位 latency `1.25x` 同折 T0。

## 8. 晋级规则

T0 只是参考，不占实验 eligibility。T1/T2 至少一个通过全部 seed0 hard gates，才允许 seed1。seed1 运行同折 T0 与全部合格实验候选；seed2 运行 T0 与固定字典序得到的 provisional winner。若 T1/T2 均失败，则冻结 D4 negative，转向 local rim-context representation。

## 9. 当前权限

本协议锁只允许实现候选和执行零步 preflight。`D4A_execution_authorized=false`、`D4_training_authorized=false`、`selection=false`、`holdout=false`、`protected=false`。后续必须分别创建 D4-A execution authorization 和 Round-A runtime authorization，不能由本锁自动启动。
