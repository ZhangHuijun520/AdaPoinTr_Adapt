# L4 Round A mechanism diagnostics 只读复盘与下一阶段干预方案 v1

- 日期：2026-09-14（UTC）
- 状态：`PLAN_ONLY_NOT_AUTHORIZED`
- 决策边界：本文件不是训练、推理、NPZ/checkpoint 访问或 Round B 启动授权
- 当前结论：保留 Q0 为 Round A 的领先候选；在完成同一 QC checkpoint 的因果干预前，不进入 Round B

## 1. 审计范围与证据

本次只读复盘仅使用已经冻结的正式 development 评估 v2 产物：

`logs/cranial_scqr_v11/l4_round_a_development_evaluation/cranial_scqr_v11_l4_round_a_dev_eval_v2_20260914T054006Z`

未加载 checkpoint，未打开 NPZ，未调用 GPU，未重新执行推理或统计分析器，也未修改任何训练/评估产物。复盘时重新执行 `sha256sum -c files.sha256`，冻结清单内文件全部通过。

关键证据文件：

| 文件 | SHA256 |
|---|---|
| `mechanism_diagnostics.csv` | `8dee42b7a56efe154b046db70c8f4e8d91678389cb1c357b5e44b17906ad5ec3` |
| `per_model_case_metrics.csv` | `c2e1317715fb037a73ab3e1054c573d0cd3efe4ea57cefb161de2b1d1bdec29e` |
| `fold_and_combined_summary.json` | `62ce0326bd7c597bc929ca339658fdf1a2f1b359187e15cd430391d2fa867aef` |
| `round_a_gate_receipt.json` | `70a4ab13bb18f4e2bb41faaca5c6814f639ae5ae8c69c86e33e8be552f36200c` |

数据结构核验结果：840 条 mechanism rows 与 840 条 case-metric rows 以 `(candidate, fold, seed, case_id)` 完全一一对应；Q0/QC 构成 210 个 case 配对、42 个 source-skull 配对，每个 source skull 恰含 5 种 defect case。

## 2. Round A 结论应如何表述

Q0 的 combined RimCover-P95 为 `8.145128 mm`，QC 为 `8.292559 mm`；QC−Q0 为：

- Fold A：`+0.103343 mm`；
- Fold B：`+0.191518 mm`；
- combined：`+0.147430 mm`；
- source-skull stratified bootstrap 95% CI：`[-0.182715, +0.476516] mm`；
- case：Q0 胜 108、QC 胜 102；source skull：Q0 胜 25、QC 胜 17。

因此准确结论是：**Q0 在预先规定的严格点估计 gate 上优于 QC，导致 Round A 为 `NO_GO`；但 QC−Q0 的 95% CI 跨 0，现有 development84 证据不足以宣称 Q0 对 QC 存在已经统计确认的总体优势。** 这不是“QC 无效”：QC 相对 B0 的 combined RimCover-P95 改善为 `-3.533705 mm`，95% CI `[-4.407872, -2.652132] mm`，两个 fold 均改善。

QC 相对 Q0 的其他 combined 差值也整体偏向 Q0：implant CD `+0.090437 mm`、final CD `+0.004559 mm`、final HD95 `+0.022159 mm`，但各自 CI 跨 0；final NSD@1mm 为 `-0.0004639`，其 95% CI `[-0.0008533, -0.0000789]`。这些属于同一 development 复盘中的辅助证据，不应被提升为独立确认结果。

## 3. mechanism diagnostics 发现

### 3.1 contact head 质量不是 QC 落后的直接解释

Q0 与 QC 的 proxy label prevalence 和 KNN32 半径逐 case 完全相同，说明配对标签与局部邻域口径一致。combined contact AUPRC：

- Q0：`0.917961`；
- QC：`0.921249`；
- QC−Q0：`+0.003289`，且 fold A 为 `-0.001329`、fold B 为 `+0.007906`。

在 source-skull 层，QC−Q0 contact-AUPRC 差值与主指标差值的 Spearman `ρ=-0.103, p=0.518`；case 层为 `ρ=-0.116, p=0.094`。这不支持“QC 因 contact classifier 明显变差而落后”的解释。

### 3.2 β=1 强烈改变了注意力分布，但没有转化为可见的平均收益

combined diagnostics：

| 指标 | Q0 | QC | QC−Q0 |
|---|---:|---:|---:|
| positive attention mass | 0.0351 | 0.6464 | +0.6113 |
| query attention entropy | 5.4879 | 2.7801 | -2.7078 |
| query residual RMS | 0.002788 | 0.000378 | -0.002410 |
| coarse RimCover-P95 (mm) | 14.0509 | 14.1322 | +0.0813 |

β=1 将注意力大幅集中到 contact-positive proxy，并显著降低熵，这是实现按设计生效的直接证据。然而 QC 的 query residual RMS 同时降低约 86%，其 `alpha_q` 也发生了强烈的 fold-specific 收缩（Fold A 甚至为很小的负值）。一种合理但尚未证实的解释是：训练优化通过压低 residual gate，部分抵消了过强或不稳定的 contact-biased attention。由于 Q0/QC 是两次独立训练，这一解释目前只能视为机制假设。

inter-query attention similarity 在两者中都接近 1，说明各 query 的注意力图高度同质。β=1 没有解决 query 间差异性不足；但该指标变化与 QC−Q0 主指标差值也无可靠关联。

### 3.3 最终差异主要随 coarse 差异移动

`coarse_rimcover_p95_mm` 在 query conditioning 之前产生。QC−Q0 的 coarse 差值与最终 RimCover-P95 差值：

- case 层 Spearman `ρ=+0.836`；
- source-skull 层 Spearman `ρ=+0.836`；
- case 层符号一致 172/210（81.9%）；
- 加入 fold 指示变量的探索性线性模型中，coarse 差值斜率约 `0.683`，模型 `R²=0.769`。

当 QC 的 coarse 更好时，96 个 case 中 80 个最终也更好；当 QC 的 coarse 更差时，114 个 case 中 92 个最终也更差。控制 coarse 差值与 fold 后，contact AUPRC、positive attention mass、entropy、query residual 等差值与剩余误差均无显著关联。

这使“差异的主要可见落点在 coarse/upstream 表征”成为当前最强的定位证据。需要特别注意：这仍是关联而非因果。虽然单次 forward 中 query bias 位于 coarse 之后，训练时 biased attention 的梯度仍可经 value/query 路径改变共享特征和上游权重；同时 `contact_probability.detach()` 只阻断了该概率分支的反向梯度，并未隔离整个 conditioning 路径。

### 3.4 defect 与 fold 异质性不支持仓促做解剖学结论

combined QC−Q0 主指标按 defect type：bilateral `+0.482 mm`、frontoorbital `-0.331 mm`、parietotemporal `+0.365 mm`、random_1 `+0.388 mm`、random_2 `-0.167 mm`。但多类在 Fold A/B 间方向翻转，例如 bilateral 为 `-0.166/+1.130 mm`，random_1 为 `+1.064/-0.287 mm`。每个 fold/defect 仅 21 case，现阶段不能据此选择某个缺损类型做定向优化。

## 4. 当前机制判断（按可信度分层）

1. **高可信事实**：β=1 显著提高 positive attention mass 并降低 entropy；QC 的 contact AUPRC 并未整体变差；QC−Q0 的平均劣势很小且 CI 跨 0。
2. **中等可信定位**：Q0 的点估计优势主要伴随 QC/Q0 两个 checkpoint 的 coarse/upstream 差异，而不是伴随 contact quality 或注意力诊断的逐样本差异。
3. **待验证因果假设**：强 contact bias 可能改变训练轨迹并诱发 residual gate 收缩及 coarse 表征漂移；不能用现有独立 checkpoint 对比区分“推理时 bias 的即时作用”和“训练形成的权重差异”。

综上，当前最合理的答案不是“contact bias 一定有害”，而是：**QC 将注意力强制集中到了预期位置，但这种集中没有稳定转化为最终几何收益；Q0 的点估计优势主要表现为更好的 coarse 起点。下一步必须在同一 QC 权重下做干预，才能判断 β=1 的即时作用是有益、无效还是有害。**

## 5. 下一阶段：QC 同 checkpoint 因果干预（Round A-I）

### 5.1 目标和边界

Round A-I 是 mechanism intervention，不是 Round B，也不产生 confirmation20/official-test 结论。它不得训练、BNCal、调参、更新 checkpoint 或自动启动后续 run。

在获得分别的“实施工具授权”和“正式执行授权”之前，不得创建工具、加载 checkpoint、读取 NPZ 或使用 GPU。

### 5.2 冻结干预条件

对 Fold A、Fold B 各自已经冻结的 QC BNCal checkpoint，仅在内存中运行以下四个条件：

1. `native_qc`：原始 `β=1` 行为；
2. `bias_zero`：以全 1 contact probability 替换 conditioner 输入，使 `log(p)=0`；
3. `case_mean_probability`：以该 case 的 mean probability 常量替换全部 proxy；
4. `fixed_seed_within_case_probability_permutation`：在 case 内固定种子打乱 probability，保留边际分布但破坏空间对应。

第三项在数学上应与第二项等价：对每个 query，常量 `β·log(mean(p))` 只给所有 proxy logits 加同一常数，softmax 会消去该常数。因此它是**实现负对照**，不是独立的生物学机制。如果两者超出冻结容差，则该次执行应判为无效。

干预应通过 runner 内的临时 forward-input hook 或等价无状态包装完成；不得修改模型源文件或持久 buffer。permutation seed 必须由冻结的 protocol id、fold、case_id 经 SHA256 推导，禁止使用 Python process-randomized `hash()`。

### 5.3 最小执行规模（未来需单独授权）

- 仅 development84 的两个固定 dev split：Fold A 105 case、Fold B 105 case；
- 每个 case 四次 forward，共 840 次 forward；
- 每 fold 的 QC checkpoint 只加载一次，共 2 次 checkpoint load；
- 每个 case 的 NPZ 最多打开一次，共 210 次；先只取 `partial` 完成四次 forward，再按原冻结评估合同读取 metric-only `implant`/`gt`；
- 不读取 train payload、confirmation20、official test、old monitor 或 MUG payload；
- 不保存点云预测，只保存标量 metrics、diagnostics、审计计数和收据；
- checkpoint/model state 在每 fold 前后计算 hash，必须完全不变；optimizer constructions/steps、parameter/buffer updates 必须均为 0。

Q0 不需要重新推理：以 v2 冻结 Q0 case metrics 作为参照。`native_qc` 必须首先复现 v2 冻结 QC 指标，构成跨执行桥接；否则停止并判 execution invalid，不分析干预结果。

### 5.4 预先冻结的比较与判读

所有距离差值均为“前者减后者”，负值更好；沿用 source-skull 为 bootstrap unit、Fold A/B 分层、seed `20260910`、10,000 次 percentile bootstrap。

| 比较 | 回答的问题 |
|---|---|
| `bias_zero − native_qc` | 去掉即时 contact bias 是否改善同一 QC 权重？ |
| `permutation − native_qc` | probability 的空间对应是否提供有效信息？ |
| `case_mean_probability − bias_zero` | softmax 常数平移与实现合同是否正确？ |
| `bias_zero − frozen_Q0` | 去掉即时 bias 后，QC 训练形成的权重是否仍落后 Q0？ |

判读规则：

- `bias_zero − native_qc` 两 fold 均不大于 0，combined 95% CI 上界小于 0：**即时 bias 有稳健伤害证据**；
- 点估计小于 0 但 CI 跨 0：**仅有方向性伤害证据**；
- `native_qc` 优于 `bias_zero`，且 permutation 明显劣于 native：**空间对齐的 bias 有益，QC−Q0 差异更可能来自训练轨迹**；
- `bias_zero` 仍劣于 frozen Q0：**训练诱导的权重差异仍存在**；
- native、zero 和 permutation 近似无差异，同时 residual gate 维持极小：**conditioning 在最终输出上近似失活**；
- `case_mean_probability` 与 `bias_zero` 不满足预先冻结的数值等价容差，或 native 无法复现 v2：**执行无效，不做机制结论**。

报告必须同时给出 Fold A、Fold B、combined point estimate、source-level CI、case/source 胜负数及原有 guardrails，不允许只挑选有利层级。

### 5.5 分阶段授权顺序

1. **P1：只读 pre-implementation 核验**：核对两条 QC checkpoint 路径/size/SHA256、v2 证据哈希、dev manifests、可插桩点与精确资源上限；不得加载 checkpoint 或 NPZ。
2. **P2：implementation-only**：只创建独立 intervention runner、analyzer、synthetic CPU contract test 和冻结机器可读 protocol；只做语法检查和 synthetic CPU tests。
3. **P3：post-implementation 只读核验**：形成单独的正式执行授权请求；不得加载真实 checkpoint/NPZ。
4. **P4：一次正式 Round A-I 执行**：只有用户按精确请求文件单独授权后才可运行；禁止自动重试。
5. **P5：只读结果判读**：冻结收据并给出机制分类；仍不得自动进入 Round B。

### 5.6 Round A-I 后的条件式路线

- 若即时 bias 有害或近似失活：维持 Q0 为主线，停止 QC；不在同一 dev 上事后搜索 β。
- 若 bias 有即时收益但 `bias_zero` 仍落后 Q0：把问题定位为训练轨迹。只有另行冻结新协议后，才考虑一个最小训练干预（例如延迟启用/弱化 bias），且需要新的 scratch-training 授权。
- 若 permutation 证明空间对应有效而 β=1 过度集中：可在新版本中预先冻结单个较弱 β 或温度方案；不得根据当前 dev 逐值挑选最优 β。
- 只有新的干预结果给出清晰、双 fold 一致且通过 guardrail 的 go 决策，并经用户再次明确授权，才讨论 Round B。

## 6. 记录完整性附注

v2 `environment.json` 中 `observed_peak_gpu_memory_used_mib=6` 是 launcher 对制表符日志误用空白字段解析造成的派生值错误。冻结的 `resource_monitor.tsv` 有 1,189 条记录，`memory_used_mib` 实际最大值为 `1109 MiB`；仍低于 `20480 MiB` gate，因此不改变执行有效性或科学结论。冻结结果目录不应回写修复；后续工具应修正解析并在新收据中记录该 provenance caveat。

## 7. 下一步唯一建议

下一步不是 Round B，也不是正式干预推理；应先执行 **P1 只读 pre-implementation 核验**，随后生成精确的 implementation-only 授权请求。任何 checkpoint/NPZ/GPU 访问都必须等待更后的独立正式执行授权。
