# Mamba v1.6 D6-A full-inference efficiency implementation zero-step 完整结果

## 实验目的

本阶段验证 R0/R1 full-inference efficiency benchmark 的实现路径，包括各自冻结的最终 selector，但不执行正式效率门控、不训练模型，也不访问 D6 development、proposal-confirmation 或 sealed 数据。

## 冻结输入与实现

- Candidate/training/efficiency protocol lock manifest：`79aad71cc9da046b1e87fbe102ec0c454a0118890b3f93dd00fe2bc82c2d1285`。
- Candidate protocol lock receipt：`372fb304305e85e6cf0c63ea08b5c7f62ee2a026492daf34f6d045ee957c71bf`。
- R0 implementation：`6cca9c11f302da3ca202f3e33547c62e4584eeb0fd81f9e96c20f2787e04f070`。
- R1 implementation：`2e71ff22800a8215001de6fb8963c3016b5056763b0e905a8149180578a75d43`。
- Efficiency implementation：`7a42c8fafe09ba3a98a052dd002137b4a9ab3d71ef630585cc85a269dfd8428b`。
- Implementation tests：`d086dcdee369d0c6beb68f5244402b270baee1b2f62fbc76af9506633bf32e12`。
- Runtime：PyTorch `2.4.1+cu118`，NVIDIA GeForce RTX 4090 D。

## Artificial zero-step

- 人工 descriptor seed：`160610`。
- 输入：`1 x 8192 x 27`，float32；不含 D6 身份或几何。
- R0 full-inference：1 次，返回 32 个唯一索引，index 范围 77-8129。
- R1 full-inference：1 次，返回 32 个唯一索引，index 范围 104-8173。
- R0/R1 state hash 在执行前后分别完全一致。
- Optimizer constructed：`False`；optimizer steps/model updates：`0/0`。
- D6 cases accessed：`0`；protected/sealed access：`False`。

## 结果边界

- Zero-step manifest：`4e85572b1dd6cd044d6ce199623ab2583326a0c6916b4d3c01cdc641acb5f6b4`。
- Zero-step receipt：`60644275e58407e3b6b4e13abad2ef6c1490984ba31b782678f6963aded7408c`。
- Artificial probe：`85eebf33b7c6d26c106e421f97ab231940834c16659cdd08a7f496ad95454bc5`。
- 正式 warmup/timed runs：`0/0`。
- Latency gate 与 peak-memory gate：均未评估，不能据此声称 R1 通过效率约束。
- 当前只允许下一步单独签发 formal efficiency execution authorization。
- Seed-0 training、seed-1、proposal-confirmation、D6-B 与 candidate selection 继续锁定。

## 运输修复审计

三项修复均只处理 CRLF/LF 或导入路径，不改变算法、门控阈值或权限：

- Parent normalization receipt：`e190c96ed46073e075cf092897576a10851cfee9b6fc66e85d7c367726244576`。
- Candidate lock LF repair receipt：`4edc1161f3c8ba1e28bac764364146eec7faea13a46c4939babb65ff73cb136c`。
- Efficiency overlay normalization receipt：`3e4309a29b65a8bad287a81d702e49690e42b2691d1057ee921d37b040f57663`。

## 结论

D6-A full-inference benchmark 的 R0/R1 调用路径、最终 selector、确定性输出形状和模型只读性均已通过 artificial CUDA zero-step。该结果是实现门控的 positive result，不是效率门控或模型效果结果。正式 benchmark 必须在独立授权后按同卡 float32、batch 1、10 warmup、50 timed runs 执行，并继续使用冻结的 `latency <= 1.15x` 与 `peak memory <= 1.10x` 硬阈值。
