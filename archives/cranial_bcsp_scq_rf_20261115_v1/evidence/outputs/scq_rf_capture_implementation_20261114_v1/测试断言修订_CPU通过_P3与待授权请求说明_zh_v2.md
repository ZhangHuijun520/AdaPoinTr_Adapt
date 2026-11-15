# SCQ-RF观察型采集：第32项修订、CPU通过、P3与待授权请求

_2026-11-14｜限定本机implementation-only收尾｜无服务器操作、部署或真实GPU forward_

## 1. 完成结论

本轮仅修正第32项人工启动合同断言，并使用全新输出目录执行一次新版CPU批次。**32项全部通过，本机P3完成，最终待授权request已创建。** 采集入口、模型、provider、生产守卫及前31项测试未改变；旧失败批次和旧测试原字节保留。

CPU通过不代表原生Mamba／CUDA通过，也不代表真实Memory重查询已证明有信息价值。真实十例采集未执行。

## 2. 断言修订与验证

新增[test_scq_rf_observer_cpu_v2.py](test_scq_rf_observer_cpu_v2.py)，输出到`artificial_cpu_batch_v2`。除新版输出目录和第32项区块外，其余测试字节保持一致，记录见[static_review_v2.json](static_review_v2.json)及[test32_only_diff_v2.patch](test32_only_diff_v2.patch)。

第32项改为解析实际timeout命令参数，检查POSIX路径、三个控制文件参数、Python及入口路径、1800秒超时、2048字节行上限、目录创建先于重定向，以及正确的退出码`printf`格式。正常shell换行转义不再被误判为Windows路径。

本轮唯一一次新版CPU执行结果：[artificial_cpu_batch_v2/result_v1.json](artificial_cpu_batch_v2/result_v1.json)，32／32通过。使用真实冻结SCQ residual及初始化；外层encoder／decoder仍为人工fixture，不加载任何真实checkpoint或病例点数组。人工十例完整流程、第三次尝试注入失败即停、hook清理及无重试均通过。

采集入口哈希保持：

`678a6fffcba13a7b4dec354833fc8275bcd3081adffe5b4581673b977086e5c9`

本机P3：[implementation_P3_v1.json](implementation_P3_v1.json)。旧`P3_gap_review_v1.json`仍保存旧批次被阻断的历史事实，不覆盖为通过。

## 3. 待授权request

文件：[SCQ_RF_ten_memory_execution_request_v1.json](pending_request_v1/payload/SCQ_RF_ten_memory_execution_request_v1.json)

状态：`AWAITING_EXPLICIT_USER_AUTHORIZATION`；`execution_authorized=false`。

完整SHA256：

```text
51ee9e42bc29c93002b71c8449b59ed14453aeb6d57cda242857e045cd536945
```

冻结范围为阶段A已固定十例，C折7例、D折3例，两份S最终checkpoint；每例一次eval forward并在Q1处额外查询一次N1。总计10 forward／10额外KNN，0 loss／backward／step／BNCal／warmup／retry。只采集实际Memory、z、Qraw、Q1、delta、N0／N1及描述量，与同病例冻结Native预测核对，不安装RF第二头或读取GT几何。

资源保持30分钟、RSS8 GiB、torch峰值20 GiB、SMI22,528 MiB、输出2 GiB、空闲磁盘至少4 GiB。失败立即停止，不自动重试或进入训练。

## 4. 运输文件及安装边界

已冻结本机运输包，目录为：

`E:/Codex/2026-06-06/mamba-ccf-c-1-high-resolution/outputs/scq_rf_capture_implementation_20261114_v1/pending_request_v1`

四个文件：

1. `bcsp_scq_rf_ten_memory_pending_20261114_v1.tar.gz`
2. `bcsp_scq_rf_ten_memory_pending_20261114_v1.tar.gz.sha256`
3. `bcsp_scq_rf_ten_memory_pending_20261114_v1.tar.gz.bytes`
4. `bcsp_scq_rf_ten_memory_pending_20261114_v1.tar.gz.contents.sha256`

压缩包大小1,021,245字节，SHA256：

`47ded0d089350fbbd5f00c2e8fdbcb0d19d563dd686fa4e626e7c93fae5b020a`

包含17个拟不覆盖安装文件及1份安装映射，共18个归档成员，已逐字节回读核验。十份Native预测参照直接从已冻结本机归档复制并核验哈希，不解码数组重算结果。CPU人工q／a／r及fixture点集没有打包。

拟安装根为`/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_memory_20261114_v1`，仅是冻结映射，当前未安装。待执行时必须重验上传包、所有新目标及控制／输出路径不存在，并核对所有复用代码、provider、环境、输入、权重和预测参照的精确身份。

## 5. 当前尚未发生的操作

本轮没有连接服务器、上传、安装、GPU调用、真实forward、checkpoint加载、训练或BNCal。未材料化真实授权回执、runtime config、launcher、单次claim或tmux会话。

请求绑定此前已观察的`zbpgzu-0`及其GPU身份，但本轮没有重新确认在线与资源状态。安装／执行前必须新核验，身份漂移时停止，不静默修改本request。必须先对上述完整request SHA256取得单独执行授权，才能按单向顺序材料化执行内容。

交付检查：[delivery_receipt_v1.json](pending_request_v1/delivery_receipt_v1.json)、[local_validation_v1.json](pending_request_v1/local_validation_v1.json)。
