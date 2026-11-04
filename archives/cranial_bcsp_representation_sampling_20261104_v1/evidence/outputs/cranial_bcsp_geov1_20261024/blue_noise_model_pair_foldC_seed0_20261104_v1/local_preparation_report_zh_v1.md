# 欧氏／表面图两臂Fold C点集与最小入口：本机准备报告

日期：2026-11-04。状态：**本机点集与最小入口准备通过；服务器资源未核验、训练未授权。**

## 完成内容

| 项目 | 结果 |
|---|---|
| 两臂 | Euclidean_elimination / surface_graph |
| 训练 | 每臂315病例、63来源、每来源5类缺损 |
| 开发 | 每臂105病例、21来源；与训练来源互斥，仅准备数据 |
| 点数／schema | 输入8192、目标8192；NPZ仅partial与implant，两者均float32 |
| 配对 | 同病例32768候选池、采样seed0、相同GT数组与D-only归一化、相同逐病例点序 |
| 数据量 | 两臂共840份模型NPZ；60病例复用并逐点核对，另外360病例新生成 |
| 批次 | 原冻结顺序文件逐字节复制；batch8、100 traversals、3900步、31200曝光、300丢弃 |
| 模型与训练 | 继承B0 AdaPoinTr Transformer、FP32、原优化器分组／调度与KNN／loss；不同时改成Mamba |
| 初始化 | 两臂scratch seed0；第二臂必须核验第一臂的相同参数与buffer初始指纹，当前没有创建模型 |
| 入口 | 新stage／两臂／train元数据绑定；训练runtime只改变输出stage文字，算术与循环不变 |

## CPU验证与本机复核

- 最终点集经原有、哈希一致的bcsp_adapter.load_case读取：630份训练文件及210份开发输入全部通过。训练GT配对315组一致，开发读取使用training=False，目标不解码。
- 执行20项CPU契约检查：两臂与阶段、来源隔离、目标／frame／输入点序、3900计数、旧stage与旧臂拒绝、路径越界拒绝、真实元数据哈希绑定，以及完整authorize→实际rebind验证逻辑。授权对象只在RAM内模拟，没有真实授权回执文件。
- 参数／状态初始化不一致时拒绝第二臂；未绑定当前服务器资源时拒绝执行。静态通过不等于CUDA或新模型实际初始化通过。
- 实际UpdateGuard执行人工3900次状态转换并核验100 traversals、31200曝光。这是计数器验证，不是优化器训练或模型forward。
- 选定D原文件、既有GT所在NPZ及旧科学实现哈希不变；本轮未重新解码完整骨C或implant NRRD。没有修改既有V1／Morton路径，没有训练、BNCal、开发评价或服务器操作。

## 文件位置

- 两臂模型文件位于各臂points/，训练与开发清单分别为train_manifest_8192.jsonl、dev_manifest_8192.jsonl。
- implementation/含新contract、runtime、entry和CPU契约测试；完整哈希见local_entry_binding.json。
- local_qualified_training_metadata_*_v1.json是本机数据绑定证明，不是授权回执。其路径为Windows本机路径，未来服务器绑定须按实际安装映射生成，不能直接执行或作Linux路径使用。
- source_selections/保留原世界坐标与候选索引，仅为本机诊断证据，不是模型输入features；模型NPZ不含J/E或GT引导标签。
- 原始Windows来源路径仅作本机溯源；服务器运行的数据根目录必须另行精确绑定，不转换或执行E盘路径。

## 执行边界与下一步

用户指定目标容器为shu-common-25721452-notebook-v2iwsa-0。本轮没有连接该容器、核验当前GPU UUID／provider资产或确认WSL登录状态，不能将历史同名容器证据当作当前实测。

入口中的resource_binding刻意保持UNBOUND_PENDING_CURRENT_SERVER_READINESS，确保不会复用旧资源授权。之后应合并完成必要的当前服务器只读就绪核对和最终资源绑定，再冻结运输映射与待授权训练request；不扩展通用库存框架。

本轮只生成共同static_training_config静态合同，没有创建execution request、授权回执、已授权runtime执行绑定或launcher，也没有上传、部署、启动训练。已准备的开发点集不授权开发评价；未来210次两模型预测仍按原阶段边界执行。

点集生成用时5204.4秒，总RSS监测峰值3.555GiB。监测不是硬隔离；整批时间也不是单病例纯采样延迟。

本机完成证据：[数据完成记录](data_preparation_completion.json)、[CPU20项结果](cpu_contract_attempt_v1/result.json)、[实际数据读取器检查](actual_reader_verification_v1.json)、[本机复核](local_preparation_review_v1.json)。
