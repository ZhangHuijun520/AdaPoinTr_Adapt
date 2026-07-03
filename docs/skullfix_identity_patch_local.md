# SkullFix Identity Patch-Local Reconstruction 实验

## 背景

当前最佳 D 组采用：

```text
query_selection: fps_preserve
denoise_weight: 0
fine_coverage_weight: 1
```

它修复了 coarse query 的主要覆盖问题，但 fine 输出仍呈现规则条带和局部 patch
重复。简单提高全局 `GT -> Prediction` Chamfer 权重没有奏效：coverage weight
为 2/4 时，Fine CD 和 NSD 均明显恶化。

## Patch-Local 损失

AdaPoinTr 的 FC decoder 为每个 coarse query 生成 16 个 fine 子点。对每个
query：

1. 在 GT 中查找距离 coarse query 最近的 16 个点；
2. 将对应的 16 个预测子点与该 GT 局部邻域计算双向 L1 Chamfer；
3. 对 batch、query 和 patch 点求平均。

最终 fine loss 为：

```text
L_fine =
    (L_global + lambda_local * L_patch_local)
    / (1 + lambda_local)
```

归一化分母用于保持不同权重下的 loss 尺度可比。`lambda_local=0` 与 D 组原始
行为完全一致。

## 对照组

| 组别 | Patch-local weight | 说明 |
|---|---:|---|
| D | 0.0 | 已完成的当前最佳组 |
| G | 0.5 | 中等局部监督 |
| H | 1.0 | global/local 等权 |

除该权重外，数据、模型、优化器、训练轮数、随机种子、query、denoise 和
directional Chamfer 设置完全一致。

## 运行

```bash
cd ~/adapointr_work/PoinTr
conda activate adapointr-server
chmod +x scripts/run_skullfix_identity_patch_local.sh
chmod +x scripts/run_skullfix_adapointr_identity_overfit.sh

tmux new -s skullfix_patch_local
bash scripts/run_skullfix_identity_patch_local.sh
```

脚本首先运行合成测试，验证：

- 完全匹配的局部 patch loss 为 0；
- 整体平移 0.25 的 patch loss 为 0.25；
- 反向梯度有限；
- global/local 组合公式正确。

测试通过后复用 D，只训练 G/H；各组支持 `ckpt-last.pth` 自动续训。

## 输出与判读

```text
logs/skullfix/identity_patch_local/
  identity_patch_local_<timestamp>.log
  identity_patch_local_summary.json
  identity_patch_local_summary.csv
```

优先比较 Fine CD、HD95、NSD@1 mm 和 `GT -> Prediction`。如果 G/H 改善，
还需要生成共享坐标范围的可视化，检查规则条带是否减少。

如果 local loss 明显降低局部误差却未改善全局覆盖，说明 coarse query 邻域仍有
重叠，下一步再加入 query/patch uniformity 或 repulsion 约束。如果 G/H
整体恶化，则保留 D，并转向修改 FC patch decoder 的输出参数化。

## 2026-06-29 实验结果

| 组别 | Local weight | Fine CD (mm) | Fine HD95 (mm) | Fine NSD@1 mm | Pred -> GT (mm) | GT -> Pred (mm) |
|---|---:|---:|---:|---:|---:|---:|
| D | 0.0 | 3.3744 | 7.0618 | 0.1182 | 2.6795 | 4.0693 |
| G | 0.5 | 3.8675 | 8.0073 | 0.0303 | 2.9306 | 4.8044 |
| H | 1.0 | 3.5184 | 7.5201 | 0.1017 | 2.4729 | 4.5639 |

相对 D：

- G 的 Fine CD 恶化约 14.6%，HD95 恶化约 13.4%，NSD@1 mm 下降约 74.4%；
- H 的 `Pred -> GT` 改善约 7.7%，但 `GT -> Pred` 恶化约 12.2%；
- H 的 Fine CD 与 HD95 分别恶化约 4.3% 和 6.5%。

因此拒绝当前 patch-local KNN 监督方案，D 仍是最佳组。结果表明局部监督能让
子点更贴近各自 coarse query 的邻域，但不同 query 的 GT KNN 邻域存在重叠，
导致多个 patch 重复覆盖局部区域并进一步损害全局覆盖。

至此，简单方向重加权与局部 KNN 重加权都未解决问题。下一步不继续叠加 loss，
而是先用自由点参数 oracle 和学习率对照验证损失本身是否可优化，以及当前失败
是否主要来自 AdaPoinTr 的优化设置或 FC patch 参数化。
