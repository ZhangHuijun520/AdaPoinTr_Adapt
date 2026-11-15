# SCQ-DAC R0／R1单次诊断：执行与结束观察

日期：2026-11-15。状态：**本次授权的唯一一次诊断已结束，待正式只读冻结审计。**

本次授权对应完整request SHA256：`129afea067a01802185719480591845e5918d52c4d28b9ec675012b1794e14a8`。授权根据本轮用户消息及其上一条唯一完整哈希对应，原request、科研源码、权重和资源阈值未改变。

## 1. 实际执行

- 重验当前 `qx2k0r-0` 身份/资源、冻结代码/provider、20个输入、四个上传文件及新目标不存在性通过。
- 重新流式核验归档30个成员，再按冻结映射不覆盖安装28个文件；两个恢复权重采用新路径，未回填已清理旧日志。
- 按单向顺序材料化授权回执 → 回执SHA → runtime → 单次launcher；实际installed authorize()入口通过，未在该检查中导入torch或模型。
- 原始文件字节用于运输，远端调用全部在本机检查长度和Python3.8语法，最大2039字节。唯一tmux启动前已落单次attempt claim。
- 没有重试、resume、训练、BNCal、GT几何评分或自动候选裁决。

## 2. 结束观察

| 项目 | 观察 |
|---|---|
| 退出码 | 0 |
| 固定tmux | 已退出 |
| worker | 已不存活 |
| 完整Native forward | 20 |
| 额外decoder-only | 40 |
| decoder总调用 | 60 |
| 原第一头 | 20 |
| 第二头新／旧proposal | 20／20 |
| 病例采集NPZ | 20份 |
| loss／backward／optimizer.step | 0／0／0 |
| Native重放 | 程序按固定atol/rtol完成；未触发停止 |
| 状态／RNG | 程序报告C/D两模型前后一致 |

输出目录：`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_DAC_R1_frozen20_20261115_v1`

程序报告生成归档 `development_predictions_v1.tar.gz`，13,610,252 bytes；报告SHA256为 `04c7b4fa54d0039c2502726b4eae284d093519b6ba91846c888646fc819d51ec`。这些哈希与计数来自本次状态回读，尚未进行独立完整冻结复核。

日志含已有timm导入弃用提示及Mamba/Triton确定性提示，没有据此升级环境；模型参数、状态及数值策略仍按冻结合同检查。日志中的历史配置类名/attn字符串不代表本轮更换了架构，实际factory身份和原生参数量由入口验证。

## 3. 下一步边界

建议下一步单独授权正式只读post-diagnostic freeze audit：重新核验输出全集、归档/成员哈希、调用claims与病例计数、输入/权重身份、状态/RNG以及资源证据。当前观察不代替该审计，也没有判断DAC是否值得训练。

通过后再下载、核验本机包并限定进行离线机制/几何解释。GT不得进入模型推理规则。当前request已消耗，不得再次执行。
