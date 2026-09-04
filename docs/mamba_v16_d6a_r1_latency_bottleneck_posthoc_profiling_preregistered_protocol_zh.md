# Mamba v1.6 D6-A R1 延迟瓶颈 post-hoc profiling 预注册协议

## 1. 冻结前提

D6-A formal efficiency 已在 commit `16b8f531bafa21805ece57053f18e1084166878d` 和 annotated tag `mamba-adapter-v16-d6a-formal-efficiency-negative-result-v1` 下冻结为负结果。R0/R1 中位延迟分别为 `0.397897325 ms` 和 `292.508788407 ms`，R1/R0 比值为 `735.136352252`；peak-memory 比值为 `1.113369586`。两个正式门控均失败，训练必须在 optimizer step 之前停止。

本协议不重跑、不修改也不解释性放宽 formal gate。它只预注册一个后续的、独立授权后才可执行的 observation-only profiling，用于定位 R1 延迟主要出现在哪个实现阶段。

## 2. 数据与权限边界

- 仅分析 R1；不再次比较 R0/R1，也不计算 gate ratio。
- 仅使用 seed `160610` 的人工 `1 x 8192 x 27` CUDA float32 descriptor。
- R1 初始 state SHA256 固定为 `d3eedd80617538c1fa0278d8d87427c27b242fd38fe2950bd8bba6cd5455cd78`。
- 不读取 D6 development、proposal-confirmation、completion holdout、official test、STL、NPZ 或 checkpoint。
- 模型必须为 eval + inference mode；前后 state hash 必须相同；optimizer 不得构造。
- 当前步骤只允许冻结协议锁。Profiling execution、代码优化、R2、training、seed-1、confirmation、D6-B、selection 和 sealed access 均未授权。

## 3. 固定诊断设计

Profiling execution 必须另行签发授权，并严格执行以下三种互补观测。

### 3.1 原路径分段 wall-clock

固定执行 3 个 block；每 block 5 次 warmup 和 20 次 timed observation，共 60 个 timed observation。每次记录：

1. descriptor validation；
2. R1 model forward；
3. global assignment total；
4. selected-index return；
5. full-inference total。

各段报告 minimum、median、P95、maximum 和 MAD。所有 CUDA synchronization 的位置必须进入凭据，instrumented 输出的 32 个索引必须与未插桩参考路径逐次一致。

### 3.2 Global assignment 分解

对当前 `deterministic_global_assignment` 的真实路径分解并记录：

1. slot-logit finite validation 与隐式/显式同步；
2. GPU hard tensor 分配；
3. slot logits 转 CPU float64 与 NumPy；
4. CPU epsilon tie adjustment；
5. SciPy `linear_sum_assignment`；
6. assignment 完整性检查；
7. selected indices 回传 GPU；
8. GPU hard scatter；
9. selected sort 与 stack。

CPU/传输阶段使用带明确同步边界的 wall-clock；纯 GPU 阶段同时记录 CUDA event time。不同计时域不能直接相加，分解结果与原路径总耗时必须分别报告。

### 3.3 PyTorch operator trace

使用 CPU + CUDA activities，固定 schedule 为 wait 1、warmup 1、active 5、repeat 1；启用 shapes 与 memory，关闭 Python stack。必须导出压缩 trace、operator summary，并用 `record_function` 标记上述阶段。

## 4. 预声明解释规则

以 instrumented full-inference total 的 median exclusive wall-clock share 为描述性基准。单一阶段占比至少 `50%` 时，标记为对应 dominant 类别：GPU model forward、validation/CUDA sync、D2H transfer、SciPy assignment 或 GPU reconstruction；否则标记为 mixed。

该标签仅表示在冻结实现上的时间归属，不构成因果证明。Profiler overhead 和强制同步可能改变运行时，因此不得用本结果替换正式 292.509 ms 结果，也不得在同一协议内实现或测试优化版本。

## 5. 固定输出

必须冻结 exact-path stage CSV、assignment-stage CSV、operator summary CSV、压缩 trace、attribution summary、执行凭据、中文报告和 `files.sha256`。所有输出应明确记录：formal gate 未改变、optimizer steps/model updates 为 0、D6 cases 为 0，且所有受保护权限仍为 false。

## 6. 当前结论

当前仅完成不可运行的 profiling 预注册。下一步只能单独签发 R1 post-hoc profiling execution authorization；不得自动运行 profiling，更不得启动 D6-A 训练。
