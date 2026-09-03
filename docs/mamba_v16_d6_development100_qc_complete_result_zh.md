# Mamba v1.6 D6 development100 模型无关 QC 冻结结果

> 本结果只冻结 D6 development 分区的数据完整性与来源边界，不生成派生病例、不运行模型、不训练，也不访问 proposal-confirmation 分区几何。

## 数据范围

- development batch：3。
- development source skull：100。
- Batch 001 / 002 / 003：40 / 40 / 20 个来源。
- QC 通过 / 失败：100 / 0。
- development 内部重复：0。
- 与既往 D3/D4/D5 几何重叠：0 / 325。
- 与既往来源 ID 重叠：0 / 375。
- proposal-confirmation：25 个 ID 仅作哈希绑定，几何文件保持 0 个。

## 冻结凭据

- development100 final lock：`mug500plus_d6_development100_qc_lock_v1`。
- `files.sha256` SHA256：`ba62bbe839e044d98a1f73be2fa2d0f2973ca771ab9e0911548dd77e81376ed2`。
- QC lock receipt SHA256：`97e26338d4d4bff743a20e0a830ca6e34f1c64f8dfd0de5115d91f22aec93cef`。
- overlap audit SHA256：`d469a24bcf7cef4cc0d3add2e98b03ef03d04bbdeb92f88d2d82d0d3a0b6f618`。
- assets CSV SHA256：`a1f06fba94158074a116033d62b37c267479c7f630a10bee94c0383980083d0c`。

## 结论与权限边界

D6 development100 数据完整性、三批次绑定、跨批重复门控和既往来源隔离均通过。下一步仅授权预注册并冻结 development400 合成生成与来源级四折协议；数据生成、梯度校准、训练、seed-1、D6-B、候选选择和 proposal-confirmation 访问均未由本结果授权。
