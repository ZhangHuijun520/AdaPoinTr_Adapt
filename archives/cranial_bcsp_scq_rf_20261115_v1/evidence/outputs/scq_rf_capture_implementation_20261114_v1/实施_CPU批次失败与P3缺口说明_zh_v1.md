# SCQ-RF观察型采集入口：实施、CPU批次失败与P3缺口

_2026-11-14｜implementation-only｜一次人工CPU批次后失败即停｜未操作服务器或运行真实病例_

## 1. 当前状态

已新增观察型采集入口和针对性CPU测试，完成静态审查并执行唯一一批人工CPU验证。**前31项通过，第32项失败，整批不通过。** 因此不形成P3通过结论，不创建十次真实forward的待授权execution request，不制作部署运输包。

失败证据为[artificial_cpu_batch_v1/failure_v1.json](artificial_cpu_batch_v1/failure_v1.json)。本轮没有自动修复或重跑。

## 2. 已完成的限定实现

- [观察入口](bcsp_scq_rf_memory_capture_v1.py)：复用冻结SCQ Native工具的模型构建、checkpoint读取、partial-only数据读入、状态／RNG、原数值及资源守卫。
- 通过原SCQ模块的前／后hook观察实际Memory坐标、特征、query生成前全局z、Qraw、delta0、Q1及N0；hook不替换模型返回值，退出时移除。
- 每例只额外执行一次同provider的Q1处KNN，形成N1；按同一个Q1分别构造Static／Requery描述量，不安装RF第二头。
- 限定两折S模型、固定十例、十次forward、0 loss／backward／step／BNCal／warmup／retry。
- 核对采集结果与冻结Native预测的Qraw／delta／Q1／dense，继承normalized最大差1e-6及world最大差0.001 mm；不自行放宽。
- 保存实际张量、邻域重合及条件差异，不读取GT或高分辨率参考数组，不做科研评分。

原母版、SCQ、LQI、provider及既有预测入口均未修改。新增[准备工具](../../local_tools/prepare_scq_rf_capture_20261114_v1.py)仅生成本机候选元数据和测试上下文，没有创建真实执行内容。

## 3. CPU验证的证据范围

[测试文件](test_scq_rf_observer_cpu_v1.py)在已明确使用的本机PyTorch CPU环境执行一次，环境为Python 3.9.21、PyTorch 2.5.1、NumPy 1.26.4，CUDA_VISIBLE_DEVICES为空。

使用真实冻结SCQ residual类与既有初始化资源；外层encoder／decoder为确定性的人工fixture。没有读取任何训练后的checkpoint、病例D／GT数组或使用GPU。它验证观察接口，不能替代完整原生Mamba／CUDA验证。

已通过的前31项覆盖：十例及权重元数据、额外次数和GT条件拒绝、完整授权／单向runtime校验、观察前后输出／参数／CPU RNG不变、实际输入捕获、张量键／形状、原KNN加一次新KNN、Qraw＋delta关系、两描述量统一以Q1为中心、邻居变化fixture、错误索引拒绝、partial-only读入、异常及重复调用时hook清理、十例完整流程、两模型状态／RNG、逐例claim、第三次注入失败即停且不启动下一模型、生产CPU绕过拒绝。

人工流程中的十次成功forward及三次注入失败尝试都是fixture计算，不是十次真实病例诊断授权的消耗。若未来形成真实请求，仍需独立执行授权。

## 4. 第32项失败的限定原因

失败断言检查整个启动脚本不得包含任何反斜杠：

```python
'\\' not in launcher
```

只读渲染核对确认，唯一反斜杠位于既有正确的退出码落盘格式：

```bash
printf "%s\n" "$rc" >.../exit_code.txt
```

这是shell换行转义，不是Windows路径泄漏。本次最长脚本行956字节、目录创建先于重定向、1800秒timeout三项均为true；整脚本反斜杠禁令为false，导致第32项失败。

详见[test32_readonly_diagnosis_v1.json](test32_readonly_diagnosis_v1.json)。该检查仅渲染文本并拆分原断言，不运行launcher，不重跑测试，也不能代替完整部署／启动合同通过。

## 5. P3缺口与停止依据

当前P3状态为`BLOCKED_BY_CPU_CONTRACT_FAILURE`。失败不是真实Mamba数值问题、科研效果失败或服务器连接失败；是测试准入条件范围过宽。但它仍是本次正式CPU批次失败，不能在记录中改为通过。

已确认的[正式计划v2第5.3节](../../docs/cranial_bcsp_scq_rf_20261114/Cranial_BCSP_FullMamba_SCQ_RF_下一阶段正式实验计划书_zh_2026-11-14_v2.md)规定：“一次失败保存结果后停止，不自动修复重跑。”因此本次保留入口和测试原字节，不自动进行第二批。

建议下一步仅授权：**修正第32项人工启动合同断言的范围，明确区分POSIX路径与shell格式转义，保留行长、父目录、重定向、超时和退出码检查；入口及生产守卫保持不变，再执行一次新版CPU验证。通过后完成P3并创建待授权request。**

这不需要修改模型、provider、采样、科研公式、checkpoint、资源阈值或通用框架。

## 6. 当前未执行和未创建的内容

没有服务器连接、上传／安装、GPU、真实forward、真实checkpoint加载、loss、backward、训练或BNCal。没有RF头实施、execution request、实际授权回执、runtime config、launcher或真实单次claim。CPU目录中的q／a／r JSON和输出均明确为人工fixture，不能用于服务器执行。

当前服务器身份／资源尚未在本轮新核验。即使下一批CPU通过，最终请求仍需绑定精确实现哈希，并要求执行前重新核验容器与冻结资产；不能将旧身份当作当前就绪结论。
