# Mamba v1.4 D4 Contact-Support Representation 修订预注册协议

> 状态：D4 训练前协议冻结版 v1。P-D3 是 selection-inert 事后诊断；D3 winner 仍为 null。MUG500+ 25-source holdout、SkullBreak confirmation20、旧 monitor、official test 与 SkullFix 选择用途均保持锁定。

## 1. 对原计划的判断

原计划的主方向合理，且与 D2、D2.1、D2.2、D3 的负结果具有清楚的因果连续性：剩余失败已经集中到少数病例的 contact-support omission，因此下一步应优先研究 representation，而不是继续扫描 contact loss 或扩大 Mamba 替换范围。

原计划在执行前需要修订以下问题：

1. **P-D3 不能替 D4 选超参数。** 旧 D3 development 已被消费，P-D3 只能分解既有 `top-96 -> FPS-32` 失败，不得选择新的 K、pool、head 或 selector。
2. **D4-A 必须 source-skull out-of-fold。** 每折只能用 75 个来源颅骨训练 proposal head，对未参与训练的 25 个来源颅骨一次性评分；不能把 400 cases 混合后训练与评分。
3. **T2 必须防止机械刷指标。** 若保留 partial anchor，除全输出指标外，还必须对去除保留 anchor 后的 generated-only 点集计算 zero-contact；两者都必须为零。
4. **T0 是参考而不是实验候选。** Round B 不再要求“至少两个候选（含 T0）通过”。只要至少一个 T1/T2 通过全部硬门，就运行同 seed T0 和全部合格实验候选。
5. **不能用未定义的 T0 Rim HD95 P95 作主门。** T0 存在 zero-contact 时 pooled P95 不可定义。改用固定阈值超限事件向量，非有限值记为超限事件，不做数值填补。
6. **必须预注册 winner 规则。** 仅列 hard-gate 顺序不足以处理 T1/T2 同时通过；本协议增加固定字典序排名和最终 lexical fallback，禁止人工 tie break。
7. **新数据不能由旧数据回填。** D4 需要额外 100 个从未进入 D3 development 或 25-skull holdout 的来源颅骨；当前本地 125-skull 数据不足，必须先继续完成 MUG500+ 获取与 QC。
8. **数据 QC 失败不能悄悄删难例。** 空 rim、尺度错误、mesh/label 异常触发整阶段 QC failure 和 generator amendment，不得依据模型表现删 case。

## 2. 已由冻结 D3 直接回答的问题

D3 的 8 个 S2 miss 病例每例仍含 `5-14` 个 GT-positive proxy。因此：

- `oracle candidate absent` 已不是这 8 例的直接原因；
- 需要通过 exact replay 区分 `ranking_miss_top96` 和 `selector_dropped_all_positive`；
- replay 只能补充失败归因，不能授权在旧数据上改 pool 或 selector 后重跑。

## 3. P-D3 exact replay

P-D3 必须恢复并核验四个冻结 S0 BNCal checkpoint，加载四个冻结 head-only checkpoint，保持所有参数 `requires_grad=False`、optimizer steps 为零，并逐病例复现原始 case hit、positive count 和 selected-positive count。

固定输出：

- positive proxy count/fraction；
- best positive rank 与 top-32/64/96/128 positive count；
- top-96 retention 与最终 FPS-32 retention；
- GT-rim 到全部 proxy、最终 anchors 的 P50/P95；
- GT-rim 在 2/5/10 mm 下的 Euclidean coverage；
- 8 个 miss 的唯一阶段归因。

点云产物没有可审计的 rim mesh adjacency，因此本版本不声称 geodesic segment coverage；使用固定阈值 Euclidean coverage，避免凭空定义拓扑。

## 4. D4 新数据锁

目标为 100 个全新健康来源颅骨，每 skull 生成 4 个 M2 v1 synthetic defects，共 400 cases。来源必须满足：

- 不与 D3 100-source development 重叠；
- 不与冻结 25-source holdout 重叠；
- STL/source hash 唯一；
- M2 generator 代码、参数和物理尺度 hash 与 D3 完全一致；
- 四折按来源颅骨划分，每折 75/25 source skull。

在下载或生成前先冻结来源清单；缺包或 QC 失败不能由查看模型结果后的替换来源补齐。

## 5. Dataset Geometry Audit

模型无关 QC 至少记录 defect surface/volume fraction、rim point count、bbox diameter、implant radial extent、midline crossing、source skull size、partial-to-GT-rim distance、有限性和尺度。任何空 label、非有限坐标、非正尺度、source overlap 或生成 hash 漂移均为硬失败。

## 6. D4-A high-resolution proposal feasibility

D4-A 的 proposal representation、head、candidate pool 和 selector 必须在查看 D4 development 结果前冻结。训练和评分按来源颅骨 out-of-fold；每折 development 仅评分一次。固定 rim query budget 为 32，不扫描 K。

进入 full D4 的必要条件：

1. candidate oracle 在所有 400 cases 上存在 GT-positive candidate；
2. learned partial-only proposal 在所有 400 个 out-of-fold cases 上至少命中一个 positive candidate；
3. case pairing 完整、全部必要输出有限；
4. 没有 holdout 或其他保护 split 访问。

任一条件失败即冻结 D4-A negative，T1/T2 full training 不得开始。

## 7. D4 Round-A

| Candidate | 作用 |
|---|---|
| T0 | same-round O0-xyz 配对参考，256 global learned queries |
| T1 | 224 global + 32 high-resolution partial-only rim-aware queries |
| T2 | T1 + contact-support preservation，输出总数仍为 8192 |

Round-A 为 `3 candidates x 4 folds x seed0 = 12 trainings`。不叠加 S1 contact objective，以保持结构归因。

## 8. T2 anti-gaming contract

若 T2 在最终输出中保留 32 个 anchor/support points，则普通 generated points 固定为 8160。必须同时报告：

- all-output zero-contact 与 support relevance；
- generated-only zero-contact 与 support relevance；
- exact partial-copy ratio；
- bounded offset 的 P50/P95/max；
- predicted support -> GT-rim 与 GT-rim -> predicted support 的双向距离。

`all-output zero-contact == 0` 且 `generated-only zero-contact == 0` 才能通过存在性门控，防止单纯复制 defective partial 点。

## 9. Hard gates 与相关性

固定顺序：完整配对、全部必要指标有限、dense zero-contact=0、T2 generated-only zero-contact=0、disaster 不高于 same-seed T0、induced 不多于 rescued、contact relevance、Final non-inferiority、efficiency。

Final 容忍量固定为：

- `Final CD delta <= +0.10 mm`；
- `Final HD95 delta <= +0.50 mm`；
- `Final NSD@1 delta >= -0.01`。

效率上限固定为：参数 `<=1.10x T0`、峰值显存 `<=1.10x T0`、中位 latency `<=1.25x T0`。

Contact relevance 使用固定阈值 `2/5/10/20/50 mm` 的超限事件向量。非有限值记为阈值超限事件，但不填入任意数值；禁止只对 finite subset 计算一个有利 P95 作为主门。

## 10. 晋级和 winner

- seed0：运行 T0/T1/T2；至少一个实验候选 T1/T2 通过全部硬门，才允许 seed1。
- seed1：运行 T0 和全部 seed0 合格实验候选。
- seed2：运行 T0 和按固定字典序排名得到的 provisional winner。
- 无实验候选通过：冻结 D4 negative，转向 local rim-context representation。

合格候选按 disaster、zero-contact、固定阈值相关性向量、共同 finite paired subset 上的 Rim HD95、Implant HD95、latency、参数量、候选名依次排序。source skull 为 bootstrap/resampling 单位，禁止人工 tie break。

## 11. 保护数据顺序

只有 D4-A、seed0、seed1、seed2 均通过且代码、协议、checkpoint rule 冻结后，才允许一次性 MUG500+ 25-source holdout。随后依次为 SkullBreak confirmation20、SkullFix robustness，最后一次 SkullBreak official test。任何受保护结果都不得返回修改候选或规则。

## 12. 当前执行顺序

1. 运行并冻结 P-D3 exact replay；
2. 获取和 QC 全新 100 个 MUG500+ 来源颅骨；
3. 生成并冻结 D4 400-case 数据锁与 geometry audit；
4. 冻结 D4-A 唯一 representation/head/selector；
5. 通过 feasibility 后才实现并运行 T0/T1/T2。
