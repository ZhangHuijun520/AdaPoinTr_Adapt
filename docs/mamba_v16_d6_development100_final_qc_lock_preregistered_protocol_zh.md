# Mamba v1.6 D6 development100 跨批最终 QC 数据锁预注册

> 本锁只汇总三批已冻结的模型无关 QC，不读取 confirmation25，不生成病例，不运行模型。

## 输入与全局门控

- 三批 development 来源固定为 40 / 40 / 20，共 100 个来源。
- 逐一重验三份 batch hash chain、100 个 STL 文件 SHA256 与 QC pass 状态。
- D6 内 asset SHA256 和 canonical surface fingerprint 均不得重复。
- 与 D3 healthy125、D4 source100、D5 development100 共 325 个既有几何来源不得发生 asset 或 surface fingerprint 重叠。
- D6 100 个来源 ID 与 D3/D4/D5 全部 375 个既有来源 ID 不得重叠。
- proposal confirmation25 在运行前后必须保持 0 文件。

## 成功后的权限

全部 hard gate 为零时，只授权单独准备 D6 合成生成与来源四折协议。当前仍禁止 synthetic generation、gradient calibration、R0/R1 training、seed-1、D6-B、candidate selection、confirmation25 和 protected access。
