# Mamba v1.5 D5 候选与训练预注册协议

> 本协议在 D5 development400 生成与独立审计冻结之后、任何 D5 候选实现或训练之前建立。它只授权下一步实现 `V0/V1` 和执行 zero-step preflight，不授权训练、候选选择或 sealed 数据访问。

## 研究问题

D4-A 在 400 个病例中命中 332 例。冻结 post-hoc 将 68 个漏失分解为 2 个 top-256 ranking miss 和 66 个 selector 丢弃全部 pool-positive。D5 因此不再扫描 top-K、pool size 或 FPS 配额，而是检验一个新的可证伪假设：

> 仅使用 partial point cloud 的多尺度局部上下文与全局 set context，并以和最终 top-32 集合一致的 set-level objective 训练，能否在独立来源上保证每个 selected-32 至少含一个 reference-rim positive？

## 候选

### V0：参考机制

`V0` 精确复现 D4-A 的 13D 描述符、`13-128-64-1` head 和 top-8 + top-256 conditioned FPS-24 selector，但在新的 D5 四折上重新训练。它只提供新数据上的参考诊断，不具备晋级资格，也不运行 seed 1。

### V1：唯一实验候选

`V1` 使用冻结的 27D partial-only 描述符：D4-A 13D、k=32 的 9 个局部统计量、相对 partial 全局质心的 3D offset、全局 RMS 归一化半径和 k16/k32 局部尺度对数比。

27D 输入首先经过共享 `27-64-64` point encoder；对全部 8192 点执行 mean/max pooling 得到 128D global context；再将 64D point feature、128D global context 和原始 27D descriptor 拼接为 219D，经 `219-128-64-1` classifier 输出分数。

训练目标固定为三项等权和：

1. case-balanced point BCE；
2. softmax temperature=1 的 positive-mass NLL；
3. margin=1 的 best-positive 与第 32 个 negative 的 top-32 margin loss。

推理 selector 固定为 score top-32，score 相同时按原 candidate index 升序。V1 禁用 FPS 和其他 post-rank diversification，使训练目标与最终 selected-set gate 直接对齐。

## 数据与防泄漏

- 100 个 D5 development 来源，400 个冻结病例；
- A/B/C/D 四折各 25 个 dev 来源、100 个 dev 病例；
- 每来源四个缺损族始终同折；
- GT reference-rim mask 只用于训练标签和冻结 gate，不作为推理输入；
- 每次运行仅在 final epoch 后访问对应 out-of-fold dev 一次；
- proposal confirmation、completion holdout 和 official test 继续 sealed。

## 训练预算

V0 与 V1 共享固定预算：50 epochs、case batch size 8、AdamW、lr `1e-3`、weight decay `1e-4`、CosineAnnealingLR、minimum lr `1e-5`、gradient clip 1.0、final epoch checkpoint only、禁止 early stopping。

Seed 0 最多运行 8 个 head：V0 A-D 后 V1 A-D。只有 V1 seed 0 达到 400/400，才允许另行授权 V1 seed 1 的四折训练。V1 seed 1 也必须达到 400/400，之后才能另行授权一个 development-all final head，并一次性打开 25-source proposal confirmation。

## 硬门控

Development seed 0、seed 1 均要求：

- 400 个病例精确配对；
- 400/400 均存在 oracle positive；
- V1 selected-32 contains positive = 400/400；
- 所有 required outputs finite；
- 四折全部通过；
- sealed/protected access 为 false。

Proposal confirmation 要求一次性精确覆盖 100 个病例，并达到 100/100。任一阶段失败立即冻结负结果，不改阈值、不换 selector、不补 seed、不重跑失败折。

## 诊断指标

Recall@8/16/32/64/128/256、positive candidate count、best positive rank、缺损族分层、来源级 miss 聚集和 V1-V0 配对转移必须完整报告，但不得用来替代或放宽 400/400 与 100/100 门控。

## D5-B 边界

本协议不定义完整 completion 模型 D5-B。只有 V1 的 development seed 0、seed 1 和 proposal confirmation 全部通过后，才能建立新的独立 D5-B 协议，冻结完整模型候选、预算、contact/global/efficiency gates 与 selection 规则。

## 当前授权状态

- `V0/V1 implementation + zero-step preflight`：下一步允许；
- D5-A seed-0/seed-1 training：禁止；
- development-all training：禁止；
- proposal confirmation：sealed，禁止访问；
- D5-B implementation/training/selection：禁止；
- completion holdout 与 official test：禁止访问。

下一步只实现冻结的 V0/V1 descriptor、context head、loss 与 selector，并执行不构造 optimizer、零 model update、零 dev access 的 zero-step preflight。训练必须由后续独立 authorization receipt 明确开启。
