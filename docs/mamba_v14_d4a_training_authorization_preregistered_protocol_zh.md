# Mamba v1.4 D4-A head-only training execution authorization

## 范围

本授权仅允许 D4-A proposal head 在 MUG500+ D4 source100 四折 development 数据上执行 seed 0 的 head-only feasibility。授权签发本身不读取病例、不创建 optimizer、不启动训练。

## 冻结输入

- 父协议：Mamba v1.4 D4 candidate/training protocol v1。
- 父实现：`mamba-adapter-v14-d4a-zero-step-preflight-v1`。
- server zero-step receipt、metrics、report 和 files manifest 均按 SHA256 精确绑定。
- D4 source100 fourfold lock：100 个来源、400 个病例，每折 75 train / 25 dev 来源。
- D4 M2 generation audit portable manifest：400 个经过独立哈希和几何审计的 NPZ。

## 训练预算

- folds：A、B、C、D；seed：0。
- 每折 train：75 个来源、300 个病例；dev：25 个来源、100 个病例。
- 每 epoch 以 source skull 为 shuffle 单位；同一来源的四个病例保持相邻且按 case ID 排序。
- epochs：50；batch size：8。
- AdamW：learning rate `1e-3`，weight decay `1e-4`。
- CosineAnnealingLR：`T_max=50`，`eta_min=1e-5`。
- gradient clip norm：1.0。
- 仅 proposal head 可训练；不得加载 backbone/completion checkpoint。
- 不早停，不做 augmentation，不写中间 checkpoint；只保留 final epoch head。
- 训练期间不得打开 dev NPZ；第 50 epoch 全部 optimizer steps 结束后只允许一次 dev evaluation。

## Gate

四折 out-of-fold dev 合计必须精确覆盖 400 个病例。每个病例必须存在 reference-rim positive candidate，且冻结 selector 选出的 32 个点中至少有一个 positive；所有输出必须有限。任何一例失败都将把 D4-A 冻结为负结果，并禁止 T0/T1/T2 Round A。

即使 D4-A 通过，本阶段也只允许后续单独物化 T0/T1/T2 Round-A 配置；不得自动启动完整模型训练或候选选择。

## 保护边界

- MUG500+ D3 25-source holdout：锁定。
- SkullBreak confirmation20、old monitor、official test：锁定。
- SkullFix selection：锁定。
- T0/T1/T2：未授权。
- candidate selection：未授权。
