# F0-LQI v1：隔离实施、CPU验证与本机P3报告

日期：2026-11-11。状态：**本次限定implementation-only完成**。没有服务器操作、GPU调用、真实数据／checkpoint读取、optimizer step或训练request。

## 实施范围

仅新增两个隔离候选源码：

- `bcsp_lqi_decoder_v1.py`：复用F0的全部外部接口、self路径、局部图、残差与FFN，仅将conditional Mamba输入改成冻结的query对齐局部摘要／query交错序列，并读出奇数位置、逆排序恢复query。
- `bcsp_lqi_factory_v1.py`：按原F0构造顺序与种子初始化，分派到隔离LQI decoder；输出明确的候选版本与trace语义。保留历史`model.f0_evidence`属性作为接口载体，但其中版本为`F0-LQI-implementation-v1`，不能冒充已冻结F0。

沿用k=8、原`cross_idx`、512个conditional token及384通道，不引入注意力、可学习参数、增益或门控。原F0文件未修改。

唯一公式及接口规格SHA256：`70ba5de31b296fc370749d7fb07c4461774ff1cba89801cb3374fd774730883b`。

## 验证结果

静态S0/S1通过；AST对照确认所有外围forward语句、其他decoder方法及公开签名保持一致。factory的差量仅为候选decoder导入分派和显式版本元数据。

在已授权PyTorch CPU环境执行**一批**人工验证，退出码0，共**55项断言通过**，耗时约4.78秒。55项包含对8层的重复合同断言，不是55个独立科研实验。

验证重点：

1. 使用真实冻结F0/LQI decoder计算类、母版FC重建头和人工因果mixer；batch=2且两样本坐标／特征不同。
2. 对每层使用显式batch与邻居循环独立构造参考，检查先LN再加PE／均值、A/B交错、奇数位置读出和Q逆排序。
3. decoder只计算原有两次KNN，cross方向为S搜索库、Q查询；8层共享索引。每次decoder保持16次self＋8次conditional mixer调用，所有conditional输入为B×512×384。
4. 原首层self结果与F0相同，local-cross分支的nq/nv/Q/S/idx保持原合同；trace开关不改变数值，层间链路及输入数据未变。
5. 候选与F0人工完整模型的state_dict键、形状、全部初始化值及参数量一致，严格state加载双向通过；真实生产参数量仍应在后续完整母版构造时验证。
6. 人工dense平方目标反传通过，X/F/S/Q、PE及8层norm_v/conditional mixer梯度有限且非零；没有optimizer，参数未更新。
7. 覆盖batch隔离、稳定Q重复坐标排序、训练全trace拒绝、denoise／FP16／错误shape／非有限输入拒绝。

CPU验证并未使用原生Mamba/CUDA；人工目标不是生产Chamfer loss。因此不能推断真实GPU kernel、完整loss、显存或补全效果已通过。

## 本机P3

`post_implementation_P3_v1.json`状态：`F0_LQI_LOCAL_IMPLEMENTATION_ONLY_P3_PASS`。

SHA256：`d96009b6a5e363385da71e179041d8d5fc532efd0214fe6d958c702424b2bbc2`。

P3重新核对最终源码与静态／已执行测试记录哈希一致、原F0与冻结规格身份、decoder及factory的限定差量，并汇总CPU记录和剩余缺口。测试结果位于`artificial_cpu_batch_v1/result.json`，差量位于`decoder_delta_v1.diff`和`factory_delta_v1.diff`，本机证据清单位于`local_implementation_manifest_v1.json`。

这是本机实施范围的P3，不等于后续实际平台运行后的正式冻结审计，也不构成训练准入。

## 剩余缺口与下一步

尚未运行新布局的原生Mamba／CUDA forward-backward、生产完整loss或峰值GPU显存验证；候选的完整母版／provider加载、专用GPU短入口及版本读取绑定也尚未验证。没有LQI Native结果，不能宣称候选优于F0或解决了D折定位退化。

下一步可单独授权限定的人工CUDA零更新短入口及其针对性CPU合同／P3，通过后仅生成待授权request。资源与数值合同保持原范围；不增加并列候选、采样搜索或通用工程框架。本轮不准备运输包、不部署、不启动GPU、不创建训练request。
