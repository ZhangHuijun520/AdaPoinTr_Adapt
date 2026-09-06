# Mamba v1.6 D6-A R1 S2 certified fast-path 可行性预注册协议

## 1. 背景与目的

S1 在 168 个人工 assignment 病例上保留了全部 S0 最终候选列，排序后的 selected set 达到 `168/168`，但 slot mapping 与 hard assignment 仅为 `128/168`，adjusted objective 为 `160/168`。失配集中在 identical rows、float32 near-tie 和 shared-top32 adversarial 三类退化或近退化矩阵。该结果说明：缩减矩阵虽包含全局最优解，却不能在多重或数值近似最优解存在时复现完整矩阵上的 SciPy 确定性选解。

本协议预注册 S2：只在能够证明最优 assignment 唯一且数值间隔充分时采用缩减矩阵结果；遇到 assignment-relevant tie、near-tie、证书不足或任何异常时，必须独立执行并直接返回完整 S0。目标是先证明这一条件快速路径在固定 168 例上严格等价且具有非零覆盖率，再讨论独立性能授权。

本步骤只冻结不可运行协议，不实现 S2，不计时、不训练、不访问 D6 数据，也不改变正式效率负结果。

## 2. 冻结候选

- **S0**：冻结 reference。完整 `32 x 8192` float32 logits 转为 CPU float64，减去 `float64 epsilon x original candidate index`，再调用 `scipy.optimize.linear_sum_assignment(maximize=True)`。
- **S1**：已冻结负结果，不重跑、不计时。其 tie-safe row-top32 union 包含正确 selected set，但在歧义矩阵上不能保持 slot mapping。
- **S2**：沿用 S1 的 tie-safe union，但只有通过 cutoff margin 与全局唯一性双证书后才能返回缩减求解结果；否则执行完整 S0，且不得混用任何未认证的 S2 输出。

S2 初始阶段仍保留完整 D2H。这样可把实验问题严格限制为 SciPy 矩阵缩减与确定性等价性，不把 GPU top-k、异步传输或生产代码修改混入同一实验。

## 3. 证书与回退

### 3.1 候选完备性

每行保留 adjusted score 不低于该行第 32 大值的所有列，并按原 candidate index 升序取并集。因为只有 32 个 slot，任何全局最优 assignment 的每条边都不可能严格落在对应行 top-32 之外；截止位并列必须全部保留。

### 3.2 Cutoff 歧义门控

逐行比较第 32 与第 33 大 adjusted score。行级 guard 固定为：

`256 * eps64 * max(1, max(abs(row)))`

任一行的 cutoff gap 小于或等于 guard，即视为 cutoff tie/near-tie，直接回退完整 S0。

### 3.3 全局唯一性证书

先在 tie-safe union 上求最优 assignment。然后依次禁止其 32 条已选边，每次用相同 SciPy 求解器求最优可行替代，取最大替代 objective 作为 second best。objective 必须按 slot 升序以 NumPy float64 累加。

全局 guard 固定为：

`256 * eps64 * max(1, |best|, |second_best|, sum_abs(best edges), sum_abs(second-best edges))`

只有 `best - second_best > guard` 时，才能把该最优解认证为稳健唯一并返回缩减结果。等于、低于 guard、非有限值、求解异常、union/唯一性约束失败均必须回退完整 S0。

这里的 tie/near-tie 指会影响 assignment 认证的歧义，而不是任意一个与最优解无关的低分重复值。

## 4. 固定人工套件

完全复用 S1 已冻结的 168 个 `32 x 8192` float32 矩阵，不得增删病例、修改 seed 或在看到结果后追加搜例：

| Family | Cases | Seed start |
| --- | ---: | ---: |
| independent normal | 64 | 160610 |
| collision-heavy shared candidate bias | 32 | 260610 |
| identical rows | 8 | 360610 |
| exact tie groups | 16 | 460610 |
| near ties in float32 | 16 | 560610 |
| shared top-32 adversarial | 16 | 660610 |
| top32 cutoff ties | 16 | 760610 |

每个病例必须另外执行一次完整 S0，并逐元素比较 S2 的 slot mapping、hard assignment、排序后 selected indices 与 adjusted objective。

## 5. 双重硬门控

**语义门控：** 四项输出均须达到 `168/168`，每例 selected candidates 为 32 个唯一索引，输入状态保持不变，全部输出有限。任何一项不足即冻结 S2 负结果，禁止性能测试。

**路由门控：** 至少 96/168 个病例必须真实走 certified fast path；其中 independent normal 必须为 `64/64`，collision-heavy 必须为 `32/32`。所有未获证书病例都必须回退 S0，false-positive certificate 必须为 0。全部回退虽然语义正确，但不构成可行性通过。

False negative 只降低覆盖率，本身不是语义违规，但若导致覆盖率门槛失败，S2 仍按工程不可行冻结为负。

## 6. 性能与正式门控边界

本协议锁和未来 168 例 zero-step 的 timing、warmup、timed run 与 profiler trace 均固定为 0。只有另行冻结的 zero-step 同时通过全部语义和路由门控，才允许再签发人工性能 benchmark 授权。

未来 benchmark 必须计入证书计算与 S0 fallback 的完整端到端成本。即使人工 benchmark 改善，也不自动修改生产 R1、不重算 formal efficiency、不授权训练。原 R0 denominator、`1.15x` formal gate 和 D6-A formal negative result继续保持不变。

## 7. 权限边界

当前只有 protocol lock 为 `true`。S2 shadow implementation、168 例 zero-step、性能 benchmark、S1 重跑、生产 R1 修改、formal rerun、seed-0/seed-1 training、confirmation、D6-B、selection 和 sealed access 全部为 `false`。

协议冻结后的唯一允许下一步，是单独准备 **S2 shadow implementation and 168-case artificial zero-step authorization**。
