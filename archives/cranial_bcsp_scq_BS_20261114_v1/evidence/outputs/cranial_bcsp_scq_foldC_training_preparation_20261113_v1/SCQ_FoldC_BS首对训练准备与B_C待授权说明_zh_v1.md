# SCQ-v2：Fold C B/S首对训练准备与B_C待授权范围

日期：2026-11-13。状态：**AWAITING_EXPLICIT_USER_AUTHORIZATION**。

本轮完成必要训练入口/bridge绑定、34项人工CPU检查、本机P3及最终B_C request冻结。没有连接服务器、部署、读取真实点集/权重、运行GPU或启动训练；不重复已经正式冻结的CUDA准入。

## 1. 科研比较与顺序

比较对象为**同设备重新训练的B（原LQI）和S（SCQ-S）**，不是把旧异设备LQI分数当配对基线。首折固定B_C→S_C；两者都从scratch开始，不以B权重初始化S。

本轮同时冻结C/D元数据、训练顺序及同设备合同，后续B_C→S_C→B_D→S_D不依据C折loss/分数调D。F对照的公式和初始化已在此前冻结，仍按原计划条件式N4另行决策，不在本次执行范围。

**本次只创建B_C待授权request。** S_C必须待B_C训练完成、正式冻结并绑定B的共有初始化/顺序/身份后，另建request、另行授权。没有创建S_C或Fold D执行内容。

## 2. 原训练合同保持

| 项目 | 冻结内容 |
|---|---|
| 数据 | 原SkullBreak V1来源/采样；每折63训练来源、315病例，21开发来源、105病例；confirmation20排除 |
| 输入/输出 | 8192→8192；coarse256；原完整骨块表面目标 |
| 初始化 | seed0，原母版与private encoder/decoder初始化；S额外加载此前固定SCQ字节；共有初始状态须匹配native CUDA指纹 |
| 批次/更新 | batch8、100 traversals、39更新/遍历、**3900更新、31200曝光、300 drop事件** |
| 优化器 | 原AdamW lr1e−4、betas0.9/0.999、eps1e−8、clip10、原LR与BN schedule |
| 参数分组 | 原runtime原字节复用：矩阵5e−4，1D/bias及显式SSM no-decay标记0；SCQ的W1/W2权重5e−4、bias0 |
| loss | 原CD(Qused,G)+CD(P,G)，denoise0，无新监督、辅助loss或GT定位 |
| 数值 | FP32、TF32=false、原确定性设置；有限梯度非位级确定性继续披露 |
| 最终权重 | epoch99/step3900固定最终checkpoint，不择dev最佳epoch；不warmstart/resume/自动重训 |
| 禁止后续 | 不自动BNCal、development evaluation或继续下一臂 |

两折共享批次计划与各自原63来源绑定均已本机复核，只读取metadata，没有重新读取真实NPZ数组或生成新采样。qualified QC包装文件因运输路径重绑定重新生成，底层原QC、manifests、fold binding、静态配置与order文件保持字节哈希，不声称重新做了几何QC。

## 3. 最小入口接入

新增`bcsp_scq_training_entry_v1.py`和`bcsp_scq_training_bridge_v1.py`，原3900-step runtime未修改：

`runtime SHA256 = 939e317dd447d04c62897849c0230f1918dc65c46ec556acdb60c9d69dfebeee`

入口核验正式SCQ CUDA冻结证据、同设备/软件/模型身份、315训练允许清单及原order；用同一个已准入SCQ factory构造B或S。bridge直接委托原runtime，不另建训练循环或优化器，也不引入新runner。

必要日志通过原模型及loss模块的只读forward hooks获取：

- 每步coarse/dense质心、范围，Q0范围和Delta均值/最大范数；B的Delta记为0。
- 原coarse CD和dense CD各一次的值，不为记录额外计算loss或forward。
- 每步case IDs与冻结plan对应；完整3900条日志是finalize前置条件。
- 共有初始化指纹、实际新参数decay、模型身份与有限非确定性说明。

训练中保存轻量摘要，不逐步导出8192点数组。后续Native评价的Q0/Qused/Delta/P全量保存仍属于未来预测入口范围。

checkpoint中原`stage=BCSP_INPUT_DENSITY_V1`保持为历史格式；新`run_identity.json`标明`CRANIAL_BCSP_SCQ`，不把旧字段误当本次科研阶段。

## 4. CPU验证和P3

最终34项人工CPU检查通过，记录在`cpu_batch_v3/result_v1.json`；`training_entry_P3_v1.json`为`SCQ_TRAINING_ENTRY_LOCAL_P3_PASS`。

覆盖：实际完整authorize路径与真实冻结CUDA证据/metadata；315清单及100×39顺序；身份/来源/授权/单向runtime错误拒绝；S缺少正式B证据时拒绝；原optimizer分组与SSM标记；B/S人工分派、实际SCQ残差和日志hooks；3900日志最终守卫；原bridge委托边界；实际文件策略中的精确SCQ源码/二进制读取、训练NPZ限定、最终checkpoint限定及整数fd兼容。

CPU分派采用tiny人工模型和runtime/bridge spy，每臂仅人工forward/backward一次、**0 optimizer step**；没有执行真实3900步或重做CUDA。最终request另做完整authorize离线语义复核，315病例、63来源及资源合同一致，真实授权/runtime/launcher均未材料化。

两次先前fixture失败均保留：v1未把本机镜像传入嵌套metadata reader；v2已通过前33项后，测试变量名同时用作CUDA证据目录与CPU Generator，导致最后策略fixture构造失败。v3只修测试镜像/变量，生产入口和科研合同未因失败改动。

## 5. 资源与尚未证明的内容

训练资源保持原预算：24小时外部timeout，TERM后5秒KILL；RSS8GiB、PyTorch allocated/reserved各20GiB、物理SMI22,528MiB、输出2GiB、磁盘剩余至少4GiB。资源失败即停，保留证据、不自动重试或resume；PID只作诊断，不要求新host procfs。

此前人工batch8 CUDA峰值allocated12.64GiB、reserved13.80GiB已正式冻结，但未分配真实AdamW状态或训练3900步，不能将其当长期训练显存/稳定性保证。本request保留原监测阈值，没有为“保证开跑”放宽资源或数值约束。

本轮没有重新确认服务器在线状态；身份继承最近正式冻结的`t6ibfm-0`、GPU `GPU-aa9e6ffb-fdbb-1836-1c32-7244231d3714`、driver570.190。执行授权后必须新鲜核验当前身份/资源、复用代码/provider、上传包和315训练文件哈希；不自动接受新设备或更换依赖。

## 6. 最终B_C request及运输包

请求：`pending_transport_v1/payload/SCQ_B_FoldC_training_execution_request_v1.json`，状态保持待授权。

完整SHA256：

`132ea92fde3fb871f4bad6d78d18d625fc83c85e9e2719d52ef7cd2b9c3b9396`

运输包：`pending_transport_v1/bcsp_scq_B_foldC_training_pending_20261113_v1.tar.gz`，**439,095 bytes**。

SHA256：

`11844500cc5ad90c69941090943c18c043d141e149cf95158276e7be68abfa93`

同目录还有完整`.sha256`、`.bytes`、`.contents.sha256`三个校验文件。包内24个不覆盖目标及1份安装映射，共25成员；含必要入口、原字节metadata/runtime和准入证据，不含真实NPZ或checkpoint。既有SCQ模型文件和初始化二进制直接按已准入哈希复用，不重新上传。

手动上传四文件至`/home/jovyan/`后，单独授权上述request完整SHA256，才可按冻结映射核验、不覆盖安装与启动唯一一次B_C训练。

冻结安装根：`/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1`。

冻结tmux：`bcsp_scq_B_foldC_20261113_v1`。

冻结输出：`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_B_foldC_seed0_train_20261113_v1`。

没有材料化真实授权回执、runtime、launcher或单次claim。本轮材料仅保存本机项目目录，未提交/推送GitHub或清理服务器。
