# F0两折30次decoder-only条件诊断：正式冻结审计与科研解读

日期：2026-11-11。正式审计结论：**PASS，35项全部通过**。本次续审仅重算既有数组统计，新增模型调用、forward、训练、checkpoint反序列化及服务器写入均为0。

## 1. 审计对象与来源

授权 request SHA256：`a21965cdefdf4a7903b5cb52b235dc5e30f0cd9d25a25915734967ee6ff7eda2`。容器：`shu-common-25721452-notebook-zv9bqd-0`。原request、运输包、模型源码和权重未修改。

正式结果JSON：`formal_post_diagnostic_freeze_audit_result_v1.json`，SHA256 `d5f7391a846101dbe86fba6b16a930d7348ce1a469d33a3e444af05145b21e28`。

复用正式计划第9.2节的固定10组recipient/donor：C来源001→003，D来源004→005；每折bilateral、frontoorbital、parietotemporal、random_1、random_2各1例。具体编号表是在Native之前枚举，不能追溯称为已证明训练前冻结。本轮没有按结果更换病例。

## 2. 正式只读审计结果

- 退出码0，worker与固定tmux均不存在，未发现执行失败产物。
- 精确73个输出文件、4个目录；7个安装文件和6个控制凭据与冻结映射一致。独立前后哈希、文件内容相关指纹一致，排除atime干扰。
- 授权回执→SHA256→runtime的单向绑定、原launcher渲染字节、单次claim、启动回执和不覆盖安装回执均一致。
- 40份原缓存／参照NPZ、两份最终权重、母版／provider／相关依赖的精确哈希重新核验通过；没有加载checkpoint。
- 精确30次decoder＋30次原重建头＋720次原生SSM调用；60条claim/complete记录连续且唯一。encoder、coarse、Native重放、backward、optimizer step均为0。
- 30份预测＋30份40数组trace均为有限FP32；coarse与固定recipient Q逐点相同；第0层input与固定X一致；8层链路衔接一致。
- 30条件的第0层after_self与Native一致；10次local-only条件的第0层prefix_suffix与Native一致。各层记录的prefix/local来源及raw-F置零位置符合合同。
- 1920条层级／分组响应及60份dense统计独立重算通过，最大浮点差 `8.88e-16`；未重新运行模型或评分。
- C/D两个模型的完整state_dict（含BN缓冲）前后SHA一致；CPU／CUDA／Python／NumPy RNG前后记录一致，格式有效。此项验证的是绑定源码产生的运行指纹，不能当作脱离源码记录的完整硬件级执行证明。
- 全部61条资源记录通过，且额外从实际数值逐项重新核算阈值。最大记录RSS 1.823 GiB，SMI显存 711 MiB，Torch峰值allocated 233.34 MiB、reserved 262.00 MiB。模型循环最大记录耗时 36.12秒；这不是含归档的端到端耗时。归档后总输出 883,445,366 bytes，小于1GiB。
- 压缩包65个成员与磁盘文件大小、SHA256、内容清单一致；不在服务器解压。

原v1整批响应重算调用没有收到有效回传，记录保留；不能据此认定模型或结果失败。本次只将审计辅助算术拆成C/D两批，各990项，限制NumPy线程并避免BLAS norm过度开销，不改变判据和科学产物。具体超时原因没有被独立证实；上述修改是有界计算优化，不把推测写成定论。

## 3. 三种干预与指标定义

固定recipient的z/Q/X和模型参数，仅运行decoder后缀及原重建头。prefix feature-null将原始F在norm_v之前置零，保留LayerNorm学习偏置、坐标PE及recipient局部图；prefix donor成对替换prefix F/S但保留recipient局部图；local-graph donor只替换局部图F/S并以donor S重算KNN，prefix保持recipient。

原重建头从干预后的decoder特征重新执行原有全局池化；不会把缓存的backbone z冒充重建global feature。三种条件均不使用GT。

下表是**同一神经点槽位的坐标RMSE响应**：

`RMSE_xyz = sqrt(mean over point and xyz coordinate of (P_condition - P_Native)^2) × recipient scale`。

这是每坐标RMSE，逐点三维欧氏位移的RMS等于其√3倍；它不是Chamfer、HD/P95、接口距离或精度改善。槽位对应只是共享同一固定query/patch索引，不是解剖点对应。

| 折 | 干预 | 例数 | 坐标RMSE响应均值/mm | 病例范围/mm |
|---|---|---:|---:|---:|
| C | prefix 特征置零 | 5 | 1.240174 | 0.867262–1.566292 |
| C | prefix donor | 5 | 0.045943 | 0.016066–0.085266 |
| C | local-graph donor | 5 | 5.361726 | 1.123202–9.831231 |
| D | prefix 特征置零 | 5 | 0.686436 | 0.427160–0.913709 |
| D | prefix donor | 5 | 0.022727 | 0.015273–0.031143 |
| D | local-graph donor | 5 | 3.879453 | 2.288128–6.666407 |
| ALL | prefix 特征置零 | 10 | 0.963305 | 0.427160–1.566292 |
| ALL | prefix donor | 10 | 0.034335 | 0.015273–0.085266 |
| ALL | local-graph donor | 10 | 4.620589 | 1.123202–9.831231 |

所有30条件均未与Native在既定allclose容差下相等，但本轮没有测量当前权重/设备的重复Native噪声底，不能将最小非零变化解释为统计显著性或临床效应。

## 4. 固定病例逐项结果

| 折 | recipient | prefix置零/mm | prefix donor/mm | local donor/mm |
|---|---|---:|---:|---:|
| C | train__001__bilateral | 0.867262 | 0.071679 | 9.831231 |
| C | train__001__frontoorbital | 1.555617 | 0.085266 | 7.122386 |
| C | train__001__parietotemporal | 1.566292 | 0.036722 | 1.123202 |
| C | train__001__random_1 | 1.251102 | 0.019982 | 3.708982 |
| C | train__001__random_2 | 0.960596 | 0.016066 | 5.022827 |
| D | train__004__bilateral | 0.717287 | 0.015274 | 6.666407 |
| D | train__004__frontoorbital | 0.913709 | 0.030063 | 3.637745 |
| D | train__004__parietotemporal | 0.701573 | 0.031143 | 3.261488 |
| D | train__004__random_1 | 0.672452 | 0.021884 | 3.543496 |
| D | train__004__random_2 | 0.427160 | 0.015273 | 2.288128 |

这些病例不是210例开发集的完整代表样本，每折只有一个完整来源的五类缺损，不能把五例当作五个独立来源做显著性推断。

## 5. 响应首先从哪里出现

下表为每折五例的特征坐标RMSE均值，特征量无毫米单位，也不能直接跨不同stage的幅值比较“作用重要性”。

| 折 | 干预 | 第0层prefix_suffix | 第0层after_cross | 第7层output |
|---|---|---:|---:|---:|
| C | prefix 特征置零 | 0.002271097 | 0.000898273 | 0.139094443 |
| C | prefix donor | 0.000620739 | 0.000259881 | 0.007138118 |
| C | local-graph donor | 0.000000000 | 0.127617525 | 0.504286154 |
| D | prefix 特征置零 | 0.003102932 | 0.001332475 | 0.108059501 |
| D | prefix donor | 0.000430504 | 0.000175267 | 0.004221432 |
| D | local-graph donor | 0.000000000 | 0.131840438 | 0.417491114 |

prefix donor在第0层conditional输出已经产生小响应，而local donor的第0层prefix输出严格保持0，响应首先出现在local merge后的after_cross。这验证了本轮隔离合同，与共享memory参数直接整体替换有本质区别。local donor在后续层出现prefix响应，是前层改变query状态后的传播，不能误称prefix来源被换成donor。

第0层prefix输出按recipient Q的既定字典序切分early86、middle85、late85个query：

| 折 | 干预 | early | middle | late |
|---|---|---:|---:|---:|
| C | prefix 特征置零 | 0.003916009 | 0.000111670 | 0.000073374 |
| C | prefix donor | 0.001070930 | 0.000007532 | 0.000004530 |
| C | local-graph donor | 0.000000000 | 0.000000000 | 0.000000000 |
| D | prefix 特征置零 | 0.005063096 | 0.001461120 | 0.000955024 |
| D | prefix donor | 0.000725813 | 0.000126021 | 0.000086611 |
| D | local-graph donor | 0.000000000 | 0.000000000 | 0.000000000 |

prefix donor的C折early/late响应均值约236倍，D折约8.4倍。该明显位置依赖与长prefix到后续query的条件传递衰减假设相容；它不证明因果原因就是SSM遗忘。query位置、特征和不同区域的输入几何难度同样可能参与。更深层也不是一律衰减：C折末层三个分组响应更接近，不能声称所有层都完全读不到prefix。

## 6. 可以得出与不能得出的结论

1. **当前F0并非完全不受条件控制。** raw-F置零有0.427–1.566mm坐标响应；合法病例donor替换的响应较小但非零。置零可能改变特征分布，不能把它的响应直接解读为病例身份信息利用程度。
2. **在这组固定配对下，dense对prefix donor的变化较小，对局部图F/S替换的变化较大。** 这是描述性敏感度差异，不是两分支重要性的等量因果比较。两者干预强度、几何兼容性和作用路径不同，不能据响应比例宣称局部分支更重要多少倍。
3. donor F/S保留其自身样本归一化后的坐标，而Q/X来自recipient。局部donor会改变邻域搜索及特征/坐标配对，可能形成较强OOD几何不匹配；因此大响应不等于正确几何条件利用，更不等于精度提升。
4. prefix donor响应小也可能受donor间特征相似、归一化、recipient固定X携带条件及当前测试病例限制。没有训练匹配消融，不能删除prefix并宣称它无用。
5. 本轮固定Q，不能修复或归因上游coarse定位误差。既有Native证据中D折coarse和dense已经有较大定位/覆盖退化；当前诊断不能把这些退化全部归罪于decoder，也不能保证改decoder会纠正coarse。
6. 禁止把这些OOD干预预测作为推理后处理、最佳挑选结果或Native正式性能。原T0/M0/F0评分结论保持原样。

## 7. 下一步最小结构候选与决策

**优先检验query对齐的局部条件交错序列，暂不改coarse或重建头、不增加scale修正或损失项。** 这是一个可证伪候选，不是已验证有效的创新。

唯一替换边界：每层conditional-SSM的输入序列构造。设现有KNN得到 `N_i = KNN_8(S,Q_i)`，在该层构造：

`A_i = mean_(j in N_i)[norm_v(F_j) + PE(S_j)]`

`B_i = norm_q(x1_i) + PE(Q_i)`

按不变的recipient Q字典序π排列为：

`[A_π1, B_π1, A_π2, B_π2, …, A_π256, B_π256]`。

同一个causal Mamba处理512个token；抽取B位置的输出再恢复原query顺序。A只来自当前输入的F/S与Q，不读取GT或缺损定位标签。复用现有k=8邻域索引，保持384宽度、参数量、SSM类型和调用数量不变；自分支、既有local-cross graph及merge、坐标头、原loss和训练合同均不改。不增加门控、增益、额外权重或扫描半径。

它把全局prefix的间接路径改为每query邻近的条件输入，针对的是“条件到生成token的路由”，而不是通过提高干预响应强度制造改善结论。该单一接口修改同时涉及局部聚合与序列排列，若后续有效，不能再把收益单独归因于二者之一。

预期与证伪：若分布更均匀的条件响应不能转化为冻结Native形状/接口指标及可靠性改善，则不接受科研有效性；若仍无条件响应，说明当前假设不足；若均值改善但新增严重失败不满足原可靠性要求，同样不能升级为主方法。不得依据本次10例扫描k、聚合权重或挑选训练病例。

下一步先审核唯一公式及替换接口，再单独授权最小implementation-only、针对性CPU验证及必要的CUDA零更新验证；之后才按原初始化、批次顺序、8k→8k、3900步合同准备待授权训练。当前没有实施候选、创建训练request或启动任何新实验。

## 8. 归档位置与哈希

服务器现有归档：`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/F0_CD_condition_diagnostic_20261111_v1/development_predictions_v1.tar.gz`

大小：441,537,116 bytes。

SHA256：`5082d0ac49ebc793fa2d8ba29a294b7b63eb17e5082e6c5a97e0b8ddf7cc0b1c`。

下载配套的`.sha256`、`.bytes`和`.contents.sha256`可将完整预测/trace留在本机。当前本机已保存审计元数据和源码副本，**尚未下载此441MB诊断压缩包，不能声称完整诊断数组已本机备份**。后续归档/清理仍应按本机实际核验结果办理。
