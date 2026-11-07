# P2 H1 最小实施、人工CPU验证、P3与首个待授权request

日期：2026-11-06。状态：**本机 implementation-only 完成；首个 Fold C request 为 AWAITING_EXPLICIT_USER_AUTHORIZATION**。

## 实际完成内容

新增两个隔离候选文件：

- `outputs/cranial_bcsp_mamba_p2_20261106/H1_implementation_v1/bcsp_p2_h1_training_entry_v1.py`。
- 同目录 `bcsp_p2_h1_training_runtime_v1.py`。

入口继承P1的文件策略、数值配置、资源监测与启动生命周期，只允许与冻结M0基线相比增加唯一H1配置；检查基线request/正式审计、P3及最终实现哈希。模型验证保留其他可选目标关闭，只允许当前H1。原母版模型、Mamba encoder、factory、provider和P1 runtime均未修改。

runtime仍调用母版原始`get_loss()`，不在外部重复增加H1。仅新增detach后的O(N)分量日志：`H1_centroid`、`H1_radius`、`H1_raw`、`H1_weighted`、`loss_without_H1_derived`。最后一项明确为总loss减加权H1的推导值，不是假装独立重新计算的CD。没有额外完整forward或Chamfer计算。

H1固定：`centroid_radius`，weight=0.1，beta=0.1，eps=1e-6；两项batch平均后乘0.5。保留cvar_fraction=0.1接口字段，但不执行CVaR分支。目标、采样、8k→8k、优化器、初始化与3900-step合同不变。

## 验证结果与边界

唯一一批人工CPU验证 **34/34通过**。使用本机既有PyTorch CPU环境，fixture与全部产物保留在项目内全新目录：

`outputs/cranial_bcsp_mamba_p2_20261106/H1_implementation_v1/artificial_cpu_batch_v1`

验证包括：

1. 从母版源码AST提取并执行原始H1与`get_loss()`，证明OFF保持原损失、ON恰好增加一次0.1H1。
2. 平移/正交变换、batch归约、排列、有限差分、坍缩、等矩异形与固定epsilon的缩放局限。
3. H1直接梯度进入coarse、不直接进入下游相对位移head；日志不修改梯度。
4. H1唯一配置、其他目标关闭、更新/模型配置漂移拒绝。
5. 完整`authorize()`路径，使用真实元数据验证器与420行人工元数据；拒绝无授权、runtime绑定错误、身份及实现漂移。
6. 微型人工几何模型执行原3900步生命周期，核对100遍、31200曝光、300丢弃与3900条H1日志。

这里的3900步是**人工微型模型的CPU契约验证**，真实科研模型训练次数为0。未构建真实Mamba/PointNet2模型，未访问真实数据、checkpoint或GPU；CPU通过不证明CUDA等价或科研收益。

P3已通过。AST差量复核确认：剔除新增日志后，训练主循环与P1相同；其余runtime函数不变。CPU使用的元数据验证函数与实际服务器绑定版本的`validate_static/bind_metadata/verify_qualified_receipt/validate_order` AST一致。原模型、factory、encoder和runtime哈希保持不变。

## 首个Fold C待授权request

文件：

`outputs/cranial_bcsp_mamba_p2_20261106/H1_implementation_v1/first_FoldC_request_v1/transport_payload/M_H1_foldC_seed0_training_execution_request_v1.json`

完整SHA256：

```text
e5fa766a408762a9a3bf3e2bd1dc993886b3422f7afaf69f9a994dc0ca20413d
```

只允许一个M-H1 Fold C seed0 run：315训练例、8k输入/8k输出、batch8、3900更新、100遍、31200曝光。由P1相同scratch初始化重建，不从已训练checkpoint继续训练。

本轮没有创建Fold D request，不授权T-H1、多seed、评价、BNCal、resume、重试或依赖安装。Fold D之后保持同一科研合同，不能根据C折效果改参。

固定未来输出：

`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2_h1/M_H1_foldC_seed0_20261106_v1`

资源阈值继承P1：wall 86400s、RSS 8GiB、SMI占用≤22528MiB、torch峰值allocated/reserved≤20GiB、产物≤2GiB、空闲磁盘≥4GiB。PID仅为诊断信息，不新增namespace硬证明。监测不等于硬隔离。

当前身份仅绑定最后验证的`v2iwsa-0`与原GPU UUID；**本轮未连接服务器，未声称容器仍在线或资产齐备**。实际安装/材料化前必须重新检查当前身份、空闲GPU、复用资产哈希、目标不存在与父目录状态。身份不符即停止，不能自动重绑定。原P1已清理的权重不用于新run初始化；该scratch训练不要求恢复最终权重。

## 手工上传的四个文件

都位于：

`E:\Codex\2026-06-06\mamba-ccf-c-1-high-resolution\outputs\cranial_bcsp_mamba_p2_20261106\H1_implementation_v1\first_FoldC_request_v1`

1. `bcsp_p2_H1_foldC_pending_20261106_v1.tar.gz`
2. `bcsp_p2_H1_foldC_pending_20261106_v1.tar.gz.sha256`
3. `bcsp_p2_H1_foldC_pending_20261106_v1.tar.gz.bytes`
4. `bcsp_p2_H1_foldC_pending_20261106_v1.tar.gz.contents.sha256`

压缩包26397字节，SHA256：`b5b21992ae94283ee69f550bc2b1149f2c0bd89d5dbf204b8b074628831660fb`。

包内仅有候选代码、H1配置、基线request/冻结审计、公式、CPU结果、P3、待授权request与不覆盖安装映射；不含权重、真实点集或测试fixture。

当前**没有**材料化真实授权回执、runtime控制文件、单次launcher、启动claim或服务器输出目录。request仅保存未来路径及命令模板。人工CPU测试目录中的合成授权记录明确仅用于fixture，与真实request无关。

后续必须在完整request哈希的单独授权范围内执行；开始前只做必要的身份、资产及不覆盖就绪核对，不重复通用框架或整套GPU preflight。失败即停。
