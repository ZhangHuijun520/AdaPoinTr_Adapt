# Mamba v1.2 D2.1 Coarse Geometry Guard 预注册实验协议

> 状态：在任何 D2.1 候选训练前冻结。D2 Round A 已因硬门槛失败而终止；本协议是独立修订，不恢复原 Round B。

## 1. 触发原因

D2 Round A 的 C0-C3 均通过 Final non-inferiority 与效率门槛，但均未通过预注册的灾难门槛：

| Candidate | 灾难数 / 420 | 灾难率 | 非有限 Rim 病例 |
|---|---:|---:|---:|
| C0 | 29 / 420 | 6.90% | 1 |
| C1 | 40 / 420 | 9.52% | 1 |
| C2 | 37 / 420 | 8.81% | 2 |
| C3 | 43 / 420 | 10.24% | 2 |

因此，按原协议不得启动 Round B。随后开展的 instrumentation 与 GT-aware replay 均明确标记为 post-hoc、observation-only 和 selection-inert，没有使用 locked confirmation、旧 monitor 或 official test。

## 2. GT-aware replay 的定位结论

四个机制的灾难病例在 coarse 阶段已经出现一致的几何异常：

1. GT 到 coarse 的 P95 距离显著增大，SMD 为 `1.2782-1.5409`；
2. coarse centroid offset 显著增大，SMD 为 `0.8816-1.1814`；
3. coarse radial RMS ratio 从对照的约 `0.89-0.92` 降至约 `0.74-0.79`；
4. coarse GT coverage@5mm 从约 `0.55-0.56` 降至约 `0.21-0.29`；
5. coarse GT-rim 到预测的 P95 距离显著增大，SMD 为 `1.3697-1.6748`。

Final 阶段仍保留相同方向的异常。灾难病例从 coarse 到 final 的 GT-to-stage P95 改善量反而更大，说明 decoder/rebuild 在补偿 coarse 错误，但无法完全恢复。因此当前证据支持：

```text
主要异常在 query-position / coarse geometry 阶段已经形成
→ decoder/rebuild 提供部分补偿
→ 最终仍表现为 implant/rim 欠覆盖和长尾失败
```

该结果不证明某个 Mamba 内部变量具有因果作用，只用于提出新的、预注册的 coarse geometry guard 候选。

## 3. 数据与信息边界

- 复用 D2 的 `development84` 与 A-D 四个 skull-level folds；
- 复用属于迭代开发，不把这些 folds 重新描述为独立验证集；
- `locked confirmation20` 继续不可访问；
- 旧 50-case monitor 不可访问；
- SkullBreak official test 不可访问；
- D2.1 结果不得恢复或改变原 D2 Round B；
- GT implant 只可作为训练监督，推理输入仍只有 defective partial skull。

## 4. 固定候选

所有候选使用同一个冻结基础：O0、单向 `xyz`、adapter depth 2、`alpha_init=0.01`、20 epoch alpha warmup、8192 输入与 8192 输出。

为避免候选因总正则强度不同而混杂，Q1-Q3 的辅助损失总权重统一为 `0.01`。几何距离均除以每个样本 GT implant 的 radial RMS，使损失无量纲。

### Q0：无 geometry guard

```text
L = L_coarse_chamfer + L_fine
```

Q0 是 D2.1 的同轮基线。新配置字段关闭时不计算任何附加几何量。

### Q1：归一化 centroid guard

```text
d_c = ||centroid(pred_coarse) - centroid(GT)|| / radial_rms(GT)
L_geo = SmoothL1(d_c, 0; beta=0.1)
L = L_base + 0.01 * L_geo
```

Q1 只检验全局平移/偏心约束。

### Q2：centroid + log-radius guard

```text
d_r = log(radial_rms(pred_coarse) / radial_rms(GT))
L_geo = 0.5 * [SmoothL1(d_c, 0; beta=0.1)
               + SmoothL1(d_r, 0; beta=0.1)]
L = L_base + 0.01 * L_geo
```

Q2 同时检验偏心与整体尺度收缩，但辅助损失总权重仍为 `0.01`。

### Q3：robust coarse coverage CVaR

对每个 GT 点计算到 coarse 点集的最近距离，除以 GT radial RMS，取最差 10% 的均值：

```text
d_i = min_j ||GT_i - coarse_j|| / radial_rms(GT)
L_geo = mean(top_10_percent(d_i))
L = L_base + 0.01 * L_geo
```

Q3 直接针对 GT 欠覆盖和尾部距离，不加入 centroid/radius 项。

## 5. Round A

运行：

```text
Q0-Q3 x folds A-D x seed 0 = 16 trainings
```

每次固定执行 epoch-100 checkpoint、fold-train BNCal、fold-dev 点云指标、零扰动 instrumentation 和同 GPU 效率评估。所有 16 个候选完成前不运行选择器。

硬门槛保持：

1. 非有限核心指标病例数必须为 0；
2. 灾难率不得高于同轮 Q0；
3. 相对 Q0，Final CD 增量不超过 `0.10 mm`；
4. 相对 Q0，Final HD95 增量不超过 `0.50 mm`；
5. 相对 Q0，Final NSD@1 增量不低于 `-0.01`；
6. 推理延迟不超过 Q0 的 `1.75x`；
7. 峰值显存不超过 Q0 的 `1.25x`；
8. 训练 epoch 时间不超过 Q0 的 `1.75x`。

通过硬门槛后，按以下字典序升序选择前二：灾难率、Rim HD95 P95、Rim HD95 maximum、Implant HD95 mean、Rim CD mean、负 Rim NSD@1 mean。

若少于两个候选通过所有门槛，D2.1 Round B 自动禁止，必须形成新的失败审计，不得临时放宽阈值。

## 6. 执行入口

```bash
TMUX_SESSION=mamba-v12-d21-geometry-round-a \
bash scripts/launch_skullbreak_mamba_v12_d21_round_a_tmux.sh
```

训练和评估沿用现有 `tqdm` 进度显示；tmux master log 位于：

```text
logs/skullbreak_mamba_v12_d21_geometry/tmux_*.log
```

## 7. 解释边界

- D2.1 是 post-hoc 假设驱动的新开发阶段，不是对原 D2 的事后重评分；
- Q1-Q3 若改善，只能说明对应训练约束在 development84 上具有重复性收益；
- locked confirmation20 只有 winner 和后续多 seed 规则全部冻结后才可一次性使用；
- confirmation 或未来 official test 的结果均不得返回修改 Q 候选、损失权重或阈值。
