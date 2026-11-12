# LQI 两折 Native 预测：授权执行与完成观察 v1

日期：2026-11-11。状态：**本次唯一预测已结束，待单独授权正式只读预测后冻结审计。**

## 授权与执行边界

用户明确授权上一条 request 对应的不覆盖安装及唯一一次 210 次 Native 预测，失败即停、不自动重试。request 完整 SHA256：

`cab2831f27913766d7009101ec86d9a6e642a40b9330359dbfc8ff5928610fb6`

前一次安装调用曾被自动审批拒绝，没有执行；上传后四文件只读核验通过。本次在用户进一步明确授权后通过工具审批，才执行真正的安装和单次启动。不得将被拒绝的调用算作一次 GPU 尝试，也不得把此前缺少上传文件的只读检查算作模型运行。

## 安装和启动观察

- 容器：`shu-common-25721452-notebook-zv9bqd-0`，UID 1000。
- 绑定 GPU：RTX 4090 D，UUID `GPU-41b45aa3-f5e3-e609-53cb-9c48bc7716ed`；启动前显存使用 0 MiB。
- 四个上传文件匹配；运输包 SHA256：`51780c72d141fe1a9b38a9c5e94eca21138b9d5990c37bc2efacc587894797b5`。
- 安装前确认新安装根、输出根不存在，父目录安全，固定 tmux 会话不存在。
- 重新哈希复用代码、provider、环境元数据、准入文件、两个 checkpoint 及 210 个输入文件；不解码目标数组、不反序列化权重完成就绪核验。安装前后本次操作累计哈希 1702815537 字节。
- 按冻结映射以不覆盖方式安装 14 个文件并回读校验。另保存精确哈希绑定的单次操作控制脚本；它用于安装及启动，不是新增模型实现。
- 授权回执→计算 SHA256→runtime→计算 SHA256→launcher→单次 claim→唯一 tmux，按单向顺序完成。未重启或重试。

安装根：`/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_lqi_CD_native_prediction_20261111_v1`

输出根：`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/LQI_CD_native_development_20261111_v1`

tmux：`bcsp_lqi_CD_native_eval_20261111_v1`；worker PID：38371。

## 结束观察

`completion_observation_v1_result.json` 显示：

- 退出码 **0**；固定 tmux 已不存在，worker 已退出。
- `inference_complete.json`：`LQI_CD_210_NATIVE_FORWARD_COMPLETE`，210 次 forward。
- `completion.json`：`PREDICTIONS_ARCHIVED_AWAITING_FREEZE_AUDIT`，request 哈希匹配。
- 210 份预测 NPZ、210 条 forward attempt、210 条 inference manifest、423 条资源记录；context 和 trace 均为 0。
- 已形成预测压缩包及 `.sha256`、`.bytes`、`.contents.sha256` 三个校验文件。
- 最后一次资源记录全部通过：约 58.49 秒，RSS 1897435136 字节，Torch peak allocated 241075712 字节、reserved 281018368 字节。这里只报告最后一条记录，不将其设备显存值冒充全程峰值。

日志中的 timm 导入弃用和 Mamba/Triton 确定性提示为警告；本次退出码及完成状态通过。静态母版配置日志仍出现 Transformer 配置名，不能单凭日志名称判断最终替换后的模型；实际 construction、LQI 模块身份和状态／RNG 证据应在正式冻结审计中核验。

## 证据边界与下一步

本次为授权执行后的状态观察，**不代替正式预测后冻结审计**。尚未独立重新哈希全部预测／归档、逐例复核数组形状与坐标绑定、完整集合和状态／RNG 指纹，也未下载预测或运行评分。

下一步单独授权有界只读 post-prediction freeze audit，核验 210 份预测、完整文件集合、哈希、两折各 105 例、调用计数、construction、状态／RNG 和资源证据；不运行任何额外 forward。通过后再下载压缩包及三个校验文件，本机核验后准备与冻结 F0 的统一 CPU 评分。

当前不能判断 LQI 是否改善补全精度或接口吻合。未运行训练、BNCal、额外机制诊断或 F0 再预测。
