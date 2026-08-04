# Mamba Adapter v1.1 O0-xyz 多 seed 完整 monitor 内部诊断协议

## 性质与边界

本诊断在 R1 seed-0/1/2 训练、monitor 评价和 strict-train instrumentation 全部完成后声明，性质为明确的事后机制分析。它不属于预注册性能验证，不产生新获胜者，也不改变已经冻结的 O0=`xyz` 结论。

诊断包含完整 50-case monitor，不依据 Rim HD95、缺损类型或灾难标签挑选病例，因此避免只观察灾难病例造成的选择偏差。三个 seed 使用相同病例集合、相同 checkpoint 类型和相同 instrumentation 实现。

## 固定设置

| 项目 | 固定值 |
|---|---|
| 模型 | Mamba Adapter v1.1 O0=`xyz` out8192 |
| seeds | 0、1、2 |
| 数据 | 完整 monitor 50 cases / 10 skulls |
| 新训练 | 无 |
| official test | 禁止 |
| 灾难阈值 | `rim_contact_hd95_mm > 50.0` 或非有限值 |
| 用途 | 机制解释和新 development protocol 的假设生成 |

## 分析内容

1. 三个 seed 的灾难病例集合、复现次数和 defect type 分布；
2. 每个 seed 内部 feature 与 implant/final/rim 指标的描述性 Pearson、Spearman 相关；
3. 150 条 seed-case 记录的 pooled 描述性相关；
4. 对每个 case 分别减去三个 seed 均值后的 case-centered 相关；
5. 灾难与非灾难记录的内部 feature 均值差和比值；
6. 两个 Mamba block 的 alpha、mixer RMS、residual/input、tail/head 和 spike 位置；
7. 三个 seed 的实际 512-token 坐标、排序索引和排序后坐标是否逐元素相同。

case-centered 分析是本轮最关键的统计量。它控制病例固定难度，描述同一病例跨 seed 的内部状态变化是否与评价指标变化同步。由于只有 3 个 seed、50 个病例，所有相关均为探索性效应量，不进行模型选择意义上的显著性判定。

## 禁止事项

- 不得根据 P1 结果选择 seed-0、seed-1 或 seed-2；
- 不得重新比较 O1/O2/O3；
- 不得修改 50 mm 灾难阈值；
- 不得运行 official test；
- 不得把 monitor post-hoc 相关当作新方法的无偏验证；
- 新的层间约束、双向扫描或其他候选必须进入新的 skull-level development folds。

机器可读协议：

```text
docs/protocols/mamba_v11_o0_multiseed_full_monitor_posthoc_v1.json
```
