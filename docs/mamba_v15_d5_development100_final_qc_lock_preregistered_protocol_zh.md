# Mamba v1.5 D5 development100 最终 QC 数据锁预注册协议

> 本锁只汇总三个已冻结 development 批次，不读取 proposal confirmation 或 completion holdout。

## 必须同时通过的条件

- 三批 receipt 和 `files.sha256` 完整，批次状态均为 QC pass。
- 100 个来源与冻结 `d5_development100_ids.txt` 精确双射。
- 100 个 STL 重新计算的 SHA256 与 extraction manifest、QC CSV 完全一致。
- D5 内部文件 SHA256 与规范化表面指纹均无重复。
- D5 与既有 D3 healthy125、D4 source100 的文件 SHA256、表面指纹和来源 ID 均无重叠。
- 两个 sealed 分区在执行前后均为零文件。

## Batch 003 转换说明

Batch 003 receipt 的通用 `next_step` 文案不构成额外批次授权。本最终锁在不改变任何几何结果或门控结论的前提下，将其正式替换为 development100 全局 QC lock。

## 成功后的权限

仅允许准备下一阶段 D5 合成数据与来源四折协议。合成生成、模型实现、训练、候选选择和所有 sealed/protected 访问仍保持锁定。
