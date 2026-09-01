# Mamba v1.5 D5-A V0/V1 zero-step 完整冻结结果

> 本报告只证明实现、loss、selector 与 CUDA backward 路径可执行；不构成训练、候选比较、开发集评估或 sealed 数据访问。

## 1. 执行结论

- 状态：`D5A_V0_V1_zero_step_frozen_complete_training_still_locked`。
- GPU：`NVIDIA GeForce RTX 4090 D`。
- 四折各使用一个冻结 training probe，V0/V1 各执行一次 backward。
- metric rows：8；backward passes：8。
- optimizer constructed：`False`；optimizer steps：0；model updates：0。
- checkpoint loaded/written：`False / False`。
- dev、proposal confirmation、completion holdout、official test：均未访问。

## 2. 候选实现

- V0：冻结 D4-A 13D 描述符、`13-128-64-1` head、case-balanced BCE、top8 + conditioned FPS24。
- V1：27D 双尺度局部几何描述符、共享点编码与全局 mean/max context、`219-128-64-1` head。
- V1 loss：case-balanced BCE、positive-mass NLL、top32 margin，冻结权重均为 1。
- V1 selector：稳定 score top32；分数相同时按 candidate index。

## 3. 八条 probe 记录

| Fold | Candidate | Case | Positive | Dim | Total loss | Gradient norm | Selected positive* | Hit* |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A | V0 | `mug500plus__A0036__ellipsoid_large` | 10 | 13 | 0.693158209 | 0.00333744846 | 0 | 0 |
| A | V1 | `mug500plus__A0036__ellipsoid_large` | 10 | 27 | 8.71573639 | 0.0572858825 | 0 | 0 |
| B | V0 | `mug500plus__A0038__ellipsoid_large` | 27 | 13 | 0.693120956 | 0.00265328167 | 1 | 1 |
| B | V1 | `mug500plus__A0038__ellipsoid_large` | 27 | 27 | 7.72198772 | 0.0437684767 | 0 | 0 |
| C | V0 | `mug500plus__A0036__ellipsoid_medium` | 20 | 13 | 0.693149924 | 0.00162584044 | 0 | 0 |
| C | V1 | `mug500plus__A0036__ellipsoid_medium` | 20 | 27 | 8.02213097 | 0.0316992961 | 0 | 0 |
| D | V0 | `mug500plus__A0036__ellipsoid_small` | 15 | 13 | 0.693152368 | 0.00264813448 | 0 | 0 |
| D | V1 | `mug500plus__A0036__ellipsoid_small` | 15 | 27 | 8.30888557 | 0.0257423464 | 0 | 0 |

\* 随机初始化下的 selected-positive/hit 仅用于确认 selector 路径，不是 gate，也不得用于 V0/V1 选择。

## 4. 候选聚合（非比较性）

| Candidate | Rows | Dim | Loss min/median/max | Gradient min/median/max | Observed hits* |
| --- | ---: | ---: | --- | --- | ---: |
| V0 | 4 | 13 | 0.693120956 / 0.693151146 / 0.693158209 | 0.00162584044 / 0.00265070808 / 0.00333744846 | 1 / 4 |
| V1 | 4 | 27 | 7.72198772 / 8.16550827 / 8.71573639 | 0.0257423464 / 0.0377338864 / 0.0572858825 | 0 / 4 |

## 5. 完整性与传输修复

- 原始 overlay、13 文件内容清单及规范 LF 安装均有 SHA256 绑定。
- D4-A 父报告按预注册 lineage 精确恢复；只修复传输字节，不更改报告内容。
- candidate lock、zero-step 三件套和两份修复凭据均进入最终归档。

## 6. 可解释范围

本结果证明 V0/V1 在四个 training probe 上输出有限、梯度非零、backward 后参数哈希不变。它不证明训练收敛、out-of-fold 泛化、V1 优于 V0，也不授权 seed-1、全 development 训练、proposal confirmation 或 D5-B。

## 7. 权限边界与下一步

- `D5A_seed0_training_authorized=false`。
- `D5A_seed1_training_authorized=false`。
- `D5B_implementation_authorized=false`。
- `D5_candidate_selection_authorized=false`。
- `protected_or_sealed_data_accessed=false`。
- 下一步仅可单独预注册 D5-A seed-0 training execution authorization，并先运行不启动训练的 training preflight。
