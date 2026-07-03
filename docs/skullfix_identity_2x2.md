# SkullFix AdaPoinTr Identity 2x2 诊断实验

## 目的

该实验只使用同一个 SkullFix 训练病例，并令输入与目标都为完整颅骨
（`gt -> gt`）。它不是正式 baseline，而是定位 AdaPoinTr 无法完成单样本
identity overfit 的原因。

固定条件如下：

- 同一病例、同一点云与同一归一化；
- batch size 8，实际为同一病例重复 8 次；
- 500 个 epoch，每个 epoch 1 个 optimizer step；
- AdamW，学习率 `5e-5`，无 weight decay；
- 同一模型规模、随机种子、验证频率和 checkpoint 选择规则；
- 使用 `ckpt-best.pth` 和同一 mm evaluator 比较。

## 2x2 因子

| 组别 | Query 选择 | Denoise 权重 | 作用 |
|---|---|---:|---|
| A | `ranking` | 0.5 | 已完成的官方行为对照 |
| B | `ranking` | 0.0 | 单独检查 denoise 梯度冲突 |
| C | `fps_preserve` | 0.5 | 单独检查 query 覆盖 |
| D | `fps_preserve` | 0.0 | 检查两项修改的组合效果 |

`ranking` 保留官方行为：将 512 个学习型 coarse 点与 256 个输入 FPS 点合并，
再由 `query_ranking + argsort` 选择 512 点。

`fps_preserve` 不改变 query 总数，但强制保留全部 256 个输入 FPS 锚点，并使用
前 256 个学习型 coarse 点补足 512 点。这样可以检查全局 coarse 覆盖是否是
主要瓶颈。

`denoise_weight=0.0` 仅令 denoise loss 不贡献梯度；训练分支仍生成 denoise
token，因此这个对照主要隔离损失冲突，不同时改变前向结构。

## 运行

上传并解压 overlay 后：

```bash
cd ~/adapointr_work/PoinTr
conda activate adapointr-server
chmod +x scripts/run_skullfix_identity_2x2.sh
chmod +x scripts/run_skullfix_adapointr_identity_overfit.sh

tmux new -s skullfix_identity_2x2
bash scripts/run_skullfix_identity_2x2.sh
```

分离 tmux：

```text
Ctrl+b，松开，再按 d
```

重新进入：

```bash
tmux attach -t skullfix_identity_2x2
```

脚本复用 A 组已有权重，只训练 B、C、D。每组若发现自己的
`ckpt-last.pth`，会自动断点续训。

## 输出

训练目录：

```text
experiments/AdaPoinTr_identity_B_nodenoise/...
experiments/AdaPoinTr_identity_C_fpspreserve_denoise/...
experiments/AdaPoinTr_identity_D_fpspreserve_nodenoise/...
```

日志与自动汇总：

```text
logs/skullfix/identity_2x2/
  identity_2x2_<timestamp>.log
  identity_2x2_summary.json
  identity_2x2_summary.csv
```

汇总表同时报告 coarse 与 fine 的：

- CD-L1，单位 mm；
- HD95，单位 mm；
- NSD@1 mm；
- prediction-to-reference 平均距离；
- reference-to-prediction 平均距离。

重点观察 `coarse_ref_to_pred_mm` 和 `fine_ref_to_pred_mm`。二者直接反映真实
颅骨表面是否仍存在大面积未覆盖。

## 判读

- B 明显优于 A：denoise 梯度冲突是重要原因；
- C 明显优于 A：不可学习 ranking 导致的 coarse 覆盖是重要原因；
- D 明显优于 B/C：两个问题存在叠加；
- B/C/D 都无法接近零误差：继续检查 Chamfer 的覆盖约束、输出参数化与优化设置，
  暂不进入正式 SkullFix baseline。

## 2026-06-29 实验结果

| 组别 | Coarse CD (mm) | Coarse HD95 (mm) | Fine CD (mm) | Fine HD95 (mm) | Fine NSD@1 mm |
|---|---:|---:|---:|---:|---:|
| A | 8.4749 | 50.8775 | 5.0286 | 11.7503 | 0.0325 |
| B | 8.4949 | 50.8775 | 5.0623 | 11.2077 | 0.0153 |
| C | 4.5792 | 14.0579 | 3.3855 | 7.5623 | 0.1008 |
| D | 4.5827 | 14.0579 | 3.3744 | 7.0618 | 0.1182 |

相对 A 组：

- B 组 Fine CD 反而增加约 0.7%，NSD@1 mm 降至 A 的约 47%；
- C 组 Coarse CD 降低约 46.0%，Coarse HD95 降低约 72.4%；
- C 组 Fine CD 降低约 32.7%，Fine HD95 降低约 35.6%；
- D 组 Fine CD 降低约 32.9%，Fine HD95 降低约 39.9%，NSD@1 mm
  提升到 A 的约 3.64 倍。

因此，不可微的 `query_ranking + argsort` 所造成的全局覆盖不足是当前主要问题。
关闭 denoise loss 不是独立有效的修复：在 ranking 模式下没有改善；在
`fps_preserve` 模式下，它主要改善 HD95、NSD 和 reference-to-prediction
覆盖，但同时增大 prediction-to-reference 距离，表现为精度与覆盖之间的权衡。

D 是当前综合指标最好的诊断组，但仍远未达到 identity overfit 应有的近零误差，
所以 `fps_preserve` 是必要修复而非充分修复。正式 SkullFix baseline 应等待
D 组的收敛趋势、train/eval 差距和可视化得到进一步确认。
