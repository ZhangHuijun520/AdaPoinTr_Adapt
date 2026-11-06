# P1 Fold D T0/M0 配对训练准备

日期：2026-11-06。状态：配对合同、数据/顺序绑定及服务器只读就绪快照已冻结；尚未实施入口适配、创建最终execution request、部署或训练。

## 1. 科研配置保持原协议

Fold C正式评分审计通过，主终点未触发预先固定的止损条件。此时继续D是完成既定配对矩阵，不是在C结果后挑选有利样本或调参。Fold C的frontoorbital回退完整保留，D不新增加权/筛选/特殊训练。

| 每个训练臂 | 固定合同 |
|---|---|
| 模型 | T0原编码器；M0仅原定六全局分支Mamba替换 |
| 数据表示 | 原实体缺损、既有V1多边界表面点集、共同GT8192 |
| 输入/输出 | 8192/8192；coarse256 |
| 来源与病例 | D原63训练来源×5缺损=315例；21开发来源×5=105例 |
| 训练 | seed0、batch8、100 traversals、每轮39 batches、精确3900 updates |
| 曝光/丢弃 | 31200 case exposures、300 drop events；两臂相同 |
| 优化 | AdamW，lr0.0001，weight_decay0.0005，clip10，FP32 |
| 调度 | 原LR/BN动量调度及epoch末更新时间不变 |
| 数值 | 既定deterministic/TF32false设置、已确认有限M0梯度非确定性披露不变 |
| 初始化 | 两臂scratch，同一seed0父模型与Mamba私有seed20261104；不加载C训练权重 |
| 禁止项 | BNCal/evaluation/resume均false；禁止自动重试 |

资源合同保持wall86400秒、RSS8GiB、torch allocated/reserved峰值分别20GiB、设备显存22528MiB、输出2GiB、空余磁盘至少4GiB。保留SSM no-weight-decay属性、原生PointNet2、分块KNN与现有loss路径；不重编译或安装依赖。

## 2. 数据与完整顺序

训练/开发来源在D内部严格隔离。D训练中包含部分C开发来源是既定跨折划分的结果，不能把两个折当作互不相交的独立数据集；不利用C结果改变D组成。开发payload本轮未读取。

直接复制原冻结shared_order_foldD_seed0_v1.json，其SHA256为4f68edd55912be0dccfb3d2a1cc72e499d3d499a36aa5f3788550145b3095720。逐轮核验39×8＋3drop，覆盖每个固定训练病例一次；100轮合计3900updates/31200exposures/300drops。另逐位置核验它与原C顺序的固定位置映射一致，没有重新shuffle、调用RNG或按结果重排。逐病例曝光/丢弃计数见order_and_exposure_verification_v1.json。

服务器315个既有D训练NPZ已逐文件重算哈希并与原manifest一致；未重新采样、转换或解码数组。训练输入索引见frozen_FoldD_training_input_index_v1.json。不需要重新运输这些数据。QC仍具有原声明限制：不能把表示QC解释为独立内外板认证或临床精度。

## 3. 本轮服务器只读快照

容器v2iwsa-0、UID1000、GPU UUID GPU-34a1b996-2bd7-88e6-9dca-164b718caea6与P1原身份一致；4090D/570.190，设备内存24564MiB，查询时使用1MiB，磁盘空余11511267328bytes（约10.72GiB）。315训练文件与29项静态配置、QC、顺序、factory/encoder/runtime/元数据合同、provider依赖及历史初始化证据均重新核验。

全部拟用新目标不存在：

- `/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p1_foldD_training_20261106_v1`
- `/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p1/T0_foldD_seed0_train_20261106_v1`
- `/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p1/M0_foldD_seed0_train_20261106_v1`

服务器写入0、模型导入0、CUDA调用0、forward0，未读开发payload。读取/哈希共约744.8MB，在60秒/2GiB预算内完成；未扩展通用库存工具。该快照不是训练准入，真正安装/执行前仍需确认身份、空闲资源及目标新鲜性。

## 4. 最小入口适配缺口

现有T0/M0 P1入口的authorize写死Fold C，并将data_root、order及pair_contract绑定到历史C量化请求；M0入口还固定C T0的审计/request哈希。直接替换request中的C为D会被正确拒绝，因此本轮不创建伪可执行request。原metadata合同中的validate_static、verify_qualified_receipt、validate_order及P1 runtime本身支持同计数D训练，可保持原字节。

下一次限定implementation-only应集中完成：

1. 新增一个隔离的Fold D P1入口，显式区分独立授权的T0_D与M0_D。将D的固定数据/顺序/QC与历史C数值证据的上下文分开；历史C证据保持原样，不重标为D GPU实测。
2. 复用原factory、encoder、runtime、metadata辅助与资源逻辑，不改科研计算。M0_D必须绑定稍后真实T0_D冻结审计的共有初始化、完整实际批次及曝光；不加载T0_D训练后权重作为初始化。
3. 新增限定人工CPU回归，覆盖完整authorize路径、D来源/顺序、C误用拒绝、单向授权、3900-step分派与M0配对证明；本机P3后，仅生成首个T0_D待授权request及最小运输包。

不新增框架，不重复已通过的GPU preflight。两臂顺序仍为T0_D→正式训练后冻结审计→绑定T0_D证据的M0_D request→独立执行授权→M0_D正式训练后配对审计。其后D开发预测及CPU评分仍另行分阶段授权。

## 5. 冻结材料

配对准备合同SHA256：`55dd8fa220af09cf1e3fabf1ee8b40c00af3483a2d7dff8da1649a6bf965fb59`。

准备草案SHA256：`7c1f3b486093bdc30e6c8f7eae06d7539f3784ed69e10cea1a75fdef8b4a0074`。

二者是准备/适配范围材料，不是execution request，也不授权执行训练。本轮没有修改现有模型或生产训练源码，没有启动测试、GPU验证、训练或评价。
