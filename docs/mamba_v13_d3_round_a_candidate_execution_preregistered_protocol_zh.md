# Mamba v1.3 D3 Round-A 候选与执行协议预注册

> 状态：候选和执行规则已预注册；12 份配置仅为不可直接训练的锁定模板。当前不授权训练，也不授权访问 25 个 source-skull locked holdout。

## 1. 候选

- `S0`：同轮 O0-xyz v1.1 参考模型，每个 fold 重新训练；只作为门控参照，不可作为新方法获胜。
- `S1`：在 dense 8192 输出上加入与评估器 2 mm 定义一致的 contact-existence 和 GT-rim worst-10% tail objective。
- `S2`：224 个全局 learned queries 加 32 个 partial-only rim queries；从 96 个高分 proxy 中 deterministic FPS，坐标不偏移，推理时不得使用 GT、implant、defect type 或人工中心。

禁止在本协议中组合 `S1+S2`，也禁止根据 development 指标扫描 loss 权重、query 数、阈值或选择规则。

## 2. 数据边界

- 仅使用冻结 MUG500+ M2 `100/25` source-skull 数据锁中的 100 个 development skull。
- 四折 `A-D`，每折 75 train skull / 25 dev skull；每个 skull 的四种缺损不得跨 fold。
- 25 个 locked holdout skull 不得出现在候选配置中；方法和 seed-2 冻结前禁止推理、指标、可视化或人工检查。
- 训练 NPZ 中的 `reference_rim_mask` 只作为训练监督，不进入推理输入。

## 3. 权重校准

`S1` 和 `S2` 必须逐 fold 独立校准一次：

1. 使用 seed-0 候选初始化，optimizer step 之前的前 8 个完整训练批次；batch size 为 8，`drop_last=true`。
2. 分别计算 reconstruction loss 与 unit-weight auxiliary loss 对全部可训练参数的 global L2 gradient norm；缺失梯度按 0 计。
3. 每批 raw ratio 为 `aux_norm / max(reconstruction_norm, 1e-12)`。
4. fold raw ratio 为 8 个 batch ratio 的中位数，最终权重固定为 `0.075 / fold_raw_ratio`。
5. 非有限、0 或负结果均硬失败；不得裁剪、人工修正、使用 dev 指标或训练启动后重新校准。
6. 回执必须记录 8 个批次的 case ID、case-list SHA256、两类梯度范数、raw ratio 和最终权重。

## 4. S2 feasibility

完整 `S2` 训练之前，每个 fold 必须使用同 fold、同 seed 的冻结 `S0 BNCal` encoder 训练 proposal head。硬门控为该 fold 每个 held-out dev case 至少选中一个 GT-positive proxy。feasibility head 权重不得初始化完整 `S2`。

## 5. 执行顺序

1. 冻结 12 份不可运行模板和 hash 链。
2. 根据 template-lock receipt 单独物化 `S0` runtime configs，训练并冻结四折 checkpoint、BNCal 和效率回执。
3. 运行四折 `S2` head-only feasibility。
4. 对 `S1` 及通过 feasibility 的 `S2` 运行训练 fold-only 权重校准。
5. 由前置回执物化授权 runtime configs；禁止手改模板获得授权。
6. 在 tmux 中按冻结顺序训练，所有长任务、评估和 replay 使用 tqdm，保存 master log 与退出状态。
7. 仅在四折 development 上聚合并应用预注册门控，生成不可覆盖的 Round-A selection receipt。

## 6. Round-A 门控

实验候选必须同时满足：完整且有限的病例记录；灾难数不高于 `S0`；dense 2 mm zero-contact 为 0；`S2` coarse 2 mm zero-support 为 0；rim-contact HD95 P95 不高于 `S0`；final CD/HD95/NSD 分别满足 `+0.1 mm / +0.5 mm / -0.01` 非劣界；参数、时延、峰值显存比不超过 `1.02 / 1.10 / 1.10`。

所有门控在 400 个 development cases 上执行：病例必须在候选与 `S0` 间按 `case_id+fold` 一一配对；final 指标使用 400 个病例的 paired delta 均值；rim HD95 P95 使用 NumPy linear percentile；灾难与 zero-support 使用 pooled count；参数、时延和显存使用四个 fold 配对比值中的最大值。缺失、重复或 case-set 不一致均为硬失败，亚组结果和不确定性区间不参与门控。

若 `S1/S2` 均不通过，则冻结负结果并停止本路线的 loss/query 微调；不得重开候选或门控。若有候选通过，只能按已冻结规则与 `S0` 一起进入 seed-1。
