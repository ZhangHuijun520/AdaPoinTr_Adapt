# S-ref_C最小接入：CPU失败与P3缺口

2026-11-14。限定本机implementation-only。未操作服务器、部署、运行GPU、读取真实点云或checkpoint、启动训练或创建执行控制文件。

## 1. 当前结论

已新增S-ref_C隔离入口及最小bridge，静态差量审查通过。唯一一次人工CPU批次通过前35项，在最后的实际训练文件策略集成检查处失败，已停止。**CPU整批未通过，P3未通过，尚未创建最终训练execution request。**

失败首错为测试子进程中的：

```text
NameError: name 'utc' is not defined
```

我从生产`main`中提取嵌套`Policy`类到测试子进程时，仅为人工exec环境传入`base_policy`和`guard`，遗漏了`utc`。生产入口在定义该类前已创建`utc`，通过闭包供它使用；测试提取丢失了这个上下文。该失败有明确的测试harness原因，尚不能认定生产策略有错，但也不能据前35项通过跳过这一集成检查。

## 2. 已实施的限定适配

- [S-ref_C入口](bcsp_scq_rf_Sref_C_training_entry_v1.py)：改绑当前RF正式post-CUDA审计、5 forward／4 backward准入、S-ref第一run身份；拒绝旧B基线前置和其他臂／折。
- [最小bridge](bcsp_scq_rf_training_bridge_v1.py)：接受当前RF准入身份，继续委托原固定runtime，不改训练循环。
- 共有初始状态指纹包含原SCQ，与当前CUDA五次原生构造一致，仅排除RF第二头；S-ref明确禁止安装RF第二头。
- 原数据／QC／顺序、模型、loss、初始化、优化器、LR／BN、3900步和资源阈值不变。原runtime及metadata contract源码哈希未变。

静态AST差量限制在准入、授权、分派状态范围及身份日志四个函数；原数值生命周期不改。没有扩展通用审计、传输或GPU准备框架。

## 3. 前35项已通过内容

包含实际authorize路径对真实冻结元数据和当前RF准入的核验；100×39批次计划；variant／fold／输入数／seed／状态／授权／设备／哈希漂移拒绝；S-ref无需旧B基线；训练315病例路径与越界／重复拒绝；POSIX launcher及24小时外部超时；完整共有SCQ初态定义；原no-decay策略；人工模型的loss／几何日志分派；3900条日志最终化守卫及bridge委托和拒绝条件。

人工分派只做一次小模型forward／backward，没有optimizer step或3900步训练。失败的最后一项仍未完成“实际嵌套文件策略下的源码／初始化读取与训练专属NPZ守卫”集成证明。

完整已通过清单和首错见[CPU失败记录](cpu_entry_batch_v1/failure_v1.json)，子进程原始错误见[policy_stderr.bin](cpu_entry_batch_v1/policy_stderr.bin)。[P3缺口复核](P3_gap_review_v1.json)明确保持未通过。

## 4. 限定下一步

已确认计划要求一次CPU失败保存后停止，不自动修复重跑。本轮没有修复或再次测试。建议下一次仅授权：

**为测试子进程的人工exec环境补入已存在的`utc`对象，创建新版测试及新输出目录，执行唯一一次新版CPU验证；入口、bridge及生产代码保持不变。**

通过后完成新P3并生成绑定最终哈希的S-ref_C待授权request，无需重复GPU preflight。旧CPU失败证据不覆盖、不复用为通过记录。
