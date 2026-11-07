# Fold D M-H1 待授权训练 request 与运输说明

日期：2026-11-06。状态：**AWAITING_EXPLICIT_USER_AUTHORIZATION**。

本轮仅完成本机request准备和静态核对，未连接服务器、运行测试、安装、材料化控制文件或启动训练。

## Request

文件：`transport_payload/M_H1_foldD_seed0_training_execution_request_v1.json`。

完整SHA256：

```text
305ce3380ae7b951c7180907f63842abc51eae5d9dec817e2a5ad89718fdd390
```

只允许一次M-H1 Fold D seed0训练。合同保持：315例/63训练来源、batch8、8192输入/8192输出、256 coarse、3900 updates、100 traversals、31200 exposures、300 drop-last。初始化保持P1 M0 D的相同scratch构造，不读取最终checkpoint作为初始化。

H1仍为已有母版`centroid_radius`：weight=0.1、SmoothL1 beta=0.1、eps=1e-6；两项batch均值后乘0.5，未加入CVaR。模型、采样、数据选择、优化器、LR、BN日程与资源阈值均未依据C折loss修改。

## 绑定与复用

- 冻结M0 D基线request：`55793bca2fa9472d45b3cca0b9598154cdb12a84a3eb89633daa52b85a039d5f`。
- 冻结M0 D正式训练后审计：`f65c3dd7d82814f705a09f11f5fa95f2583fba71380cdd29cd8b9f4f59e5bb61`。
- 复用P2入口：`cdcc7ea20e6c16791ddc3f5665cb8404852ed50b7d9934301def21f24e4d3e47`。
- 复用P2 runtime：`ef67d09dc8b3a645aebe455655b69aa37d7f3edf104349a41b1740198596b57d`。
- D折原始order：`4f68edd55912be0dccfb3d2a1cc72e499d3d499a36aa5f3788550145b3095720`，已本机核对全部100遍批次结构与基线审计的canonical order一致。
- 复用Fold C已经安装的H1静态配置、公式与原P3记录。未修改或重新生成其代码，不重复运行34项CPU验证或GPU preflight。
- Fold C H1正式训练后冻结审计作为来源证据存入新包；它不提供调参依据，不被解释为H1性能通过。

复用的入口、runtime、配置、公式和P3保持服务器原路径：`/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p2_h1_foldC_20261106_v1`。这不是D折读取C折数据：D折data_root、QC、来源与order来自冻结M0 D request。执行前需重新核验所有复用文件的精确哈希。

## 新路径与资源

- 新安装根：`/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p2_h1_foldD_20261106_v1`。
- 新输出：`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2_h1/M_H1_foldD_seed0_20261106_v1`。
- 新tmux：`bcsp_p2_H1_D_seed0_20261106_v1`。
- 授权/runtime/launcher/claim均冻结为新安装根下`control/`中的独立路径；当前尚未创建。
- wall86400s、RSS8GiB、torch峰值20GiB、SMI22528MiB、产物2GiB、最少空闲磁盘4GiB，与C折一致。PID仍仅作诊断。

身份继续绑定已冻结的`v2iwsa-0`与原GPU UUID，本轮没有重新查询服务器。任何身份、资产、空闲资源或目标不存在性不符均停止，不自动重绑定或恢复依赖。

## 手动上传的四个文件

都在本说明同一目录：

1. `bcsp_p2_H1_foldD_pending_20261106_v1.tar.gz`
2. `bcsp_p2_H1_foldD_pending_20261106_v1.tar.gz.sha256`
3. `bcsp_p2_H1_foldD_pending_20261106_v1.tar.gz.bytes`
4. `bcsp_p2_H1_foldD_pending_20261106_v1.tar.gz.contents.sha256`

压缩包大小：**15707 bytes**；SHA256：`3c5120d8c3ea8279a1ff8858db12e8f1598e1d51be96f7506b6e6f6064f123e2`。

包内4个新安装文件：M0 D基线request、M0 D基线审计、Fold C H1冻结审计、当前D request；另有不覆盖安装映射。不含代码副本、真实点集、checkpoint或已授权控制材料。

完整request哈希获单独执行授权后，才可按冻结范围核验上传与当前资产、不覆盖安装，依序材料化授权→hash→runtime→hash→launcher，并启动唯一一次训练。失败即停，不自动retry/resume，不运行评价或BNCal。
