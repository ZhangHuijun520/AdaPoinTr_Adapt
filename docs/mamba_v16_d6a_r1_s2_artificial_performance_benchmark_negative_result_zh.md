# Mamba v1.6 D6-A R1 S2 artificial performance benchmark 冻结负结果

## 1. 实验目的

本实验评估冻结的 S2 certified fast path 是否能在保持 S0 完整 assignment 语义的前提下，降低人工 descriptor 上的完整 selector 延迟。S2 对可认证样本执行缩减矩阵求解与 32 次 edge-exclusion 唯一性检查；对 tie、near-tie 或无法证明全局最优唯一的样本，完整回退冻结 S0。

实验只使用冻结的 168 个人工矩阵，不访问 D6 development、proposal-confirmation 或 sealed 数据。计时边界覆盖 CUDA slot logits 输入、D2H、CPU float64 调整、候选并集、证书检查、缩减求解、edge-exclusion 求解、必要的完整 S0 回退及输出构造。正式 R0/R1 efficiency gate 未重跑，也未构造 optimizer 或更新模型。

## 2. 预注册设计

- Correctness replay：计时前重放 168 例，要求 slot mapping、hard assignment、selected set、objective、route 和 fallback reason 全部精确一致。
- Routing：96 例必须进入 certified fast path，72 例必须完整回退 S0。
- Warmup：S0/S2 合计 28 次。
- 正式计时：3 个 block，每个 block 含 168 例、每例各测 S0/S2 一次，共 1008 条观测。
- 顺序控制：各 block 内交替 S0-first 与 S2-first，各 84 例。
- 异常值：不删除、不重试。

性能硬门控预先固定为：

1. 三个总体 block ratio 的中位数不高于 `0.90`；
2. 每个总体 block ratio 严格小于 `1.00`；
3. 96 例 fast-path 的聚合 S2/S0 ratio 不高于 `0.50`；
4. 72 例 fallback 的聚合 S2/S0 ratio 不高于 `1.25`；
5. 1008 条计时均为有限正值且数量完整。

## 3. 正确性与执行边界

| 项目 | 结果 | 判定 |
| --- | ---: | --- |
| Correctness replay | 168/168 | 通过 |
| Certified fast path | 96/96 | 通过 |
| Complete S0 fallback | 72/72 | 通过 |
| Warmup calls | 28 | 完整 |
| Timed observations | 1008 | 完整 |
| Measurement blocks | 3 | 完整 |
| 有限正计时及数量 | True | 通过 |
| Optimizer steps / model updates | 0 / 0 | 保持锁定 |
| D6 cases accessed | 0 | 保持锁定 |

因此，本结果是有效的性能负结果，不是执行异常、正确性失败或样本路由漂移。

## 4. 总体性能结果

| Block | S0 total (ms) | S2 total (ms) | S2/S0 | 是否小于 1 |
| ---: | ---: | ---: | ---: | --- |
| 0 | 1094.011035 | 1620.397318 | 1.481153 | 否 |
| 1 | 1083.269714 | 1615.905253 | 1.491692 | 否 |
| 2 | 1088.142639 | 1617.464545 | 1.486445 | 否 |

三个 block ratio 的中位数为 `1.4864453308`，即 S2 总体约比 S0 慢 `48.64%`。三个 ratio 的最大差仅约 `0.01054`，相对中位数约 `0.71%`，说明负结果跨 block 稳定，不符合偶发 GPU/CPU 抖动或单个异常值主导的特征。

总体 504 对观测中：

- S0 mean latency：`6.479015 ms`；S2 mean latency：`9.630490 ms`；
- S0 median latency：`3.593038 ms`；S2 median latency：`8.753317 ms`；
- 聚合 S2/S0 ratio：`1.4864127984`；
- paired ratio median：`1.9894088032`；
- paired mean difference：`+3.151476 ms`。

## 5. 分路由结果

| Route | 病例 | 配对观测 | S0 mean (ms) | S2 mean (ms) | 聚合 ratio | Paired ratio median | 门控 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| certified_fast_path | 96 | 288 | 5.468003 | 7.590811 | 1.388224 | 3.511903 | 失败，要求 <=0.50 |
| fallback_s0 | 72 | 216 | 7.827030 | 12.350062 | 1.577873 | 1.675767 | 失败，要求 <=1.25 |

Fast path 自身的聚合延迟仍比 S0 高约 `38.82%`，因此失败不能归因于 fallback 比例过高。Fallback 路径比 S0 高约 `57.79%`，说明先运行证书逻辑、再执行完整 S0 的组合带来了明显附加成本。

## 6. 专业分析

S2 已证明语义正确，但没有实现工程加速。Fast-path 路径需要完成候选构造、tie/cutoff 检查、一次缩减最优求解以及 32 次 edge-exclusion 求解，证书成本超过了缩减矩阵带来的求解收益。Fallback 路径还要在上述前置工作后执行完整 S0，因而天然叠加额外开销。

该判断与当前计时边界和路由分层一致，但属于机制性推断，而不是新的算子级 profiling 结论。本实验没有授权或运行额外 profiler，不能在本结果之后把某个内部子步骤的精确占比作为实测事实。

四项性能门控全部失败：总体中位数超限、三个 block 均未快于 S0、fast-path ratio 超限、fallback ratio 超限。有限性和计数门控通过。由于失败幅度大、方向一致且跨 block 稳定，没有统计或工程依据通过重跑、删异常值、调整阈值或改变 case mix 来挽救 S2。

## 7. 冻结结论

S2 状态固定为 `D6A_R1_S2_artificial_performance_benchmark_failed`。依据预注册协议：

- S2 不得进入 production R1；
- 不允许 formal efficiency rerun；
- 不允许重跑本 artificial benchmark；
- 不得修改阈值、样本、路由、证书或计时边界后重新解释本结果；
- 不授权 seed-0/seed-1 training、D6-B、confirmation 或 selection；
- 继续保留冻结 S0 作为有效实现。

下一步仅为提交、打 annotated tag、创建最小可恢复归档并下载核验。归档完成后 S2 路线停止；任何后续优化必须以新的名称和独立预注册协议开始，且不能声称改变本次冻结负结果或原 formal efficiency negative gate。
