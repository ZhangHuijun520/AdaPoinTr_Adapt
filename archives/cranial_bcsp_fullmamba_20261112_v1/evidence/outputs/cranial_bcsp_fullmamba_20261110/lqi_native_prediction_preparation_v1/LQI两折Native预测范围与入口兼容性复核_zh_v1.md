# LQI 两折 Native 预测范围与入口兼容性复核 v1

日期：2026-11-11。状态：**范围已冻结，尚需专用入口适配；不是可执行 request，未授权或执行预测。**

## 目的与当前证据

取得 LQI 在与 F0 完全相同的两折开发病例上的 Native 预测，再以既有指标统一比较完整骨块补全及接口误差。两折训练完成、训练 loss 或 CUDA 准入通过，均不构成补全效果改善的证据。

本轮只读取本机源代码、索引和已冻结的审计元数据，不读取真实 NPZ payload、不加载 checkpoint、不连接服务器、不运行模型或评分。

LQI C、D 正式训练后审计各通过 42 项检查；训练 request 哈希均与审计一致。最终 checkpoint 各为 478810419 字节：

| 折 | checkpoint SHA256 | 已冻结训练合同 |
|---|---|---|
| C | `d8d819ffb9ed1f931c60f0ee96e9ae9c4093d61c73c2152a52f13b8cd95a0ddf` | 3900 updates／100 traversals／31200 exposures／300 drops |
| D | `2afd1b4540b856d4c829786729d8c2df80943edd65a0f01af412940fd973e5ed` | 同上 |

上述哈希继承正式服务器冻结审计，本轮没有重新读取服务器权重。

## 冻结的预测范围

- C、D 各 105 例，共 210 次 batch=1 Native forward；每折 21 来源，每来源五种既定缺损；不筛病例、不调参。
- 新索引逐行继承 F0 的病例顺序、来源、真实输入路径、大小、SHA256、归一化中心／尺度及目标数组摘要。只替换模型、输出标签和权重／审计绑定，并关闭旧机制诊断缓存。
- 保持 8192 输入、8192 dense 输出及 256 coarse；每例保存 coarse 和 dense，另记无 GT 的几何摘要、预测清单、调用日志与模型状态／RNG 指纹。
- 原数据目录名称与 Fold 字母看起来相反，必须依照冻结索引和 source/fold 证据使用，不按目录名称自行改路径。
- eval + inference_mode、FP32、TF32=false、既定确定性设置、实际 native Mamba 及既有 Python3.10 PointNet2 provider；不安装或编译依赖，不接受 fallback。
- loss、backward、optimizer step、BNCal、warmup、TTA 均为 0。预测只读取 partial；目标数组摘要仅作元数据绑定，不读取 GT payload。
- 资源上限沿用 F0 Native：7200 秒、RSS 8 GiB、Torch peak 20 GiB、设备显存 22528 MiB、产物 1 GiB、最低可用磁盘 4 GiB。失败立即记录并停止，不重试或替换病例。
- 不重复已通过的 GPU preflight，不执行旧 30 次 decoder-only 诊断，不产生原 F0 的 20 份 context／10 份全层 trace。

## 入口兼容性结论与最小适配

既有 `bcsp_f0_twofold_native_predict_v1.py` 不能原样执行 LQI：

1. `authorize()`、`validate_index()`、`FROZEN_MODELS` 固定 F0 request/index schema、标签、训练权重与审计。
2. `load_f0_builder()` 和精确源码读取绑定固定 F0 decoder/factory；`validate_model()` 固定旧 construction version。LQI 虽然 state_dict 形状、参数量与 F0 一致，但条件序列语义不同，不能仅换权重后仍使用 F0 factory。
3. 原索引校验强制旧 recipient/donor 选取及 20 context／10 trace；执行完成条件强制 240 数组文件。当前范围只需 210 份 coarse+dense 预测文件，必须同步调整完整集合和计数检查，保留全部病例及输入身份校验。
4. LQI 的兼容 trace 字段 `prefix_suffix` 已指向交错序列中的条件 query 出口，不是 F0 全局 prefix/suffix。当前不采全层 trace；后续也不得混用解释。

建议下一步单独授权：**新增 LQI 两折预测短入口＋针对性人工 CPU 验证＋P3**。验证应覆盖完整 authorize 路径、实际 LQI factory/decoder 加载路径与只读策略、错误 F0 路由拒绝、210 例索引与产物计数、状态／RNG合同和失败路径；不扩展通用框架、不修改模型或数据、不重复 GPU preflight。通过后再做必要的当前身份／资产／资源核对，创建绑定最终入口哈希的待授权 execution request。运行路径、安装映射和运输包在该阶段冻结；本文件没有预先材料化它们。

## 后续与冻结 F0 的统一评分

复用 F0 已冻结的 210 份 Native 预测，不重新运行 F0。LQI 预测需先经单独授权的正式冻结审计、下载和本机核验，再准备评分入口及其待授权 request。

以 fold、case_id、source_id、输入 SHA256 和归一化元数据严格配对，沿用冻结指标、分区、阈值及来源等权汇总，保留所有开发病例与退化病例。预测生成阶段不访问 GT；统一 CPU 评分阶段才按既定协议访问 GT。不得把训练 loss、无 GT 几何摘要或单例可视化当成最终性能结论。

当前仍未创建可执行预测 request、授权回执、runtime config、launcher 或 tmux 会话；未进行预测、评分、训练或 BNCal。

## 交付与可复核性

- `LQI_CD_Native_input_index_candidate_v1.json`：两折完整元数据及权重、训练审计、配对证据绑定。
- `LQI_CD_210_Native_prediction_scope_v1.json`：预算、禁止事项、资源、后续评分边界与最小入口缺口。
- `preparation_validation_receipt_v1.json`：本轮本机元数据校验结果。它不是 CPU 模型测试、P3 或实时服务器核验。
- `prepare_scope_v1.py`：只读元数据准备过程，输出采用不覆盖写入。

范围文件 SHA256：`716b7cbfc48eaa858776174ab01bb145cc00ced96f86c9fc46edaaf53f1e440c`。此为范围文件哈希，**不是 execution request 哈希**。
