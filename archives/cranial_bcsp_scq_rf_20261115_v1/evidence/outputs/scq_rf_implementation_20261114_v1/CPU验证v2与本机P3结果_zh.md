# SCQ-RF新版人工CPU验证及本机P3结果

日期：2026-11-14。授权范围：唯一一次本机人工CPU验证；不改实现或初始化、不连接服务器、不使用CUDA、不读取真实点集或checkpoint、不训练。

## 结果

唯一一次进程退出码为0，**59项检查全部通过**。测试计算约36.05秒，进程托管总耗时约40.22秒。保存产物的本机P3复核状态为`LOCAL_RF_IMPLEMENTATION_P3_PASS_ARTIFICIAL_CPU_ONLY`。

授权绑定的范围SHA256仍为`d512ffbb57622357a14e32c96befbe5b17337d01ca7d3ffa8ecb538b0d49c5f2`；最终测试SHA256为`7e5f4e8573d9a2a4d1046dada1e0e5260004ca51980d4342b3c0d24f23061924`。

原v1失败证据保留。RF两份生产候选源码、原SCQ与继承源码、初始化二进制及清单均与冻结记录一致。没有将原v1失败记录改成通过。

## 梯度与原失败问题的验证

人工完整模型副本为第一头输出weight设置固定非零值后，原8192点完整coarse＋dense损失反传到Q2、原SCQ头和新增RF头。逐参数梯度在断言前落盘，独立回读检查全部有限且非零。

| 梯度对象 | 梯度L1 |
|---|---:|
| Q2 | 1.861165 |
| scq.W1.weight | 191.270462 |
| scq.W1.bias | 0.174162 |
| scq.W2.weight | 72.901062 |
| scq.W2.bias | 1.101948 |
| rf.V1.weight | 53.294430 |
| rf.V1.bias | 0.048372 |
| rf.V2.weight | 25.462053 |
| rf.V2.bias | 1.101952 |

另保留第二头零初态测试：V1梯度为零、V2梯度有效，符合零输出层的链式法则。非零V2诊断态下，梯度到达V1及连续M／F／z／Q1。以上是人工可导性检查，不是效果指标。

## 其他通过的关键合同

- 两臂共有参数、初始化state及随机流一致；各新增231,171参数。
- Static沿用N0但在Q1重算几何，Requery使用同一KNN在Q1重查询；已覆盖邻域相同和改变的人工情形。
- Q2进入实际query-MLP、位置编码、排序、self／cross KNN、FC条件、dense中心、返回coarse及原损失；原coarse和dense损失各调用一次。
- no-decay回归调用精确继承的分组函数，验证显式矩阵标记、向量、bias、普通矩阵和冻结参数；RF适配保留共有参数豁免，新增两头weight／bias分组正确。
- 完整反传后没有optimizer step；人工模型参数未更新，临时BN buffer已恢复。没有自动重试。

## 证据与适用边界

- [59项CPU结果](cpu_batch_v2/result_v2.json)
- [逐参数梯度](cpu_batch_v2/gradient_evidence_v2.jsonl)
- [继承no-decay证据](cpu_batch_v2/inherited_no_decay_evidence_v2.json)
- [共有参数分组证据](cpu_batch_v2/shared_optimizer_policy_evidence_v2.json)
- [本机P3复核及哈希](P3_implementation_v2.json)
- [单次进程退出记录](CPU_validation_authorized_execution_v2/process_exit_v2.json)

本次完整forward／loss使用原母版计算类、LQI decoder和FC head，但构造器、grouper／FPS及Mamba mixer使用保留的人工替代。CPU结果不证明原生Mamba／PointNet2 CUDA、完整batch8 loss／backward、显存预算、原生参数总量或科研效果通过。实际SSM对象的no-decay清单仍须在原生模型准入中核对。

下一步可准备RF模块专用人工CUDA短入口及待授权request，固定**5次forward／4次完整loss／4次backward／0次optimizer step**。本轮没有创建CUDA或训练执行请求，也没有运行任何GPU任务。
