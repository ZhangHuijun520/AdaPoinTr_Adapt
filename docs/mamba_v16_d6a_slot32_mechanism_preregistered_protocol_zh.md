# Mamba v1.6 D6-A assignment-consistent slot32 mechanism 预注册

> 本协议在 D6 development geometry 提取前冻结。它只授权实现、人工 toy-case tests 和无 D6 数据的 synthetic zero-step，不授权提取、生成、校准或训练。

## 科学问题

D5 V1 证明 partial-only context 与 set-level loss 有效，但 scalar top-32 仍有 32 个 rank-tail miss。D6-A 只检验一个结构变化：把单一标量排序替换成 32 个 slot 的联合唯一分配，同时保持 8192 candidates、32 proposal 和 V1 低层表征不变。

## R0

R0 精确复现 D5 V1：27D descriptor、64D point encoder、mean/max global context、219-128-64-1 classifier、冻结三个 loss 和 stable scalar top-32。R0 是新来源参考，不具备推进资格。

## R1

R1 使用：

- 与 R0 相同的 27D descriptor 和 64D point feature；
- 32 个 64D learnable slots；
- 一层单头 slot-to-point cross attention；
- 64-128-64 FFN；
- slot-conditioned 32x8192 pointer logits；
- shared point calibration logits 作为 pointer bias；
- trainable parameters 不得超过 100,000。

## Assignment-consistent 选择

Final inference 不使用 slot-index 顺序 greedy。它对 32x8192 logits 运行 deterministic maximum-weight rectangular linear assignment，输出恰好 32 个 unique candidate indices。

训练使用 deterministic straight-through assignment：

```text
hard forward = global unique assignment one-hot
soft backward = row softmax(slot logits / 1.0)
STE = hard + soft - stop_gradient(soft)
```

因此 `L_support` 的 forward 看到的 selected set 与 inference 完全相同，避免 soft-positive-mass 与最终 hard set 脱节。相关 slots 不再通过 noisy-OR 被解释为独立概率。

## Loss

- `L_point`：shared point calibration logits 的 case-balanced BCE。
- `L_support`：对 STE assignment 中的 selected positive mass 使用固定 smooth threshold loss。
- `L_shape`：归一化 row entropy 与 column collision penalty 之和。

唯一性由 hard assignment 保证，`L_shape` 只用于避免所有 slot 学成同一标量排序。正式总 loss 权重必须在 generation audit 后通过 fold-training-only shared-feature gradient calibration 冻结。

## Positive mask 与 leakage

Positive mask 必须是冻结 NPZ 的 `reference_rim_mask`，shape=`8192`、dtype=`bool`，并与 audit 的 `reference_rim_points` 一致。空 positive mask hard fail。

GT mask 只允许进入 loss 和冻结 scoring，不得进入 descriptor、point encoder、slot context、pointer logits、assignment 或 tie rule。

## 当前测试权限

下一步只允许：

1. 实现 R0/R1；
2. 在人工 points/masks 上做 deterministic、uniqueness、matching、collapse、leakage 和 tiny-learning tests；
3. 通过测试后做 artificial CUDA zero-step，optimizer=0、model updates=0。

继续禁止 D6 development extraction、generation、gradient calibration、seed-0 training、seed-1、confirmation、D6-B 和所有 protected 数据。

## 未来门控

Seed-0 必须达到 400/400、四折各 100/100、四类各 100/100、每例 32/32 unique、finite、exact pairing 和效率通过。`399/400` 即冻结失败。

只有 seed-0 全部通过才单独授权 seed-1；两个 seed 均通过后才一次性打开 confirmation25，并要求 100/100。零失败门控仍必须报告有限样本 miss-rate 上界，不能宣称总体零失败。

