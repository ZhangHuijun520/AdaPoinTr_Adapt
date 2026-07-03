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

第一轮 `batch=1`、200 step 实验仅表现出基础可学习性，未达到强过拟合：

```text
best epoch:           70
best CDL1:            49.2525
best CDL2:            7.6842
best F-Score:         0.0167

input -> GT CD:       2.8448 mm
prediction -> GT CD:  5.2648 mm
input -> GT HD95:     5.3350 mm
prediction -> GT HD95: 12.2129 mm
```

因此增加第二轮受控 overfit：

- 唯一病例保持不变；
- 将该病例重复 8 次组成 `batch=8`；
- 从头训练 1000 step；
- 学习率 `5e-5`；
- weight decay 设为 0；
- 每 25 step 验证并保存 checkpoint；
- 脚本检测到 `ckpt-last.pth` 时自动恢复。

运行：

```bash
tmux new -s skullfix_overfit2
cd ~/adapointr_work/PoinTr
bash scripts/run_skullfix_adapointr_overfit1_controlled.sh
```

配置文件：

```text
cfgs/SkullFix_models/AdaPoinTr_overfit1_controlled.yaml
```

日志：

```text
logs/skullfix/skullfix_adapointr_overfit1_controlled_<timestamp>.log
```

第二轮最低通过门槛：

```text
prediction complete -> GT CD-L1 < 2.8448 mm
prediction complete -> GT HD95  < 5.3350 mm
prediction complete -> GT NSD@1mm > 0.0948
```

同时可视化必须恢复完整颅骨轮廓，不能出现明显覆盖塌缩。若第二轮仍未达到门槛，
停止完整 baseline，转而检查任务定义、输入点数、完整颅骨目标和 AdaPoinTr
输入保留机制之间的适配。

第二轮在 1000 step 时仍未超过缺损输入基准，主要表现为 GT 到 prediction
的方向距离过大，即预测点靠近真实表面，但没有覆盖完整表面：

```text
best epoch: 975

input -> GT:
  CD-L1: 2.8448 mm
  HD95:  5.3350 mm
  NSD@1 mm: 0.0948

prediction -> GT:
  CD-L1: 3.6884 mm
  HD95:  9.3093 mm
  NSD@1 mm: 0.0940

prediction -> GT directed mean: 2.3293 mm
GT -> prediction directed mean: 5.0475 mm
```

### 7.3 Identity overfit 诊断

在继续完整 baseline 前，使用同一病例执行 `complete -> complete` 诊断。该实验只用于
区分“模型本身无法记忆”与“defective -> complete 任务不适配”，不得作为正式结果。

配置通过 `input_key: gt` 令模型输入与监督目标读取同一份固定 GT 点云：

```text
cfgs/SkullFix_models/AdaPoinTr_identity_overfit_controlled.yaml
```

实验保持 batch=8、weight decay=0，训练 500 step：

```bash
tmux new -s skullfix_identity
cd ~/adapointr_work/PoinTr
bash scripts/run_skullfix_adapointr_identity_overfit.sh
```

预期数据日志：

```text
train: samples=8 unique_samples=1 repeat=8 input_key=gt
val:   samples=1 unique_samples=1 repeat=1 input_key=gt
```

判定：

- 若 identity 能显著过拟合且无覆盖塌缩，问题位于 `defective -> complete` 的任务适配；
- 若 identity 仍无法过拟合，优先检查 AdaPoinTr 的 denoising queries、BatchNorm
  统计、训练/推理分支和当前优化配置；
- identity 实验中模型输入与 GT 是同一组点，因此输入自身的 CD、ASSD、HD95
  必须为 0，NSD 必须为 1；
- 预测建议达到 CD-L1 < 1 mm、HD95 < 2 mm、NSD@1 mm > 0.5；
- 若未达到理想门槛，也必须显著优于 defective -> complete 的 3.6884 mm，
  且两个方向的平均距离不能继续严重失衡。

Identity overfit 实际未通过。输入配置已经确认是 `input_key=gt`，训练 reconstruction
loss 从 256.4390 降至约 119.4，但验证最佳结果仍约为 CDL1=47.0432、
CDL2=7.2927，说明需要区分训练/推理分支差异。

使用以下脚本比较四种模式：

```text
tools/diagnose_skullfix_train_eval_gap.py
```

四种模式分别为：

1. `eval_standard`：标准推理分支和 running BN statistics。
2. `eval_branch_batch_bn`：推理分支，但 BN 使用当前 batch statistics。
3. `train_branch_eval_layers`：启用 denoising 训练分支，其余子层保持 eval。
4. `train_full`：完整训练模式。

运行：

```bash
python tools/diagnose_skullfix_train_eval_gap.py \
  --config cfgs/SkullFix_models/AdaPoinTr_identity_overfit_controlled.yaml \
  --ckpt experiments/AdaPoinTr_identity_overfit_controlled/SkullFix_models/\
skullfix_adapointr_identity_overfit/ckpt-best.pth \
  --batch_size 8 \
  --out logs/skullfix/identity_train_eval_gap.json
```

判断：

- `eval_branch_batch_bn` 明显优于标准 eval：BatchNorm running statistics 是主因。
- `train_branch_eval_layers` 明显优于标准 eval：denoising 训练分支与推理分支不一致。
- `train_full` 明显更好、其余仍差：多个训练态因素共同作用。
- 四种模式都差：优先检查 reconstruction objective、输出覆盖和架构适配。

实际四路诊断表明，batch BN 能改善预测点贴近表面的精度，但不能改善
GT 到 prediction 的覆盖距离；denoising 分支差异影响很小。下一步使用：

```text
tools/diagnose_skullfix_loss_gradients.py
```

该工具只执行一次 train-mode forward 和若干次 backward，不执行 optimizer step，
也不写入 checkpoint。它会：

- 独立复算 denoise、coarse、fine reconstruction loss；
- 断言分解结果与 `model.get_loss` 完全一致；
- 分别对 denoise、coarse、fine 和 total loss 反向传播；
- 按 grouper、encoder、coarse prediction、query ranking、transformer decoder、
  decode head 等模块统计梯度；
- 分别报告 coarse、fine 和 denoised fine 的毫米制双向覆盖；
- 报告 fine patch 相对其 coarse parent 的半径和点云内部最近邻分布。

运行：

```bash
python tools/diagnose_skullfix_loss_gradients.py \
  --config cfgs/SkullFix_models/AdaPoinTr_identity_overfit_controlled.yaml \
  --ckpt experiments/AdaPoinTr_identity_overfit_controlled/SkullFix_models/\
skullfix_adapointr_identity_overfit/ckpt-best.pth \
  --batch_size 8 \
  --out logs/skullfix/identity_loss_gradient_diagnostic.json
```

### 7.4 完整内部划分 baseline

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
