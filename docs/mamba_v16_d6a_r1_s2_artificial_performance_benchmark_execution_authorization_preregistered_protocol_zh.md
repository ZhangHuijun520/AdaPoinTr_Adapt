# Mamba v1.6 D6-A R1 S2 artificial performance benchmark 执行授权

## 1. 授权依据

S2 zero-step 已在固定 168 例上达到 slot、selected、hard 与 objective 全部 `168/168`，路由为 certified fast path 96 例、完整 S0 fallback 72 例，false-positive certificate 为 0。随后冻结的不可运行 benchmark 协议固定了完整计时边界、执行顺序、样本数和通过阈值。

本授权只允许一次固定人工套件的 S0-versus-S2 性能执行。它不授权修改 S0/S2、访问 D6、替换 production R1、重跑 formal efficiency 或训练。

## 2. 源码和父锁绑定

授权必须验证 benchmark protocol lock 与 S2 positive result 的精确 SHA256。S2、S1 support、人工 suite generator 和 S2 zero-step reference 源码采用 LF-normalized SHA256 对照冻结值，以兼容既有 CRLF/LF 运输差异；签发授权时同时记录实际 raw SHA256。此后 preflight 和 benchmark 必须要求 raw bytes 与授权时完全一致。

换行差异可以被分类，但不能掩盖授权之后的源码修改。

## 3. 零计数 CUDA preflight

正式计时前必须单独运行 preflight：仅生成 `independent_normal / seed=160610` 人工矩阵，分别调用一次 S0 和 S2，要求所有输出精确一致、S2 路由为 certified fast path、输入不变。

Preflight 的 warmup、timed calls、measurement blocks 和 profiler traces 必须均为 0。它只能证明 CUDA、导入、授权和单例语义链可运行，不能产生性能结论。

## 4. 唯一获准的 benchmark

正式 runner 必须先完成全部 168 例 correctness/routing replay。只有重放仍为 `168/168`、fast/fallback 为 `96/72`、fallback reason 为 `32/40` 且 false-positive 为 0，才允许进入：

- 7 个 family anchor，2 轮 warmup，每候选 14 次；
- 3 个完整 measurement block；
- 每候选 504 次 timed call，共 1008 行原始观测；
- 每个 block 内按 `(block + case) mod 2` 平衡交替候选先后；
- 每次 timed call 前后 CUDA synchronize，使用 `time.perf_counter_ns`；
- CPU 数值线程和 PyTorch CPU threads 固定为 1；
- 不删除异常值、不因慢观测重试、不运行 torch profiler。

计时必须包含完整 D2H、S2 certificate、32 次 edge-exclusion、fallback 和输出构造。人工矩阵生成、H2D 输入创建、验证、序列化与哈希不计时。

## 5. 结果门控

正结果要求 1008 行观测全部有限且大于 0，并同时满足：3 个 overall block ratio 中位数不高于 `0.90`，每个 block ratio 严格低于 `1.00`，fast-path aggregate ratio 不高于 `0.50`，fallback aggregate ratio 不高于 `1.25`。

任一正确性失败必须在 0 timed calls 下冻结；任一性能阈值失败必须冻结性能负结果。结果不得自动授权 production 修改、formal rerun 或训练。

## 6. 权限边界

本次授权将 `S2_artificial_performance_benchmark_execution_authorized` 和 `authorization_preflight_authorized` 设为 `true`，但初始 `execution_started=false`。S2 implementation change、production R1 修改、formal rerun、seed-0/seed-1 training、confirmation、D6-B、selection 与 sealed access 均为 `false`。

授权签发后的下一步只能是零计数 CUDA preflight；preflight 通过后，正式 benchmark 仍须单独以 tmux 启动。
