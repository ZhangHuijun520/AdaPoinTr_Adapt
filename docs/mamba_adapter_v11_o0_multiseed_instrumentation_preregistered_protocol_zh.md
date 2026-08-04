# Mamba Adapter v1.1 O0-xyz 多 seed 稳定性与内部 token instrumentation 预注册协议

## 1. 协议定位

本协议在 seed-1 和 seed-2 开始训练前冻结，用于复核已经冻结的
`Mamba Adapter v1.1 O0=xyz out8192` 是否存在明显的 seed 敏感性，并在不改变模型输出的前提下记录真实 encoder token 序列及 Adapter 内部状态。

本阶段是稳定性复核与机制诊断，不重新选择 ordering，不增加新候选，不依据 seed-1 结果修改 seed-2，也不运行 SkullBreak official test。冻结基础版本为：

- Git tag：`mamba-adapter-v11-ordering-o0-xyz-out8192-seed0`
- Git commit：`0cbdf8d8d379f4d57e6a2a60d5b5c71c00319721`
- 配置：`cfgs/SkullBreak_models/MambaAdapterV11OrderingO0_xyz_out8192_monitor.yaml`

机器可读协议位于：

```text
docs/protocols/mamba_v11_o0_xyz_multiseed_instrumentation_seed1_seed2.json
```

## 2. 固定训练设计

| 项目 | 固定值 |
|---|---:|
| ordering | O0=`xyz` |
| 输出点数 | 8192 |
| 新增 seeds | 1、2 |
| strict train | 520 cases / 104 skulls |
| monitor | 50 cases / 10 skulls |
| epoch | 100 |
| deterministic | 开启 |
| BN recalibration | strict train 65 batches |
| official test | 本阶段脚本禁止运行 |

seed-1 和 seed-2 必须由同一总脚本顺序启动。完成 seed-1 后不得根据日志、monitor 结果或 instrumentation 修改 seed-2 的超参数、数据、停止条件或代码。

## 3. 固定评价原则

本阶段只将 monitor 作为冻结模型的重复测量集，不再用于选择 ordering。所有 seed 均报告：

- implant：CD-L1、HD95、NSD@1 mm；
- final reconstruction：CD-L1、HD95、NSD@1 mm；
- rim contact：CD-L1、HD95、NSD@1 mm；
- 灾难失败数和失败率。

灾难失败继续使用 ordering ablation 之前预定义的规则：

```text
rim_contact_hd95_mm > 50.0 mm，或该值为 NaN/Inf
```

阈值是严格大于，不得在看到 seed-1/seed-2 结果后修改。R1 不产生新的模型获胜者，只报告 seed-0/1/2 的均值、标准差、范围和病例一致性。

## 4. Instrumentation 固定面板

instrumentation 只对 strict train 建立 20-case、20-skull 的固定面板。面板选择只读取 case ID、skull ID 和 defect type，不读取预测、标签几何或评价结果：

1. 按 defect type 平衡分配数量；
2. 使用固定 seed `20260803` 对元数据执行 SHA256 排序；
3. 全局禁止重复 skull；
4. 生成 JSON 和 SHA256 后锁定，seed-0/1/2 必须共用同一面板。

面板不是性能评价子集，只用于比较内部状态在不同 seed 下是否稳定。

## 5. 记录内容

每个病例保存实际 512-token：

- encoder 输出 token 的原始坐标；
- `xyz` 排序索引；
- 排序后的 token 坐标；
- 顺序跳跃 mean、P95、max、路径长度和路径效率。

每个 Adapter block 保存：

- input、LayerNorm output、Mamba mixer output、有效残差和 block output 的 RMS；
- token norm 的 mean、P95、max、min 与非有限值数量；
- alpha、alpha scale 和 effective alpha；
- residual/input RMS 比、token 比例 P95/max；
- input-residual cosine；
- 序列前 10% 与后 10% 的残差强度及 tail/head 比；
- 最大残差尖峰在序列中的相对位置。

instrumentation 默认关闭，只允许在 `model.eval()` 下显式开启。常规训练和推理继续执行原始前向分支。

## 6. 零扰动门槛

开始 seed-1/seed-2 前必须通过：

```text
python tools/test_mamba_adapter_instrumentation.py
```

通过条件：同一输入、同一权重、eval 模式下，instrumentation 关闭与开启的模型输出必须 bitwise equal；记录数量、排序索引尺寸、pop 清理和训练态保护必须正确。

正式服务器脚本还会在每个 seed 开始前，对完整 AdaPoinTr 模型的两个固定 strict-train 病例比较所有输出张量和 CPU/CUDA RNG 后状态。任一张量不是 bitwise equal、RNG 状态不同或记录缺失时，训练立即终止。

## 7. 禁止事项

- 不得运行本阶段脚本未包含的 official test；
- 不得依据 seed-1 修改 seed-2；
- 不得重新比较 O1/O2/O3；
- 不得把 strict-train instrumentation 面板当作性能选择集；
- 不得依据内部统计临时增加或删除病例；
- 不得在 R1 中同时加入双向扫描、PCA、Morton、rim loss 或结构替换。

## 8. 完成判据

R1 完成需要同时满足：

1. seed-1 和 seed-2 均完成 100 epoch、BN recalibration 和 monitor 评价；
2. 两个 seed 均完成同一 strict-train 面板的 instrumentation；
3. 所有输出带 SHA256；
4. 汇总 seed-0/1/2，不遗漏灾难病例；
5. 在结果冻结前不启动下一轮 ordering 或结构候选。
