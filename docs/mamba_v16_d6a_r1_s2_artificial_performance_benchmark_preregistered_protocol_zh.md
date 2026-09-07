# Mamba v1.6 D6-A R1 S2 artificial performance benchmark 预注册协议

## 1. 背景与问题

S2 certified fast path 已在冻结的 168 个人工 assignment 矩阵上通过零步验证：slot mapping、sorted selected set、hard assignment 与 adjusted objective 均为 `168/168` 精确一致；96 例走 certified fast path，72 例回退完整 S0，false-positive certificate 为 0。

正确性通过并不等于性能可行。S2 的 fast path 包含一次缩减矩阵最优求解和 32 次 edge-exclusion 求解；fallback 还会叠加完整 S0 成本。因此必须独立测量包含完整 D2H、证书、回退和输出构造的端到端 selector latency，不能用缩减矩阵尺寸推断加速，也不能只计时其中一个 SciPy 调用。

本步骤只冻结不可运行的人工性能 benchmark 协议。它不签发执行授权，不启动 warmup 或计时，不访问 D6 数据，不修改 production R1，也不改变已经冻结的 formal-efficiency 负结果。

## 2. 冻结候选与计时边界

- **S0**：完整 `32 x 8192` logits 从 CUDA 复制到 CPU，转为 float64，执行冻结 epsilon 调整和 `scipy.optimize.linear_sum_assignment(maximize=True)`，直到 mapping 输出返回。
- **S2**：从相同 CUDA 输入开始，包含完整 D2H、float64 调整、tie-safe union、cutoff guard、一次 reduced best solve、32 次 edge-exclusion solve、未认证时独立执行完整 S0，以及最终 mapping 输出返回。

计时不包括人工矩阵生成、输入 H2D 创建、正确性比较、CSV/JSON 写入、报告生成或哈希计算。S0 与 S2 的实现、数值 guard、回退规则和输入矩阵均不得在看到性能结果后修改。

## 3. 计时前正确性重放

在任何 timed call 前，必须按冻结顺序完整重放 168 例：S0 与 S2 各执行 168 次，并重新满足以下硬门控：

- slot mapping、selected set、hard assignment、objective 与 input state 均为 `168/168`；
- certified fast path / fallback 精确为 `96 / 72`；
- independent-normal 为 `64/64` fast path；collision-heavy 为 `32/32` fast path；
- fallback reason 精确为 `cutoff_tie_or_near_tie=32`、`global_optimum_not_certified_unique=40`；
- false-positive certificate 为 0。

任何不一致都必须在零 timed call 状态冻结 correctness/routing 负结果并停止。性能数据不能覆盖语义失败。

## 4. 固定执行设计

执行必须在一个进程、一个 CUDA device 中完成，只保留一个人工 score matrix。使用 `torch.inference_mode()`，并固定 `OMP_NUM_THREADS`、`MKL_NUM_THREADS`、`OPENBLAS_NUM_THREADS`、`NUMEXPR_NUM_THREADS` 与 PyTorch CPU threads 为 1。

### 4.1 Warmup

每个 frozen family 取第一个病例作为 anchor，共 7 个。执行 2 轮，每个候选 14 次、合计 28 次，不计入结果。候选先后顺序按 family index 与 warmup round 交替。

### 4.2 Timed measurement

- 3 个完整 block；每个 block 包含全部 168 例。
- 每个候选 `3 x 168 = 504` 次 timed call；总计 1008 行观测。
- block 内病例顺序固定为 family order 后按 seed 递增。
- 若 `(zero-based block index + zero-based case index) mod 2 == 0`，顺序为 S0 后 S2；否则为 S2 后 S0。每个 block 中两者各先执行 84 次。
- 每次 selector call 前后立即执行 CUDA synchronize，使用 `time.perf_counter_ns`。
- warmup 与 measurement 期间禁用 Python GC，结束后恢复原状态。
- 不运行 torch profiler，不删除异常值，不因观测偏慢而重试。

环境信息、CUDA memory 与系统状态必须记录，但只作描述，不作为事后排除数据的理由。

## 5. 预注册统计量

主要分析单位是一个完整 168 例 block。对每个 block 分别计算：

`overall ratio = sum(S2 latency) / sum(S0 latency)`

主统计量为 3 个 block ratio 的中位数。另在全部 block 上分别聚合冻结的 96 个 fast-path 病例和 72 个 fallback 病例，计算 fast-path ratio 与 fallback ratio。

支持性结果包括 overall、route 和 family 分层的 min、median、mean、p95、max，逐病例配对 `S2/S0` ratio，以及绝对时延差。百分位固定使用 NumPy linear 方法。固定人工套件不进行假设检验，所有原始观测必须保留。

## 6. 性能硬门控

只有以下条件全部成立，才能冻结人工性能正结果：

1. 1008 行 timed observation 全部有限且严格大于 0；
2. 3 个 overall block ratio 的中位数不高于 `0.90`；
3. 每个 overall block ratio 都严格低于 `1.00`；
4. 聚合 fast-path ratio 不高于 `0.50`；
5. 聚合 fallback ratio 不高于 `1.25`。

该门控要求 S2 不仅在可认证病例上获得实质加速，而且不能以失控的 fallback 开销换取总体均值。任何阈值失败都冻结人工性能负结果并停止 S2，不允许事后改阈值或筛除慢样本。

## 7. 与 formal gate 的边界

该 benchmark 只比较人工 descriptor 上的完整 S0 与完整 S2 selector 路径。它不使用 formal R0 denominator，不评估 `R1/R0 <= 1.15`，不改变现有 `R1 median = 292.508788407 ms` 的 frozen-negative formal result。

即使人工 benchmark 通过，也只能进入单独的 **S2 production-path shadow integration feasibility protocol**。正结果不会自动授权 production 修改、formal rerun 或训练；负结果则归档并保留 S0。

## 8. 当前权限边界

当前只有 protocol lock 为 `true`。S2 benchmark execution、S2 implementation change、production R1 修改、formal rerun、seed-0/seed-1 training、proposal confirmation、D6-B、candidate selection 和 sealed access 全部为 `false`。

协议冻结后的唯一允许下一步，是单独准备 **S2 artificial performance benchmark execution authorization**。
