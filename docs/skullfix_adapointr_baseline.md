# AdaPoinTr 接入 SkullFix 点云 baseline

## 1. 实验定位

SkullFix 用于跑通医学点云数据链路和建立第一版 AdaPoinTr baseline；
SkullBreak 后续用于正式主实验、缺损类型泛化和鲁棒性验证。

第一版任务定义为：

```text
input:  defective skull point cloud
target: complete skull point cloud
label:  implant point cloud, only for defect-region evaluation
```

训练阶段不得把 implant 输入模型。当前 `SkullFixDataset` 只返回
`(partial, gt)`；implant 保存在预处理文件和 manifest 中，供后续专用评估使用。

## 2. 数据协议

SkullFix 原始数据是 NRRD 二值体。公开资料描述：

- 训练集包含 100 个 complete/defective/implant triplet；
- 挑战测试集包含 100 个常规缺损和 10 个鲁棒性缺损；
- 挑战测试集的 complete skull 与 implant ground truth 由组织方保留；
- SkullFix 体数据尺寸为 `512 x 512 x Z`，不同病例的 Z 和体素间距可能不同。

因此，本地可复现实验不能默认使用官方 110 个测试病例计算监督指标。
本项目将公开训练 triplet 按固定 seed 做病例级 `80/10/10` 划分：

```text
train: 80
val:   10
test:  10
seed:  20260628
```

该划分只用于第一版医学 baseline。论文中必须明确它是从 SkullFix 公开训练集
生成的内部划分，不能写成 AutoImplant 官方 test 成绩。

## 3. 推荐目录

原始数据和转换结果都放在仓库外的持久数据目录：

```text
~/datasets/
├── SkullFix_raw/
└── SkullFixPC/
    ├── manifest.jsonl
    ├── pairing_report.json
    ├── splits.json
    ├── SHA256SUMS
    ├── summary.json
    └── points/
        ├── <case_id>.npz
        └── ...
```

仓库中只建立转换结果的软链接：

```bash
cd ~/adapointr_work/PoinTr
mkdir -p data
ln -s ~/datasets/SkullFixPC data/SkullFixPC
```

## 4. 下载和原始数据审计

官方数据页：

```text
https://figshare.com/articles/dataset/14161307
```

先通过浏览器下载到本机 D 盘，再上传或直接解压到服务器：

```bash
mkdir -p ~/datasets/SkullFix_raw
```

解压后先查看真实目录，不要直接猜文件名：

```bash
find ~/datasets/SkullFix_raw -maxdepth 4 -type f -name '*.nrrd' \
  | sort | head -60

find ~/datasets/SkullFix_raw -type f -name '*.nrrd' | wc -l
du -sh ~/datasets/SkullFix_raw
```

只对同时具备 complete、defective 和 implant 的公开监督数据执行转换。

## 5. NRRD 转点云

安装轻量依赖：

```bash
cd ~/adapointr_work/PoinTr
conda activate adapointr-server
python -m pip install -r requirements_skullfix.txt
```

如果原始目录名称能被自动识别：

```bash
python tools/prepare_skullfix_pointcloud.py \
  --input_root ~/datasets/SkullFix_raw \
  --output_root ~/datasets/SkullFixPC \
  --n_partial 8192 \
  --n_complete 8192 \
  --n_implant 4096 \
  --split 80,10,10 \
  --seed 20260628
```

如果自动识别报告目录不唯一，明确指定三个目录。相对路径以
`--input_root` 为基准：

```bash
python tools/prepare_skullfix_pointcloud.py \
  --input_root ~/datasets/SkullFix_raw \
  --complete_dir path/to/complete \
  --defective_dir path/to/defective \
  --implant_dir path/to/implant \
  --output_root ~/datasets/SkullFixPC \
  --split 80,10,10 \
  --seed 20260628
```

转换器会：

1. 为三类 NRRD 推导统一 case ID；
2. 检查一一对应、重复 ID、体数据 shape、origin 和 direction；
3. 检查 `implant` 与 `complete - defective` 的体素 IoU；
4. 从二值体边界体素采样物理坐标点；
5. 只用输入端 defective skull 表面计算 centroid 和最大半径；
6. 对 defective、complete、implant 使用完全相同的平移和缩放；
7. 生成固定随机种子的 `80/10/10` manifest。

首轮建议不要使用 `--strict_geometry`。先审阅 warning；确认数据头信息可靠后，
再以 strict 模式重跑最终预处理。

## 6. 转换结果检查

```bash
python tools/check_skullfix_pointcloud.py \
  --data_root ~/datasets/SkullFixPC

cd ~/datasets/SkullFixPC
sha256sum -c SHA256SUMS
```

还应人工检查：

```bash
cat ~/datasets/SkullFixPC/pairing_report.json
cat ~/datasets/SkullFixPC/summary.json
head -3 ~/datasets/SkullFixPC/manifest.jsonl
```

预期关键结果：

```text
paired_triplets: 100
split_counts: train=80, val=10, test=10
partial shape: 8192 x 3
gt shape: 8192 x 3
implant shape: 4096 x 3
```

如果 triplet 数不是 100，先停止训练并检查下载内容、目录选择和配对规则。

## 7. 训练前三级验证

### 7.1 8-sample sanity

使用完整 AdaPoinTr 架构，只限制数据量：

```bash
bash scripts/run_skullfix_adapointr_sanity.sh
```

通过条件：

- Dataset 能加载；
- partial/gt tensor shape 正确；
- forward、loss、backward 和 validation 完成；
- 没有 NaN、CUDA OOM 或 taxonomy KeyError；
- 生成 `ckpt-last.pth`。

### 7.2 单样本 overfit

```bash
bash scripts/run_skullfix_adapointr_overfit1.sh
```

配置让 train/val/test 都读取同一个训练病例。通过条件不是“loss 必须等于 0”，
而是训练损失持续明显下降，预测形状逐步逼近该病例的 complete skull。

建议同时记录 epoch 0、20、50、100、199 的 CD-L1、CD-L2 和可视化。
若单样本无法过拟合，不应开始完整 baseline。

### 7.3 完整内部划分 baseline

```bash
tmux new -s skullfix_baseline
cd ~/adapointr_work/PoinTr
bash scripts/run_skullfix_adapointr_baseline.sh
```

分离会话：

```text
Ctrl+b，然后松开，再按 d
```

重新进入：

```bash
tmux attach -t skullfix_baseline
```

脚本发现 `ckpt-last.pth` 时会自动使用 `--resume`。默认配置为单卡、
`total_bs=8`、300 epoch；正式运行前可先 profile batch size，但不要在不同方法
之间随意改变 total batch size。

评估：

```bash
bash scripts/eval_skullfix_adapointr_baseline.sh \
  experiments/AdaPoinTr_baseline/SkullFix_models/\
skullfix_adapointr_baseline/ckpt-best.pth
```

可视化：

```bash
bash scripts/visualize_skullfix_adapointr.sh \
  experiments/AdaPoinTr_baseline/SkullFix_models/\
skullfix_adapointr_baseline/ckpt-best.pth
```

每个病例会保存：

```text
input_defective.npy/.png
prediction_complete.npy/.png
ground_truth_complete.npy/.png
ground_truth_implant.npy/.png
meta.json
```

## 8. 当前指标与后续补充

当前通用 runner 可直接报告：

- Chamfer Distance L1；
- Chamfer Distance L2；
- F-Score（归一化坐标下的通用阈值）。

SkullFix 正式实验还必须补充缺损区域指标：

- implant/defect-region Chamfer Distance；
- HD95，单位恢复到 mm；
- ASSD；
- implant precision、recall 或 F-Score；
- 缺损边界连续性和局部法向一致性。

其中 HD95、ASSD 和 mm 单位指标必须使用 manifest 保存的原始空间变换与
normalization scale 还原，不能直接在归一化坐标中解释为临床距离。

## 9. 防止数据泄漏

- split 必须按病例，而不是按点、切片或增强样本；
- normalization 只能由 defective skull 输入计算，再将同一变换应用到
  complete 和 implant；val/test 的 complete/implant 不能参与输入预处理；
- implant 只用于训练后的局部评估，不能混入 partial；
- 后续扩增同一病例时，所有增强版本必须留在同一个 split；
- SkullBreak 的患者/原始 skull ID 也必须做 group split，五种缺损不能跨集合。

## 10. 本阶段完成标准

- 原始 NRRD 下载来源和许可证已记录；
- 100 个训练 triplet 一一对应；
- 转换后 manifest 和质量报告已归档；
- sanity 完成；
- 单样本 overfit 完成；
- 80/10/10 baseline 完成并保存权重、日志、指标和可视化；
- baseline 代码单独 commit；
- 然后再开始 SkullBreak 接入和正式鲁棒性实验。

## 11. 真实数据首次转换记录

2026-06-28 已对 Figshare SkullFix 训练包完成首次转换：

```text
raw complete skulls:   100
raw defective skulls:  100
raw implants:          100
paired triplets:       100

train/val/test:         80/10/10
seed:                   20260628
partial points:         8192
complete points:        8192
implant points:         4096
normalization source:   defective_surface

prepared files:         100 NPZ + metadata
prepared size:          about 13.35 MiB
min implant/missing IoU:  1.0
mean implant/missing IoU: 1.0
```

固定测试病例：

```text
000, 001, 014, 030, 047, 053, 054, 056, 079, 092
```

固定验证病例：

```text
028, 031, 035, 042, 058, 069, 072, 080, 082, 088
```

其余 80 个病例属于训练集。转换结果位于：

```text
D:\dataset\SkullFix\pointcloud_defective_norm
```

已生成服务器上传包：

```text
D:\dataset\SkullFix\SkullFixPC_defnorm_8192_seed20260628.tar.gz
```

SHA256：

```text
da4e3b50acf5d8768cf497bc9b848e4db849ecdc01abeef21e08e7d31d128a3c
```

服务器解包：

```bash
mkdir -p ~/datasets/SkullFixPC
tar -xzf ~/SkullFixPC_defnorm_8192_seed20260628.tar.gz \
  -C ~/datasets/SkullFixPC

cd ~/adapointr_work/PoinTr
mkdir -p data
ln -s ~/datasets/SkullFixPC data/SkullFixPC

python tools/check_skullfix_pointcloud.py \
  --data_root ~/datasets/SkullFixPC
```
