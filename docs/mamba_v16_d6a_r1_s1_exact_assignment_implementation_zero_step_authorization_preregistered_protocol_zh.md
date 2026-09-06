# Mamba v1.6 D6-A R1 S1 implementation 与 artificial zero-step 执行授权

## 1. 授权目的

本协议只授权实现隔离的 S1 shadow selector，并在人工 `32 x 8192` assignment matrix 上执行一次预注册的 168 例 CUDA zero-step。它不授权性能计时、替换生产 R1、重跑 formal efficiency gate 或训练。

## 2. 冻结父结论

- R1 formal latency median 为 `292.508788407 ms`，formal ratio gate 已失败且保持不变。
- Post-hoc profiling 将主要延迟描述性归因于 SciPy global assignment。
- 已冻结的优化可行性协议只允许下一步单独签发 S1 implementation 与 artificial zero-step 授权。

## 3. S1 实现边界

- 冻结生产文件 `utils/mamba_d6a_slot_allocator.py` 不得修改。
- S1 位于独立 shadow 模块，仅接受 `1 x 32 x 8192` finite float32 logits。
- 保留完整 CUDA-to-CPU float64 传输和原始 epsilon 调整。
- 每行保留 adjusted score 不低于该行第 32 大值的全部列，包含 cutoff ties。
- 以原候选索引升序构造 union，使用相同的 SciPy `linear_sum_assignment(maximize=True)`，再映射回原索引。
- 不允许 greedy、approximate、fallback 或生产路由修改。

## 4. 168 例 zero-step

人工套件严格继承父协议的 7 个 family、case 数和 seed 顺序。每例必须同时满足：

1. S0 与 S1 的 slot-to-candidate 逐槽完全一致；
2. 排序后的 32 个 selected indices 完全一致；
3. 完整 hard assignment tensor 完全一致；
4. adjusted objective 逐位一致；
5. S0 的 32 个列全部包含在 S1 union 中；
6. 每例恰有 32 个唯一候选。

全部 168 例必须按预注册顺序执行后再分类。任意一例失败时不得写入成功状态，而应冻结 S1 等价性负结果并停止，且不得进入性能 benchmark。

## 5. 明确不执行的事项

- 不调用计时 API，不 warmup，不产生 timed observations，不运行 profiler。
- 不读取 D6 case、STL、NPZ、checkpoint 或 sealed 分区。
- 不构造 optimizer，不执行 backward，不更新模型。
- 不评估或改变 formal gate，不授权 seed-0/seed-1 training、confirmation、D6-B 或 selection。

## 6. 成功后的唯一下一步

只有 168/168 全部等价时，结果才支持另行预注册 **S1 artificial performance benchmark execution authorization**。若任一硬门控失败，则归档负结果并停止 S1。性能 benchmark、S2、生产替换、formal rerun 和训练均不会自动获得授权。
