# Stage A：FullMamba有限只读差量核对 v1

2026-11-10。**本机冻结源码层面已收敛到明确替换接口，可以进入单独授权的集中implementation-only。** 不代表F0已经实现、attention-free动态通过、GPU可运行或训练获准。

## 1. 范围与身份

读取7个明确文件：冻结母版及Transformer_utils、P1 factory/encoder/runtime、既有H2配置中的共享model段、FullMamba v2计划。没有读取真实NPZ/checkpoint、实例化模型、调用Torch、运行CPU测试、访问服务器或扩大依赖库存。

母版SHA256：`1f3eb07ad0c3e2f78756682dcb273d745939dc7efda5563c6528915d6d89a1d4`。配置来源是H2历史文件，只用于确认共享结构；F0必须显式禁用H1/H2/H3、SCQR/rim和旧adapter，不能复制H2总配置直接训练。完整身份和源码行号见source_identity_v1.json。

## 2. 已确认的原始计算链

`D→grouper(FPS512→256)→input_proj+pos_embed→M0 encoder→x`。

`x→increase_dim→max(token)→z1024→coarse_pred→Q256×3`。

`mem=mem_link(x)`，本配置encoder/decoder均384，因此mem_link为Identity，不是额外attention或维度投影。Query为`mlp_query(cat(z,Q))`，没有独立的现有decoder Q-PE。旧临时FPS128候选在learned_only分支不进入Q，不顺手删除。

`decoder(q,mem,q_pos=Q,v_pos=coor)→query features→重建global max与query/Q拼接→reduce_map(1411→384)→FC相对点32×3→Q+Δ→8192点`。不同的increase_dim属于base_model和外层head，不能误复用。

## 3. 精确替换与保留

- 实际decoder层路径为`base_model.decoder.blocks.blocks[i]`，i=0..7，当前类为CrossAttnBlockApi。
- 每层self_attn是Attention，cross_attn是CrossAttention，共16个真正QK-softmax-V分支，全部替换。
- 首层另有local_self_attn/local_cross_attn，均为DynamicGraphAttention：KNN(k8)、cat(local_v−q,q)、Linear(768→384)/LeakyReLU/max。没有内容attention，保留。
- 首层self_attn_merge_map/cross_attn_merge_map均Linear768→384，保留原参数；新SSM结果必须与local graph各输出384，再沿末维concat。不得删merge或把已concat的768特征送进384维SSM。
- 其余7层各只有一个全局self和cross支路，不生成额外local graph或merge。
- M0 encoder已有6个双向共享SSM支路，P1 wrapper保留首层graph、merge和FFN；继续复用，不再次替换或二次初始化。

## 4. Norm和残差映射已确定

| v2记号 | 实际成员 | 输入与时序 |
|---|---|---|
| Ns | norm1 | 原始X，进入query self SSM和首层local self graph |
| Nq | norm_q | 第一次残差后的X1，进入conditional query和首层local cross graph |
| Nv | norm_v | 原始mem，进入conditional prefix和首层local cross graph |
| Nf | norm2 | 第二次残差后的X2，进入mlp |
| self残差 | drop_path1(ls1(f_s)) | X1=X+... |
| cross残差 | drop_path4(ls4(f_c)) | X2=X1+... |
| FFN残差 | drop_path2(ls2(mlp(norm2(X2)))) | 输出Xnext |

本配置未传init_values、drop_path_rate、drop_rate，继承默认None/0；故LayerScale和DropPath为Identity，dropout0。LayerNorm eps1e−6，FFN ratio2，即384→768→384。不要在新类构造时错误继承其他默认ratio4或加γ=1e−5。

## 5. 外层容器必须同时适配

当前TransformerDecoder.forward提前算self_attn_idx/cross_attn_idx，八层复用；F0仅首层graph需要这些几何邻域。可以保留其语义并只算所需索引，不能把旧Attention模块仅设None而继续旧block.forward：它仍按block_length和两路concat数检查，会报错或遗漏分支。

建议新增隔离F0 block和薄容器，替换整个decoder入口；保留原调用签名(q,v,q_pos,v_pos,denoise_length=None,return_instrumentation=False)，本任务拒绝非零denoise路径。输出常规为B×256×384；instrumentation模式返回同shape结果和8层records，不改变外层base_model/FC head约定。

outer DecoderEntry含通用apply(_init_weights)，母版构造也会调用apply。必须先构造完整母版/M0，之后用隔离RNG构造并装入16个新native Mamba和一份PE；禁止再对整个模型或新SSM调用母版apply。需保留dt bias _no_reinit和A_log/D no-decay标记。共同Norm/FFN/graph/merge等转移原对象/张量并核验，不用新建后声称共同初始化相同。

## 6. PE、排序与条件归因

保留encoder的3→128→384 pos_embed和原mlp_query。新增decoder共享Linear3→384无bias，仅按v2公式加到SSM分支输入；local graph依旧使用原normalized feature和q_pos/v_pos，不把加PE后的feature误塞进去。

Memory排序坐标是coor而非Q；Query排序是Q。P1 lexicographic_order按z/y/x三次稳定排序得到x优先字典序，完全tie沿原slot。正反扫描先恢复方向再平均，最后逆排序回原query slot；不能对整个prefix调用现有双向wrapper。

M0旧factory的native_attention_retained等字段不能作为F0合规判据：它的证据作用域不涵盖全部decoder。F0要新增分层结构和动态算子覆盖；本次仅确认旧路径，未宣称F0 attention调用已经为0。

首层local cross graph和z同样能传入D条件，所以后续prefix干预必须冻结recipient Q/X/z和local memory；donor只替换被研究的路径。测试早段Memory且保留末尾d_conv−1 tokens，可区分SSM状态与边界短卷积的作用。当前没有检验任何条件响应。

## 7. 损失、日志与尚未验证的接口

原get_loss仍含coarse CD和dense CD；denoise关闭时第一个loss返回值为0不代表没有coarse监督。保留原函数和后端，F0不开启任何几何辅助项。训练日志宜增加只读分量，不重复累加loss。

完整full_instrumentation源码显式限eval，训练不能直接打开该flag来取层轨迹；须在新F0训练日志中仅保存同forward detached轻量统计。Native可保留完整inference instrumentation，并增加每例完整Q保存。

源码推导的memory256、width384、Q256、relative32与配置一致；并未实际构造模型/执行张量验证。优化器新参数分组、CUDA原生SSM、输出slot相等性、零缓存和静态/动态无attention检查，仍须implementation-only及后续单独CUDA验证，不能把本次AST读取当CPU合同测试。

## 8. 实施范围建议与停止点

集中实施为四类隔离文件：F0 decoder/block/container；F0 factory（复用M0、独立新模块初始化）；最小runtime/短入口适配；针对性CPU测试。精确新增文件名及新模块种子、共享PE初始化、原调用兼容和优化器分类应在该次implementation-only范围中同时固定，不逐点滚动扩展。

不改母版、P1/P2入口、数据、采样、评分或3900步；不恢复历史权重，不开始GPU检查或创建训练request。先实现并完成有针对性的CPU验证/P3，之后才形成限定CUDA待授权范围。

**Stage A结论：静态差量核对完成，无需扩大通用准备；当前没有发现阻止该隔离实现的源码级接口歧义。** 它不是性能承诺，也不自动授权下一阶段。
