# Mamba v1.3 D3 S1 seed-0 runtime 配置物化预注册协议

> 本协议在 S1 training-only gradient-ratio calibration 完成后、配置物化前冻结。物化本身不授权训练，也不访问 development 指标或 locked holdout。

## 输入凭据

- 冻结的 D3 Round-A `S1` fold A-D 非运行模板；
- 状态为 `S1_gradient_ratio_calibration_frozen_complete` 的 completion receipt；
- completion receipt 绑定的四份 fold calibration receipt 及其哈希链；
- 每个 fold 固定 `8 x 8` training-only slots、`0` optimizer step 和目标梯度比 `0.075`。

## 唯一允许的变换

对每个 fold，从同 fold calibration receipt 读取未裁剪、未舍入、未人工修改的 `calibrated_weight`，并精确写入：

```text
model.dense_contact_objective.weight
```

不得使用跨 fold 均值，不得修改 loss 定义、数据字段、模型结构、训练超参数或候选规则。

## 物化后的权限

- `training_authorized=false`；
- `holdout_authorized=false`；
- `S2_authorized=false`；
- `selection_started=false`；
- 四份配置不可直接训练。

物化与哈希验证通过后，只允许进入独立的 S1 seed-0 training authorization；授权器必须再次绑定物化 receipt、配置 SHA256 和实现代码，不能由物化脚本自动启动。
