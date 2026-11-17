# TRACE D0最小运输包与不覆盖安装映射

日期：2026-11-17。状态：仅本机冻结完成；没有连接服务器、上传、安装、执行测试或启动GPU。

本机目录：

`E:/Codex/2026-06-06/mamba-ccf-c-1-high-resolution/outputs/trace_D0_implementation_20261117_v1/pending_transport_v1/`

## 手动上传四文件

建议上传至服务器`/home/jovyan/`，保持原文件名。只上传以下四个文件；无需上传本机payload目录或CPU测试fixture。

| 文件名 | bytes | SHA256 |
|---|---:|---|
| bcsp_trace_D0_minimal_pending_20261117_v1.tar.gz | 32389 | 2ae574bcb691291f7472096ba9e79bb33eb0c152563dcb3f8e808f66043b0734 |
| bcsp_trace_D0_minimal_pending_20261117_v1.tar.gz.sha256 | 115 | f9b86b9f8bda6172c757b1aefb83b7a2b10bb007e0f7305459eac2354fb832fb |
| bcsp_trace_D0_minimal_pending_20261117_v1.tar.gz.bytes | 6 | 960008fd87837e27ad34e40095ae6002c8c0c6f50d2e28c02b28ed5a67cf20f0 |
| bcsp_trace_D0_minimal_pending_20261117_v1.tar.gz.contents.sha256 | 713 | 9294b2d4bba09c4f1881ed7827236ae1514ae074e97b6ce6ad67d1ed07df08e9 |

## 包内范围

归档共7个普通文件，已逐成员回读核验：6个拟安装文件，以及1个只供核对、不安装或执行的`installation_mapping_v1.json`。

6个拟安装文件为：

- `bcsp_trace_D0_entry_v1.py`
- `bcsp_trace_D0_observer_v1.py`
- `bcsp_trace_D0_analysis_v1.py`（仅保存实现；GPU诊断不调用CPU分析）
- `TRACE_D0_preparation_scope_v1.json`
- `TRACE_D0_P3_v1.json`
- `TRACE_D0_execution_request_v1.json`

唯一拟安装根：

`/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_trace_D0_20261117_v1`

映射冻结77个复用文件引用，包括既有代码／配置／provider／依赖、4个checkpoint及40份开发输入。这些复用文件不在运输包中，不覆盖、不重新安装。本轮没有重新连接服务器确认它们的当前状态。

包内不含权重、真实或人工预测数组、测试fixture回执、生产授权回执、runtime、launcher、单次claim或安装脚本。P3／准备材料中的Windows路径仅为本机证据位置，不得转换为猜测出的Linux路径执行。

## 后续边界

上传完成后，仅进行单独授权的只读上传核验。安装前必须重新核验身份、GPU、上传包、复用资产、全部目标不存在以及父目录安全；另获安装授权后才可按映射排他创建目录并以`xb`写入，异常停止，不覆盖或自动清理。

正式request的SHA256保持不变：

`7ad5a27aee302b877af7903b00da107c47560250d18135566315609b12a01b0f`

状态仍为`AWAITING_EXPLICIT_USER_AUTHORIZATION`。本次冻结不授权执行80次forward、后续CPU分析、G3或训练。

完整映射见同目录`installation_mapping_v1.json`；逐文件身份及本机核验记录见`transport_freeze_receipt_v1.json`。
