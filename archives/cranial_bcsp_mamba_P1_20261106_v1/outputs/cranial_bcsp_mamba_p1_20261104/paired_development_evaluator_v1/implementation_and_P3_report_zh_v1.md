# P1 Fold C 配对预测：implementation-only 交付与本机 P3

日期：2026-11-06。状态：本机实现及 P3 完成，仅生成待授权 request，未操作服务器。

## 实现与验证

新增两个隔离文件：`bcsp_p1_paired_predict_v1.py` 与 `test_p1_paired_predict_v1.py`。保持模型、factory、Mamba encoder、训练 runtime、真实点集与数值阈值不变。复用既有 GPU 准入，不再运行 preflight。

最终 CPU 批次 35/35 通过，涵盖真实清单的元数据配对、单向授权、严格最终 checkpoint 加载合同、只读 partial、eval/inference_mode、完整 210 次人工调用循环、调用前持久化 claim、首错停止、参数/BN 与 Python/NumPy/CPU RNG 不变、payload 边界和独占写入。生产入口还检查 CUDA RNG，CPU 测试未验证 CUDA 本身。人工完整预测归档 213 个成员均重新计算内容哈希；这只是人工 fixture，不是科研预测结果。

第一批 34/35 通过：来源检查错误地从旧索引读取 normalization；实际归一化记录在已冻结 manifest。保留旧源码快照、失败 stdout、fixture 及结果。限定修正为旧索引绑定输入、manifest 绑定 D-only 坐标与目标后，第二批 35/35 通过。未使用真实权重、真实点云 payload、服务器或 GPU。

P3 结果见 `local_P3_v1.json`；复核源码/测试哈希与语法、105 唯一输入/21 来源/每来源 5 缺损、两臂冻结训练证据、213 人工归档成员、既有 factory/encoder/helper/timezone 哈希及资源 Budget AST 不变。本机 P3 不代表真实 CUDA 预测通过。

## 冻结执行范围

固定 T0 → M0，各 105 例，共 210 次完整 forward；8k 输入/8k 输出、batch1、epoch99/update3900 最终权重、同一 V1 输入与顺序。训练/反向/优化器/BNCal/loss/warmup/TTA 均为 0。不读取 implant 数组，不进行 ICP、Oracle、GT 对齐或评分。每臂保留状态与四类 RNG 不变证据；异常停止，不自动重试。

全部病例保存 dense 预测和低维 coarse/dense 几何摘要。仅保存冻结顺序首例来源的五种缺损及 025/parietotemporal、072/random_2 的额外 coarse 点集：每臂 7 例、共 14 份。不增加 forward，不根据结果选例。摘要不作为已量化的根因解释。

资源：7200 秒，RSS 8 GiB，torch allocated/reserved 峰值分别 20 GiB，设备使用不超过 22528 MiB，输出不超过 1 GiB，磁盘空余至少 4 GiB。启动要求固定 GPU UUID、单卡可见、空闲显存使用不超过 256 MiB；SMI PID 只记录，不作命名空间归属推断。

权重内部 legacy stage 仍为 BCSP_INPUT_DENSITY_V1；通过精确 checkpoint SHA256、P1 训练审计与配对回执确认身份，不修改权重。Fold C 开发输入复用原 D 训练存储目录中的文件，通过 C 开发来源清单和精确哈希绑定，目录名字不等同于逻辑划分。

## 最终 request 与运输

request：`transport_payload/FoldC_T0_M0_development_execution_request_v1.json`

SHA256：`d4e5665e7c285f0d8246e6ca3b104d6f003afd4faf35683e8170aa9ec8215418`

状态：`AWAITING_EXPLICIT_USER_AUTHORIZATION`。未创建真实授权回执、runtime、launcher、launch claim 或 tmux。包内 .sh 仅为含占位哈希的待材料化模板。

运输包：`bcsp_p1_foldC_paired_development_transport_v1.tar.gz`，52128 bytes，SHA256 `cf125586d868d0c9c95f3cef8e8c616150f164888da5263877302a158322ba14`。共 9 个目标文件；所有成员大小与内容哈希已核对。Windows Path 排序与字符串排序口径差异导致首个包装清单比较断言失败，随后仅统一排序比较并逐成员核验；包内容、request 与源码未因此改动。运输包不含真实点集或权重。安装映射见 `transport_manifest_v1.json`。

本轮未核查当前服务器身份/空闲资源/目标存在性；下一阶段上传后必须重验身份、包哈希、所有新目标不存在及父目录状态、复用依赖、两份权重及 105 份输入哈希。不覆盖安装；首次失败即停。

下一步：将运输包及三个校验文件手动上传至 /home/jovyan，之后单独对上述完整 request SHA256 授权，才能进行限定核验、安装、材料化及唯一一次预测。完成后按既定边界做正式只读预测冻结审计、下载核验，再单独进入 CPU 统一评分；不新增训练或重复 GPU 准入。
