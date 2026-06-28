# ShapeNet34 AdaPoinTr 官方配置完整训练复现实验记录

本文档整理截至 2026-06-23 为止，为完成 AdaPoinTr 在 ShapeNet34 上的官方配置完整训练、评估和问题排查所做的主要工作。目标是留下一个可迁移、可复查、可继续扩展到后续 Mamba 改进实验的实验记录。

## 1. 实验目标

本阶段目标不是提出新方法，而是先把 AdaPoinTr 官方 baseline 跑通并复现到可信状态，为后续“基于 Mamba 的点云补全 + 颅骨/骨缺损修复”方向建立稳定底座。

具体目标如下：

- 跑通官方 PoinTr/AdaPoinTr 代码；
- 在服务器上完成 CUDA 扩展和真实数据集环境配置；
- 在 ShapeNet34 上使用 AdaPoinTr 官方模型配置完成 full training；
- 完成 ShapeNet34 seen 和 unseen 的 easy / median / hard 全部评估；
- 保存 checkpoint、日志、指标和可视化结果；
- 将复现实验结果与 AdaPoinTr 原论文 Table II 进行对照；
- 排查 F-Score 和 EMD 等异常指标。

## 2. 实验环境

服务器平台为学校自强5000容器环境。最初选择了 CUDA 11.8 相关镜像，并在容器中创建 `adapointr-server` 环境。

主要环境信息：

```text
GPU: NVIDIA GeForce RTX 4090 D
GPU memory: about 24 GB per card
Python: 3.9.23
PyTorch: 2.1.2+cu118
CUDA used by PyTorch: 11.8
nvcc: CUDA 11.8
Conda env: adapointr-server
```

正式 full training 使用 4 张 4090D：

```text
official total_bs: 48
4 GPU per-GPU batch size: 12
max_epoch: 600
```

容器最初不能加载 Open3D，原因是缺少系统动态库：

```text
libX11.so.6
libGL.so.1
```

容器没有 `sudo`，因此后来通过 conda-forge 在用户态补齐：

```bash
conda install -c conda-forge -y xorg-libx11
conda install -c conda-forge -y libgl
```

补齐后 Open3D 可正常导入：

```text
open3d ok 0.19.0
```

## 3. 代码与环境准备

### 3.1 官方代码与本地 toy 流程

首先克隆并整理官方 PoinTr/AdaPoinTr 代码。由于本机配置较低，先在本地接入了一个极小的 ToyPCN 数据集，用于验证前向传播、反向传播和官方 `main.py` 训练入口。

已完成内容包括：

- 添加 ToyPCN dataset；
- 添加 ToyPCN 配置；
- 支持本机 CPU / fallback smoke test；
- 编写本地 smoke test 文档；
- 保存“已跑通”状态，便于后续改坏模型时回退。

相关文件示例：

```text
datasets/ToyPCNDataset.py
cfgs/dataset_configs/ToyPCN.yaml
cfgs/ToyPCN_models/AdaPoinTr.yaml
tools/toy_smoke_adapointr.py
docs/local_smoke_test.md
```

### 3.2 服务器环境脚本

为了在服务器上避免使用本机 fallback，而是安装官方 CUDA 扩展，整理了服务器版环境说明和脚本。

涉及扩展包括：

```text
extensions/chamfer_dist
extensions/emd
pointnet2_ops
```

服务器环境准备中遇到并解决的问题：

- `conda env create` 求解环境时被 killed，后来改为更轻量方式创建环境；
- `pkg_resources` 缺失导致 CUDA extension build 失败，通过调整 setuptools 相关依赖解决；
- `pointnet2_ops_lib.zip` 在 Linux 解压时出现反斜杠路径问题，手动修复目录结构后安装；
- Open3D 因 `libX11` / `libGL` 缺失无法 import，后续通过 conda-forge 补库解决。

相关文件：

```text
environment_server.yml
scripts/setup_server_env.sh
docs/server_setup.md
```

## 4. ShapeNet34 数据准备

本阶段决定跑原论文使用过的物体级 ShapeNet-34 / ShapeNet-Unseen21 协议。

数据来源是官方 ShapeNet55 数据包。虽然文件名是 ShapeNet55，但其中同时包含 ShapeNet-55 和 ShapeNet-34 所需数据与 split。为了和官方代码配置一致，服务器上统一组织为：

```text
~/datasets/ShapeNet55-34/
~/adapointr_work/PoinTr/data/ShapeNet55-34/
```

关键数据结构：

```text
data/ShapeNet55-34/ShapeNet-34/train.txt
data/ShapeNet55-34/ShapeNet-34/test.txt
data/ShapeNet55-34/ShapeNet-Unseen21/test.txt
data/ShapeNet55-34/shapenet_pc/*.npy
```

已核验数据量：

```text
ShapeNet-34 train: 46765
ShapeNet-34 seen test: 3400
ShapeNet-Unseen21 test: 2305
shapenet_pc npy files: 52470
```

样本点云格式：

```text
shape: (8192, 3)
dtype before loading: float64
dataset loader converts to float32 and normalizes
```

为了节省仓库空间，真实数据放在 `~/datasets` 下，通过链接接入仓库。

## 5. 训练前 sanity 与短 baseline

### 5.1 ShapeNet34 1 epoch sanity

在正式训练前，先准备并运行了 ShapeNet34 AdaPoinTr 1GPU / 1epoch sanity 配置。

目的：

- 验证 ShapeNet34 数据可读；
- 验证官方模型可 forward/backward；
- 验证 checkpoint 保存；
- 验证 evaluation 入口；
- 检查 CUDA 扩展是否正常工作。

sanity 训练完成后，说明真实数据流水线已经跑通。

### 5.2 batch size profiling

为了估算训练时间，编写并运行了 batch size profiler。4090D 单卡结果如下：

```text
bs=2:  mean_batch_time_sec 1.3353, estimated_epoch_hours_no_validation 8.67, peak_cuda_memory_gb 1.36
bs=4:  mean_batch_time_sec 1.2789, estimated_epoch_hours_no_validation 4.15, peak_cuda_memory_gb 1.97
bs=8:  mean_batch_time_sec 1.4404, estimated_epoch_hours_no_validation 2.34, peak_cuda_memory_gb 3.40
bs=16: mean_batch_time_sec 1.4562, estimated_epoch_hours_no_validation 1.18, peak_cuda_memory_gb 6.24
bs=24: mean_batch_time_sec 1.4949, estimated_epoch_hours_no_validation 0.81, peak_cuda_memory_gb 9.09
bs=32: mean_batch_time_sec 1.6599, estimated_epoch_hours_no_validation 0.67, peak_cuda_memory_gb 11.94
bs=48: mean_batch_time_sec 1.6803, estimated_epoch_hours_no_validation 0.45, peak_cuda_memory_gb 17.67
bs=64: OOM
```

结论：

- 单卡 `bs=48` 可以跑，但显存占用已经较高；
- `bs=64` 会 OOM；
- 官方 total batch size 是 48，若用 4GPU，则每卡 batch size 为 12，更稳也更符合官方设置。

### 5.3 5 epoch short baseline

正式 600 epoch 前，先跑了 5 epoch 短 baseline。最终使用单卡 `bs=48`，训练完成并完成 seen/unseen evaluation。

短 baseline 训练趋势：

| epoch | F-Score | CDL1 | CDL2 |
|---:|---:|---:|---:|
| 0 | 0.228 | 28.966 | 4.018 |
| 1 | 0.246 | 24.586 | 2.733 |
| 2 | 0.274 | 21.468 | 2.044 |
| 3 | 0.293 | 19.821 | 1.701 |
| 4 | 0.307 | 19.005 | 1.587 |

这说明训练曲线正常下降，评估脚本、checkpoint、日志和可视化流程都可以继续使用。

短 baseline 完整评估结果：

| split | mode | F-Score | CDL1 | CDL2 |
|---|---|---:|---:|---:|
| seen | easy | 0.3125 | 17.5820 | 1.1852 |
| seen | median | 0.3106 | 18.7502 | 1.5328 |
| seen | hard | 0.2888 | 22.7337 | 2.6457 |
| unseen | easy | 0.2806 | 19.4866 | 1.6338 |
| unseen | median | 0.2771 | 21.6098 | 2.3913 |
| unseen | hard | 0.2524 | 28.0931 | 4.5936 |

短 baseline 还完成了可视化样例：

```text
experiments/visualizations/shapenet34_5epoch_bs48/
```

其中：

```text
input_partial.png: 输入残缺点云
pred.png: 模型预测补全点云
gt.png: 完整 ground truth 点云
```

## 6. 官方配置 4GPU full training

### 6.1 代码修改与脚本

为了使用 4GPU DDP 跑官方配置，做了以下工程准备：

- `utils/parser.py` 支持 `--local_rank` 和 `--local-rank`，并读取 `LOCAL_RANK`；
- `utils/dist_utils.py` 按 `LOCAL_RANK` 设置 CUDA device；
- `tools/runner.py` 加入 rank0 的 `tqdm` 进度条；
- 编写官方 4GPU 训练脚本；
- 编写官方 seen/unseen evaluation 脚本；
- 编写官方可视化脚本；
- 增加自动 resume 逻辑，避免训练中断后白跑。

相关文件：

```text
scripts/run_shapenet34_adapointr_official_4gpu.sh
scripts/eval_shapenet34_official_seen_unseen.sh
scripts/visualize_shapenet34_official.sh
docs/shapenet34_official_4gpu.md
```

官方配置：

```text
cfgs/ShapeNet34_models/AdaPoinTr.yaml
total_bs : 48
max_epoch : 600
consider_metric: CDL2
```

4GPU 设置：

```text
total_bs = 48
world_size = 4
per-GPU bs = 12
```

### 6.2 运行方式

训练在 `tmux` 中运行：

```bash
tmux new -s shapenet34_official_4gpu
cd ~/adapointr_work/PoinTr
bash scripts/run_shapenet34_adapointr_official_4gpu.sh
```

detach：

```text
Ctrl+b then d
```

训练日志与 checkpoint 路径：

```text
logs/shapenet34_official_4gpu/
experiments/AdaPoinTr/ShapeNet34_models/shapenet34_adapointr_official_full_4gpu/
```

训练脚本支持从以下 checkpoint 自动恢复：

```text
experiments/AdaPoinTr/ShapeNet34_models/shapenet34_adapointr_official_full_4gpu/ckpt-last.pth
```

### 6.3 训练完成状态

训练完成于 epoch 600，并保存：

```text
ckpt-best.pth
ckpt-last.pth
ckpt-epoch-600.pth
```

日志显示 `ckpt-best.pth` 来自 epoch 560：

```text
ckpts @ 560 epoch( performance = {'F-Score': 0.41636083172250254,
                                  'CDL1': 12.177465782258123,
                                  'CDL2': 0.6750047724217534,
                                  'EMDistance': 0.0})
```

epoch 600 附近 validation：

```text
Overall F-Score 0.412
Overall CDL1 12.281
Overall CDL2 0.687
EMDistance 0.000
```

后续检查 0-600 epoch 的 validation 日志，共 61 条记录，发现：

```text
epoch=560 F=0.4164 CDL2=0.6750 CDL1=12.1775
```

该 epoch 同时是：

- F-Score 最高 epoch；
- CD-L2 最低 epoch；
- `ckpt-best.pth` 对应 epoch。

因此可以排除“因为 `consider_metric: CDL2` 导致错过 F-Score 最优 checkpoint”的可能。

## 7. 官方 seen/unseen evaluation

训练完成后，使用 `ckpt-best.pth` 分别评估：

```text
seen: easy / median / hard
unseen: easy / median / hard
```

评估命令：

```bash
cd ~/adapointr_work/PoinTr
bash scripts/eval_shapenet34_official_seen_unseen.sh \
  experiments/AdaPoinTr/ShapeNet34_models/shapenet34_adapointr_official_full_4gpu/ckpt-best.pth
```

评估日志：

```text
logs/shapenet34_official_eval/
```

本次完整评估结果：

| split | mode | F-Score | CDL1 | CDL2 | EMD |
|---|---|---:|---:|---:|---:|
| seen | easy | 0.4337 | 11.0794 | 0.4736 | 0.0000 |
| seen | median | 0.4186 | 11.9999 | 0.6315 | 0.0000 |
| seen | hard | 0.3815 | 14.2977 | 1.0953 | 0.0000 |
| unseen | easy | 0.4034 | 11.8139 | 0.5776 | 0.0000 |
| unseen | median | 0.3840 | 13.3681 | 0.9307 | 0.0000 |
| unseen | hard | 0.3386 | 17.5877 | 2.0708 | 0.0000 |

三种难度平均：

| split | F-Score Avg | CD-L2 Avg |
|---|---:|---:|
| seen | 0.4113 | 0.7335 |
| unseen | 0.3753 | 1.1930 |

## 8. 与原论文 Table II 对照

AdaPoinTr TPAMI 论文 Table II 中 ShapeNet34 AdaPoinTr 结果为：

| split | CD-S | CD-M | CD-H | CD-L2 Avg | F-Score@1% Avg |
|---|---:|---:|---:|---:|---:|
| 34 seen categories | 0.48 | 0.63 | 1.07 | 0.73 | 0.469 |
| 21 unseen categories | 0.61 | 0.96 | 2.11 | 1.23 | 0.416 |

与本次复现实验对照：

| split | Paper CD-L2 Avg | Reproduced CD-L2 Avg | Delta | Paper F-Score | Reproduced F-Score | Delta |
|---|---:|---:|---:|---:|---:|---:|
| seen | 0.73 | 0.7335 | +0.0035 | 0.469 | 0.4113 | -0.0577 |
| unseen | 1.23 | 1.1930 | -0.0370 | 0.416 | 0.3753 | -0.0407 |

按难度对照 CD-L2：

| split | mode | Paper CD-L2 | Reproduced CD-L2 | Delta |
|---|---|---:|---:|---:|
| seen | easy/simple | 0.48 | 0.4736 | -0.0064 |
| seen | median/moderate | 0.63 | 0.6315 | +0.0015 |
| seen | hard | 1.07 | 1.0953 | +0.0253 |
| unseen | easy/simple | 0.61 | 0.5776 | -0.0324 |
| unseen | median/moderate | 0.96 | 0.9307 | -0.0293 |
| unseen | hard | 2.11 | 2.0708 | -0.0392 |

结论：

- CD-L2 与论文高度一致；
- seen 的 CD-L2 几乎完全复现；
- unseen 的 CD-L2 略优于论文；
- F-Score 低于论文，需单独分析；
- 原论文 Table II 不报告 CD-L1；
- 原论文 Table II 不报告 EMD。

## 9. 可视化结果

训练完成后，使用官方 full checkpoint 保存了 seen hard 和 unseen hard 的可视化样例。

命令：

```bash
cd ~/adapointr_work/PoinTr
bash scripts/visualize_shapenet34_official.sh \
  experiments/AdaPoinTr/ShapeNet34_models/shapenet34_adapointr_official_full_4gpu/ckpt-best.pth
```

输出路径：

```text
experiments/visualizations/shapenet34_official_full_4gpu/seen_hard/
experiments/visualizations/shapenet34_official_full_4gpu/unseen_hard/
```

每个样例包含：

```text
input_partial.npy
input_partial.png
missing_crop.npy
pred.npy
pred.png
gt.npy
gt.png
meta.txt
```

含义：

- `input_partial`: 输入残缺点云；
- `pred`: AdaPoinTr 预测的完整点云；
- `gt`: 完整点云 ground truth；
- `missing_crop`: 被裁掉的缺失部分；
- `meta.txt`: taxonomy、model id、split、mode 等信息。

可视化过程中出现过 matplotlib figure warning：

```text
RuntimeWarning: More than 20 figures have been opened.
```

该 warning 不影响已保存的可视化结果，后续可通过显式 `plt.close()` 优化。

## 10. 主要问题与排查

### 10.1 EMD 为什么全是 0.0000

ShapeNet 分支中调用：

```python
Metrics.get(dense_points, gt)
```

默认参数：

```python
require_emd=False
```

因此 `utils/metrics.py` 中会直接把 EMD 填为 0：

```python
if not require_emd and 'emd' in item['eval_func']:
    _values[i] = torch.tensor(0.).to(gt.device)
```

结论：

- EMD=0 不是模型结果；
- 是当前 ShapeNet evaluation 默认不计算 EMD；
- 原论文 ShapeNet34 Table II 也不报告 EMD；
- 因此本阶段不使用 EMD 作为对照指标。

### 10.2 Open3D 缺失与 F-Score fallback

最初服务器无法导入 Open3D：

```text
OSError('libX11.so.6: cannot open shared object file')
OSError('libGL.so.1: cannot open shared object file')
```

为保证 headless 服务器可运行，代码中增加了 F-Score Torch fallback：

```python
try:
    pred = cls._get_open3d_ptcloud(pred)
    gt = cls._get_open3d_ptcloud(gt)
except (ImportError, OSError):
    return cls._get_f_score_torch(pred_tensor, gt_tensor, th)
```

后来补齐 Open3D 依赖后，重跑完整 seen/unseen evaluation，F-Score 与 fallback 结果完全一致。

结论：

- F-Score 偏低不是 Open3D 缺失导致的；
- Torch fallback 与 Open3D 路径在本实验中结果一致。

### 10.3 F-Score 低于论文的原因分析

论文 Table II 中 F-Score：

```text
seen: 0.469
unseen: 0.416
```

本次复现实验：

```text
seen: 0.4113
unseen: 0.3753
```

已经排除的原因：

- 不是训练没收敛：CD-L2 与论文高度一致；
- 不是 Open3D/fallback：补齐 Open3D 后结果不变；
- 不是 checkpoint 选择：epoch 560 同时是 F-Score 最优和 CD-L2 最优；
- 不是 sample/category 平均方式主导：两者差距较小。

最可能原因：

```text
F-Score@1% 的阈值/尺度口径差异
```

官方代码中的 F-Score 默认阈值是：

```python
def _get_f_score(cls, pred, gt, th=0.01):
```

但 F-Score 对阈值极其敏感。为此编写了诊断脚本：

```text
tools/diagnose_shapenet34_fscore.py
```

诊断方法：

- 加载 `ckpt-best.pth`；
- 对指定 split/mode 的前 100 个模型；
- 每个模型使用 8 个固定视角；
- 在多个 threshold 下计算 F-Score；
- 同时输出 sample-weighted 和 category-weighted 平均。

诊断结果：

| split | mode | CD-L2 x1000 | F@0.010 | F@0.011 | F@0.012 |
|---|---|---:|---:|---:|---:|
| seen | easy | 0.4223 | 0.4505 | 0.5042 | 0.5554 |
| seen | median | 0.5456 | 0.4378 | 0.4906 | 0.5412 |
| seen | hard | 0.9541 | 0.4022 | 0.4521 | 0.5000 |
| unseen | easy | 0.6043 | 0.3830 | 0.4293 | 0.4744 |
| unseen | median | 0.9815 | 0.3628 | 0.4073 | 0.4508 |
| unseen | hard | 2.1238 | 0.3168 | 0.3560 | 0.3948 |

观察：

- 从 `th=0.010` 到 `th=0.011`，F-Score 通常提升约 `0.04-0.05`；
- 这与论文和复现之间的 F-Score 差距量级高度一致；
- sample-weighted 和 category-weighted 差异较小；
- 因此差异更可能来自 `F-Score@1%` 的尺度解释或论文报告口径，而不是模型训练失败。

### 10.4 官方仓库是否有更全面指标

已检查官方 GitHub 仓库：

```text
https://github.com/yuxumin/PoinTr
```

结论：

- 官方 README 中只提供了较粗的 pretrained performance；
- 对 AdaPoinTr ShapeNet34，没有比 TPAMI Table II 更完整的 seen/unseen easy/median/hard 指标；
- supplementary 中更细的 ShapeNet34 类别结果主要对应 PoinTr，而不是 AdaPoinTr；
- 因此正式对照仍以 AdaPoinTr TPAMI Table II 为准。

## 11. 最终结论

本阶段已经成功完成 AdaPoinTr 在 ShapeNet34 上的官方配置完整训练和评估。

可以确认的结论：

1. **ShapeNet34 官方数据流水线已跑通。**
2. **AdaPoinTr 官方模型配置已完成 4GPU full training。**
3. **训练 checkpoint、日志、评估结果和可视化结果均已保存。**
4. **CD-L2 与原论文 Table II 高度一致，可认为核心几何指标复现成功。**
5. **F-Score 低于论文，但已排除 Open3D/fallback、checkpoint 选择、平均方式等原因。**
6. **F-Score 差异更可能来自 F-Score@1% 阈值/尺度口径差异，而非训练失败。**
7. **EMD 在当前 ShapeNet evaluation 中默认不计算，不应作为本阶段正式指标。**

因此，本实验可以作为后续 Mamba 改进工作的官方 baseline。

## 12. 对后续小论文实验的建议

后续进入方法改进阶段时，建议遵循以下原则：

### 12.1 baseline 使用方式

正式对比中保留：

```text
AdaPoinTr official ShapeNet34 baseline
```

重点报告：

```text
CD-L2
CD-L1
F-Score
```

但解释时要注意：

- CD-L2 可直接和论文 Table II 对照；
- CD-L1 可用于内部方法对比，但原论文 Table II 不报告；
- F-Score 可用于内部公平对比，但与论文绝对值存在口径疑点；
- EMD 暂不报告，除非后续专门修复和验证 EMD evaluation。

### 12.2 后续方法对比

对于后续 Mamba 模块改进，建议所有方法统一使用同一份 evaluation 代码和同一阈值：

```text
F-Score th=0.01
```

这样即使 F-Score 的绝对值和论文不完全一致，内部对比仍然公平。

### 12.3 论文中如何表述复现情况

可写为：

```text
We reproduced AdaPoinTr on ShapeNet-34 using the official configuration.
The reproduced CD-L2 is nearly identical to the reported TPAMI results.
F-Score is lower under the released evaluation implementation with th=0.01.
Additional threshold sweeps show that F-Score is highly sensitive to the exact
distance threshold, suggesting that the discrepancy is more likely due to the
metric threshold/scale convention than model convergence.
```

中文解释：

```text
我们按照官方配置复现了 AdaPoinTr 在 ShapeNet-34 上的实验。复现得到的 CD-L2 与 TPAMI 论文报告值高度一致，说明训练与评估主流程正确。F-Score 在官方代码 th=0.01 口径下低于论文，但进一步的阈值扫描表明该指标对阈值极其敏感，差异更可能来自 F-Score@1% 的尺度/阈值口径，而不是模型没有收敛。
```

## 13. 关键文件索引

训练脚本：

```text
scripts/run_shapenet34_adapointr_official_4gpu.sh
```

评估脚本：

```text
scripts/eval_shapenet34_official_seen_unseen.sh
scripts/eval_shapenet34_adapointr_seen_unseen.sh
```

可视化脚本：

```text
scripts/visualize_shapenet34_official.sh
tools/visualize_shapenet34_completion.py
```

F-Score 诊断脚本：

```text
tools/diagnose_shapenet34_fscore.py
```

官方配置：

```text
cfgs/ShapeNet34_models/AdaPoinTr.yaml
cfgs/ShapeNetUnseen21_models/AdaPoinTr.yaml
```

训练输出：

```text
experiments/AdaPoinTr/ShapeNet34_models/shapenet34_adapointr_official_full_4gpu/
logs/shapenet34_official_4gpu/
```

评估日志：

```text
logs/shapenet34_official_eval/
```

可视化输出：

```text
experiments/visualizations/shapenet34_official_full_4gpu/
```

复现实验对照文档：

```text
docs/shapenet34_official_comparison.md
docs/shapenet34_official_4gpu.md
docs/shapenet34_adapointr_official_full_report_zh.md
```
