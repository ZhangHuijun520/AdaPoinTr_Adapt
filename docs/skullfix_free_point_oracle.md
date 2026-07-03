# SkullFix Free-Point Oracle

## 目的

该实验用于区分两类原因：

1. 当前双向 Chamfer 与最近邻优化本身无法从 D 组预测恢复 GT；
2. Chamfer 可以恢复，但 AdaPoinTr 的优化设置或 FC patch decoder 限制了拟合。

实验首先加载 D 组 checkpoint，生成一个 `(8192, 3)` 的预测点云。随后删除模型，
把预测点坐标本身设为唯一可学习参数，并直接用官方 `ChamferDistanceL1`
优化到同一个 identity GT。

## 默认设置

```text
initialization: D group prediction
optimizer: Adam
steps: 2000
initial lr: 0.001
scheduler: cosine
minimum lr: 0.00001
metric interval: 50 steps
```

保存初始、最佳和最终点云，以及每个记录点的 CD、HD95、NSD 和双向平均距离。
oracle 使用平方距离下限 `1e-12` 的稳定 L1 Chamfer。该下限对应约
`1e-6` 个归一化距离单位，只用于避免精确重合点处 `sqrt(0)` 的非有限梯度，
不会改变 mm 级结论。

## 运行

```bash
cd ~/adapointr_work/PoinTr
conda activate adapointr-server
chmod +x scripts/run_skullfix_free_point_oracle.sh

tmux new -s skullfix_free_oracle
bash scripts/run_skullfix_free_point_oracle.sh
```

## 输出

```text
logs/skullfix/free_point_oracle/
  oracle_<timestamp>.log
  oracle_<timestamp>/
    initial_prediction.npy
    ground_truth.npy
    best_free_points.npy
    current_free_points.npy
    final_free_points.npy
    progress.csv
    summary.json
```

## 判读

- 最佳 CD `< 0.5 mm`：Chamfer 和最近邻优化能够恢复 GT，后续进行 D 组学习率
  对照或修改 FC patch decoder；
- 最佳 CD 仍为数毫米：当前全局 Chamfer 的匹配盆地是主要问题；
- CD 降低但 HD95/NSD 改善有限：平均误差可优化，但仍需覆盖或分布约束。

该 oracle 不是论文方法，也不参与正式结果，只用于排除损失和优化链路问题。

每次记录指标时会同步保存 `current_free_points.npy`、最佳点云和 CSV。如果新版本
运行意外中断，可这样继续：

```bash
INIT_POINTS=/path/to/current_free_points.npy \
STEPS=1000 \
bash scripts/run_skullfix_free_point_oracle.sh
```

## 2026-06-29 实验结果

```text
Initial CD:        3.374400 mm
Best/final CD:     1.013344 mm
Final HD95:        4.793316 mm
Final NSD@1 mm:    0.699524
Final Pred -> GT:  0.055584 mm
Final GT -> Pred:  1.971104 mm
Pass CD < 0.5 mm:  false
```

自由点使 CD 降低约 70%，但没有通过 `< 0.5 mm` gate。约 step 1100 后，
`GT -> Prediction` 始终停留在约 `1.97 mm`，而 `Prediction -> GT` 继续下降
到 `0.056 mm`。这说明预测点几乎全部贴到某些 GT 表面位置，但没有重新分配到
未覆盖区域。

因此，当前主要问题是全局最近邻 Chamfer 的 many-to-one 坏匹配盆地，而不是
AdaPoinTr 的普通学习率、BN 或梯度链路。继续对 D 做常规学习率 sweep 不足以
解决覆盖。后续应采用输入表面保留机制，并把学习目标转向缺损/implant 区域；
如仍需全点云生成，应引入具有分布或近似一一对应约束的损失。
