# Mamba v1.6 D6-A R1 梯度比例校准完整结果

> 本结果只使用四折各自的 development train 子集完成梯度比例测量。没有训练、模型更新、dev 访问、seed-1、D6-B、proposal-confirmation 或 sealed 数据访问。

## 1. 校准定义

- 候选：D6-A R1，seed 0，fold A-D。
- 每折：8 个冻结 batch，每 batch 8 个病例，共 64 个 train-only case slots。
- 公共测量对象：global pooling 前的共享 64D point feature `F`。
- 原始损失：`L_point`、`L_support`、`L_shape`。
- 同折权重：
  - `lambda_support = 0.5 * median(||dL_point/dF||) / median(||dL_support/dF||)`；
  - `lambda_shape = 0.1 * median(||dL_point/dF||) / median(||dL_shape/dF||)`。
- 不跨折汇总，不裁剪、不扫描、不取整、不人工调整。

## 2. 四折冻结权重

| Fold | lambda_support | lambda_shape |
|---|---:|---:|
| A | 0.494150599249 | 4316.05849206 |
| B | 0.527897066392 | 4345.89188804 |
| C | 0.497502166326 | 4021.99250307 |
| D | 0.535437539569 | 4579.44433601 |

- `lambda_support`：mean 0.513746842884，sample CV 4.080840%。
- `lambda_shape`：mean 4315.8468048，sample CV 5.296132%。
- 四折均位于冻结允许区间 `[1e-4, 1e4]`，且独立复算完全一致。

`lambda_shape` 的数值较大并非数值错误；其原因是原始 `L_shape` 对公共特征 `F` 的梯度比 `L_point` 小约四个数量级。权重只改变训练目标中的相对尺度，不代表 `L_shape` 本身异常。

## 3. 参数组诊断

该诊断是冻结校准完成后的 observation-only 分析，不修改原校准规则，也不构成新的通过门控。

### 共享 point encoder

- 加权 support / point：0.448-0.547。
- 加权 shape / point：1.400-1.595。

### point calibration branch

- 加权 support / point：0.142-0.163。
- 加权 shape / point：0.432-0.497。

### slot attention and pointer

- `L_point` 梯度为 0，符合分支结构：该参数组不在 point-classification 路径上。
- support 与 shape 的加权梯度均为有限非零值。

## 4. 结果解释

公共特征 `F` 上的 0.5/0.1 目标不能被解释为所有参数组都应具有相同梯度比。各参数组还受到自身 Jacobian、分支连接关系与损失支持域的影响。因此，当前结果证明的是：

1. 四折校准计算稳定、有限、可复现；
2. 同折权重必须保持独立绑定，不能用四折均值替代；
3. 较大的 `lambda_shape` 在参数空间中产生了可观但有限的梯度；
4. 仅有分量范数仍无法判断加权总梯度中的方向相消或放大。

## 5. 结论与下一门控

D6-A R1 梯度比例校准完成并通过其冻结协议，但这不等于训练获批。下一步仅授权独立的 calibrated weighted zero-step：在每折一个冻结 train-only batch 上计算

`L_total = L_point + lambda_support * L_support + lambda_shape * L_shape`

并记录公共特征及三个参数组的合成梯度范数、分量范数和方向余弦。该 zero-step 必须保持 optimizer steps=0、model updates=0、dev/protected access=0。通过人工审阅前，D6-A seed-0 训练继续禁止。

