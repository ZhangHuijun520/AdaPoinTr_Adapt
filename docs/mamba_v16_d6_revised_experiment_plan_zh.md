# Mamba v1.6 D6 修订实验计划

> 状态：待分阶段冻结和执行。
>
> 父结果：D5-A V0=`322/400`，V1=`368/400`，正式状态为 seed-0 frozen negative。
>
> 核心边界：结束 D5；不修改 K；不运行 D5 seed-1；不打开 D5 proposal confirmation、completion holdout 或其他 sealed/protected 数据。

## 1. 研究目标

D6 检验一个单一、可证伪的问题：

> 在 partial-only inference 和固定 32 proposal 预算下，assignment-consistent 的 32-slot joint support allocator 能否在全新来源上，使每个病例的最终离散 32-anchor 集合至少包含一个冻结定义的 positive contact-support candidate？

D6 不把 `400/400` 解释为总体零失败证明。它是有限测试套件上的操作性安全门控；结果必须同时报告 source-clustered uncertainty 和零失败时的一侧 miss-rate 上界。

## 2. 数据与终局治理

官方 Figshare v20 健康 A-series 共 500 个来源。冻结排除：

- D3 source125；
- D4 source100；
- D5 source150，包括其未打开的 sealed partitions。

三者并集必须恰好为 375，pairwise overlap 必须为 0。剩余集合必须恰好包含 125 个来源和 25 个完整官方 ZIP，不允许部分 archive 重叠。

D6 在任何 geometry 打开前一次性冻结：

- development100：20 个完整 ZIP，未来用于四折 feasibility；
- proposal confirmation25：5 个完整 ZIP，只允许离线下载和 checksum，seed-0 与 seed-1 全部门控通过前禁止提取。

分区采用五个预定义编号宏分层，每层通过固定 salt 和官方 archive metadata 确定性选择一个 confirmation ZIP，其余 archive 进入 development。禁止人工换源、QC 后替换或基于几何/model metric 调整。

D6 是当前 MUG500+ proposal-allocation 路线的 terminal decision stage。D6 失败后不得建立 D7 并复用 D6 development；后续必须切换到新独立来源和 patch/graph representation family。

## 3. 分阶段访问策略

1. **M0 metadata-only acquisition lock**：冻结精确 100/25 来源及下载计划；geometry access=false。
2. **M1 mechanism protocol**：冻结 R0/R1、positive-mask、assignment、loss、效率门、tie rule 和失败语义。
3. **M2 implementation tests**：只用人工 toy cases 与历史非证据输入，验证 assignment 可学习性、唯一性和 soft/hard 一致性。
4. **M3 zero-step**：CUDA forward/backward，optimizer=0、dev=0、model updates=0。
5. **M4 development extraction/QC**：M1-M3 通过后才授权提取 development100；confirmation25 继续 sealed。
6. **M5 generation/audit**：继承冻结 M2 几何协议，生成 100x4=400 个病例并独立审计。
7. **M6 training-only calibration**：只使用 fold-train，optimizer=0、dev=0。
8. **M7 seed-0**：R0/R1 四折 head-only；final epoch only；一次性 dev。
9. **M8 seed-1**：仅当 R1 seed-0 全部门控通过后单独授权。
10. **M9 confirmation**：两个 seed 均通过后，全 development100 训练预指定 final seed，一次性打开 confirmation25。

## 4. 候选定义

### 4.1 R0

R0 是 D5 V1 的精确复现：27D descriptor、shared point encoder、partial global context、三个冻结损失及 stable score top-32。R0 只用于新数据参考和 paired comparison。由于该机制已在 D5 失败，R0 不具备 D6 推进资格。

### 4.2 R1

R1 复用 R0 的低层 partial-only representation，仅替换候选集合形成机制：

```text
8192 point context features
+ 32 learnable support slots
-> slot-conditioned point logits
-> assignment-consistent soft training allocation
-> deterministic global unique hard assignment
-> exactly 32 unique anchors
```

禁止使用 GT、implant、完整颅骨、defect family 或 sealed 信息作为 inference feature。

## 5. 对原计划的关键修订

### 5.1 拒绝独立 noisy-OR 概率解释

不再把 `1-product(1-m_j)` 称为 32 个相关 slot 的真实命中概率。相同 slot 会被错误地重复计数，因此该公式不能单独作为正式 existence objective。

### 5.2 训练与推理必须 assignment-consistent

原先按 slot index 顺序 greedy 会引入任意优先级，并与连续 softmax loss 不一致。正式协议优先采用：

- 训练：具有 row-mass 与 candidate-capacity 约束的确定性 soft assignment；
- 推理：确定性的 maximum-weight bipartite assignment；
- tie rule：先比较 logit，再比较 slot index 和 candidate index；
- 输出：恰好 32 个 unique candidate indices。

具体 soft assignment、support-mass surrogate、temperature 和 numerical stabilization 必须在不打开 D6 geometry 前通过 toy-case tests 后一次性冻结。D6 只允许一个 R1 实现。

### 5.3 Loss 原则

R1 只保留必要目标：

- `L_point`：point-level calibration；
- `L_support`：对 assignment 后 positive support mass 的固定门槛约束；
- `L_sharp`：抑制仅靠弥散概率通过 soft objective。

唯一性由 assignment capacity 直接实现，不主要依赖 cosine diversity。不得在看到 D6 dev 后追加 margin、扩大 K、改变 slot 数或引入其他 contact/completion loss。

### 5.4 Gradient calibration

分项梯度比例必须在共同对象上计算，优先使用 shared point feature `F` 或 shared encoder 参数。必须分别记录 shared、point-only 和 slot-only 参数组，不能把不相交参数的 global norm 直接比较。

Calibration 固定 initialization、batch IDs、batch count、raw norm、clipped norm、median rule、zero/non-finite failure。Optimizer 不构造或 steps=0，不访问 dev。

## 6. Positive-mask contract

正式 M1 协议必须逐字绑定 D5 的 candidate universe、坐标归一化、GT rim/contact 定义、距离阈值、边界等号规则及 case ID。每个正式病例必须至少有一个 oracle positive；空 positive mask 是 hard failure。

GT positive mask 只允许进入 training loss 和 frozen dev scoring，不得进入 descriptor、slot feature、assignment logit 或 inference tie rule。

## 7. 必需实现测试

- 相同输入、state 和 device 得到相同 32 indices；
- 32 indices 全部唯一；
- 全局 assignment 的总 logit 不低于顺序 greedy；
- 提高 positive candidate logit 不得恶化 support loss；
- 相同 slot/candidate 并列时 tie rule 稳定；
- synthetic collapse case 被 capacity constraint 拒绝；
- soft positive mass 与 hard assignment miss 的 F2 情形可检测；
- empty positive mask、NaN/Inf、短输入和重复 candidate hard fail；
- GT mask 不进入 inference path；
- tiny synthetic task 能通过 optimizer 学到 positive assignment，但该测试不使用任何 D6 geometry，也不构成科研结果。

## 8. 效率门

建议冻结：

- trainable proposal-head parameters <=100,000；
- descriptor+head inference latency <=1.15x R0；
- peak GPU memory <=1.10x R0。

Benchmark 必须固定 GPU、CUDA/PyTorch、dtype、batch size、warmup=10、timed runs=50、CUDA synchronize、median latency 和 reset peak memory。效率失败发生在 dev 打开前，只能通过版本化 protocol amendment 简化实现，不能放宽门槛。

## 9. Seed-0 门控

R1 必须同时满足：

- 400/400 OOF cases present；
- A/B/C/D 各 100/100；
- 四个 defect family 各 100/100；
- 32/32 selected indices unique；
- all required outputs finite；
- exact case pairing；
- efficiency gates passed；
- sealed/protected access=false。

`399/400` 即失败。失败后冻结，不运行 seed-1，不修改 assignment、loss、temperature、slot 数、K 或 random seed。

结果报告必须给出一侧 95% miss-rate 上界。即使观察到 0/400，有限样本上界仍约为 0.75%，不得宣称总体零失败。

## 10. Seed-1 与 confirmation

仅当 seed-0 通过所有硬门控，才单独授权 R1 seed-1 四折，再次要求 400/400 和效率通过。同一 400 病例上的两个 seed 是训练稳定性检查，不增加独立来源样本量。

两个 seed 均通过后，按预注册 seed 在 development100 上训练 final head，一次性打开 confirmation25 的 100 个派生病例，要求 100/100。零失败 0/100 的一侧 95% miss-rate 上界约为 2.95%，必须一并报告。

Confirmation 失败后冻结 generalization failure，不换 final seed、不调 loss、不改 assignment。

## 11. D6-B 边界

D6-A 通过只证明 proposal support feasibility，不证明 completion 改善。D6-B 必须另立协议；在 D6-A 完成前不冻结其具体 non-inferiority 数值。

D6-B 首轮原则上比较同轮 baseline 与加入冻结 allocator 的 completion，保持总 query=256，并冻结 allocator。D6-A confirmation 不得被重新命名为 completion holdout。目标域 SkullBreak confirmation、SkullFix 和 official test 继续锁定。

## 12. 停止规则

- Seed-0 失败：冻结并停止 D6-A。
- Seed-1 失败：冻结跨 seed 不稳定并停止。
- Confirmation 失败：冻结独立来源泛化失败并停止。
- 任一阶段失败后只允许 frozen-output observation-only 分析。
- 新假设必须使用新独立来源；不得继续消费 D6 development。

## 13. 当前授权状态

本计划本身不授权下载、提取、生成、模型实现或训练。下一步仅授权创建 metadata-only source125 acquisition lock；该 lock 通过后，可下载 development 与 confirmation ZIP 并校验，但 development extraction 仍须等待 M1-M3，confirmation extraction 继续禁止。

