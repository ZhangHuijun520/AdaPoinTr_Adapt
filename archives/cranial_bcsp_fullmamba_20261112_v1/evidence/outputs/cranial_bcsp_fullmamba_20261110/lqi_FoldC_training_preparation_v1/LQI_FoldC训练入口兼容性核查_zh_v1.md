# LQI Fold C训练入口兼容性核查与请求准备

结论：**既有F0训练入口与bridge不能直接执行LQI；待授权训练request尚不具备生成条件。** 本轮仅本机只读核查及文档准备，没有修改训练源码、运行CPU测试、连接服务器或启动训练。

已发现的精确阻断：

1. `bcsp_f0_training_entry_v1.py`的variant、源码PINS及模型导入分派仍为F0，替换文件路径或哈希不足以支持LQI。
2. 同一入口的`validate_admission`锁定旧F0回执/审计结构与4F+6decoder调用合同。LQI已正式冻结的证据是2F/2loss/2B，需绑定其真实审计、construction及completion，不得改名伪装为旧F0。
3. `bcsp_f0_runtime_adapter_v1.py`的`forward_loss`和`train_lifecycle`都锁定旧模型版本／准入状态。需要专用版本，而不是放宽为任意Mamba或直接绕过守卫。
4. 身份、模型版本及trace/日志语义应明确记录LQI交错序列；历史prefix_suffix字段若保留仅作兼容名，不得误称global prefix布局。原coarse/dense几何日志计算仍可复用。

首运行范围已准备：Fold C、seed0、8k→8k、315病例/63来源、batch8、100次遍历，每次39批，共3900更新/31200曝光/300丢弃。保持原静态优化器、学习率与BN合同、QC和完整顺序计划；从相同初始化构造，不加载F0最终权重继续训练。资源维持RSS8GiB、Torch20GiB、SMI22528MiB、输出2GiB、磁盘余量4GiB、最长86400秒。

本轮验证的是既有本机冻结元数据，没有重新检查服务器当前315份点集或可用资源，不能称服务器训练就绪已通过。下次最终request前应做限定重验，不扩展库存框架。

最小后续实施范围集中为两个隔离生产文件（LQI专用entry及bridge）和针对性人工CPU测试/P3；decoder、factory、原训练runtime、数据与科研合同均不改。不重复GPU preflight。验证应覆盖完整authorize、模型分派和读取路径、错误F0/错误准入拒绝、初始化及顺序/计数/日志合同，避免仅查字段名而漏掉实际谓词。

按既定分阶段边界，本轮不自动进入这一新的implementation-only。通过该阶段后才能生成绑定最终实现哈希、状态AWAITING_EXPLICIT_USER_AUTHORIZATION的首个训练request；不会先写一个不可执行的request再补代码。

机器可读准备范围：`LQI_FoldC_training_preparation_scope_v1.json`。
