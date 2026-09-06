# Mamba v1.6 D6-A R1 S1 exact-assignment artificial zero-step 冻结负结果

## 1. 实验目的

本实验评估隔离的 S1 assignment shadow implementation：在保留完整 `32 x 8192` D2H、CPU float64 epsilon 调整和同一 SciPy `linear_sum_assignment(maximize=True)` 的前提下，将求解矩阵缩减为各 slot 的 tie-safe row-top32 并集。预注册成功条件要求 168/168 人工病例的 slot mapping、hard assignment、排序后 selected indices 和 adjusted objective 全部与冻结 S0 完全一致。

本步骤只做 CUDA artificial zero-step 等价性验证，不计时、不运行 benchmark、不修改生产 R1、不训练、不访问 D6 病例或 sealed 分区。

## 2. 执行与谱系修复

首次授权测试暴露 S1 shadow module 缺少运行时 `torch` 导入。hotfix 只将 `torch` 从 `TYPE_CHECKING` 导入改为运行时显式导入，S1 算法与权限边界不变，生产 R1 SHA256 仍为 `2e71ff22800a8215001de6fb8963c3016b5056763b0e905a8149180578a75d43`。

随后发现父协议 JSON 经 Windows 运输后为 CRLF。其 LF 规范化 SHA256 与冻结版本完全一致；由该 CRLF 文件派生的 receipt 和 manifest 因绑定原始字节而变化。服务器通过冻结生成器在临时目录重建 canonical LF 父锁，逐文件匹配预期哈希后原子替换，并保留原 CRLF 派生锁和独立恢复凭据。协议语义、门控和授权状态均未改变。

## 3. 总体结果

| 门控 | 通过数 | 结论 |
| --- | ---: | --- |
| slot-to-candidate mapping 精确一致 | 128/168 | 失败 |
| hard assignment 精确一致 | 128/168 | 失败 |
| 排序后 selected set 精确一致 | 168/168 | 通过 |
| adjusted objective 严格一致 | 160/168 | 失败 |
| S0 列全部包含在 S1 union | 168/168 | 通过 |
| 输入状态未改变 | 168/168 | 通过 |
| 全部等价门控 | 否 | S1 冻结负结果 |

S1 union size 的 min/mean/max 为 `32 / 436.142857 / 981`。Timing、warmup、timed run、torch profiler trace、optimizer step、model update 和 D6 case access 均为 0。

## 4. 分族结果

| 人工族 | 病例 | slot/hard | selected | objective | union min/median/max |
| --- | ---: | ---: | ---: | ---: | --- |
| collision_heavy_shared_candidate_bias | 32 | 32/32 | 32/32 | 32/32 | 33/36/41 |
| exact_tie_groups | 16 | 16/16 | 16/16 | 16/16 | 484/509.5/529 |
| identical_rows | 8 | 0/8 | 8/8 | 7/8 | 32/32/32 |
| independent_normal | 64 | 64/64 | 64/64 | 64/64 | 945/963/981 |
| near_ties_float32 | 16 | 0/16 | 16/16 | 12/16 | 32/32/32 |
| shared_top32_adversarial | 16 | 0/16 | 16/16 | 13/16 | 32/32/32 |
| top32_cutoff_ties | 16 | 16/16 | 16/16 | 16/16 | 64/64/64 |

40 个 slot mapping 失配全部集中在 `identical_rows`、`near_ties_float32` 和 `shared_top32_adversarial`；8 个 objective 失配也只来自这三族。

## 5. 结果分析

所有 S0 选择列都被 S1 union 保留，且排序后的 32 个 selected indices 在 168 个病例中全部一致。因此失败不是 row-top32 裁剪遗漏全局最优候选，也不是候选集合发生变化。

失配发生在退化或近退化矩阵，且 union size 恰为 32。完整 `32 x 8192` 与缩减 `32 x 32` 问题虽然包含相同最终列集合，但 SciPy 求解器面对大量等价或近等价解时，其确定性 tie-resolution 路径依赖矩阵维度和列布局。S1 因而得到相同无序集合但不同的 slot-to-column 配对；hard assignment 随之不同。8 个病例的严格 objective 也不同，进一步违反预注册的逐字节等价要求。

这说明“保留所有 S0 最终列”不足以推出“复现 S0 的确定性 assignment 输出”。对于下游按 slot 解释结果的 R1，不能把 selected set 等价替代为 slot mapping 等价。

## 6. 冻结结论

S1 状态固定为 `D6A_R1_S1_exact_assignment_artificial_zero_step_equivalence_failed`。依据预注册协议：

- 不授权 S1 artificial performance benchmark；
- 不允许 S1 替换生产 R1；
- 不允许 formal efficiency rerun；
- 不授权 seed-0/seed-1 training、D6-B、confirmation 或 selection；
- 不访问 D6 development、proposal-confirmation 或 sealed 数据；
- 不得通过放宽 slot mapping 或 objective 门控重新解释本结果。

## 7. 后续建议

先归档本负结果、canonical 与 CRLF 父锁、恢复凭据、授权和 168 例审计。S1 路线到此停止。若未来研究新的 S2，只能另行预注册，并应直接针对完整求解器的工程开销，同时保持 S0 的 exact slot mapping；在新协议获批前不得实现、计时或训练。
