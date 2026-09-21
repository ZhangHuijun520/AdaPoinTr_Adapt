# Cranial-SCQR v1.1 完整实验归档说明

**日期：**2026-09-21（UTC）  
**归档协议：**`cranial-scqr-v1.1-complete-experiment-archive-v1`  
**性质：**服务器端运输归档及恢复核验说明，不构成新实验、训练、推理、数据访问或 Round B 授权。

## 1. 归档目的

本归档用于长期保存 Cranial-SCQR v1.1 从 P0 数据审计、L1/L2/L3 验证、L4 Round A 八条训练与 BNCal 审计链、development 正式评估、Round A-I QC 同权重干预、数值负对照诊断，到 Q0 反向推理干预和最终科学报告的完整可审计材料。归档同时保存与本研究线直接相关的协议、授权、配置、launcher、分析器、契约测试、核心实现和完整性材料。

归档的目标是让研究者能够回答以下问题：使用了什么协议和授权；执行了哪些候选、fold、seed 和条件；成功与失败尝试分别是什么；正式结果及统计结论是什么；哪些源文件参与了实验；归档是否可无损恢复；哪些内容应进入 GitHub；哪些数据和权重被明确排除。

## 2. 包含范围

- `docs/cranial_scqr_v1_research_2026_09_10/` 下的研究计划、协议、授权请求/回执、机制复盘和正式中文实验报告；
- 两套 Cranial-SCQR v1.1 配置目录，包括 L1 生成配置和 L4 实际授权配置；
- 名称绑定到 Cranial-SCQR v1.1 的 launcher、runner、analyzer、audit 和 synthetic contract 工具；
- `models/AdaPoinTr.py`、`models/cranial_scqr/*.py`、训练入口、数据接口及实验直接使用的关键 `utils/`；
- `logs/cranial_scqr_v11/` 下的全部现存审计材料，包括 canonical 正式结果、训练完成回执、tmux 日志，以及有明确失败回执的被替代尝试；
- 归档级 artifact inventory、GitHub 内容清单、payload SHA256、freeze receipt、创建环境和恢复验证报告。

失败或被替代的尝试保留是为了形成完整审计链，不应与 canonical 正式结果混合解释。canonical 科学结论仍以 development v2、Round A-I protocol-v2/run1、negative-control diagnostic v3、Q0 reverse intervention v2 及最终中文实验报告为准。

## 3. 明确排除

归档不包含任何原始数据、NPZ payload、confirmation20、official test、old monitor、MUG payload、checkpoint 二进制、optimizer/training state 二进制、预测点云、Git 元数据、认证信息、密钥、令牌、Cookie、缓存、`.pyc`、`.orig` 或无关仓库内容。

因此，本包是“完整实验审计与可复核实现归档”，不是包含数据集和模型权重的独立可运行镜像。八条训练回执中保存了训练与 BNCal checkpoint 的 SHA256，可用于和单独保管的权重核对，但这些哈希不能替代 checkpoint 本身。

## 4. 关键冻结结论

- 八条 B0/A1/Q0/QC、Fold A/B、seed-0 训练均记录 `TRAINING_AND_BNCAL_PASS`，各 101 次遍历、3939 optimizer steps；
- Round A development 正式评估的冻结门控为 `NO_GO`，关键失败项是 `QC-Q0=+0.1474303516079068 mm`，`round_b_authorized=false`；
- QC 同权重干预通过执行控制，分类为 `SPATIAL_ALIGNMENT_BENEFIT_ROBUST`，但即时空间收益仅约 0.00035 mm，不能扩大为实际或临床显著收益；
- Q0 反向推理干预通过原生复现、coarse invariance、状态不变和 β 精确恢复检查，分类为 `WEIGHT_STATE_DOMINANT_DIRECTIONAL`，同时 `Q0_REVERSE_EFFECT_INACTIVE`；
- 上述权重状态结论仅来自每折 seed 0，来源骨骼 bootstrap 不包含训练种子方差，不能声称已经证明跨 seed 因果优势；
- 当前 Q0/QC 配置的 `mamba_adapter.enabled=false`，这些结果不能作为 Mamba 增益证据。

## 5. 完整性与恢复方法

归档根目录中的 `metadata/files.sha256` 覆盖除其自身之外的全部 payload。`artifact_inventory.tsv` 列出项目源文件的角色、字节数和 SHA256；`github_content_manifest.tsv` 只列入建议提交到本机规范 Git 仓库的代码、配置、协议和报告，不含运行日志。

服务器创建压缩包后，必须在独立临时目录解压，并依次完成：payload SHA256 验证；现有结果级 `files.sha256` 验证；JSON 语法验证；八条训练完成回执的状态与步数验证；Round A、QC intervention 和 Q0 reverse intervention 的冻结语义验证。最终运输包的 SHA256、字节数、tar 内容清单和外部恢复回执作为独立交付文件保存。

## 6. Windows 与 GitHub 边界

Windows 目标目录 `E:\ResearchBackups\AdaPoinTr` 与服务器不是同一文件系统。本任务只能在服务器生成运输文件，不能把 Windows 路径转换成猜测的 Linux 路径，也不能声称文件已经在本机归档。只有研究者将所有交付文件下载到该目录、核验压缩包 SHA256/bytes，并确认恢复回执后，才能将其视为有效本机备份。

服务器项目当前不是 Git 工作树，因此不得在这里伪造 commit、annotated tag 或 GitHub push。`github_content_manifest.tsv` 应在本机规范仓库 `E:\Codex\2026-06-06\mamba-ccf-c-1-high-resolution` 中逐项同步和复核，再由研究者在 `feature/mamba-v12-mechanism-dev` 分支完成 commit、annotated tag，并推送到 `ZhangHuijun520/AdaPoinTr_Adapt`。推送前仍需检查本机工作区的既有修改，禁止无关暂存或强制推送。

## 7. 删除边界

本次归档不删除、移动或覆盖任何服务器实验文件，也不删除归档运输文件。即使压缩包和恢复核验均通过，在研究者明确确认六个交付文件已下载到本机并通过哈希与恢复核验之前，也不得提出或执行服务器清理。
