# H2 implementation-only：实现合同、CPU验证与本机P3 v1

日期：2026-11-07。**限定本机实现完成，最终33项人工CPU检查通过，本机P3通过；不具备直接GPU或训练执行授权。**

## 1. 与已确认草案一致的实现

- `bcsp_h2_range_v1.py`：1025参数零初始化标量头，无RNG消耗；动态范围残差标签；beta0.1／权重0.1；a=log1.25有界软缩放；半径不加epsilon，退化即停。
- `bcsp_h2_model_adapter_v1.py`：先用原factory构建M0，之后安装头和唯一coarse输出hook；AUX返回原Q，COUPLE返回Qc；OFF不新增头／hook／state_dict键。原模型源码不修改。
- 原前向所有消费者在原控制流内接收相同Q_used：query拼接、decoder q_pos、重建特征、Q＋相对位移、coarse返回及loss。实际父函数的这些消费点已用人工组件执行核对。
- `get_loss`包装只加入一次0.1辅助项；辅助标签中原Q detach，耦合条件delta detach，Q／muQ不detach。训练前向必须恰好对应一次loss；拒绝重复loss、未消费训练上下文、重复安装及训练时干预。
- 原runtime仅新增已计算日志的取得／合并及checkpoint H2元数据；没有新增forward、CD、backward、optimizer或调度调用。原3900步生命周期AST经去除这三处增量后与父版相同。

## 2. 最终CPU证据

最终33项检查全部通过。首批32项也通过；后续静态审查补齐AUX纯推理的非有限条件输出拒绝，新增第33项并完成新版本全批验证。旧结果和旧源码字节均保留，不将重复检查相加为65项独立验证。

使用本机PyTorch2.5.1 CPU、Python3.9.21环境；未调用CUDA。执行冻结PCTransformer.forward、AdaPoinTr.forward／get_loss／get_fine_loss_components函数体，人工替代局部聚合、encoder、decoder和几何损失。1024特征、256 coarse、8192输入／输出形状按合同验证，但不等于运行了真实Mamba或真实Chamfer算子。

验证包含：OFF／初值中性、五处真实坐标消费者、中心／半径代数、有界极端值、退化与非有限拒绝、等半径异形反例、两条detach梯度路径、真实loss包装反向、原参数衰减不变、严格checkpoint roundtrip／模式拒绝，以及日志不重复计算。

3900次仅是原UpdateGuard的计数模拟；本轮optimizer step为0，没有执行3900次人工或真实模型训练。训练order／计数／调度不变的另一证据是runtime AST只发生上述日志和元数据增量。

## 3. 初始化、参数和checkpoint合同

新增头在母版／Mamba初始化结束后安装，CPU FP32 zero参数创建不使用随机初始化。共同state_dict键值与公共RNG保持；新增键只有h2_range_head.weight和bias。复用原分组函数：矩阵W衰减5e-4，bias不衰减，原SSM no-decay标记及所有原参数分类不变。

H2 checkpoint仍是原BCSP任务／末步格式，新增H2模式与固定常数元数据。未来加载须先调用validate_checkpoint_contract拒绝AUX／COUPLE模式混用，再strict加载state_dict。OFF继续严格加载原M0。禁止pickle整个带hook模型或对已安装hook的模型做deepcopy；按factory重新构建再加载权重。

## 4. 日志解释

原loss_dense／loss_reconstruction字段在该runtime记录的是模型返回的“原重建＋H2辅助”总支路；新增loss_original_reconstruction、H2_aux_raw／weighted明确拆分，不能将总支路误称纯CD。另保存每例delta、动态目标t、实际尺度s、原Q／Q_used／P／G经验矩与generation。日志取已计算的loss／张量，不重跑forward或CD。

推理不调用get_loss也不读取G；eval干预仅用于未来固定病例诊断，不进入Native主表。模型没有外部GT条件入口。

## 5. P3结论和下一步边界

P3状态：LOCAL_H2_IMPLEMENTATION_P3_PASS。三个生产候选与测试、stdout、已确认草案和父源码均有SHA256绑定。未部署、联网下载／升级、访问真实点集或权重、运行GPU、训练或生成execution request。

下一步仅准备草案中必要的新路径人工CUDA准入：两臂合计2 forward／2 backward／0 optimizer step。尚需一个最小设备短入口，明确合成输入、eval／train及BN／RNG语义，完成针对性CPU入口验证后才创建待授权request。不重复通用GPU preflight，不扩大依赖库存，不因CPU通过直接启动四次训练。

本轮验证的是实现正确性，不是残差头可预测、耦合有效或完整骨块／接口改善的证据。范围上限与损失权重不扫描，科研判断继续遵守已确认的AUX／COUPLE对照和完整形状／风险条件。
