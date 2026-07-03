# SkullFix Identity Fine Directional Chamfer 实验

## 动机

`fps_preserve + no denoise` 的 D 组已明显改善 coarse 覆盖，但 identity overfit
的 fine 输出仍表现为：

```text
CD-L1:       3.37 mm
HD95:        7.06 mm
NSD@1 mm:    0.118
Pred -> GT:  2.68 mm
GT -> Pred:  4.07 mm
```

可视化显示预测保留了低频颅骨轮廓，但丢失大量外壳覆盖，并呈现规则 patch
排列。train/eval 四模式下 `GT -> Prediction` 几乎不变，说明 BN 和推理分支
不是主因。

注意，旧版单图可视化会为每个点云独立设置坐标范围，因此不能仅凭 PNG 中的
显示尺寸判断物理收缩；覆盖结论以 mm 指标为准。

## 损失定义

只修改 fine reconstruction loss：

```text
L_fine(lambda) =
    (mean distance(Prediction -> GT)
     + lambda * mean distance(GT -> Prediction))
    / (1 + lambda)
```

分母保持不同 lambda 下的损失尺度可比。coarse loss、query 选择、denoise
设置、模型结构、数据、随机种子和训练轮数全部保持不变。

| 组别 | Query | Denoise | Fine coverage weight |
|---|---|---:|---:|
| D | `fps_preserve` | 0.0 | 1 |
| E | `fps_preserve` | 0.0 | 2 |
| F | `fps_preserve` | 0.0 | 4 |

lambda=1 与原始 `ChamferDistanceL1` 数值等价。

## 运行

```bash
cd ~/adapointr_work/PoinTr
conda activate adapointr-server
chmod +x scripts/run_skullfix_identity_directional.sh
chmod +x scripts/run_skullfix_adapointr_identity_overfit.sh

tmux new -s skullfix_directional
bash scripts/run_skullfix_identity_directional.sh
```

脚本首先运行解析值、兼容性和梯度测试。测试通过后复用已有 D checkpoint，只
训练 E/F，并支持从各自的 `ckpt-last.pth` 自动恢复。

## 输出

```text
logs/skullfix/identity_directional/
  identity_directional_<timestamp>.log
  identity_directional_summary.json
  identity_directional_summary.csv
```

重点比较：

- `fine_ref_to_pred_mm` 是否随 lambda 增大而下降；
- HD95 是否下降；
- NSD@1 mm 是否提高；
- `fine_pred_to_ref_mm` 是否因过度追求覆盖而明显恶化；
- 对称 Fine CD 是否取得净改善。

如果 E 优于 D 而 F 变差，后续优先采用 lambda=2。如果 E/F 都不能明显改善，
则缺失覆盖不能只靠方向重加权解决，下一步检查 patch 重复与 uniformity/
repulsion 约束。

## 2026-06-29 实验结果

| 组别 | Coverage weight | Fine CD (mm) | Fine HD95 (mm) | Fine NSD@1 mm | Pred -> GT (mm) | GT -> Pred (mm) |
|---|---:|---:|---:|---:|---:|---:|
| D | 1 | 3.3744 | 7.0618 | 0.1182 | 2.6795 | 4.0693 |
| E | 2 | 3.6711 | 7.0251 | 0.0288 | 3.2780 | 4.0643 |
| F | 4 | 3.5766 | 7.1253 | 0.0331 | 3.2457 | 3.9074 |

相对 D：

- E 的 `GT -> Pred` 仅改善约 0.1%，但 `Pred -> GT` 恶化约 22.3%；
- F 的 `GT -> Pred` 改善约 4.0%，但 `Pred -> GT` 恶化约 21.1%；
- E/F 的对称 Fine CD 分别恶化约 8.8% 和 6.0%；
- E/F 的 NSD@1 mm 分别下降约 75.6% 和 72.0%。

因此拒绝“仅提高全局 Chamfer 覆盖方向权重”的方案，D 仍是当前最佳组。全局
最近邻损失允许不同 coarse query 生成的 patch 竞争同一批 GT 邻域，简单提高
`GT -> Prediction` 权重只会把更多预测点拉离局部表面，不能解决 patch 的
结构化重复和局部对应退化。

下一步优先测试 patch-local reconstruction loss：按照每个 coarse query 的
GT KNN 邻域，分别监督其 16 个 fine 子点。该实验保持 D 的 query、denoise 和
全局 Chamfer 设置不变，只增加局部 patch 对应约束。
