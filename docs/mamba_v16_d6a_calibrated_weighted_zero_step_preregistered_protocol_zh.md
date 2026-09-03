# Mamba v1.6 D6-A calibrated weighted zero-step 预注册协议

本协议位于四折梯度比例校准完成之后、任何 D6-A 训练授权之前。

- 仅运行 R1、seed 0、fold A-D。
- 每折只读取该折校准日程中的第一个冻结 8-case train batch，共 32 个 case slots。
- 每折只使用该折冻结的 `lambda_support` 与 `lambda_shape`。
- 计算加权总损失及公共特征/三个参数组上的分量和总梯度。
- 梯度余弦只用于解释相消或同向放大，不设置事后阈值。
- 不构造 optimizer，不执行 step，不更新模型，不写 checkpoint。
- 不读取 development dev、proposal-confirmation、completion holdout、official test 或 sealed 数据。
- zero-step 通过后仍不自动授权 seed-0 训练；必须先冻结结果并独立审阅。

