# H2四模型Native预测：兼容性核对与冻结范围

2026-11-07。四份训练request/正式审计及两折初始配对证据已核对，四个checkpoint的路径、大小和SHA256已绑定。只冻结本机元数据，未读权重、连接服务器、修改生产代码或运行预测。

## 固定科研范围

顺序C_AUX、C_COUPLE、D_AUX、D_COUPLE，每模型105例，总420次Native forward。每折两臂使用相同105病例，共210个独立病例、42个开发来源；420份预测不代表420个独立患者。开发/训练来源分离，归一化与已开放输入身份延续冻结清单。batch1，8192输入/8192输出，无warmup、TTA、loss、backward、optimizer或BNCal。

推理仅读取NPZ的partial数组，不能读取训练目标G。AUX/COUPLE各自按实际模式重建带范围头模型，再检查checkpoint的H2模式/常量/epoch99/update3900并strict加载。不加载优化器用于更新。原M0预测复用，不计入本次额外forward。

同一forward可保存coarse/dense几何及D-only条件量。H2在eval中不调用get_loss，不能为了日志重新forward；参数/持久BN及Python、NumPy、CPU、CUDA RNG前后必须相同。未设置条件override，禁止把未来delta0/置换混入Native预测。

每折每类型首例的精确ID已在新预测出现前冻结，未来COUPLE额外20次条件干预仍须单独授权，本420次Native范围不包含它们。主性能要等正式预测冻结及统一CPU评分，不能以训练loss或矩改善替代完整形状/接口结果。

## 入口不兼容与最小接入

现有H1两折预测入口仍要求H1启用，builder只创建无H2头的原M0；strict加载会出现H2新增键不匹配，旧checkpoint验证也不识别H2模式和常量。原计数210、2模型索引必须扩展为本次固定4模型420，允许同折两臂复用同输入，仍只有210个unique病例。原精确源码读策略只覆盖factory/encoder，还需覆盖真实H2 range/adapter加载路径，避免再次出现CPU facade未覆盖实际文件访问的问题。

所以正式execution request尚未创建。不能把仅含元数据的草案称为可执行待授权request，也不创建绑定错误入口的request。

建议一次限定implementation-only：一个H2四模型专用Native预测入口、一个人工CPU测试文件及本机P3。复用已有推理循环、文件策略和三个H2实现，不扩展通用框架。测试须覆盖人工checkpoint strict加载、模式/常量/键错误拒绝、实际源码读取策略、四模型420计数、状态/RNG和不读G。通过后再创建绑定最终实现哈希的AWAITING_EXPLICIT_USER_AUTHORIZATION request及运输范围；不重复GPU preflight。

## 现有交付

- H2_C_D_fourmodel_input_index_v1.json：精确四模型/420行输入及四份训练冻结证据。
- H2_fourmodel_native_prediction_protocol_v1.json：固定Native及额外干预边界。
- prediction_entry_compatibility_review_v1.json：实际源码缺口。
- minimal_H2_native_prediction_implementation_scope_v1.json：下一步限定接入范围。

本次没有执行或创建runtime、授权回执、launcher、server安装或预测目录，也没有评分或gate。
