# Mamba v1.5 D5-A seed-0 训练执行授权预注册

> 本文件在任何 D5-A 训练开始前冻结。授权只覆盖 V0/V1、seed 0、四个 development fold；签发授权和运行 preflight 都不得启动训练。

## 授权范围

- 候选：V0 reference 与 V1 experimental。
- 顺序：V0 A-D，随后 V1 A-D。
- 总预算：8 个 head-only training；每个 50 epoch、1900 optimizer steps。
- 每折：75 source / 300 case 训练，25 source / 100 case 在最终 epoch 后一次性评估。
- checkpoint：仅 final epoch；不允许 intermediate 或 best-dev checkpoint。

## 判定边界

- V0 只作同数据、同预算 reference，不具有晋级资格。
- V1 必须在 400 个 out-of-fold case 中全部保留至少一个 reference-rim positive，四折输出全部有限且配对完整。
- 即使 seed-0 通过，本授权也不自动开放 seed-1；只能另行签发 V1 seed-1 授权。
- seed-1、development-all、proposal confirmation、D5-B、completion holdout 和 official test 当前全部禁止。

## Preflight

preflight 只复核候选锁、zero-step 冻结结果、数据锁、generation audit、8 个 runtime config 与执行代码；允许构造 V0/V1 module，但不构造 optimizer、不读取 dev case、不写 checkpoint、不执行 optimizer step。

## 防止结果后调参

禁止扫描 kNN、loss 权重、margin、pool/query 数、seed 或训练预算；禁止根据 dev 选择 epoch；禁止失败 fold 重跑；禁止将诊断指标替代 400/400 硬门控。
