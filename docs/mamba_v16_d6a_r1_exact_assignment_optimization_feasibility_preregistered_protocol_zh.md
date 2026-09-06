# Mamba v1.6 D6-A R1 exact-assignment 优化可行性预注册协议

## 1. 目的

D6-A R1 的正式效率结果已冻结为负：R1 median latency 为 `292.508788407 ms`，相对 R0 的比值为 `735.136352252`，远高于预注册上限 `1.15`。后续只读 profiling 将主要计时归属于 SciPy global assignment（median `103.007906 ms`，占 instrumented denominator 的 `70.8744%`）和完整 logits 的 device-to-host transfer（median `40.269705 ms`）。

本协议只冻结一个严格等价 assignment 缩减实验的设计。它不修改 R1，不运行优化实现，不重算正式效率结果，不访问 D6 数据，也不授权任何训练。

## 2. 冻结候选

- **S0**：当前 R1 reference。将完整 `32 x 8192` float32 logits 转移到 CPU float64，执行冻结的 candidate-index epsilon 调整，再调用 `scipy.optimize.linear_sum_assignment(maximize=True)`。
- **S1**：在完整 D2H 和完整 CPU float64 epsilon 调整之后，对每个 slot 保留不低于该行第 32 大 adjusted score 的全部列；将这些列按原 candidate index 升序取并集，然后调用同一个 SciPy 求解器。S1 不减少 D2H，只检验缩小 SciPy 矩阵能否严格等价并获得工程加速。
- **S2**：未来可能在 GPU 上形成 tie-safe 列并集并减少 D2H。S2 当前未授权，只有 S1 的等价性和工程门控都冻结通过后，才可另行预注册。

## 3. 数学边界

共有 32 个 slot。若某个 slot 在一个严格最优匹配中选择了该行 top-32 之外的列，则另外 31 个 slot 最多占用其 top-32 中的 31 列，至少还存在一个更高分且未占用的列；替换后总分提高，产生矛盾。因此，每行 top-32 的列并集包含至少一个全局最优匹配。

该论证有两个明确限制：

1. 第 32 位存在并列时，必须保留截止阈值上的全部并列列。
2. 并集包含某个最优解，不保证 SciPy 在多重最优时返回与完整矩阵相同的 slot mapping。

因此，S1 必须同时逐元素匹配 S0 的 `slot_to_candidate`、排序后 selected indices 和 hard assignment。仅目标值相同或 selected set 相同都不构成通过。

## 4. 人工等价性套件

固定测试 168 个 `32 x 8192` float32 人工矩阵：

| Family | Cases | Seed start |
|---|---:|---:|
| independent normal | 64 | 160610 |
| collision-heavy shared candidate bias | 32 | 260610 |
| identical rows | 8 | 360610 |
| exact tie groups | 16 | 460610 |
| near ties in float32 | 16 | 560610 |
| shared top-32 adversarial | 16 | 660610 |
| top-32 cutoff ties | 16 | 760610 |

任何测试后的补充搜例、删除失败例或调整 seed 均禁止。168 例必须全部满足：slot mapping、selected indices、hard assignment、adjusted objective 完全一致，S0 所选列均在 S1 union 内，每例恰有 32 个唯一 selected indices，所有输出 finite。

## 5. 后续人工性能测试

等价性未达到 `168/168` 时，性能测试不得开始。未来性能测试需要单独授权，并固定：

- Artificial descriptor seed：`160610`，shape：`1 x 8192 x 27`。
- 3 blocks；每候选每 block 10 次 warmup、50 次 timed，共每候选 150 次 timed observation。
- Block 顺序：`S0→S1`、`S1→S0`、`S0→S1`。
- 每次 timed run 前后 CUDA synchronize。
- `OMP_NUM_THREADS`、`MKL_NUM_THREADS`、`OPENBLAS_NUM_THREADS`、`NUMEXPR_NUM_THREADS` 均固定为 1。
- 报告 minimum、median、p95、maximum 和 MAD。
- 模型 state hash 前后必须一致。

工程 progression gate 为：S1 SciPy solver median speedup 至少 `4.0x`，assignment-total median speedup 至少 `2.0x`，并通过全部等价性门控。通过只允许另行预注册 S2，不自动授权 S2、正式门控复核或训练。

## 6. 与正式门控的关系

冻结 R0 median 为 `0.397897325 ms`，原 `1.15x` 上限对应 R1 不超过 `0.457581924 ms`。Profiling 中 R1 model-forward median 已为 `1.341352239 ms`，而 S1 还保留完整 D2H。因此即使 S1 显著降低 SciPy 时间，也不能解释为原正式门控已经可通过。

正式效率负结果、R0 denominator 和 `1.15x` 阈值均不可改变。只有未来一个另行冻结的 optimized full-R1 artificial benchmark 先满足原比值和全部等价门控，才可以讨论单独的正式效率复核授权。

## 7. 权限边界

当前只允许冻结不可运行协议。S1 implementation、zero-step、benchmark、S2、R1 production change、formal rerun、seed-0/seed-1 training、confirmation、D6-B、selection 和 sealed access 全部为 `false`。

下一步只能单独准备 **S1 implementation and artificial zero-step authorization**，且不得作为本协议锁定的副作用执行。
