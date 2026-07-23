# Mamba Adapter v1.1-xyz Implant-8192 正式冻结记录

## 1. 冻结结论

Mamba Adapter v1.1-xyz 于 2026-07-23 正式冻结，作为后续 ordering
ablation 的稳定训练母版和 `xyz` 对照组。

本次冻结覆盖 SkullFix 与 SkullBreak，统一采用：

- 输入点数：8192；
- 输出 implant 点数：8192；
- seed：0；
- Mamba Adapter 插入位置：AdaPoinTr encoder 后、decoder 前；
- Adapter depth：2；
- ordering：`xyz`；
- `alpha_init=0.01`；
- alpha warmup：前 20 epochs 从 0.0 线性增加到 1.0；
- Mamba fast path：启用；
- 主体 loss：沿用 AdaPoinTr implant-8192 baseline；
- 不启用 v1.2 系列 rim-aware loss。

对应 Git tag：

```text
mamba-adapter-implant-out8192-v1.1-xyz-seed0
```

## 2. 冻结范围

冻结提交只包含：

- alpha scale 与 alpha warmup 的最小实现；
- SkullFix/SkullBreak v1.1 配置；
- SkullFix/SkullBreak v1.1 训练、BNCal、评估和可视化脚本；
- SkullFix/SkullBreak 双归档脚本；
- 本冻结记录。

明确不包含：

- v1.2、v1.2b、v1.2c 的 rim-aware loss；
- ordering 候选实现；
- symmetry-aware ordering；
- official-test 驱动的后续调参。

## 3. 数据与评估协议

### 3.1 SkullFix

- 使用固定 seed-0 数据划分；
- train/val/test 及数据预处理与 AdaPoinTr Implant-8192 baseline 一致；
- BN calibration：10 batches；
- test：10 个病例；
- point/rim 与 Windows voxel 指标均已完成。

### 3.2 SkullBreak

- official train：570 cases / 114 skulls；
- monitor：50 cases / 10 skulls；
- official test：100 cases / 20 skulls；
- BN calibration：72 batches；
- point/rim 与 Windows voxel 指标均已完成。

SkullBreak official test 已用于 v1.1 基线诊断。后续 ordering 候选只能使用
monitor split 进行选择；候选冻结后，获胜版本才能再次运行 official test。

## 4. 主要结果

### 4.1 SkullFix

相对 AdaPoinTr Implant-8192 baseline：

- point Implant CD：-0.0180 mm；
- point Implant HD95：-0.1251 mm；
- point Final CD：-0.0276 mm；
- point Final HD95：-0.2958 mm；
- point Rim CD：+1.6096 mm；
- point Rim HD95：+2.7409 mm。

Windows voxel 主要均值：

- Implant DSC：0.336530；
- Implant ASSD：2.736922 mm；
- Implant HD95：6.756395 mm；
- Final DSC：0.954981；
- Final ASSD：0.324608 mm；
- Final HD95：2.830991 mm；
- Rim CD：3.423493 mm；
- Rim HD95：18.668573 mm；
- Rim NSD@1：0.583741。

结论：alpha warmup 保持了整体和最终重建稳定性，但 rim-contact 仍明显落后。

### 4.2 SkullBreak

Point/rim official-test 主要均值：

- Implant CD：3.6217 mm；
- Implant HD95：7.9431 mm；
- Implant NSD@1：0.2141；
- Final CD：2.3603 mm；
- Final HD95：5.2336 mm；
- Final NSD@1：0.1419；
- Rim CD：6.1024 mm；
- Rim HD95：22.4346 mm；
- Rim NSD@1：0.4646。

Windows voxel 主要均值：

- Implant DSC：0.362601；
- Implant ASSD：3.589187 mm；
- Implant HD95：8.387193 mm；
- Final DSC：0.947009；
- Final ASSD：0.381786 mm；
- Final HD95：2.731330 mm；
- Rim CD：4.012917 mm；
- Rim HD95：15.153326 mm；
- Rim NSD@1：0.601466。

相对 Mamba Adapter v1：

- Implant DSC：+0.020228；
- Implant HD95：-0.556834 mm；
- Final DSC：+0.001720；
- Final ASSD：-0.063392 mm；
- Final HD95：-0.479649 mm；
- Rim CD：+1.176261 mm；
- Rim HD95：+1.067518 mm。

已确认 `test__004__frontoorbital` 为灾难性 rim 失败病例：

- point Rim CD：133.299807 mm；
- point Rim HD95：149.955117 mm；
- point Rim NSD@1：0。

结论：v1.1 缓解了 v1 对 encoder feature 的整体扰动，并使 Final
reconstruction 基本恢复到 AdaPoinTr 水平；但 frontoorbital 与局部
rim-contact 仍是主要失败来源。因此 v1.1 适合作为 ordering ablation
母版，而不能声明为全面优于 AdaPoinTr 的最终模型。

## 5. 正式归档

### 5.1 SkullFix

```text
skullfix_mamba_adapter_v11_xyz_out8192_seed0_v1.tar
SHA256:
b4d672ed4c74877c8242b2c1fb427e5914433adb0949fafccc5e29ebdafb5680
```

Windows voxel summary：

```text
skullfix_voxel_summary.json
SHA256:
cab7685188f1f85a8ad4f2a85e836a49ca0e76e14468217906d3d7cf3aeb91f9
```

### 5.2 SkullBreak

```text
skullbreak_mamba_adapter_v11_xyz_out8192_seed0_v1.tar
SHA256:
2da726c5b8119ddf6b0b506b23e675561d1dce15aecaa7010b466b0bf7cd803d
```

Windows voxel summary：

```text
skullbreak_mamba_v11_voxel_voxel_summary.json
SHA256:
5ff6ecdfa6c573c34136d1029b1f82faed1d9e44f7a2870d8a54978a4e06c6b3
```

两套服务器 tar 均已通过本地 SHA256 校验和 tar 结构检查。Windows voxel
结果保存在各自正式本地归档目录，不重复写入服务器 tar。

## 6. 后续 ordering ablation 约束

所有 ordering 候选必须保持以下变量不变：

- v1.1 alpha 初始化与 warmup；
- Adapter depth、网络宽度和参数规模；
- 数据划分、seed、训练轮数、BNCal 参数；
- loss、输入/输出点数和评估实现；
- checkpoint 选择规则。

第一阶段仅比较不会改变参数量的纯 ordering，并将 `xyz` 作为 O0 对照组。
候选选择只能依据 SkullBreak monitor split，优先级为：

1. NaN 和灾难性失败数；
2. Rim HD95；
3. Rim CD；
4. frontoorbital Implant/Rim 指标；
5. Final reconstruction 无明显退化。

灾难性失败预定义为：

```text
任一核心 rim 指标为 NaN
或 Rim CD > 50 mm
或 Rim HD95 > 50 mm
```

在 ordering 获胜版本冻结前，不得根据 official-test 结果更换候选或调整
ordering 参数。
