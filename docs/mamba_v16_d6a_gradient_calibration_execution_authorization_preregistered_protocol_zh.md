# Mamba v1.6 D6-A 梯度校准执行授权

本授权只允许 R1、seed-0、A-D 四折按已冻结 schedule 执行梯度比校准。

- 每折严格使用 8 个冻结 train-only batch，每 batch 8 例。
- 三项损失在同一次 forward 的公共 `F (B,8192,64)` 上分别求原始梯度范数。
- 每折独立取 8 个范数的中位数；禁止跨折合并、裁剪、扫描、四舍五入或人工改值。
- CUDA preflight 只使用确定性人工张量，不读取 D6 病例，不产生校准权重。
- 正式校准不构造 optimizer，不更新模型，不写 checkpoint，不访问 dev 或 sealed 数据。
- 校准完成只允许生成 receipt-bound R1 runtime config；不授权 seed-0 训练。

Seed-1、proposal-confirmation25、D6-B、候选选择和所有保护数据继续锁定。
