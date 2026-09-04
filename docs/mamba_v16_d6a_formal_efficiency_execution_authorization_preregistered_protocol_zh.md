# Mamba v1.6 D6-A formal efficiency 执行授权预注册

## 授权范围

本授权只允许在同一 CUDA 设备、同一进程内，对冻结的 R0 与 R1 依次执行一次正式 full-inference efficiency benchmark。输入为 seed `160610` 生成的 `1 x 8192 x 27` 人工 float32 descriptor，不含任何 D6 病例身份或几何。

## 公平性约束

- 固定顺序为 R0 后 R1。
- 全局随机种子只设置一次；依次构造 R0、R1，以复现 zero-step 冻结状态。
- 每次只保留一个候选模型，前一候选删除并清理 CUDA cache 后才构造后一候选。
- 每候选严格执行 10 次 warmup 与 50 次 timed full inference，包含冻结 final selector。
- 每个 timed run 前后 CUDA synchronize；使用 median latency。
- 每候选 timed block 前重置 peak-memory statistics；记录 `torch.cuda.max_memory_allocated`。

## 硬门控

- R1/R0 median latency 不得超过 `1.15`。
- R1/R0 peak CUDA memory 不得超过 `1.10`。
- 两项同时通过时，只允许后续单独签发 seed-0 training authorization。
- 任一失败时冻结 efficiency negative result，并停止 D6-A 训练路线。

## 权限边界

授权与 preflight 不执行正式 10/50 benchmark，不构造 optimizer，不更新模型，不访问 development、proposal-confirmation 或 sealed 数据。Seed-0 training、seed-1、D6-B、confirmation 与 candidate selection 均继续锁定。
