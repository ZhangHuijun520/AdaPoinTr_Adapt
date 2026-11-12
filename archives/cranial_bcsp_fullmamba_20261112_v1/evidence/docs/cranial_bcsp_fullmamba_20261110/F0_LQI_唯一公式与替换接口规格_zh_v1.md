# F0-LQI：唯一公式与替换接口规格 v1

日期：2026-11-11。

状态：**候选公式与接口规格冻结；未实施、未测试、未部署、未创建执行request、未授权训练。** F0-LQI仅为该候选的工作名，不代表已经证明创新性或有效性。

## 1. 唯一假设与决策边界

在现有F0模型中，将每层conditional Mamba的“完整memory prefix＋完整query suffix”，改成“每个query对应的局部memory摘要＋该query”的交错序列，检验输入条件到生成token的短路径能否改善条件利用及最终Native补全。

依据是已正式冻结的30次decoder-only诊断：固定10组配对中，prefix donor平均dense坐标RMSE响应0.034335mm，local-graph donor为4.620589mm；第一层prefix响应集中于序列前段。该结果仅支持提出假设，不能证明prefix无用、局部分支必然更重要，不能把响应增加当成精度改善。

本规格只确定一个候选，不并列提出k值、池化、交错间隔、门控或增益变体，不扫描参数。

## 2. 变量与不变的计算位置

所有张量在同一次输入归一化坐标系中；不读取GT、人工缺损标签或接口定位结果。

| 变量 | 形状 | 定义 |
|---|---|---|
| F | B×256×384 | 当前样本encoder memory，保留原数据流及梯度 |
| S | B×256×3 | F对应的输入proxy坐标 |
| Q | B×256×3 | 原coarse/query坐标；整个decoder中坐标不更新 |
| x1^(l) | B×256×384 | 第l层原self分支残差相加后的特征，l=0…7 |
| PE | 3→384 | 原共享`coordinate_pe`，Linear且无bias |
| LN_v^(l)、LN_q^(l) | 384通道 | 第l层原`norm_v`与`norm_q`，保留学习参数和eps |
| π、π⁻¹ | B×256 | 原recipient Q的稳定字典序排列及其逆排列 |

π沿用现有`lexicographic_order(Q.detach())`：x优先、y次之、z再次；完全相同坐标保持输入索引顺序。本候选不新增坐标轴或旋转对齐，不宣称该排序具有旋转不变性。

## 3. 冻结唯一公式

### 3.1 邻域

\[
\mathcal N_i=\operatorname{KNN}_{8}(S,Q_i).
\]

代码方向严格为：`cross_idx = knn(8, v_pos, q_pos)`。搜索库为S，查询为Q；返回B×256×8的**memory索引**。不是Q→Q自邻域，也不是输入8192点上的邻域。

直接复用原decoder在层循环前计算的`cross_idx`，8层共享同一邻域索引；不重复搜索、不改k、不增加半径过滤、表面分层或距离加权。既有KNN后端及等距点处理语义保持不变，不另换tie-break规则。

即使Q在缺损内部或离S较远，也严格取现有k=8最近邻；不临时加距离阈值、fallback、GT邻域或病例剔除。这是候选局限，不在本轮补救。

### 3.2 每层条件token与query token

\[
A_i^{(l)}=\frac{1}{8}\sum_{j\in\mathcal N_i}
\left[\operatorname{LN}_v^{(l)}(F_j)+\operatorname{PE}(S_j)\right],
\qquad
B_i^{(l)}=\operatorname{LN}_q^{(l)}(x1_i^{(l)})+\operatorname{PE}(Q_i).
\]

**先逐memory token做LN，再加PE，最后沿8个邻居取算术平均。** 不得换成`LN(mean(F))`；不得另归一化A/B，不加入relative PE、距离缩放、role embedding、参数化池化、注意力、门控或残差系数。

每层均使用该层自己的LN参数重新计算A；F/S和邻域索引不变，但A不跨层共享缓存。B始终来自当前层x1，不复用初始query特征X。

### 3.3 交错、单向Mamba与读出

\[
T^{(l)}=[A_{\pi(1)}^{(l)},B_{\pi(1)}^{(l)},\ldots,
A_{\pi(256)}^{(l)},B_{\pi(256)}^{(l)}]
\in\mathbb R^{B\times512\times384},
\]

\[
U^{(l)}=\operatorname{Mamba}_{\mathrm{cond}}^{(l)}(T^{(l)}),
\qquad
C^{(l)}=\operatorname{gather}\big(U^{(l)}[:,1::2,:],\pi^{-1}\big).
\]

从零计数：A放偶数位置0、2、…、510；B放奇数位置1、3、…、511。**读出B位置**，而不是前256个、后256个或A位置。抽取后先得到按Q排序的256个query，再用π⁻¹恢复原query顺序。

conditional Mamba保持单向、同一个原模块、每层调用一次；不增加反向扫描，不在query之间重置SSM状态，不引入inference cache。当前query可利用紧邻的局部条件以及更早的交错历史，不等价于256个相互独立的局部预测器。

## 4. 精确替换接口

母版：`outputs/cranial_bcsp_fullmamba_20261110/implementation_v1/bcsp_f0_decoder_v1.py`中的`F0Block.forward`。

唯一科研修改区间为：原`nq, nv = ...`之后的prefix/suffix序列构造、`cond_ssm`输入和query位置读出。保持外部decoder和block方法签名、输入/返回张量形状不变。

原逻辑：

```python
nq, nv = self.norm_q(x1), self.norm_v(memory)
prefix = gather_tokens(nv + m_pe, order_m)
suffix = gather_tokens(nq + q_pe, order_q)
c = self.cond_ssm(torch.cat([prefix, suffix], 1).contiguous())
cq = gather_tokens(c[:, 256:], inverse_q)
```

拟替换的**规范性伪代码**（仅文档，不是已实现源码）：

```python
nq, nv = self.norm_q(x1), self.norm_v(memory)
# memory_tokens: B,256,384; cross_idx: B,256,8, indexes memory
memory_tokens = nv + m_pe
batch = torch.arange(memory_tokens.shape[0], device=memory_tokens.device)[:, None, None]
neighbors = memory_tokens[batch, cross_idx]       # B,256,8,384
local_condition = neighbors.mean(dim=2)         # B,256,384
a = gather_tokens(local_condition, order_q)
b = gather_tokens(nq + q_pe, order_q)
tokens = torch.stack([a, b], dim=2).reshape(memory_tokens.shape[0], 512, 384)
c = self.cond_ssm(tokens.contiguous())
require(c.shape == (memory_tokens.shape[0], 512, 384), "conditional output shape")
cq = gather_tokens(c[:, 1::2, :], inverse_q)
```

`cross_idx`不按memory的字典序重排；它索引的仍是原memory槽位。先在原query顺序构造A，再与B一起按`order_q`排序，不得把`order_m`用于A。既有`order_m`参数可为接口兼容保留，但不参与新conditional路径，不以此顺带重构其他代码。

这一接口是**内嵌计算图替换**，不是复用此次诊断用forward hook作为正式训练实现。后续实现应放在版本化隔离候选中，保留原F0文件与结果不变。

## 5. 明确保留的路径

- encoder、coarse/query初始化、z/X构造、代理点、采样及8k输入／8k输出保持不变。
- 原self-SSM双向扫描、自局部图、残差、FFN、drop/LayerScale设置保持不变。
- 第0层原local-cross graph仍用recipient的`nq/nv/Q/S/cross_idx`，仍与新`cq`走原`cross_attn_merge_map(cat([cq, local]))`；不删除、增强或更换它。其余7层仍无local-cross graph。
- 原重建头及两次原有max pooling、固定Q加相对坐标、原loss均保持不变。
- B×512×384条件序列长度、8层conditional调用、单decoder合计24次原生SSM调用保持不变；不新增可学习参数。邻域gather/mean会新增计算和临时张量，因此**不宣称FLOPs、运行时间或峰值显存完全相同**。
- 原FP32、确定性／TF32设置和资源阈值保持不变；不恢复已经放弃的宿主PID硬归属检查。
- 将来训练从与F0同一初始化合同构造，不能把“使用同一参数结构”误写为“加载F0最终权重继续训练”。同初始化、批次顺序、source/fold和3900步合同保持；是否进入训练仍须单独授权。

## 6. 梯度、状态与记录合同

- 训练时保留memory、norm_v、PE及query路径的正常梯度；**不对A、B、F/S或Q新增detach**。排序／KNN的离散索引不可微这一既有性质不改变；通过被索引特征/坐标的可微数据路径仍保留。
- 不生成或注册新的Parameter、buffer、token状态；同一模块state_dict名称、形状和参数数量应与对应F0一致。
- 外层trace字段及返回形状保持兼容。历史字段名`prefix_suffix`可保留为工具兼容字段，但在该候选元数据中必须标注其语义为“conditional query-position output after interleaving”，禁止称其为仍使用global-prefix/suffix。原F0历史trace不修改。
- 后续若开展条件诊断，应明确干预的是新A条件token来源或原local graph；不能将原prefix hook直接套在新交错序列上。当前规格不授权追加诊断。

## 7. 后续验证范围与否定条件

实现阶段应集中覆盖：带batch的KNN索引方向、先LN后聚合、A/B精确交错、奇数位读出和逆排序、梯度可达、512-token及调用预算、既有local分支参数不变、state_dict/初始化一致、trace语义，以及非有限输入／shape拒绝。需包含B>1的人工fixture，防止只在batch1下正确。这里是验证范围，尚未运行测试。

后续Native评价仍沿用原冻结评分定义及可靠性判据，不因本次10例响应另设增益阈值。条件敏感性增加不是成功标准；必须看到完整Native形状／接口及失败病例风险的实际变化。若只增加输出扰动而不改善Native补全，否定该候选有效性，不扫描参数补救。

该候选在一个接口内同时改变局部条件聚合与序列排列，若有效只能先归因于这个组合，不能单独声称证明了“缩短距离”或“局部聚合”哪一个机制。局部摘要可能丢失远端memory信息，也可能因Q偏移而聚合错误邻域；既有全局X不能被假定足以抵消这些损失。它不会直接纠正固定coarse坐标，因此不能保证解决此前D折定位退化。

## 8. 本轮交付与权限

本轮仅核对母版源码并冻结上述文档规格及来源哈希；不实施模型修改，不测试，不连接服务器，不创建GPU或训练request。下一阶段可单独授权一次限定implementation-only，按本规格实施隔离候选并完成针对性CPU验证/P3；不再增加并列候选或通用框架。
