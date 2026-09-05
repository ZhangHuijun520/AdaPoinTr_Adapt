# Mamba v1.6 D6-A R1 latency post-hoc profiling 完整冻结结果

## 1. 实验目的与边界

D6-A R1 在预注册 formal efficiency gate 中得到 `292.508788407 ms` 的 median latency，R1/R0 latency ratio 为 `735.136352252`，未通过 `1.15` 上限。本实验只定位该冻结 R1 推理路径的时间归属，不重跑 formal gate，不访问 D6 development、proposal-confirmation、official test 或 sealed 数据，也不授权优化、R2 或训练。

本结果属于 observation-only 描述性分析。Profiling 产生的阶段占比不能替代干预实验，不能被解释为已经证明某个算子是全部 formal latency 的唯一因果来源。

## 2. 冻结执行条件

- Candidate：仅 R1，不运行 R0。
- Artificial descriptor seed：`160610`。
- Descriptor：`1 x 8192 x 27`，float32，CUDA。
- R1 state SHA256：`d3eedd80617538c1fa0278d8d87427c27b242fd38fe2950bd8bba6cd5455cd78`。
- Profiling blocks：3。
- 每 block warmup/timed：5 / 20。
- Timed observations：60。
- Torch profiler schedule：wait/warmup/active/repeat = 1/1/5/1。
- Dominant descriptive share threshold：0.50。
- GPU：NVIDIA GeForce RTX 4090 D。
- PyTorch：`2.4.1+cu118`。

执行前 authorization 和 zero-count CUDA preflight 均已冻结。Preflight 只执行一次人工 descriptor 前向和一次 assignment 等价检查，profiling blocks、timed observations、traces、optimizer steps、model updates 与 D6 cases 均为 0。

## 3. 完整性结果

- Result status：`D6A_R1_latency_posthoc_profiling_complete_observation_only`。
- Timed observations / profiler traces：60 / 1。
- 32 个 selected indices 与未插桩冻结参考逐元素一致。
- Model state hash before/after 完全一致。
- Optimizer constructed/steps/model updates：`False / 0 / 0`。
- D6 cases accessed：0。
- Formal gate evaluated/changed/rerun：`False / False / False`。
- Causal claim authorized：`False`。
- R1 implementation change、optimized alternative、R2 和训练授权：全部 `False`。

## 4. Exact-path 与阶段分解

| 指标 | Minimum (ms) | Median (ms) | Maximum (ms) | MAD (ms) | P95 (ms) |
|---|---:|---:|---:|---:|---:|
| Exact full inference | 8.314956 | 204.080154 | 490.548236 | 104.399226 | 409.866755 |
| Instrumented segment sum | 8.287121 | 197.033578 | 410.810219 | 104.038569 | 399.827372 |
| R1 model forward | 0.593519 | 1.341352 | 90.593675 | 0.726096 | 73.497705 |
| Descriptor validation | 0.058601 | 0.084451 | 0.344455 | 0.025365 | 0.225734 |

冻结 formal median `292.508788 ms`、instrumented exact-path median `204.080154 ms` 与 segment-sum median `197.033578 ms` 不相等。原因包括独立运行波动、插桩影响，以及“各阶段中位数之和不等于总时延中位数”。因此本实验使用预注册的 instrumented median denominator 进行描述性占比，不回算或替换 formal gate。

## 5. 延迟归因

| Category | Median (ms) | Share |
|---|---:|---:|
| SciPy global assignment | 103.007906 | 70.8744% |
| Device-to-host transfer | 40.269705 | 27.7075% |
| GPU model forward | 1.341352 | 0.9229% |
| CPU assignment other | 0.449005 | 0.3089% |
| GPU reconstruction | 0.145442 | 0.1001% |
| Validation/CUDA synchronization | 0.125316 | 0.0862% |

预注册分类为 `scipy_global_assignment_dominant`，leading share 为 `0.7087436968007994`，超过 0.50 描述阈值。SciPy assignment 与 device-to-host transfer 的阶段中位数占比合计约 98.58%，而 R1 神经网络前向只占约 0.92%。这支持“当前冻结实现的主要计时归属位于 GPU 到 CPU 的往返和 CPU 全局 assignment 路径”，但不构成优化收益的因果保证。

## 6. 波动与可靠性分析

`scipy_linear_sum_assignment_cpu_ms` 的 min/median/max 为 `6.703284 / 103.007906 / 309.155161 ms`，MAD 为 `96.218221 ms`。`slot_logits_d2h_float64_numpy_ms` 的 min/median/max 为 `0.227632 / 40.269705 / 196.695060 ms`，MAD 为 `39.918771 ms`。两者离散程度都很高。

R1 model forward 的 median 仅 `1.341352 ms`，但 P95 为 `73.497705 ms`，提示同步边界、CPU 调度、线程运行时或异步 CUDA 工作归属可能影响个别阶段的表观计时。下一阶段若研究性能修复，必须固定线程环境、同步边界、warmup 和重复次数，并同时报告分布而非只报告单个 median。

## 7. 冻结哈希

- Result manifest：`8c0fb421188abe6efdd0081013eb451cb87bf5a3768f9279b7bf16678709f385`。
- Profiling receipt：`ba4382e9af597189ec75ff3ea12175d3a4add8ec9894e02ccab3301d6469a0d9`。
- Result report：`772e080e644d377a865e6cd40628a5a82550a639c8d01a3f2514c9c2fe7b173d`。
- Assignment-stage CSV：`99d6601c0994d8966412f0b23f29f4bf80f393ec569f663c67830c670c3dfe12`。
- Exact-path CSV：`2cd82f348c910d6b699b759661c1fcf99a064802aba4d02917d0e2880a40f327`。
- Attribution summary：`b5f1ca7f37fde4c06a8564700799b2e32ae05b01842dd399047415f7d0607c37`。
- Operator summary：`90e9d7f75032e3f170b89d05af5f03e3756546f4ea49e06f35d4715631b8fc4e`。
- Torch profiler trace：`98503b3721e6973dc921ad54f70942442a97f423461210a68a6065d2823ef03e`。
- 57-artifact inventory：`698551249e7983fb98a42ad7fd7bc146b229c612013dded274d6a97e3d6d4c1f`。
- Freeze receipt：`4156c7a0fb75c7d4f4108bf2d3e14b9483a415ba21e8c56ff2b11c8a66f02501`。

## 8. 冻结决定与下一阶段建议

1. 当前 profiling 结果作为 D6-A R1 formal-efficiency 负结果的只读解释证据冻结，不修改原 `735.136352252` latency ratio 或负 gate。
2. 不签发 D6-A seed-0/seed-1 训练授权，不访问 confirmation、D6-B 或 sealed 数据。
3. 在任何实现变化前，先完成 Git commit、annotated tag、服务器最小归档和本地恢复验证。
4. 后续只能另行预注册 artificial-descriptor 性能修复可行性协议。首先检验固定 CPU 线程环境、同步边界和内存分配对 SciPy/D2H 波动的影响。
5. 任何优化候选都必须保持 32 个 selected indices 逐元素一致、R1 state 不变，并重新通过独立 formal efficiency gate；不得用 post-hoc 结果追溯替换原负结果。

## 9. 最终结论

本次 profiling 成功将冻结 R1 实现的主要描述性延迟归属于 SciPy global assignment 和 device-to-host transfer，其中 SciPy 占 70.87%。结果解释了为什么 R1 完整 selector 远慢于纯 GPU 前向，但由于阶段波动和总时延口径差异，尚不能直接证明某项替换会获得等量加速。当前唯一合规结论是冻结该 observation-only 结果、继续禁止训练，并在独立预注册协议下研究严格等价的性能修复可行性。
