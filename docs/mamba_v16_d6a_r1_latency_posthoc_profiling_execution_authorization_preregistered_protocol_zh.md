# Mamba v1.6 D6-A R1 latency post-hoc profiling 执行授权预注册

## 授权目的

本授权只允许一次 R1 人工 descriptor、observation-only latency profiling。父协议锁已将 formal efficiency 负结果固定为 R1 median `292.508788407 ms`，本步骤不得重跑 R0/R1 gate、修改 R1、实现 R2 或启动训练。

## 固定执行条件

- Candidate：仅 R1。
- Descriptor：seed `160610`，shape `1 x 8192 x 27`，CUDA float32。
- R1 state SHA256：`d3eedd80617538c1fa0278d8d87427c27b242fd38fe2950bd8bba6cd5455cd78`。
- 初始化顺序：设置 seed，构造并释放 R0，再构造 R1，以精确复现冻结 R1 state。
- 正式 profiling：3 blocks；每 block 5 warmup + 20 timed，共 60 个 timed observation。
- PyTorch profiler：wait/warmup/active/repeat 固定为 1/1/5/1。
- 输出必须包含 exact-path、assignment decomposition、operator summary、压缩 trace、attribution summary、receipt、中文报告和哈希清单。

## Zero-run preflight

授权后必须先运行独立 preflight。Preflight 仅构造一份人工 descriptor，执行一次 R1 forward 和一次 assignment 等价性探针；不得进入 profiling block、timed loop 或 torch profiler trace。其固定计数为 profiling blocks/timed observations/traces = `0/0/0`，optimizer steps/model updates = `0/0`。

## 结果解释边界

正式 profiling 只能报告冻结实现的时间归属。单一类别达到 instrumented total 的 50% 时可标记为 descriptive dominant，否则标记 mixed。该标签不是因果证明，也不能授权代码修改、R2、训练、seed-1、confirmation、D6-B、selection 或 sealed access。

## 当前权限

本文件允许签发一次 profiling execution authorization，但授权器和 preflight 均不得自动启动 profiling。正式执行必须在授权与 preflight 均冻结后，由单独 tmux launch 命令启动。
