# LQI Fold C训练入口、CPU验证、P3与待授权request

本轮限定implementation-only及请求准备完成，未部署、未运行GPU或训练。

新增两个隔离生产文件：`bcsp_lqi_training_entry_v1.py`与`bcsp_lqi_runtime_adapter_v1.py`。适配真实LQI模型版本、准入/正式审计证据结构及哈希链、模型导入与读取目录、训练分派和日志语义。原F0入口、bridge、LQI decoder/factory、数据、loss及原3900-step runtime保持不变。

CPU证据：一批25项完整authorize/真实LQI surrogate factory分派、人工8k batch8 forward/backward、几何日志和拒绝合同检查通过；另7项实际bridge人工调用/拒绝检查通过，没有optimizer step或实际训练。随后仅补入已准入LQI源码目录到main的read_roots；25项批次所测authorize/dispatch/lifecycle函数不变，差量已独立记录，不能宣称25项曾执行最终main。最终入口还通过一次使用真实冻结元数据与准入证据的完整authorize复核，授权对象只在本机内存中存在，未材料化真实回执/runtime。

本机P3为`training_entry_P3_v1.json`，保持CPU人工loss/mixer与runtime spy的局限披露；实际原生CUDA已由前一步正式审计证明，不重复GPU preflight。本轮仅只读重验九个元数据/复用工具哈希及315个训练点集存在、路径和大小；没有解码点集数组，完整315 payload SHA256须在实际授权执行前重验。

首运行固定Fold C、seed0、8k→8k、315病例/63来源、batch8、100次遍历、3900更新、31200曝光、300丢弃；复用原初始化种子、批次顺序、优化器/LR/BN、数值及资源合同。从同初始化重新训练，不从F0最终权重warmstart。不依据本次结果调参或筛病例。Fold D另行分阶段准备。

最终request状态：`AWAITING_EXPLICIT_USER_AUTHORIZATION`。

完整SHA256：`b616a762783fd4f43af4467c6c47e41e73aa40a24fac223317e710ee7372825e`。

上传当前目录的四文件到`/home/jovyan/`：

1. `bcsp_lqi_FoldC_training_pending_20261111_v1.tar.gz`
2. `bcsp_lqi_FoldC_training_pending_20261111_v1.tar.gz.sha256`
3. `bcsp_lqi_FoldC_training_pending_20261111_v1.tar.gz.bytes`
4. `bcsp_lqi_FoldC_training_pending_20261111_v1.tar.gz.contents.sha256`

包内11个拟安装文件，不含数据、checkpoint或依赖。安装映射为本机`frozen_transport_installation_mapping_v1.json`。request的implementation字段包含复用文件，不能把未安装的入口/bridge或新证据当成已有资产提前读取；部署前应按映射逐一分流核验包内/复用内容，并评估完整安装前合同。

上传后须单独明确授权上述完整SHA256，才可按冻结范围不覆盖安装、生成单向回执/runtime/launcher并启动唯一一次训练。失败即停，不自动重试或resume；不进入BNCal或evaluation。
