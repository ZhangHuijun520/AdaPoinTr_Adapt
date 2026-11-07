# H2／M0三臂统一CPU评分：实施、人工验证、P3与待授权request

2026-11-07。状态AWAITING_EXPLICIT_USER_AUTHORIZATION。已新增一个专用评分入口及一个人工CPU测试文件；不修改旧H1评分入口及冻结指标源码。未执行真实评分、服务器操作、GPU或模型加载。

## 科学与数据范围

M0、H2_AUX、H2_COUPLE三模型臂，各210例；两个共享控制Nop_D、GT_8192各210例，共630模型行+420控制行=1050病例行，42来源x5臂/控制=210来源行。每折105病例/21来源，每来源固定五类缺损；保留frontoorbital。M0仅选旧C/D档案中的M0结果，旧T0成员不进入本次模型评分。

主比较H2_COUPLE-H2_AUX；次比较H2_COUPLE-M0、H2_AUX-M0分开输出。来源等权E P95主指标及原E/J/CD、覆盖率、reverse>20mm离群、严重几何及位置/紧缩风险定义保持不变。不计算bootstrap/p值/正式gate，不筛病例、不对齐GT或ICP，不重跑推理或条件干预。原指标文件SHA256：af938519125b25b6d22d862dd4967dabef3be6d97d38e60eb9995ee7e9ce9766。

H2 Native同forward日志仅用于离线尺度/位置诊断；GT半径只在评分副本计算，不进入推理。矩改善不代表形状/接口改善。两折既有checkpoint与归档身份保持冻结。

## 实现及验证证据

H2归档425成员/420预测、两个M0档案各215成员/210预测的读取合同已适配，严格校验成员、模式、case/fold、checkpoint/input SHA、frame、状态/RNG和固定coarse成员。新评分索引允许同210病例两臂共享输入但拒绝不一致框架/目标。共享控制只在每个病例循环计算一次。

35项人工CPU检查通过：真实数据仅用于索引/路径/哈希元数据合同，不读取真实预测或参考数组；实际原指标在两个解析人工病例x五模型/控制共10行计算。完整1050行编排复用这10行人工模板，验证210唯一病例、630模型/420控制、210来源行、六个分折pair、630病例差值、风险新增/挽救及失败即停。该编排验证不是1050次真实指标计算，也不证明研究结果。

原load_prediction_arrays、select_metrics、position_shape、risk_labels、stage_geometry、aggregate_source和CSV数值路径AST与父版一致；原指标源码完整哈希不变。测试还覆盖共享GT零CD、人工主/次方向、模式/frame/target/hash错误拒绝、undefined配对不丢弃、20mm/0.9边界和J coverage0严重判定。P3已绑定最终scorer/test/result/metric/protocol哈希。

预算按1050/840行在原4小时基础上冻结5小时（18000秒），外部18030秒；RSS8GiB、输出2GiB、线程2保持不变。此为新增CPU工作量预算，不改任何科学阈值。

## 最终request

完整SHA256：

```text
3531fa8ca3282a7896be7df2b501be0ec1687f0448ebe7a613d2414e32d4f2b3
```

文件：local_scoring_execution_request_v1.json。仅待授权，execution_authorized=false。绑定本机已核验的H2归档四文件、既有M0 C/D归档、210参考/210点集、冻结指标及CPU环境。

这是本机CPU任务，无需上传服务器。下一步须对完整request哈希单独授权唯一一次真实CPU评分；执行前重新核验所有绑定、CPU环境及全新输出/授权目录，再材料化单次授权和启动。失败即停，保留日志，不重试/resume或删病例。完成后仍须独立正式只读评分后冻结审计，再解读效果。

本次没有创建授权回执、进程claim或unified_scores_v1真实结果目录，没有运行真实评分或读取checkpoint，也没有自动进入下一阶段。
