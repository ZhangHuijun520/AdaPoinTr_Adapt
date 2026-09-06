# Mamba v1.6 D6-A R1 S2 certified fast-path artificial zero-step 完整结果

## 1. 实验目的

D6-A R1 的正式效率负结果显示，完整 SciPy global assignment 是主要延迟来源。S1 虽然把求解矩阵缩小到 tie-safe row-top32 union，但在冻结的 168 个人工样例上仅获得 128/168 的 slot/hard 精确一致，不能进入性能测试。

S2 的目标是在不改变冻结 R1 语义的前提下，仅对可证明无歧义的样例采用缩减矩阵求解；对 cutoff tie、near-tie 或无法证明全局最优唯一性的样例，必须独立执行完整 S0 并只返回 S0 输出。

## 2. 冻结实现与认证规则

- 输入固定为 `1 x 32 x 8192` float32 artificial descriptor logits。
- 保留完整 device-to-host transfer，并采用冻结的 CPU float64 epsilon adjustment。
- 每行保留第 32 大 adjusted score 及其全部并列项，union 按原候选索引升序排列。
- Cutoff guard 固定为 `256 * eps64 * max(1, row_max_abs_score)`。
- 对缩减矩阵最优解逐一排除 32 条已选边，执行 32 次 exact SciPy assignment，以最大可行替代 objective 构成 second-best。
- 仅当 `best - second_best` 严格大于冻结 numerical guard 时，返回缩减矩阵结果。
- 任何未认证样例均重新、独立执行完整 S0；不得复用未认证 S2 输出。

生产 R1 与失败的 S1 shadow 均未修改。

## 3. 数据与执行边界

- 使用与 S1 完全相同的 168 个人工 assignment matrices，共 7 个预注册 family。
- CUDA 设备：NVIDIA GeForce RTX 4090 D。
- S0 reference 与 S2 各执行 168 次。
- 本阶段 timing calls、warmup、timed runs 与 torch profiler traces 均为 0。
- 未构造 optimizer；optimizer steps 与 model updates 均为 0。
- 未读取 D6 development、confirmation、holdout、official test、checkpoint、NPZ、STL 或 sealed 数据。

## 4. 精确等价结果

| 硬门控 | 结果 | 要求 | 结论 |
|---|---:|---:|---|
| slot-to-candidate mapping | 168/168 | 168/168 | 通过 |
| sorted selected indices | 168/168 | 168/168 | 通过 |
| hard assignment | 168/168 | 168/168 | 通过 |
| adjusted objective | 168/168 | 168/168 | 通过 |
| finite outputs | 168/168 | 168/168 | 通过 |
| input state unchanged | 168/168 | 168/168 | 通过 |

S2 在所有冻结人工样例上逐位保持完整 S0 的 slot mapping、selected set 和 hard assignment，并保持 float64 adjusted objective 精确相等。

## 5. 路由完整性结果

| Family | Cases | Certified fast path | Complete S0 fallback | Exact |
|---|---:|---:|---:|---:|
| independent_normal | 64 | 64 | 0 | 64 |
| collision_heavy_shared_candidate_bias | 32 | 32 | 0 | 32 |
| identical_rows | 8 | 0 | 8 | 8 |
| exact_tie_groups | 16 | 0 | 16 | 16 |
| near_ties_float32 | 16 | 0 | 16 | 16 |
| shared_top32_adversarial | 16 | 0 | 16 | 16 |
| top32_cutoff_ties | 16 | 0 | 16 | 16 |
| **合计** | **168** | **96** | **72** | **168** |

Fast-path gate 要求至少 96/168，实际为 96/168；其中 independent-normal 为 64/64，collision-heavy 为 32/32。False-positive certificate 为 0。

72 个 fallback 中：

- `cutoff_tie_or_near_tie`：32；
- `global_optimum_not_certified_unique`：40。

所有歧义 family 均保守回退，没有出现未认证缩减输出泄漏。

## 6. 专业分析

S2 解决了 S1 的核心正确性缺陷。S1 的 selected set 在 168 例中始终一致，但 tie-resolution 会改变 slot mapping，说明“候选集合包含完整最优解”不足以保证求解器返回相同的冻结映射。S2 通过 cutoff guard、全局唯一性证书和完整 S0 fallback，把这种不确定性显式隔离，因此获得了 168/168 的严格语义等价。

路由分布也符合机制预期。连续随机和碰撞密集但仍具稳定唯一最优的 96 例全部通过认证；相同行、离散 tie、near-tie、共享 top32 和 cutoff tie 等 72 例全部回退。该结果支持“证书在无歧义样例上有选择性、在歧义样例上保持保守”的机制解释。

不过，本结果只证明语义与路由可行，不能证明性能改善。Certified fast path 每例需要一次缩减最优求解和 32 次 edge-exclusion 求解；fallback 样例还会承担认证前处理与完整 S0 的叠加成本。因此 S2 可能加速 96 个 fast-path 样例，也可能因证书成本而整体变慢。必须以包含 D2H、union、cutoff、33 次缩减求解、fallback 和输出构造的完整路径进行独立性能测试。

## 7. 结论与下一步

冻结状态为 `D6A_R1_S2_certified_fast_path_artificial_zero_step_passed`。S2 已通过全部等价和路由完整性门控，可以进入“单独预注册人工性能 benchmark 协议”的阶段。

下一阶段仅允许：

1. 比较完整 S0 与完整 S2 路径，包含 certificate 与 fallback 全部成本；
2. 固定 warmup、timed runs、CUDA synchronization、执行顺序和人工 suite；
3. 分别报告 fast-path、fallback 与总体 latency，且不套用正式 R0/R1 gate；
4. benchmark 结果另行冻结后，才讨论是否存在 production feasibility。

当前仍不授权 production R1 修改、formal-efficiency rerun、训练、seed-1、proposal confirmation、D6-B、candidate selection 或 sealed access。

## 8. 冻结结果哈希

- `files.sha256`: `5713a4fa4307cd0a68c8d429848b6055e2b0d888c2eea0c5e39cd9d965fcbeb6`
- `s2_artificial_equivalence_metrics.csv`: `be1ea8643a169293cf258bd39473557f8a40f72da31427b84cfc5fcc85677244`
- `s2_certification_routing_metrics.csv`: `182654d18b1c428f80f4f796449c35eafe17d782e11238fa7856811a302a4cc1`
- `s2_family_summary.csv`: `102a7c4d3b5c0dff5410f17a3f6d88c14b2d755267d9dde2eacb0ed2c7c79fd0`
- `s2_artificial_zero_step_summary.json`: `a3b9c5ede525f3b29e638abdc55f97c7367d8b760fb34d829d0472b3093813d1`
- `s2_artificial_zero_step_receipt.json`: `85d8a0946504bb02d471b0087df7d6a8ccb929c01dc40df031088c6143a9c061`
- `s2_artificial_zero_step_report_zh.md`: `a166d0fb514716d2e71477dc064243a3e0623a85c93477127f7f0d1d50e4df7b`
