# ShapeNet34 官方 baseline 归档与恢复

## 目标

在开始颅骨数据实验前，固定一份可验证、可恢复的 AdaPoinTr
ShapeNet34 官方 baseline。归档分为两层：

1. Git 保存代码、配置、脚本和文档的版本历史。
2. 独立实验归档保存权重、日志、指标、可视化、运行环境和代码快照。

不要把 `.pth` 权重和整个 `experiments/` 提交进 Git。它们体积大，而且
仓库的 `.gitignore` 已经有意忽略这些文件。

## 一、先固定本机代码版本

在本机 D 盘仓库执行：

```powershell
cd D:\Codex\2026-06-06\mamba-ccf-c-1-high-resolution\work\PoinTr
git status --short
git add docs tools scripts cfgs models datasets utils main.py
git commit -m "Freeze reproduced AdaPoinTr ShapeNet34 official baseline"
git tag -a shapenet34-adapointr-official-baseline-v1 -m "600-epoch ShapeNet34 official baseline"
```

如果 `git status` 中出现与本次 baseline 无关的文件，不要把它们一起提交。
提交后执行：

```powershell
git status --short
git show --stat --oneline HEAD
git tag --list "shapenet34-adapointr-official-baseline-*"
```

建议再把仓库历史导出成单文件：

```powershell
git bundle create ..\PoinTr_shapenet34_baseline_v1.bundle --all
git bundle verify ..\PoinTr_shapenet34_baseline_v1.bundle
```

## 二、在服务器创建完整实验归档

归档前确认正式实验文件仍在：

```bash
cd ~/adapointr_work/PoinTr

ls experiments/AdaPoinTr/ShapeNet34_models/\
shapenet34_adapointr_official_full_4gpu/ckpt-best.pth

ls experiments/AdaPoinTr/ShapeNet34_models/\
shapenet34_adapointr_official_full_4gpu/ckpt-last.pth

ls logs/shapenet34_official_4gpu
ls logs/shapenet34_official_eval
ls experiments/visualizations/shapenet34_official_full_4gpu
```

运行归档脚本：

```bash
cd ~/adapointr_work/PoinTr
chmod +x scripts/archive_shapenet34_official_baseline.sh
bash scripts/archive_shapenet34_official_baseline.sh
```

默认输出到：

```text
~/baseline_archives/
  shapenet34_adapointr_official_full_4gpu_YYYYMMDD_HHMMSS.tar
  shapenet34_adapointr_official_full_4gpu_YYYYMMDD_HHMMSS.tar.sha256
```

归档使用未压缩 `.tar`。PyTorch 权重通常已经是压缩容器，再套 gzip
节省空间有限，却会明显增加服务器时间和临时空间压力。

归档包含：

- `ckpt-best.pth`、`ckpt-last.pth` 和存在时的 `ckpt-epoch-600.pth`；
- 完整训练目录；
- full training 日志；
- seen/unseen 的 easy、median、hard 评估日志；
- seen/unseen 可视化样例；
- ShapeNet34 与 Unseen21 的模型和数据集配置；
- 运行、评估、可视化与 F-Score 诊断脚本；
- 中文实验报告与指标对照文档；
- `pip freeze`、Conda 环境、CUDA、GPU 和系统信息；
- 不含数据和实验产物的完整代码快照；
- Git bundle、commit、diff 和未跟踪文件清单（服务器副本有 `.git` 时）；
- 每个实验文件的 SHA256 清单。

ShapeNet55-34 原始数据不进入归档，避免重复占用约 10GB。数据目录结构和
文件数量应另行记录，原始压缩包可单独保存在移动硬盘或网盘。

## 三、下载并校验

将 `.tar` 和相邻的 `.tar.sha256` 一起下载到 D 盘，例如：

```text
D:\ResearchBackups\AdaPoinTr\ShapeNet34_official_v1\
```

在服务器下载或删除归档前，先校验：

```bash
cd ~/baseline_archives
sha256sum -c shapenet34_adapointr_official_full_4gpu_*.tar.sha256
```

下载到本机后，再用 PowerShell 计算一次。以下命令不能直接在传统的
`cmd.exe` 中运行。如果当前提示符类似 `C:\Users\zhj>`，先输入
`powershell`；进入后提示符应以 `PS` 开头。

```powershell
Set-Location D:\ResearchBackups\AdaPoinTr\ShapeNet34_official_v1

Get-FileHash .\shapenet34_adapointr_official_full_4gpu_*.tar -Algorithm SHA256
Get-Content .\shapenet34_adapointr_official_full_4gpu_*.tar.sha256
```

两处哈希必须一致。建议至少保留两份：

- D 盘工作备份；
- 移动硬盘、NAS 或可靠网盘中的异地备份。

确认本机副本和第二份副本均可读取后，才删除服务器上的临时 `.tar`。

## 四、恢复与验收

不要直接覆盖正在修改的仓库。先恢复到一个新目录：

```bash
mkdir -p ~/restore_tests/shapenet34_baseline_v1
cd ~/restore_tests/shapenet34_baseline_v1
tar -xf /path/to/shapenet34_adapointr_official_full_4gpu_TIMESTAMP.tar
bash scripts/verify_shapenet34_official_archive.sh .
```

如果只需恢复代码：

```bash
mkdir code
tar -xzf metadata/code_snapshot.tar.gz -C code
```

如果归档包含 `metadata/repository.bundle`，也可恢复 Git 历史：

```bash
git clone metadata/repository.bundle PoinTr
```

恢复后还需重新挂载或下载 ShapeNet55-34 数据，并重新创建 Conda 环境和
CUDA 扩展。权重与结果恢复不依赖原训练 GPU，但重新评估仍需可工作的
Chamfer Distance、PointNet2 和运行环境。

## 五、归档验收清单

- Git commit 和 tag 已创建；
- Git bundle 已通过 `git bundle verify`；
- `.tar` 与 `.tar.sha256` 已下载；
- 本机 SHA256 与服务器一致；
- `verify_shapenet34_official_archive.sh` 校验通过；
- `ckpt-best.pth`、`ckpt-last.pth` 均存在；
- 6 组 seen/unseen 日志均存在；
- 可视化目录中有 `input_partial.png`、`pred.png`、`gt.png`；
- 中文完整报告和指标对照文档已归档；
- 至少有两份物理位置不同的备份。

完成上述检查后，当前状态才算真正“可回退”，可以安心开始颅骨 baseline。

## 六、已完成归档记录

2026-06-28 已完成首个正式归档及恢复测试：

```text
archive:
shapenet34_adapointr_official_full_4gpu_20260627_031302.tar

size:
约 1.7GB

sha256:
7af4e91fa6481b4e34a0ee7a97a2081596791b38a1662e0c00cdba10729369be
```

验收结果：

- 服务器归档外层 SHA256 校验通过；
- 下载到 D 盘后的 SHA256 与服务器一致；
- 在服务器 `/tmp/shapenet34_restore_test` 中成功解包；
- `verify_shapenet34_official_archive.sh` 逐文件校验全部为 `OK`；
- `ckpt-best.pth`、`ckpt-last.pth`、epoch 599 和 epoch 600 权重完整；
- ShapeNet34 seen/unseen 评估日志和可视化样例完整；
- 原始 ShapeNet55-34 数据按设计未放入归档。
