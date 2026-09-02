# Mamba v1.6 D6 source125 metadata-only acquisition 预注册

> 本阶段只冻结官方元数据、来源 ID、完整 ZIP 边界和下载计划，不读取任何 D6 geometry。

## 固定来源边界

- 官方健康 A-series：500 个来源。
- 排除 D3：125。
- 排除 D4：100。
- 排除 D5：150，包括 development100、proposal confirmation25 和 completion holdout25。
- prior union：375，pairwise overlap=0。
- D6 剩余：恰好 125 个来源、25 个完整 ZIP、0 个部分重叠 ZIP。

## 盲分区

剩余 25 个 ZIP 按编号范围进入五个预定义 macro strata。每层仅根据固定 salt、archive name、官方 MD5 和 size 选择 hash 最小的一个 ZIP 进入 proposal confirmation，其余进入 development。

- Development：20 ZIP，100 来源。
- Proposal confirmation：5 ZIP，25 来源。
- 分区后未使用 MUG500+ 来源：0。

不允许人工换源、QC 后替换或基于 geometry/model metric 分区。

## 当前权限

Lock 通过后只允许：

- 下载 development ZIP 并校验 MD5/size；
- 下载 confirmation ZIP 并校验 MD5/size；
- 冻结 D6 assignment-consistent R0/R1 mechanism protocol。

仍然禁止：

- 提取任何 D6 clear STL；
- D6 geometry QC、生成、server deployment；
- R0/R1 实现、训练或 dev；
- confirmation geometry；
- D6-B、SkullBreak confirmation 和 official test。

Development 提取必须等待 mechanism protocol、toy-case tests 和 zero-step preflight 的独立授权。Confirmation25 必须等待 R1 seed-0 与 seed-1 均通过 `400/400` 后才可能一次性打开。

## 终局语义

D6 使用完剩余 source125 后，当前 MUG500+ 未用来源池耗尽。D6 失败后不得创建 D7 并复用 D6 development；新假设必须转向新的独立数据来源和新的 representation family。

`400/400` 与 `100/100` 是有限测试集上的操作性门控，不是总体零失败证明。未来报告必须给出相应的一侧 miss-rate confidence bound。

