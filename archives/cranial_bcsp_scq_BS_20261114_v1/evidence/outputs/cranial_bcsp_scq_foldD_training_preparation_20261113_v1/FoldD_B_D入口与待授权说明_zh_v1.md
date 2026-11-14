# Fold D B_D入口适配与待授权训练

日期：2026-11-13。状态：**AWAITING_EXPLICIT_USER_AUTHORIZATION**。

本次按原冻结B_C→S_C→B_D→S_D顺序准备B_D。C折两臂已经正式冻结；没有使用其训练loss选择超参数、病例、采样或训练预算，没有评价补全效果。

## 1. 最小接入与验证

新增`bcsp_scq_foldD_training_entry_v1.py`：从已验证的C入口v2复制，仅修改Fold D准入、run名前缀、FoldD元数据/配对选择、未来S_D的B_D冻结检查以及run_identity折名。

所有其他函数（含模型分派、原loss日志、main、UTC策略及launcher）经AST比较保持一致；复用原bridge、模型、provider、initializer、3900-step runtime，未重新训练/修改生产源码或重复GPU准入。

**27项本机CPU/标准库合同检查通过**，覆盖实际完整authorize路径与真实已冻结metadata/native admission、D折清单和order、禁止交叉Fold C元数据/设备/授权漂移、B_D先于S_D、原3900最终日志守卫以及实际发出的D折run_identity。没有导入torch模型或打开真实点集/checkpoint；人工授权字典只在内存中存在。

`FoldD_training_entry_P3_v1.json`为限定本机P3，通过并继承C入口/CPU/正式CUDA证据。最终request另做完整authorize语义检查及短launcher渲染检查。尚未实际核验当前服务器、部署或运行。

## 2. 原科学合同保持

- 首个C训练前冻结的FoldD原QC/来源、63训练来源315病例、21开发来源105病例，confirmation20排除。原metadata字节保持，只切换已存在的FoldD记录。
- 原V1表面采样，8192输入/8192输出、256 coarse；B_D为原LQI，无SCQ头。
- seed0、scratch；batch8，100遍历×39更新=3900更新、31200曝光、300 drop；原批次顺序，不把C权重用于warmstart。
- 原AdamW、权重衰减分组、LR/BN schedule、clip10、原coarse+dense CD、denoise0，不新增监督。
- FP32、TF32=false、原确定性标志及有限Mamba梯度非位级确定性披露。
- 同`t6ibfm-0`、同GPU UUID `GPU-aa9e6ffb-fdbb-1836-1c32-7244231d3714`、driver570.190和原软件合同；实际执行前重新核验，身份变化停止。
- 原预算24小时timeout、RSS8GiB、torch allocated/reserved各20GiB、SMI22528MiB、输出2GiB、剩余磁盘至少4GiB，失败即停，不自动重试或resume。

原runtime最终checkpoint仍使用历史stage字段，实际run_identity标注SCQ与FoldD，不改checkpoint格式。原GPU准入没有分配AdamW状态，实际长期训练资源仍由原guard约束。

## 3. B_D request

请求：`pending_transport_v1/payload/SCQ_B_FoldD_training_execution_request_v1.json`。

完整SHA256：

`4f1db753d12693eb909d5d795997b542ca7a2082b73b6737521a1154f1777ed4`

仅B_D一次训练。S_D待B_D完成并正式冻结后再创建request。本次不生成真实授权回执/runtime/launcher/claim，也不运行BNCal、evaluation或额外实验。

## 4. 运输与不覆盖部署范围

四文件在`pending_transport_v1/`：

- `bcsp_scq_B_foldD_training_pending_20261113_v1.tar.gz`
- 同名`.sha256`
- 同名`.bytes`
- 同名`.contents.sha256`

包大小 **16423 bytes**，SHA256：

`5950205c3719fb0f9bd12e65685099c93f87dd644c3b54ae26df6962994d242c`

包内4个新增目标及1份安装映射，共5成员。新增为D入口、D本机P3、D元数据就绪说明及B_D request；原32个已安装payload复用并须重新核验，不重传模型、点集或权重。

安装仍在已存在的`/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1`下新增版本文件，避免改变原metadata读路径；该路径名称中的FoldC只是已有工具容器，不代表此次使用C折数据。

全新控制目录：`control_B_D_v1`。

全新tmux：`bcsp_scq_B_foldD_20261113_v1`。

全新输出：`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_B_foldD_seed0_train_20261113_v1`。

请上传四文件至`/home/jovyan/`，再单独明确授权request完整SHA256。授权后先核验当前身份/资源、上传、复用资产和**Fold D的315个训练文件**哈希；4新增目标及控制/输出须不存在，不覆盖写入。不能沿用C折控制/claim或C折训练payload核验结果。

## 5. 当前结论

准备完成不等于训练准入或效果改善。当前仅锁定既定D折B/S比较的首运行；所有性能结论仍待原协议Native开发集预测、正式冻结和统一评分。

证据：`static_review_v1.json`、`FoldC_to_FoldD_entry_diff_v1.patch`、`CPU_contract_v1/result_v1.json`、`FoldD_training_entry_P3_v1.json`、`final_full_authorize_review_v1.json`及`delivery_receipt_v1.json`。
