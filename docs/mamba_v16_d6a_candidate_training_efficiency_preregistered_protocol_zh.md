# Mamba v1.6 D6-A 候选训练与效率门控预注册协议

本协议冻结 R0/R1 的训练预算和训练前效率门控，但不签发效率执行或训练权限。

## 候选与执行顺序

- R0：冻结 D5 V1 reference 在 D6 上的 seed-0 重训，仅作对照，不具备晋级资格。
- R1：唯一的 assignment-consistent slot32 实验候选。
- 先用无 D6 身份的确定性人工 `8192 x 27` 描述符完成 full-inference 效率实现与 zero-step。
- 再单独签发效率执行授权；延迟或显存任一失败，立即冻结 negative，并在训练前停止。
- 只有冻结效率结果同时通过两项门控，才允许另行签发 seed-0 训练授权。

## 效率硬门控

- 同一 GPU、同一软件环境、float32、batch size 1。
- warmup 10 次，计时 50 次；每次计时前后 CUDA synchronize。
- 统计 median latency；每个候选前重置 peak CUDA memory。
- `R1/R0 latency <= 1.15`，`R1/R0 peak memory <= 1.10`。
- 测试包含最终 selector；不得读取 development、confirmation 或 sealed 病例。

## Seed-0 训练预算

- 固定顺序：R0 A-D，然后 R1 A-D，共 8 个 run。
- 每 run 50 epoch、batch size 8、300 train cases、1900 optimizer steps。
- AdamW，lr `1e-3`，weight decay `1e-4`；CosineAnnealingLR，T_max 50，eta_min `1e-5`。
- gradient clip norm 1.0；无 early stopping；仅保存 final epoch checkpoint。
- dev 仅可在完整 1900 steps 后一次性打开，训练过程中 dev access 为 0。

## 损失边界

- R0 沿用冻结 D5 V1 等权损失，不重新校准。
- R1 必须使用同折校准权重，禁止四折均值。
- 由于 `lambda_shape` 约为 4022-4579，R1 scalar total loss 不得用于 early stopping、LR 调度、checkpoint 选择或候选比较。
- 必须分别记录 raw/weighted 三个分量；任一分量或梯度非有限即 hard failure。

## 当前权限

- 仅授权下一步实现效率 benchmark 与 artificial zero-step。
- 效率正式执行、训练、seed-1、proposal-confirmation、D6-B、selection 与 sealed access 均未授权。
