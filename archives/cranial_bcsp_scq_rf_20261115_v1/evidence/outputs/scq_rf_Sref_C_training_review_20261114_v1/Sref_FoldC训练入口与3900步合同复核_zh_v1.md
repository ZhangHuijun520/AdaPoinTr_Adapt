# SCQ-RF首个S-ref Fold C训练入口与3900步合同复核

2026-11-14。仅有限源码与本机冻结元数据核对；未连接服务器、修改生产代码、执行CPU契约测试／模型、读取真实NPZ或checkpoint、生成执行控制文件或启动训练。

## 1. 结论

**模型、数据元数据、初始化与3900步数值合同可以复用；旧B／S训练入口不能直接承担本轮S-ref_C。当前尚不能创建绑定最终入口哈希的可执行待授权request。**

阻断是旧入口锁定历史准入和B→S协议，而不是CUDA能力不足。新RF人工CUDA已正式冻结通过，不需要重复GPU preflight。下一步应只做一个集中的S-ref_C最小入口／bridge适配及针对性CPU验证、P3，再生成最终待授权request；不能伪造旧B基线或绕过旧入口的守卫。

## 2. 已核实的科研合同

| 项目 | 固定值及核对结果 |
|---|---|
| 模型 | 原SCQ `S`分支，作为当前环境新训练的S-ref；40,596,676参数，不安装RF第二头 |
| 来源／病例 | Fold C训练63来源、315病例，每来源五类缺损；开发21来源、105病例仅元数据核对，训练与开发来源无交叉 |
| 表示 | 原BCSP V1，8192输入／8192输出／256 coarse，D-only归一化 |
| 初始化 | 从头seed0，继承已准入Mamba／LQI初始化及原SCQ冻结初始化；不加载旧S或B checkpoint |
| 批次 | 100遍历，每遍历39个batch8；每遍历312曝光、3丢弃 |
| 精确更新 | **3900 steps**；31,200曝光，300丢弃，每病例曝光＋丢弃=100 |
| 优化器 | 原AdamW，lr1e-4、betas=(0.9,0.999)、eps1e-8、clip10；矩阵衰减5e-4，显式SSM／1D／bias例外0 |
| 调度 | LR=`1e-4*max(.9**(epoch/21),.02)`；BN momentum=`max(.9*.5**(epoch/21),.01)` |
| 输出选择 | 固定epoch99／step3900最终checkpoint，不按开发结果选epoch |
| 禁止 | warmstart、resume、自动重试、训练内开发选择、BNCal、评价 |
| 资源 | 24小时，RSS8GiB、torch峰值20GiB、SMI22,528MiB、输出2GiB、空闲磁盘至少4GiB |

复用原metadata validator，重核QC receipt、8192／16384配对清单、fold绑定及原实际批次计划。仅读取冻结JSON／JSONL，不重新采样、不重新生成顺序、不读取点数组。既有QC语义限制原样保留，不把metadata通过写成新解剖精度认证。记录的20个封存来源排除合同不变。

完整顺序canonical SHA256：

`349189dcada4c41b9e6b0152fa24695b2c71ce5fce4144865247d03c445f795f`

训练315病例allowlist SHA256：

`3c5883d1f582b90533ffed3ae61b1bbe8b88c39b75f40faddf25b63d8f93836d`

训练数据根沿用冻结Fold C训练request的精确值：`/home/jovyan/adapointr_work/PoinTr/data/bcsp_geov1_foldc_8192_seed0_v1`。没有从Windows路径或目录折名推断映射。本轮没有核验这315个服务器payload的存在性或文件哈希；正式执行前仍需新鲜核验。

## 3. 原入口不兼容点

| 位置 | 旧合同 | 本阶段所需 |
|---|---|---|
| `validate_admission` | 硬编码旧SCQ准入哈希、4 forward／4 backward、144个原生调用 | 当前RF正式冻结，5 forward／4 backward、180原生调用；不重复GPU |
| `authorize`／pair | 仅B／S，顺序B_C→S_C→B_D→S_D | S-ref_C→Static_C→Requery_C→S-ref_D→Requery_D→Static_D |
| S臂前置 | 必须有同设备B_C正式训练后冻结 | S-ref_C是新阶段第一run，不依赖旧B训练或checkpoint |
| 共有初态指纹 | 排除整个SCQ模块 | 与本次CUDA准入一致，包含原SCQ，仅排除RF第二头 |
| 设备及准入来源 | 旧pair锁定历史训练设备与历史证据 | 本轮`zbpgzu-0`／GPU-dabcc897…当前准入，启动前重验 |
| bridge及身份日志 | 接受旧SCQ准入状态，运行身份记旧SCQ阶段 | 接受精确新RF准入，明确实际SCQ_RF／S-ref_C身份 |

旧原生runtime本身的3900更新、曝光、调度与no-decay实现不需要改。原checkpoint内`stage=BCSP_INPUT_DENSITY_V1`为继承的序列化来源字段；新入口须独立记录本次实际stage／arm，不能将其误解为科学设置发生变化。

实际源码哈希及行号锚点见[机器复核结果](training_contract_and_entry_review_v1.json)。本轮没有通过禁用assert、改旧request或把旧B的结果冒充新参考来处理不兼容。

## 4. 当前设备与初始化证据

当前绑定依据是已通过的v3正式post-CUDA冻结审计，不是本轮新检查的服务器在线状态：

- hostname：`shu-common-25721452-notebook-zbpgzu-0`；
- GPU UUID：`GPU-dabcc897-ac69-efac-4438-a6186dea9aaa`；
- 驱动575.51.03，PyTorch2.4.1+cu118，原生Mamba／PointNet2后端不变；
- 原SCQ初始化SHA256：`e7858ee3ae4c0bf6d68e447727c36514f5bbab42b95e1935f1686620ec089416`。

新S-ref应匹配CUDA构造证据的完整共有初态SHA256：

`b7e5b640c1f0e709ab6697139db1267584266a51b4e0e29f2d5217bfd1236cc5`

指纹范围包括原SCQ和BN持久状态，不能套用旧入口“排除SCQ”的不同定义。当前人工CUDA batch8可执行不代表3900步长期资源已被证明，训练时继续监测与超限停止。

## 5. 最小接入收尾范围

[限定适配范围](minimal_entry_adaptation_scope_v1.json)已具体列明，状态为`PROPOSED_MINIMAL_SREF_C_ENTRY_ADAPTATION_NOT_EXECUTION_REQUEST`，不是执行请求或训练授权。建议仅新增三份隔离候选源码：

1. `bcsp_scq_rf_Sref_C_training_entry_v1.py`：绑定新正式准入、S-ref_C身份、完整共有初态和同一QC／顺序，保留精确授权及资源合同。
2. `bcsp_scq_rf_training_bridge_v1.py`：仅适配新准入身份，仍委托原固定runtime，数值循环不改。
3. `test_scq_rf_Sref_C_entry_cpu_v1.py`：实际authorize路径、过期准入／错误fold／设备／计数拒绝、状态指纹范围、原runtime分派及一次性启动合同的人工检查。

通过一批针对性CPU验证和P3后，才能创建绑定最终源码哈希的S-ref_C待授权request。不扩展通用框架、不再做GPU准入，不改数据、模型、loss、采样、初始化、顺序、3900步或阈值。本轮未实施这三份候选，也未创建训练request或launcher。
