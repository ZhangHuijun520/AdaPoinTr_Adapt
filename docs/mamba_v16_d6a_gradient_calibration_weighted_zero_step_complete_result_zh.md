# Mamba v1.6 D6-A R1 梯度校准与 weighted zero-step 完整结果

> 本阶段只完成 R1、seed 0、四折 train-only 梯度比例校准与加权总损失 zero-step。没有训练、模型更新、dev 评估、seed-1、D6-B、候选选择或 sealed 数据访问。

## 冻结校准权重

| Fold | lambda_support | lambda_shape |
|---|---:|---:|
| A | 0.494150599249 | 4316.05849206 |
| B | 0.527897066392 | 4345.89188804 |
| C | 0.497502166326 | 4021.99250307 |
| D | 0.535437539569 | 4579.44433601 |

- `lambda_support` sample CV：4.080840%。
- `lambda_shape` sample CV：5.296132%。
- 四折权重均有限、为正、位于冻结区间 `[1e-4, 1e4]`，并被独立复算。

## Weighted zero-step

- 每折读取第一个冻结 8-case train-only batch，共 32 个 case slots。
- 损失为 `L_point + lambda_support_fold*L_support + lambda_shape_fold*L_shape`。
- forward passes：4；gradient queries：16。
- optimizer constructed：`False`；optimizer steps：0；model updates：0。
- model state unchanged：`True`；random state restored：`True`。
- development dev、proposal-confirmation、completion holdout、official test 与 sealed 数据：均未访问。

### 合成梯度诊断

- common-F `total/sum(component norms)`：0.745-0.767。
- common-F total 与 point cosine：0.901-0.933。
- shared point encoder 最低 total/sum：0.420（fold C）。
- point calibration branch 最低 total/sum：0.465（fold C）。
- slot attention/pointer 最低 total/sum：0.473（fold C）。
- slot support 在 fold B/C 与 total 的 cosine 为 -0.677/-0.816，但 total 仍有限非零并与 shape 高度同向。

这些结果表明存在可解释的多目标方向冲突，但没有总梯度消失、非有限值或数值爆炸。预注册的实现安全门控通过；该结果不构成效果门控，也不自动授权训练。

## 训练前约束

1. R1 必须使用同折权重，禁止用四折均值替代。
2. `L_total` 的标量值由加权 `L_shape` 主导，不得用于 early stopping、LR 调度、跨折比较或候选选择。
3. 必须分别记录 raw/weighted 三项 loss 与总梯度 finite 状态。
4. R0 保持冻结 D5 V1 loss，不使用 R1 校准权重。
5. 训练预算、final-only checkpoint、R0/R1 执行顺序与效率门控必须另行预注册。
6. seed-1、proposal-confirmation、D6-B、candidate selection 和 sealed access 继续禁止。

## 冻结哈希

- calibration completion manifest：`8b848b241a7218e26551e52ab3d2922bceb826ab1784b166583edcd6712874eb`。
- calibration completion receipt：`b86ad7e35f91e8d03fad6d11d2b4879e294a52f59b9836ee5e73bd300449b100`。
- calibrated fold weights：`077920aad2e8890ea0028718d9e56f973320f20340505c551708b13dbf224290`。
- weighted zero-step manifest：`128e4eb9ad14fdd25474fb86ffef107db8a7b46788756d29d2f35332a41f0e0a`。
- weighted zero-step metrics：`f65ba54bcc1727db026cef54bc78d7bea997fb76e7b47c51bfbc839f6c87f41e`。
- weighted zero-step receipt：`33e4a9450475ef00e1df57f6f96fe1d71e89aade81dda952ca9e56edc20821db`。
- weighted zero-step report：`96b4f90a10eef3fe2311c8be72a559c391ccb6cc73453c6539c9e49cd1ea16bc`。

## 结论

D6-A R1 梯度校准与 calibrated weighted real-train zero-step 完整通过并冻结。下一步是先完成最小归档与本地恢复验证，再单独冻结 R0/R1 seed-0 训练协议；当前训练权限仍为 `False`。

