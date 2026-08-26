# MUG500+ M2 protected-overlap audit v2.1 预注册修订协议

## 1. 协议定位

本协议是 overlap audit v2 运行结束后的透明修订，协议 ID 为：

`mug500plus-m2-protected-overlap-audit-v2.1-source-stratified-provenance`

它只回答一个数据治理问题：MUG500+ healthy125 是否可以进入后续 `100 development / 25 locked holdout` 的 source-skull 数据冻结步骤。

它不选择模型、loss、ordering、seed、query allocation 或 checkpoint，也不直接启动 D3 训练。

## 2. 修订原因

冻结 v1 得到：

- exact hash intersection：0；
- 1024-point geometry suspect：769；
- automatic gate：失败。

冻结 v2 得到：

- exact hash intersection：0；
- 1250 个 high-resolution candidate 中 suspect：0；
- pooled positive q99 与 pooled negative q01 未分离；
- automatic gate：失败。

v2 的问题不是重新出现跨数据集疑似项，而是把不同采样域的尾部分位数放进同一个极值比较：pooled positive q99 由 MUG500+ 主导，pooled negative q01 由 SkullBreak 主导。这种比较不能回答单个来源域中的同源与异源样本是否可分。

v2.1 只修正这一统计层级，不重新计算 v2 的跨数据集距离，不删除病例，也不改写 v1/v2 的失败结论。

## 3. 不可变输入

v2.1 只能读取以下冻结产物：

- v2 `calibration_pairs.csv`；
- v2 `exact_hash_intersections.csv`；
- v2 `high_resolution_candidates.csv`；
- v2 `overlap_audit_v2_summary.json`；
- source provenance v1 JSON。

上述文件的 SHA256 已写入机器可读协议。任何字节变化都必须使锁定或裁决失败。

禁止重新打开 protected raw arrays、预测、评价指标、implant/defect 数组，以及 MUG500+ B-series/craniotomy 数据。

## 4. 独立来源凭据

来源凭据固定以下公开信息：

| Dataset | 报告来源 | 主要参考 |
|---|---|---|
| MUG500+ | Medical University of Graz 临床常规 head CT | `10.1016/j.dib.2021.107524` |
| SkullBreak / SkullFix | CQ500 public head CT collection | `10.1016/j.dib.2021.106902` |

来源、机构和国家均不同，因此公开元数据支持两个 acquisition cohort 相互独立。

但来源凭据不能单独证明几何零重复，必须同时满足 exact-hash 与 high-resolution geometry 条件。

## 5. 按来源分层校准

对每个具有真实 repeated-source positive pair 的来源分别计算：

\[
Q^{+}_{0.99,d}(m),\qquad Q^{-}_{0.01,d}(m),
\]

其中 `d` 是 source domain，`m` 分别为 normalized symmetric CD-L1 和 HD95。

来源域通过条件为：

\[
Q^{+}_{0.99,d}(m) < Q^{-}_{0.01,d}(m)
\]

并且两个指标必须同时满足。

固定样本数如下：

| Domain | Positive pairs | Negative pairs | 是否要求分离 |
|---|---:|---:|---|
| MUG500+ | 125 | 125 | 是 |
| SkullBreak | 134 | 134 | 是 |
| SkullFix | 0 | 100 | 不适用 |

SkullFix 每个 source skull 只有一个 point sample，因此不得人为拆分或重采样后冒充独立 positive pair。它的 negative pairs 只用于诊断分布，不定义 duplicate envelope。

严禁再次汇总不同来源的 q99/q01 极值。

## 6. 几何裁决

跨数据集候选固定为 v2 已生成的 1250 对：

- MUG500+ 对 SkullBreak：625；
- MUG500+ 对 SkullFix：625；
- 每个 MUG source skull、每个 protected dataset 固定 descriptor rank 1--5。

duplicate-like envelope 只由 MUG500+ 同源 positive calibration 定义：

\[
CD \le Q^{+,MUG}_{0.99}(CD)
\quad\land\quad
HD95 \le Q^{+,MUG}_{0.99}(HD95).
\]

选择 MUG positive envelope 的原因是每个跨数据集 pair 都包含一个 MUG source；它回答候选是否已经接近“MUG 同一 source 的独立采样”水平。该阈值只来自同源 positive controls，不使用跨数据集结果拟合。

自动通过要求 duplicate-like candidate 为 0。不得根据裁决结果删除个别 MUG 病例后重新计算。

## 7. 自动门控

只有以下条件全部满足时，v2.1 才能通过：

1. v1/v2 与 v2.1 输入 SHA256 全部匹配；
2. 独立来源凭据通过；
3. exact hash intersection 为 0；
4. MUG500+ 域 positive q99 与 negative q01 在 CD、HD95 上均分离；
5. SkullBreak 域 positive q99 与 negative q01 在 CD、HD95 上均分离；
6. 1250 个冻结候选中 duplicate-like candidate 为 0。

通过只意味着允许生成独立的 `100/25` source-skull data lock。训练仍保持关闭，直至该 data lock 自身完成、校验并冻结。

任一条件失败时，D3 继续锁定，且只能进入人工 source-level review 或新的显式协议修订。

## 8. 禁止事项

- 改写或删除 v1/v2 结果；
- 使用跨数据集候选反向拟合阈值；
- 再次混合不同来源的校准极值；
- 为 SkullFix 虚构 positive pairs；
- 裁决后删除疑似病例再运行；
- 使用 overlap 结果选择模型或训练设置；
- 在独立 `100/25` data lock 前启动 D3 训练。

## 9. 当前状态

当前状态为 `preregistered_not_adjudicated`。

此文档及机器可读 JSON 只完成规则冻结；尚未执行 v2.1 裁决，也未允许生成 100/25 split。
