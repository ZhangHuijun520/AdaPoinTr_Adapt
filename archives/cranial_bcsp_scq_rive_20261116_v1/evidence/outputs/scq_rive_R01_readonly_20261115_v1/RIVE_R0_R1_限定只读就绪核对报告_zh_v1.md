# SCQ-RIVE模式A：R0–R1限定只读就绪核对

日期：2026-11-15。范围：用户授权的一次限定只读核对。状态：**核对完成；模型/资产可复用，但训练入口和矩阵空间预算尚待收尾，不构成训练准入。**

## 1. 结论

没有发现需要更换模型、重采样数据、重装provider或重新恢复六个历史终态权重的问题。当前设备与历史RF-Static_D成功训练及后续RF/DAC诊断使用的qx2k0r设备相同，实际相关源码和依赖哈希也一致。可以继承既有实际CUDA执行证据，**本轮没有理由再重复相同模型的人工GPU preflight**；若后续设备/provider或模型路径改变，再按精确差量判断。

目前不能直接复用旧request或入口启动RIVE。最小缺口为：

1. **RIVE专用训练入口与双臂bridge**：旧入口硬绑定SCQ-RF六运行顺序、S-ref/其他臂冻结证据、旧run ID、旧授权schema和设备身份；旧bridge仅允许Static。需要新版本调用层，保持RF公式和原3900-step runtime不变。
2. **资源合同显式接入**：本计划每run墙钟3600秒，旧入口/原静态配置为86400秒。新调用层必须明确实际生效的3600秒上限及计时口径，不能只在文档改数字，或静默修改旧静态文件/旧守卫。
3. **完整矩阵空间尚不充足**：当前剩余8.485GiB，足够首个run按2GiB输出上限+4GiB余量启动；不能据此认定四run和预测归档均有空间。首批四训练的2GiB/run最坏输出已达8GiB，加4GiB余量需12GiB；若采用计划12GiB总新增包络，则需16GiB。后续需明确分阶段归档/保留安排或增加空间，本轮没有删除文件。

完成最小接入、针对性人工CPU验证和P3后，才可创建首个Static_C待授权request。未来预测入口的M/F/z/邻居同次采集在预测阶段适配，不作为首个训练入口的额外结构开发。

## 2. 现场身份和资源

身份观察时间：服务器`2026-11-15T10:22:51+00:00`，即北京时间18:22:51；其后同轮哈希/文件核对均重新断言相同hostname与uid。

| 项目 | 实测 |
|---|---|
| WebShell目标与hostname | shu-common-25721452-notebook-qx2k0r-0 |
| 用户 | uid1000 jovyan，gid100 users |
| 项目实际目录 | /home/jovyan/adapointr_work/PoinTr |
| GPU | NVIDIA GeForce RTX 4090 D |
| UUID | GPU-383d118a-368c-94e3-166a-cad3efab8fd7 |
| driver / SMI总显存 | 570.190 / 24564MiB |
| 当时SMI占用 / 利用率 | 1MiB / 0%；compute-apps查询无记录 |
| /home/jovyan可用字节 | 9,111,076,864，约8.485GiB |
| Python | /opt/conda/envs/adapointr-mamba/bin/python3.10，3.10.20 |
| 软件文件身份 | torch2.4.1+cu118、NumPy2.2.6、timm1.0.27的已绑定元数据/源码哈希匹配 |
| CPU/内存可见信息 | os.cpu_count=64；MemTotal528006348kB，MemAvailable496065772kB |
| Git | 项目不在Git工作树内；未初始化、提交或修改Git |

CPU/内存信息是容器可见的系统视图，不等于专属CPU配额或保证可独占的RAM；本轮未扩展cgroup/PID映射调查。GPU空闲与磁盘是当时快照，执行前仍须新鲜检查。软件版本来自精确文件及解释器信息，没有导入torch或启动CUDA来查询。

首次受限上下文调用WSL返回E_ACCESSDENIED；经工具批准后，在非管理员上下文完成读取。没有修改WSL、代理或登录配置。远端身份命令末尾Git查询返回非仓库，使该组合命令退出1；此前身份、GPU和磁盘查询成功，这不是训练失败。后续三次有界文件核对均返回0。

## 3. 核验的冻结资产

第一组28条：encoder/factory、LQI、SCQ、RF、旧训练entry/bridge、runtime/contract/budget、必要读取辅助工具、两份初始化、静态配置、frozen scope、两折order、两折qualified、8192 manifest、fold binding及既有QC文本，全部大小/SHA匹配。

第二组32条：scope中14份实际项目源码、base_model.yaml、PointNet2实际包装器/编译模块、Python二进制、Mamba/causal-conv相关源码/二进制与固定软件元数据，全部大小/SHA匹配。仅绑定实际依赖，没有扩展环境库存。两组合计60个文件，无重复；未执行这些源码或导入扩展。

关键身份：

| 资产 | 当前核验SHA256 |
|---|---|
| RF residual v2 | c50cbdb0986fafe3ff2309ef8c02d74fdc5e651218c71f4bb13a87bacefc726a |
| RF factory v1 | 6e243f7a6463241f6c24c6feb6928bde9499ffd3a17afe1442eca54fd6738570 |
| 原training runtime | 939e317dd447d04c62897849c0230f1918dc65c46ec556acdb60c9d69dfebeee |
| SCQ初始化bin | e7858ee3ae4c0bf6d68e447727c36514f5bbab42b95e1935f1686620ec089416 |
| RF初始化bin | a4024fbdb49feb41c609ae1171f04c2cb14ab794fc3663855d81395c6a1ea79e |
| 编译PointNet2实际_ext | e70d00108bacba4a905dc011f4b8c4868f06ec2d44d8e322148e2e452578fbb5 |
| selective_scan CUDA | 5e6a5bfabe7628720631568ec364426e6066da9a9a0946302ebe9fb86f4aa58c |
| causal_conv1d CUDA | 6ac9c334498773ee337503094d7b5aae4b0f38fa3ba8a0dcd81cca707f48a79a |

初始状态需准确表述：两个bin分别保存SCQ和RF头初始值，不是全部40827847参数的一份完整初始化checkpoint。backbone以原factory的seed0、encoder私有seed20261104、LQI decoder私有seed20261110构造；两个头加载冻结字节。既有完整共同状态摘要为`b7e5b640c1f0e709ab6697139db1267584266a51b4e0e29f2d5217bfd1236cc5`，属于历史RF冻结证据，本轮没有构造模型重算该摘要。未来新入口的人工CPU验证/P3应保证构建合同未改，实际训练在更新前记录并比较相应初态。

PointNet2必须使用当前编译provider；Chamfer沿用明确选择的PyTorch cdist分支。现有helper明确要求compiled Chamfer为None且PointNet2非fallback。没有安装、编译或导入来重试后端。

## 4. 唯一结构差异与完整训练合同

从当前哈希对应的本机源码进行只读核对：

- Static的第二头复用N0，Requery以Q1在M中重新KNN8；两者都按Q1重算相对几何。
- 实际Memory为256×3、特征256×384、全局1024，描述子1802；第二头1802→128→3；参数增量231171。
- RF factory把Q2交回原SCQ coarse handoff，位于query MLP之前；继续进入decoder坐标、FC中心、返回coarse与loss，而非只更新日志。
- 两臂联合训练可导致所有参数分化；本次对照估计训练配置总效应，不能解释为固定同权重的单次邻域因果效应。
- 原runtime固定100 traversals、39 batch/traversal、batch8、3900更新；AdamW lr1e−4、betas(.9,.999)、eps1e−8、clip10、decay5e−4/0；原LR与BN动量序列不变；保留FP32、TF32=false。
- 保留coarse+dense原loss，无BNCal、dev评价、resume或其他监督；最后epoch99/update3900保存。

旧Static_C `authorize()`要求旧stage/schema、S-ref参考、旧admission同身份、六run顺序；Static_D v2另绑定历史跨设备迁移凭据，旧bridge拒绝Requery。它们可作为实现参考，**旧执行授权已消耗，不得复用或靠换JSON字段绕过**。新RIVE入口应直接复用已核验的模型factory/runtime，建立新实验的配对合同。

## 5. 数据、fold和实际路径

服务器当前8192 manifest、fold binding、两折order等与本机副本逐字节相同，随后在本机读取这些文本做语义核对，没有执行训练合同测试或模型。

| 项目 | C | D |
|---|---:|---:|
| train来源 / 病例 | 63 / 315 | 63 / 315 |
| dev来源 / 病例 | 21 / 105 | 21 / 105 |
| 同折train/dev来源重叠 | 0 | 0 |
| order内更新 / 曝光 / drop | 3900 / 31200 / 300 | 3900 / 31200 / 300 |

总计84来源、420唯一病例，每源五缺损，D-only defective_bbox归一化、8192输入/目标，manifest字段一致。每个order的100轮均为39个不重复batch8和3个drop，组成该折完整315例，没有重生成order。

C/D开发来源互斥；两折train重叠42来源。C开发21来源全部位于D训练，D开发21来源全部位于C训练。这是交叉划分的既有结构，不是同折泄漏，但两折结果不能称为两个独立训练人群或盲测复制。

实际文件对应：

| 用途 | 服务器相对项目目录 | 数量 |
|---|---|---:|
| C train | data/bcsp_geov1_foldc_8192_seed0_v1/points | 315 |
| C dev | data/bcsp_geov1_foldd_8192_seed0_v1/points | 105 |
| D train | data/bcsp_geov1_foldd_8192_seed0_v1/points | 315 |
| D dev | data/bcsp_geov1_foldc_8192_seed0_v1/points | 105 |

共840个用途映射、630个唯一物理NPZ路径，全部存在、非链接、非空。本轮只stat这些已开放路径，**没有打开或哈希NPZ，没有重新验证数组、坐标或几何QC**；point内容身份继承冻结manifest/既有训练前哈希证据，执行前需按最终授权范围核验。manifest中的Windows raw路径仅作来源记录，没有在服务器引用或转换它们。

本机评分基础指标文件SHA重新核验为`af938519125b25b6d22d862dd4967dabef3be6d97d38e60eb9995ee7e9ce9766`，可继承A1/A2、E/J、未平方双向CD半和及风险边界。本次没有重评分、bootstrap或访问confirmation20。

## 6. 为什么无需再次相同GPU准入

历史Static_D正式冻结记录在当前UUID/driver上完成3900次forward/backward/step，56项核验通过，Torch allocated峰值13,955,896,320字节、SMI峰值14638MiB、elapsed约1512.83秒。当前源码/provider二进制精确一致；同设备后续Native与DAC诊断也有冻结记录。

这些是既有运行证据，不是本轮GPU测试。结合只改调用层的拟定范围，可复用它们，不再重复同模型preflight。新增入口仍需验证真实授权/读取/分派路径及错误回溯，不能因历史CUDA成功跳过调用层CPU回归。

如果实施时改变模型计算、loss、provider或换GPU，必须重新审查这个结论；不能将本次只读观察自动延伸到未来不同环境。

## 7. 建议的下一步限定实施范围（尚未授权）

建议一次集中implementation-only接入，生产候选以**RIVE训练entry、双臂bridge、对应人工CPU测试**为核心，不复制修改模型/数据/runtime：

1. 新stage、schema、全新run/output/控制路径，按fold/arm/seed0分派；取消对旧S-ref训练顺序和旧终态日志的执行依赖，保留其初态/顺序作为历史证据。
2. 绑定当前qx2k0r与GPU UUID选择器；以原RF factory、SCQ/RF初始化和原runtime为精确复用对象。
3. 同一新实验配对合同绑定两臂相同数据、共同初态、原完整order、优化器和最终3900步；首运行不伪造另一臂已冻结，后续臂绑定已产生的配对证据。
4. 3600秒实际墙钟、其余显存/RSS/单run输出阈值保持；采用新入口的外层限时与预算适配明确处理，旧静态配置/contract文件不覆盖、不放宽。
5. 集中覆盖完整authorize/实际加载顺序、双臂bridge、读取白名单、UTC先后顺序、原字节传输/短命令、参数与计数、初态保护、错误落盘的一批人工CPU回归。无需重新测试所有通用工具。
6. 完成P3后只创建首个Static_C待授权request；仍须完整SHA单独执行授权。后续预测同次Memory/F/z采集到预测接入时完成，不加到训练图。

空间应在request前写清：若先做首个run，可声明仅首运行空间就绪；不得标注整个矩阵PASS。若要一次冻结全矩阵容量，需先扩大可用空间或提出精确归档/保留方案。没有授权自动清理或下载/删除文件。

## 8. 证据文件及边界

- `scope_v1.json`：冻结的只读范围与第一组命令，最多96文件、源码/元数据/初始化8MiB、原生二进制768MiB、最多840个payload路径stat；单远端文件核对50秒。
- `assets_stdout.bin` / `assets_transport.json`：28项精确核对。
- `dependencies_stdout.bin` / `dependencies_transport.json`：32项精确核对；包含大型二进制流式SHA。
- `payload_metadata_stdout.bin` / `payload_metadata_transport.json`：路径与CPU/内存只读回传。
- `local_metadata_semantic_review_v1.json`：已核验相同字节的本机文本分析、fold/order计数、指标源码身份。
- `readiness_and_delta_review_v1.json`：本轮汇总、缺口与权限边界。

本轮只新增本机核对报告/回传证据，不新增服务器文件；没有修改生产源码、初始化、配置、provider或数据；没有下载/反序列化权重、NPZ payload读取、CPU模型测试、CUDA初始化、forward、backward、optimizer、训练、预测、评分、统计、部署或清理；没有创建execution request、授权回执、runtime或launcher。

**下一步最小动作是一次RIVE训练调用层implementation-only接入及针对性CPU验证/P3；空间安排须在训练request中闭合。不是继续扩大只读审计，也不是直接启动训练。**
