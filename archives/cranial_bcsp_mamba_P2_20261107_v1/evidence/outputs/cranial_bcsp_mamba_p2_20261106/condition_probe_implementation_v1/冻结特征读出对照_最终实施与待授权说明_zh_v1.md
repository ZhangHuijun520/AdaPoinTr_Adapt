# 冻结特征读出对照：实施接入、CPU验证与待授权说明 v1

日期：2026-11-07。**限定implementation-only完成；最终本机P3通过，request保持待授权。真实Mamba／CUDA尚未执行。**

## 完成内容

专用入口复用P1模型factory、strict checkpoint loader、确定性／TF32合同、精确源码读取、provider检查、资源采样与归档函数。新增实际coarse head hook前缀退出、GT后读、1680计数、固定CPU读出和结果保存。未改生产模型、provider或原P1代码。

来源／数据合同：T0_C、M0_C、T0_D、M0_D；每模型315训练＋105开发，均为原固定来源。index包含1680条模型输入绑定，底层420个唯一点集。同折两模型共享输入／目标；每折内部来源不交叉。四份权重直接绑定已上传路径，不重复复制到旧logs。

## 验证与P3

此前20项核心CPU检查与本轮8项集成检查全部通过。新增完整人工四模型编排实际执行1680次前缀、保存1680份特征文件和4组CPU读出结果；每组105开发病例、21来源、五缺损分层。实际使用既有P1 strict loader载入人工权重，覆盖授权／runtime单向绑定、目标哈希拒绝、原coarse摘要不一致拒绝、输出不覆盖及资源失败回执。人工数据和产物保留在integration_cpu_batch_v1。

P3重新核对测试时源码哈希、stdout、完整人工manifest中1680文件哈希、计数、状态／RNG与失败分支，再静态审查生产bootstrap和完整输入index。生产helper／provider／真实Mamba／CUDA未执行，不把CPU通过解释为服务器准入。

## 冻结执行范围

- 四模型合计1680次encoder/coarse前缀；不执行dense decoder、backward、optimizer step或BNCal。
- 目标为GT8192表面经验质心3坐标＋log半径；G不进入模型prefix。
- 比较训练常数、已有coarse、18维输入几何ridge、1024维冻结特征ridge。标准化只拟合训练来源，平均损失ridge权重固定1，无正则／病例扫描。
- 开发Q摘要按P1既定容差比较；跨设备数值不匹配即停，不能放宽容差续跑。
- 复用7200秒超时、RSS8GiB、torch峰值20GiB、设备22528MiB、输出1GiB、磁盘至少4GiB；这些是保守停止上限，不是性能保证。
- CPU读出包含在同次request，按来源等权、分折报告；不计算bootstrap、正式gate或选择H2。

## 部署前必须核对

新容器基本身份与上传权重已核验，但源码、扩展／provider、Python／driver、420个服务器点集精确哈希及全部新目标不存在仍须在部署前有界复核。request明确把这些作为阻断前提；继承的Python3.10.20／driver570.190是所需期望，非本轮新实测。只核对实际绑定资产，不扩展库存框架，不重复GPU preflight。

## 待授权request

完整SHA256：`9f2a04c381070d54d9e82cc70e800403b12ac7867124ff4b5e52043c1997549c`。状态`AWAITING_EXPLICIT_USER_AUTHORIZATION`。未材料化授权回执、runtime或launcher，未安装、连接服务器、载入真实权重或执行真实GPU／CPU科研读出。

运输包仅含六份最终工具／index／P3／request，不含权重、数据、人工fixture或已授权控制文件。原四份权重上传保持不变。
