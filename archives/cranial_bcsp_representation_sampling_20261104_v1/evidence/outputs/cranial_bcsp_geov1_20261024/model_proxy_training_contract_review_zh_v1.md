# 模型取点、16k信息路径与训练合同集中核对

_2026-10-24 · 本机源码／历史合同只读 · 未运行模型、FPS、CUDA或训练_

## 📋 结论

16k输入在源码层面并非先被裁回8k；它会参与全输入局部特征与后续512中心邻域聚合。但最终encoder坐标仍为256个proxy。能否保留切壁信息必须区分坐标保留、邻域覆盖和学习特征，源码不能给出实际保留率。

目前不具备冻结可执行四run训练合同的条件。最重要阻断是全点对KNN内存风险、最新生产实现身份未绑定、新数据source/fold及实际更新数未冻结，而不是需要扩展通用框架。

## 🔍 取点链证据

核对[工作副本AdaPoinTr](E:/Codex/2026-06-06/mamba-ccf-c-1-high-resolution/work/PoinTr/models/AdaPoinTr.py:1042)、[归档模型](E:/Codex/2026-06-06/mamba-ccf-c-1-high-resolution/outputs/cranial_scqr_v12_qa_github_publish_20261019/models/AdaPoinTr.py:1266)及本机保存的QA-1 B0 Fold C配置。

| 环节 | 实际行为 | 对16k的含义 |
|---|---|---|
| Dataset | 要求partial.shape严格等于N_PARTIAL；无自动重采样 | 16k文件配8k配置会直接报错，不会默默截断 |
| SkullBreak runner分支 | 将partial送入模型；非KITTI/CARS分支不执行random_dropping | 未发现固定压回8k步骤 |
| DGCNN第1层 | 全输入k=16邻域，聚合后每原始点有特征 | 新增点参与特征计算 |
| 第一FPS | N→512中心 | 坐标变少，特征并非仅来自512个原点 |
| 第2层 | 512中心向原始N点查邻域并聚合 | 原始16k仍可提供局部支持 |
| 第3层 | 在512中心上计算图特征 | 后续几何分辨率开始受中心预算限制 |
| 第二FPS及第4层 | 512→256，向512支持集聚合 | 最终encoder memory为256个proxy |
| Transformer | 基于256个位置／特征 | 不能将输入覆盖直接等同proxy覆盖 |
| coarse queries | num_query=256，learned_only | 查询来自学习的全局上下文，不保留原始FPS anchor作为输出query |
| FC输出 | num_points=8192，factor=32 | 输入点数变化不自动增加输出数量 |

配置显式center_num=[512,256]，优先于类默认[512,128]。此前讨论“512 proxy”需修正为第一层中心；最终proxy是256。learned_only分支仍可能计算随后未选用的coarse_inp FPS，不能因源码有FPS就宣称其坐标进入输出。

输入合法性：采样provenance可作离线诊断，不应进入模型特征。当前几何NPZ键xyz/provenance_face_ids与现有Dataset所需partial/implant并不直接兼容；不能直接把研究输出目录作为训练数据根。

## ⚠️ 全点对KNN资源风险

[Transformer_utils.py](E:/Codex/2026-06-06/mamba-ccf-c-1-high-resolution/work/PoinTr/models/Transformer_utils.py:17)的knn_point调用square_distance生成[B,S,N]矩阵，再topk；DGCNN最初S=N。

仅单个FP32距离张量的理论尺寸：

| 输入／batch | 距离矩阵尺寸 | 字节换算 |
|---|---|---:|
| 8192，B=8 | 8×8192×8192 | 2 GiB |
| 16384，B=8 | 8×16384×16384 | 8 GiB |
| 16384，B=1 | 1×16384×16384 | 1 GiB |

这不是实测peak VRAM，未计临时张量、图特征、模型激活、decoder及优化器。torch.no_grad避免邻居索引反传，但不消除该前向距离矩阵。不能保证24GB GPU上的B=8可运行16k。

不建议未经验证直接减小microbatch再声称训练合同相同：梯度累积不自动保持BN统计，当前runner还直接对每microbatch loss.backward，未显式按累积步数除loss。现有step_per_update也应检查epoch末不足整组的处理。公平首选是保留共同batch与数值语义；必要时对KNN做限定分块等价适配，保持k、距离和并列点处理合同，须另获implementation-only授权，不在本轮修改。

## 📚 历史合同与新合同边界

从本机保存的B0 Fold D request及数值hotfix runner/guard核对：

| 项目 | 历史QA-1实际合同 | 新任务状态 |
|---|---|---|
| 数据 | 每fold 63源／315缺损case | 未确定新source及生成manifest，不继承 |
| batch | global8，drop_last=true，step_per_update=1 | 建议共同8，资源尚未验证 |
| epoch | range(0,max_epoch+1)，max_epoch=100 | 实为101遍，不是100遍 |
| batches／updates | floor(315/8)=39；101×39=3939 | 由新M和遍历数重新计算 |
| 样本曝光 | 101×39×8=31512；每遍有3case不进入batch | 需保存数据顺序与逐源曝光，不只记epoch |
| 优化器 | AdamW，lr1e-4，decay5e-4；一维参数/bias不衰减 | 可作为建议母版，不冒称已冻结 |
| LR | LambdaLR；decay_step21，lr_decay0.9，floor0.02 | 需绑定实际scheduler代码与调用次序 |
| BN momentum | 初始0.9；bn_decay0.5，step21，floor0.01 | 与额外BNCal是不同阶段 |
| clip | norm10 | 建议保持 |
| precision | FP32，deterministic，TF32=false | 需新preflight核实完整数值设置 |
| checkpoint | scratch，final-only | 不自动加载旧QA权重 |
| BNCal/eval | 分阶段授权，训练不得自动执行 | 本轮仍未授权 |

若新计划采用精确100遍，现runner需max_epoch=99或新路径显式100次循环；不能写max_epoch=100却声称100遍。新updates=100×floor(M/8)仅适用于单卡、drop_last、无额外dataset repeat、step_per_update=1且每遍数据长度不变；M必须由新manifest确定。

旧守卫硬编码315case／39batch／3939updates／101遍，绑定旧request和数据。不得通过改掉旧常数来复用旧授权，也不能把新任务伪装为V12_QA1_training。需要新任务入口的最小计数合同，保持旧路径不变。

## 📍 实现身份与未闭合项

本机work模型SHA256为f114917c3302389d21c7c80f2950fdb6589486cda3b5eab2e909bfb0145e63ca；GitHub轻量归档模型为1f3eb07ad0c3e2f78756682dcb273d745939dc7efda5563c6528915d6d89a1d4；旧Fold D request绑定模型62a743c4c2143b77b0f1656c59d0482563976440d841f04bae995017dbf7588f。三者不同，不认定任一是当前服务器生产源码。

work runner也不具备上述新版QA分派；本报告分别核对普通runner和明确保存的hotfix runner，不将它们拼成一个已部署版本。未连接服务器，本轮不认证远端身份或部署状态。

仍需闭合的范围限定为：

1. 选定实际母版代码身份和KNN等价／资源策略；不做全环境库存。
2. 在既有固定六例8k/16k点集上，有界核对FPS512/256的J距离及邻域支持。CPU仿真只能作几何代理，不能冒称CUDA PointNet2同序列结果；特征质量仍需后续模型结果。
3. 锁定训练允许source、两个互斥source fold、全新partial/implant资产及共享target、M、归一化、精确更新／曝光。六例工具pilot不足以直接训练完整比较。

本轮没有重新读取真实NPZ/NRRD/checkpoint，没有运行FPS、模型或任何训练，也没有修改生产代码。

## 🎯 最多四run的范围建议

不启动原先“旧8k采样 vs 新8k采样胜出”的矩阵。若资源与proxy核对支持，建议改为**同一V1母版下8k→8k与16k→8k，两source folds、seed0，共4run**。选择V1只是定义可追溯的同一几何，不称它优于V0；该矩阵回答输入密度能否转化为预测收益，不回答采样方法优越性。

另一方案是保留V0作为两臂的共同母版比较8k/16k，但需要补齐V0-16k资产；不能把V0-8k与V1-16k差异解释为纯点数作用。此二选一必须明确确认，不同时扩张成8run。

输出先固定8192、query256、中心[512,256]，不同时加proxy或输出点数。共同GT、训练曝光、前处理和数值合同必须一致。若16k不能被入口利用或受限资源不能运行，先形成合法单基线，不硬凑四次训练。

本次结论为源码合同审阅，不是实际proxy保留率证明、GPU资源通过或完整P3。科学文档规范用于区分已核对事实、理论尺寸和待验证项；未新增通用工具链。
