# Mamba v1.6 D6-A formal efficiency 完整负结果

## 1. 实验目的与判定边界

本阶段在任何 D6-A optimizer step 之前，比较冻结候选 R0 与 R1 的完整推理效率。测试包含各候选最终 selector，使用相同 GPU、软件环境、人工 descriptor、float32 和 batch size 1。该门控只评价架构与完整推理路径的运行代价，不访问 D6 development case、proposal-confirmation、official test 或其他 sealed 数据。

预注册硬阈值为：

- `R1/R0 median latency <= 1.15`；
- `R1/R0 peak CUDA memory <= 1.10`；
- 两项必须同时通过，才允许另行签发 D6-A seed-0 训练授权；
- 任一门控失败即冻结负结果并在训练前停止，不允许按观察结果修改阈值或重跑。

## 2. 冻结执行条件

- Candidate order：R0 后 R1。
- Artificial descriptor seed：`160610`。
- Descriptor：`1 x 8192 x 27`，float32。
- 每候选 warmup：10 次；正式计时：50 次。
- Latency statistic：50 次计时的 median，且每次计时前后执行 CUDA synchronization。
- Peak memory：每候选独立 reset peak memory；同一时刻只驻留一个候选。
- GPU：NVIDIA GeForce RTX 4090 D。
- PyTorch：`2.4.1+cu118`。
- R0 state SHA256：`d65faa30fdb4e648c8dfc6f7fd2112fc2b01bd18a16a9ea7f84e5fd9f1d43642`。
- R1 state SHA256：`d3eedd80617538c1fa0278d8d87427c27b242fd38fe2950bd8bba6cd5455cd78`。

两个模型在 benchmark 前后 state hash 均保持不变。Optimizer 未构造，optimizer steps/model updates 均为 `0/0`。

## 3. 正式结果

| Candidate | Latency min (ms) | Latency median (ms) | Latency max (ms) | Peak CUDA memory (bytes) |
|---|---:|---:|---:|---:|
| R0 | 0.375108793 | 0.397897325 | 0.633588061 | 27,304,960 |
| R1 | 8.820619434 | 292.508788407 | 492.147045210 | 30,400,512 |

- R1/R0 median-latency ratio：`735.1363522524863`；阈值 `1.15`；**失败**。
- R1/R0 peak-memory ratio：`1.1133695855991`；阈值 `1.10`；**失败**。
- 两项效率门控同时通过：`False`。
- Result status：`D6A_formal_efficiency_gate_failed`。
- Frozen next step：`freeze_negative_result_and_stop_before_training`。

## 4. 结果分析

### 4.1 延迟是决定性失败项

R1 median latency 为 292.509 ms，R0 为 0.398 ms，倍率约 735.14。相对预注册上限 1.15，观测倍率高出约 639.25 倍，因此不存在由计时舍入、轻微系统抖动或少量优化即可跨过门槛的解释空间。

R1 的 min/median/max 为 8.821/292.509/492.147 ms，离散程度明显高于 R0。结合 R1 完整 selector 使用全局 assignment 的实现，CPU 求解、CUDA 到 CPU 的同步或传输、以及主机调度是优先排查方向；但这只是基于实现路径与分布形态的诊断假设，不是本门控已经证明的因果结论。任何 profiler 或机制分解都必须另行预注册为 observation-only，且不能回写或推翻本次冻结 gate。

### 4.2 显存也独立失败

R1 peak CUDA memory 比 R0 多 `3,095,552` bytes，增幅约 11.337%。协议最多允许 10%，实际 ratio `1.11337` 比阈值高 0.01337，约为阈值的 1.215% 超额。该差距远小于延迟差距，但按照“两个 gate 同时通过”的预注册规则，它本身已足以阻止训练授权。

### 4.3 结论不涉及模型效果

本实验使用人工 descriptor，D6 cases accessed 为 0，因此不能从本结果推断 R1 的准确率、召回率或最终点云质量。此前的实现 zero-step、梯度校准和 calibrated weighted zero-step 说明实现与损失路径可执行，但不抵消本次完整推理效率门控失败。

## 5. 完整性与哈希

- Result manifest：`a448a65b1f83a9bde232395a18c491bc33b192ebd091a5a08b1a15be18cd35d3`。
- Candidate metrics：`452a31019ec528991543dc33e31c6d30cb28b56873309f8303d45020af559e94`。
- Result receipt：`3ef41b0e0c211935d2e0f900732dbf4d30b792e86c5144115d8850671a3d3303`。
- Frozen result report：`dd6758baa8bc780397d315831978b7b5e085c44418d97a659e7ba75aca8f26d1`。

## 6. 冻结决定与后续建议

1. 将当前结果冻结为正式 efficiency negative；不重跑、不调整阈值。
2. 不签发 D6-A seed-0 训练授权；seed-1、proposal-confirmation、D6-B、candidate selection 与 sealed access 继续禁止。
3. 如需继续研究，只允许新建独立的 observation-only profiling 协议，分离 GPU scoring、host transfer、global assignment 和最终索引回传耗时，并记录同步边界。
4. 若未来提出 R2，应在新版本协议中先消除 CPU 关键路径或采用有复杂度上界的 GPU-compatible assignment/selector，再从 artificial zero-step 和独立 formal efficiency gate 重新开始；不得将 R2 结果追溯替换本次 R1 负结果。

## 7. 最终结论

D6-A R1 未通过预注册 formal efficiency gate。延迟门控以 735.14 倍对 1.15 倍的结果构成决定性失败，显存门控也以 1.11337 对 1.10 小幅失败。D6-A 必须在训练前停止；该结论与相关权限锁保持不可变。
