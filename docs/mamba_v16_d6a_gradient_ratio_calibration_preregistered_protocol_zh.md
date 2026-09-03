# Mamba v1.6 D6-A R1 training-only 梯度比校准预注册协议

> 状态：在任何 D6 梯度测量之前冻结。本阶段只定义 R1 的两项辅助损失权重如何测量；协议锁本身不授权校准执行，不训练模型，也不访问任何 dev 或 sealed 数据。

## 1. 科学问题与候选边界

D6-A 只允许一个实验候选 R1。R0 是精确 D5 V1 参考，继续使用其冻结损失定义，不对 R0 创建新校准权重。R1 的总损失保持：

```text
L_point + lambda_support * L_support + lambda_shape * L_shape
```

机制协议已经在读取 D6 geometry 前冻结目标梯度比：`lambda_support * L_support` 相对 `L_point` 为 `0.5`，`lambda_shape * L_shape` 相对 `L_point` 为 `0.1`。本协议不能修改这两个目标，也不能根据 D6 结果选择其他比例。

## 2. 数据与固定 batch

- 仅使用每折 300 个 training case；dev、proposal-confirmation25、holdout 和 official test 的访问数均为 0。
- 每折固定 8 个完整 batch，batch size 为 8，共 64 个 case slots。
- 为避免单一来源内四种缺损被拆散，每个 batch 恰好包含两个完整来源，每个来源贡献四种冻结缺损族。
- 每折 75 个 train 来源按照 `sha256(protocol_id|fold|seed0|source_id)` 排序，固定取前 16 个来源；同一来源内病例顺序严格继承 fold train case-ID 文件。
- 锁输出直接冻结每折八个 batch 的 case IDs；后续授权和执行只能读取该清单，不能重新抽样。

## 3. 共同梯度对象

校准的唯一共同对象是 global pooling 前的 shared 64D point feature `F`，每个病例形状为 `8192 x 64`。在同一 forward graph 上分别用 `autograd.grad` 获得 `L_point`、`L_support` 和 `L_shape` 对完整 batch `F` 的 global L2 norm。

不允许用互不相交的参数组范数直接形成权重。`shared_point_encoder`、`point_calibration_branch`、`slot_attention_and_pointer` 三组参数范数必须额外记录，用于诊断梯度去向，但不得参与权重计算或候选选择。

校准不执行 gradient clipping。回执中的 `raw_norm` 与 `reported_clipped_norm` 必须相同，并记录 `clipping_applied=false`。任何缺失、零、负或非有限的共同对象梯度都硬失败。

## 4. 唯一聚合与权重公式

对每项损失分别取恰好 8 个 raw norm 的中位数，然后计算：

```text
lambda_support = 0.5 * median_norm_L_point / median_norm_L_support
lambda_shape   = 0.1 * median_norm_L_point / median_norm_L_shape
```

两个权重都必须位于闭区间 `[1e-4, 1e4]`。禁止 clip、round、人工修正、跨折汇总或根据诊断参数组改权重。每折权重只能绑定回同一折的 R1 seed-0 runtime config。

## 5. 模型状态和副作用

- 每折使用未来 R1 seed-0 训练的精确初始化，seed 固定为 0；
- 不加载或保存 checkpoint；
- 不构造 optimizer，optimizer steps 和 model updates 均为 0；
- 使用 train mode 计算冻结损失，但测量后必须恢复模型 state、buffers 及 Python/NumPy/PyTorch CPU/CUDA RNG，并逐项验证；
- 已完成折不可覆盖或重跑，存在残缺 working directory 时必须人工检查。

## 6. 凭据与后续权限

每折回执冻结 8 个 batch IDs、train case-list SHA256、三项共同对象梯度 norm、三个诊断参数组 norm、中位数、两个最终权重、state 恢复和 RNG 恢复结果。只有四折全部完成且哈希链通过后，才能生成 completion receipt。

协议锁完成后只允许另行签发 calibration execution authorization。即使四折校准完成，也只允许下一步单独物化 receipt-bound R1 runtime configs；校准回执本身不授权 seed-0 training。Seed-1、proposal-confirmation25、D6-B 和 candidate selection 继续锁定。

## 7. 停止规则

任一共同对象梯度缺失、为零、非有限，任一权重越界，batch 成员漂移，state/RNG 恢复失败，或发现 dev/sealed 访问，都使校准失败并停止。不得更换 batch、重跑以挑选数值或放宽边界。
