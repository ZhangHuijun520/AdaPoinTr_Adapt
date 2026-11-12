# LQI 两折 Native 预测入口、CPU 验证、P3 与待授权范围

日期：2026-11-11。

## 本轮结论

完成 LQI 专用两折 Native 预测入口、唯一一批针对性人工 CPU 检查及本机 P3，创建绑定最终源码哈希的待授权 request。状态为 **AWAITING_EXPLICIT_USER_AUTHORIZATION**，不是已经获得预测执行授权。

本轮无服务器操作、真实数据数组读取、真实 checkpoint 加载、CUDA 调用、真实模型预测、训练或评分；没有生成真实授权回执、runtime config、launcher、单次启动 claim 或 tmux 会话。

## 实现与最小差量

新增 `bcsp_lqi_twofold_native_predict_v1.py`，保持既有 F0 预测入口和 LQI 模型源文件不变。

- 绑定 LQI C、D 已冻结 checkpoint、训练 request 与正式训练后审计。
- 经实际文件读取策略加载既有 encoder、母版 factory、LQI decoder 与 LQI factory；禁止源码写入及相邻源码的泛化读取。
- 检查 `F0-LQI-implementation-v1`、`F0-LQI-v1`、`query_aligned_local_memory_interleaving`、交错条件 query 出口语义及零新增学习参数；拒绝误用 F0 factory。
- 继承原有病例来源、顺序、归一化和输入点集；保持两折各 105 例，共 210 次 Native forward、8k→8k、batch=1。
- 全部 210 例保存 `prediction[8192,3]` 与 `coarse[256,3]`，生成输入／权重／坐标绑定清单和无 GT 几何摘要。关闭旧 20-context／10-trace 机制诊断缓存，不追加干预调用。
- 保留参数／BN 状态与 CPU／CUDA／Python／NumPy RNG 的逐模型前后校验，以及实际调用计数、资源日志、首次错误记录和失败即停。
- 原 `load_partial`、`predict_once`、`source_module`、`make_policy`、`Budget`、`pack`、`rng_state`、`geometry_summary`、`load_checkpoint`、`render_launcher` 经 AST 差量复核保持不变。

入口 SHA256：`b1c4bee971e73c297ce1a9e22a21ef5da69cc6891fba110a6fc2544819362309`。

## CPU 验证与 P3

测试环境：既已授权的本机 Python 3.9／PyTorch 2.5.1+cpu，隔离启动、不写字节码。产物保留于 `artificial_cpu_batch_v1`。

**46/46 检查通过**，覆盖：

1. 实际两折索引及来源／归一化元数据；错误权重、缺例、顺序漂移、额外缓存、错误模型身份和交换两折审计的拒绝。
2. 完整 `authorize()` 的 request→authorization→runtime 单向绑定；未授权、runtime 错配、额外 forward 和 warmup 的拒绝。
3. 在真正审计 hook 下执行四个实际源码的加载；检查源码写入和邻近文件读取被拒绝。
4. 使用实际 LQI factory／decoder 配合人工因果 mixer；八层 trace 开关等值、状态／RNG 不变、生产 factory 调用签名及旧 F0／旧条件序列语义拒绝。
5. 人工 checkpoint 的严格加载与错误更新计数／缺失键／多余键拒绝；NPZ 加载路径只索引 `partial`。
6. 两个轻量人工模型合计 210 次 forward，210 个唯一 coarse+dense 文件、210 条调用清单与几何记录，无旧机制缓存，归档集合与哈希一致。
7. 首次人工 forward 失败后不启动下一个模型；失败计数保留；POSIX 路径、参数与先建父目录再重定向合同。

人工外层 forward 不是完整科研模型 forward，人工 mixer 不是 native Mamba。CPU 报告中部分继承的测试说明仍含“F0”字样，实际执行来源由记录的 LQI 文件哈希、loader 和 construction evidence 证明，不能据旧文字将其误解为 F0 代跑。

`implementation_P3_v1.json` 状态为 **LOCAL_LQI_NATIVE_PREDICTION_P3_PASS**。最终绑定复核另有 12 项通过，核验最终源码、CPU／P3 绑定、14 个安装文件、唯一目标、精确归档集合与成员字节、待授权状态和未产生真实执行控制文件。

CPU 通过不证明 native CUDA 或科研效果通过；复用已经通过正式冻结审计的 LQI CUDA 准入，本轮无需重复 GPU preflight。

## 打包过程中的辅助问题

首个本机打包辅助检查误将 launcher 合法的 `printf` 换行转义识别为 Windows 路径错误，停在生成 request 之前。保留 `pending_request_v1` 的未完成材料，不作为上传包或执行内容。

新增打包辅助 v2，将路径检查限定为实际命令参数；复用已经生成且内容复核一致的 P3，另写 `pending_request_final_v1`。入口、模型、测试及 CPU 产物均未修改或重跑。最终包是下节唯一指定包。

## 最终待授权 request

文件：`pending_request_final_v1/transport_payload/LQI_CD_native_prediction_execution_request_v1.json`

完整 SHA256：

`cab2831f27913766d7009101ec86d9a6e642a40b9330359dbfc8ff5928610fb6`

冻结安装根：
`/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_lqi_CD_native_prediction_20261111_v1`

冻结输出根：
`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/LQI_CD_native_development_20261111_v1`

冻结 tmux 名称：`bcsp_lqi_CD_native_eval_20261111_v1`。

资源合同：7200 秒、RSS 8 GiB、Torch allocated/reserved peak 各不超过 20 GiB、设备显存不超过 22528 MiB、输出不超过 1 GiB、可用磁盘至少 4 GiB；启动前设备使用不超过 256 MiB。维持 FP32、TF32=false、严格确定性配置和既有 native Mamba／PointNet2 provider；资源观测与超限停止不等于独占硬隔离。

request 绑定最后正式确认的 `zv9bqd-0` 身份，**本轮未实时核验服务器就绪，不能把本机 P3 或待授权状态理解为服务器准入已通过**。原范围中的实时身份／资产核验要求尚未履行，已在 request 中作为安装及启动前强制前置条件保留：必须重新核验容器、设备、上传包、14 个新目标不存在、父目录安全、复用代码／provider／配置／准入／权重与 210 个输入文件身份；漂移、未知或异常即停止。不得直接沿用旧身份启动。

禁止 loss、backward、optimizer step、BNCal、warmup、TTA、GT 对齐、后处理、真实 GT payload 读取、重训、F0 再预测、自动重试／resume、评分、bootstrap 或正式 gate。

## 待上传四文件

均在 `pending_request_final_v1`，上传至 `/home/jovyan/`：

1. `bcsp_lqi_CD_native_prediction_pending_20261111_v1.tar.gz`
2. 同名 `.tar.gz.sha256`
3. 同名 `.tar.gz.bytes`
4. 同名 `.tar.gz.contents.sha256`

压缩包：65741 字节；SHA256：`51780c72d141fe1a9b38a9c5e94eca21138b9d5990c37bc2efacc587894797b5`。

包内 14 个不覆盖安装文件及一份安装映射，逐成员回读与本机字节相同。其余模型、provider、静态配置和权重复用既有精确路径，未重新打包或编译。

上传后仍需用户对上述 **request 完整 SHA256** 单独明确执行授权。授权范围是核验前置条件、不覆盖安装及唯一一次 210-forward Native 预测；失败立即停止。只有授权后才可按单向顺序生成真实授权回执、runtime、launcher 和单次 claim 并启动。

预测完成后另行正式只读冻结审计、下载并本机核验；随后再单独准备 LQI／冻结 F0 统一 CPU 评分。当前尚不能判断 LQI 是否改善补全精度或接口吻合。
