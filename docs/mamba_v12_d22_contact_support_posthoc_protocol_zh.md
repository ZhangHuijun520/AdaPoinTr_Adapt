# Mamba v1.2 D2.2 contact-support replay 事后诊断声明

> 本分析在 D2.2 Round A 已经因 `nonfinite` 安全门控失败后声明。它是
> observation-only、selection-inert 的 post-hoc 机制诊断，不得改变 D2.2
> 的冻结负结果，不得选择 R1/R2，不得解锁 Round B。

## 已知事实

- D2.2 的 12 个 Round-A 运行已经完成；
- R0/R1/R2 的灾难数分别为 45/37/36；
- R1、R2 唯一失败门控均为 `nonfinite_case_count == 0`；
- nonfinite 数分别为 2/2/3，均由主评估定义 2 mm 下
  `predicted_rim_points = 0` 引起；
- 三个候选的零接触病例集合完全不重叠；
- `winner = null`，Round B 已禁止；
- confirmation20、旧 monitor、official test 尚未访问。

## 固定分析范围

- 数据：原冻结 `development84` 的 A-D 四折 dev 集；
- 模型：冻结的 R0/R1/R2、seed-0、12 个 BNCal checkpoint；
- 病例：每候选 420 个病例，不只分析 7 个已知失败病例；
- 阶段：coarse 与 dense；
- 接触 band：0.5、1、2、3、4、5 mm；
- 距离统计：min、P1、P5、P50、P95、max；
- 主完整性检查：dense 2 mm 支撑点数必须逐病例严格重放冻结 CSV。

## 诊断问题

1. 零接触病例需要多大的 band 才恢复局部支撑？
2. dense 零接触时 coarse 是否已经存在接触支撑？
3. R1/R2 是消除还是迁移病例级接触缺失？
4. 支撑转移是否集中于特定 defect type 或 fold？

## 明确禁止

- 不得把 2 mm 主指标替换成更宽 band；
- 不得事后放宽 nonfinite 门控；
- 不得据 replay 选择 R1/R2；
- 不得扫描 loss 权重、deadzone、rim band 或 trust tolerance；
- 不得启动 D2.2 Round B；
- 不得访问 confirmation20、旧 monitor 或 official test。

## 输出解释

replay 只用于判断失败发生在 coarse、dense refinement 还是 2 mm 接触边界附近，
并为未来独立编号的新实验提出病例级接触存在性保证或安全 fallback 假设。任何新方法
都必须重新声明协议，且不能把本次事后分析包装成预注册验证结果。
