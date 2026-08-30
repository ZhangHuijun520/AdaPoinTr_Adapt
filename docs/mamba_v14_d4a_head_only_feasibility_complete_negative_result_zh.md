# Mamba v1.4 D4-A head-only feasibility 完整负结果

## 1. 结论

D4-A 在冻结的 MUG500+ D4 M2 source100 四折开发协议上完成了 seed-0 head-only 训练和一次性 out-of-fold dev 评估。四折共 400 个病例，最终 query selector 命中 332 例、漏失 68 例，未达到预注册的 `400/400` 全病例安全门控。因此 D4-A 被正式冻结为负结果，T0/T1/T2 Round A 不得物化或启动，候选选择与保护数据访问继续锁定。

## 2. 冻结设计

- 来源颅骨：100 个，每个来源 4 个缺损病例，共 400 例。
- 四折：每折 75 个训练来源、25 个 dev 来源，来源级互斥。
- 候选：每例 8192 个点，13 维 non-leaky 几何描述符。
- head：`13-128-GELU-64-GELU-1`，仅训练 proposal head。
- selector：固定 top-8，加 top-256 排序池内 conditioned deterministic FPS-24，共 32 个 query。
- 训练：每折 50 epochs、1900 optimizer steps，只保存 final-epoch checkpoint。
- 评估：每折训练结束后仅打开一次 dev；不访问保护数据。
- 门控：四折合并后 400 个病例均须至少选择 1 个 reference-rim positive candidate。

## 3. 结果

| Fold | Hits | Misses | Gate |
|---|---:|---:|---|
| A | 85 | 15 | fail |
| B | 80 | 20 | fail |
| C | 83 | 17 | fail |
| D | 84 | 16 | fail |
| 合计 | 332 | 68 | fail |

全部 required outputs 均为有限值，400 个病例配对和 100 个来源的折绑定均完整。失败不是数值异常、病例缺失或跨折泄漏造成的。

按缺损族统计，68 个 miss 分布为：`ellipsoid_large=11`、`ellipsoid_medium=23`、`ellipsoid_small=25`、`irregular_medium=9`。每种缺损族在冻结数据中各有 100 例，因此对应 miss rate 分别为 11%、23%、25% 和 9%。小型与中型椭球缺损的失败更明显，但四折 miss 数为 15、20、17、16，未表现为单一折异常。

## 4. Post-hoc failure decomposition

所有 68 个 miss 的 8192 点候选集中都存在 positive candidate，数量范围为 10 到 59，中位数为 22；但最终 32 个 query 的 positive count 均为 0。这证明 D4-A 的失败发生在 learned ranking 与固定 selector 的联合路径中，而不是 reference-rim positive candidate 在输入候选集中不存在。

冻结 CSV 只保存最终 32 个 query 的总 positive count，因此另行预注册并执行了 selection-inert、observation-only replay。Replay 加载四个冻结 final head checkpoint，对相同 400 个 out-of-fold dev 病例复现 logits、top-256、top-8 和 FPS-24；原 `332/400` 结果逐例精确复现，optimizer steps 和 model updates 均为 0。

- `ranking_miss_top256=2`：两个病例的 best positive rank 分别为 291 和 312，positive 未进入 top-256。
- `selector_dropped_all_pool_positive=66`：positive 已进入 top-256，但 mandatory top-8 和 conditioned FPS-24 均未保留 positive。
- 68 个 miss 的 best positive rank 最小值、中位数、最大值为 9、22、312。
- miss 病例在 top-256 内的 positive count 最小值、中位数、最大值为 0、4.5、12。
- 68 个 miss 来自 46 个来源颅骨，其中 20 个来源出现多个 miss，单一来源最多 3 个 miss。

这表明扩大排序池只能影响极少数失败。主要瓶颈是 learned score 未把 positive 推入 mandatory top-8，同时纯几何 conditioned FPS-24 不保证保留已位于 top-256 的 positive support。该结论是 post-hoc 机制解释，不修改原门控，也不构成对任何新 selector 的授权。

两个 top-256 ranking miss 为：`mug500plus__A0094__irregular_medium`（fold C，best rank 291）和 `mug500plus__A0292__ellipsoid_small`（fold A，best rank 312）。

## 5. 冻结决定

- D4-A all-case gate：`False`。
- D4-A 状态：`D4A_frozen_negative_all_case_gate_failed`。
- T0/T1/T2 materialization：禁止。
- T0/T1/T2 training：禁止。
- D4 candidate selection：禁止。
- seed rerun 或阈值修订：禁止。
- protected data：未访问，继续锁定。
- D4-A post-hoc：完成且 selection-inert；原门控保持不变。
- 下一步：归档 D4-A 完整负结果并停止当前 D4 Round A。

## 6. 可复现性

冻结结果目录包含 all-case CSV、completion receipt、中文结果和 `files.sha256`。四个 fold 目录分别包含 final head checkpoint、dev per-case CSV、fold summary、run receipt 和哈希清单。正式归档时必须同时保留 authorization lineage、四个 final head checkpoint、completion receipt、post-hoc 输出及运行环境凭据。
