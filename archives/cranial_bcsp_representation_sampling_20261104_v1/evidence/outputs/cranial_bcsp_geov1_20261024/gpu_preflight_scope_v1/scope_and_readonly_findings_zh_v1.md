# 8k／16k 人工 GPU 零更新验证：冻结范围与只读核对 v1

_Cranial-BCSP-GeoV1 · 2026-10-24（Asia/Shanghai）· 范围冻结，不是执行 request_

---

## 📋 当前结论

已完成候选四文件与现有 provider 的限定只读核对，冻结两档验证的科研、数值、状态、资源及权限范围。本轮不部署、不运行测试或 GPU、不安装／编译依赖，也不修改候选或服务器源码。

状态为 `FROZEN_SCOPE_AWAITING_MINIMAL_ENTRY_IMPLEMENTATION`。当前文件 **不是可执行授权 request**：尚无专用短入口、该入口的 CPU 契约证据／P3 与最终代码哈希。不能对本范围 SHA 单独表示“执行”就绕过这些缺口。

文档采用科学记录规范分开描述静态来源核对、已确认的后端选择与尚未执行的运行验证；不将静态哈希吻合写成 CUDA 已通过。

## 🔍 实际核对结果

| 项目 | 只读发现 | 判断 |
| --- | --- | --- |
| 容器 | `shu-common-25721452-notebook-o9mz8z-0`、uid 1000 | 与用户新目标一致 |
| GPU | RTX 4090 D，24564 MiB，查询时使用 0 MiB | 尚未进行 CUDA 计算 |
| GPU UUID | `GPU-2f32f6fb-ea5d-730a-4ea2-2f6063e31065` | 固定物理身份 |
| 实验环境 | Python 3.10.20；PyTorch 2.4.1+cu118；NumPy 2.2.6；timm 1.0.27 | 版本／来源元数据，不是导入测试 |
| PointNet2 | 既有 cp310 provider、wrapper、wheel 均存在 | native SHA 与既有 e70d…fbb5 完整记录一致 |
| Chamfer | 限定安装位置未找到 cp310；项目 build 下仅发现 cp39 模块 | 不把 cp39 绑定到 cp310，也不作全环境穷尽性声明 |
| 模型母版 | 服务器 `AdaPoinTr.py` 带有 R1-B bypass 参数／分支 | 不静默替代已选本机归档母版 |
| runner | 服务器包含 QA-1 数值／训练守卫的后续修改 | 不覆盖服务器 runner，不把它混入已冻结候选 |
| 其他比较源码 | Transformer_utils、PointNet2 adapter、misc、Chamfer wrapper 的 LF 文本及 AST 相同 | 字节哈希仍不同；不放宽字节绑定 |

主 probe 用时约 0.82 秒，对所列文件累计哈希约 18.12 MB；只使用远程 Python stdlib。随后仅比较六个指定源码，并核查 Chamfer 的既有项目构建位置。没有递归扫描环境、导入 torch/provider、加载模型或读取真实病例。

PointNet2 native：`e70d00108bacba4a905dc011f4b8c4868f06ec2d44d8e322148e2e452578fbb5`。

既有 PointNet2 wheel：`530496a0d1d5dea6151a466b7c0874632322223308a7016910fb1bfbaaaab1e5`。本轮只读核验，没有重新安装 wheel。

## 🎯 已明确的母版与后端决策

继续使用此前选定的本机冻结母版，而不是服务器的漂移模型。机器范围绑定了 14 个有限实际项目源码、四个候选文件与一份基础配置；它们仍在本机，尚未复制到服务器隔离路径。

未来短入口只在独立目录加载这些冻结字节：`models/Transformer_utils.py` 和 `tools/bcsp_adapter.py` 进入实际模型取点路径；`tools/runner.py` 与 `tools/bcsp_runtime.py` 仅核验身份，不导入或执行，因为 `run_bcsp` 会进入 3900-step 训练循环，不能用作 preflight。

通过受控 namespace 加载必要 `models/utils/tools/extensions` 子模块，不执行会导入无关模型或训练器的顶层包 initializer，不部署人工测试用空 `tools/__init__.py`，不修改全局 `.pth`／环境路径。入口实施后须验证实际模块 `__file__`，不能仅 AST 抽取后冒称实际模型接入。

用户已明确选择：**两档都使用现有项目的 PyTorch `cdist` Chamfer 分支**，不编译、不安装。运行时必须断言 `extensions.chamfer_dist.chamfer is None`，并绑定现有 wrapper 字节；若意外解析到编译模块，则停止，不能换后端或把该变量改为 None 来放行。

PointNet2 则相反：必须使用指定 cp310 编译 provider，并断言项目 adapter 没有走 fallback。静态文件名／哈希不能代替这项运行断言。

## ⚙️ 冻结的单次科学验证

| 项目 | 固定范围 |
| --- | --- |
| 基线 | 新任务 B0 AdaPoinTr Transformer，Mamba／SCQR／附加几何机制关闭 |
| 模型 | center `[512,256]`，query 256，FC 输出 8192，denoise 0 |
| 输入 | 人工内存 float32 数组，`8×16384×3`；前 8192 点构成小档 |
| 目标 | 两档共用同一人工 `8×8192×3` 数组 |
| 输入生成 | NumPy PCG64，uniform(-0.5,0.5)；输入 seed 20261024，目标 seed 20261025 |
| 张量接口 | `torch.from_numpy`；实际检查当前 NumPy/Torch 桥接，不改环境绕过失败 |
| 初始化 | 两个 scratch 实例各 seed 0，参数初始哈希相同 |
| 顺序与次数 | 同一进程先 8k 后 16k，各 1 次完整 forward、1 次真实 get_loss、1 次 backward |
| 合计 | 成功时 2 forward＋2 backward；optimizer／scheduler／BNCal／开发评价均为 0 |
| KNN | 全部 keys，query chunk 256，不近似、不截断输入 |
| KNN 小型 oracle | 每档 candidate／dense parent 各 1 次，B=1、query=257、k=16；不构造 16k 平方矩阵 |
| KNN 比较 | 有效唯一索引、排序距离与 cutoff/tie 合法性；atol=rtol=1e-5，不要求并列索引顺序逐位相同 |

实际 loss 为冻结模型的 `get_loss(ret,target,epoch=0,partial=input)`，两项相加后反向，不替换为用于绕开 Chamfer 的代理损失。输入和目标都不来自患者文件，不读取真实点集或 checkpoint，也不写训练权重。

严格 FP32、无 AMP、TF32 关闭；deterministic algorithms 开启，cuDNN deterministic=true、benchmark=false，`CUBLAS_WORKSPACE_CONFIG=:4096:8`。不支持严格确定性的算子即失败，不自动降低要求。

### 参数、BN 与 RNG 保护

保留模型的 training 分支和 BN 批统计计算，但在人工调用期间临时令 BN `track_running_stats=False`，避免 running mean／variance／batch counter 写入；调用后恢复原 flag。此策略必须先由人工 CPU 契约验证，不能假定已经可用。

每档前后核对参数和 persistent buffer 的精确字节指纹，恢复模块 training flag 与 Python、NumPy global、torch CPU／CUDA RNG。反向须产生有限、有效的 active grouper／encoder／decoder 梯度，采证后清空梯度；不创建 optimizer。普通诊断缓存不冒充 persistent state，每档使用新实例，绝不直接复用于训练。

这项 BN 策略是已披露的 preflight-only 差别：可以检查批统计梯度路径和资源，但不能据此认证完整正式训练的所有状态更新或精确显存行为。

## 🔐 资源、输出与失败合同

| 项目 | 固定值 |
| --- | --- |
| batch／精度 | 8／FP32；失败时不减 batch、不改点数 |
| 整体超时 | 900 秒，终止宽限 5 秒 |
| RSS 监测阈值 | 8 GiB |
| Torch peak allocated／reserved | 分别不超过 20 GiB |
| 设备显存停止阈值 | 22528 MiB；启动时 used≤256 MiB 且无其他计算任务 |
| 最低剩余磁盘／输出预算 | 2 GiB／16 MiB |
| CUDA 映射 | `CUDA_VISIBLE_DEVICES` 固定物理 UUID；torch 仅一个逻辑 `cuda:0` |
| 隔离源码目录 | `/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v1` |
| 结果目录 | `/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/artificial_gpu_zero_update_v1` |
| tmux | `bcsp_geov1_artificial_gpu_zero_update_v1` |

这两个拟用目录只读观测均不存在，没有创建。SMI 的物理 UUID／取整显存与 torch 的逻辑设备／属性分别记录，不凭猜测要求两种查询的显存字节完全相等。

显存测量在模型移入 GPU 后同步，记录 baseline，并在 forward 前重置 peak counters；覆盖真实 forward/loss/backward 后同步读取。两档之间释放本进程拥有的模型、梯度和 allocator cache，不影响他人进程。没有 warmup 或性能计时循环，不比较速度排名。

外层 timeout 要真正约束进程；RSS／设备显存属于监测及合作式停止，不是独占 cgroup 硬隔离。峰值超限、OOM、导入／ABI、数值、状态或身份失败，全部立即停止；第一档失败不进入第二档，不自动修复、重试或 resume。单次 launcher 即使未进入 forward 也消耗 attempt。

未来授权后才可创建授权回执→其 SHA→runtime config→单次 launcher；不存在 runtime SHA 反向绑定授权回执的循环。日志父目录必须先建立再重定向，PID／退出码必须落盘，本机调用显式保留 `$LASTEXITCODE`，复用既有 byte-safe transport，不再开发通用传输器。

只允许在新隔离目录和结果目录进行届时授权的写入。秘密、真实数据、checkpoint、项目越界与链接守卫保留；依赖自身名为 `data` 的代码目录不自动等同项目真实数据禁区。禁止联网下载、NVCC/扩展构建、安装升级、修改母版或覆盖旧产物。

## 📍 唯一剩余实施范围与证据

下一次若获 implementation-only 授权，仅新增一个专用短入口和一个针对性人工 CPU 契约测试文件，保持四候选、冻结母版和 provider 不变；集中验证隔离导入、实际后端断言、输入／次数、BN/RNG/零更新、资源／失败／PID 合同，不增通用框架。

完成一次限定 CPU 契约批次和实施 P3 后，才创建绑定最终源码哈希的待授权 execution request。本轮不实施这些内容，不创建 runtime config、launcher、运输包或执行 request。CPU 通过仍不代表 CUDA 通过。

这不是科研数值失败：数据配对 QC 已完成；本次只识别并冻结实际执行边界。GPU 通过以后，也只对当前模型、点数、batch、设备和 PyTorch Chamfer 后端有效，不认证临床精度、不等同训练准入，也不允许自动开始四次训练。

- [机器可读冻结范围](E:/Codex/2026-06-06/mamba-ccf-c-1-high-resolution/outputs/cranial_bcsp_geov1_20261024/gpu_preflight_scope_v1/artificial_gpu_zero_update_frozen_scope_v1.json)
- [只读核对回执与来源哈希](E:/Codex/2026-06-06/mamba-ccf-c-1-high-resolution/outputs/cranial_bcsp_geov1_20261024/gpu_preflight_scope_v1/candidate_provider_readonly_review_v1.json)
- [真实开发数据 QC 报告](E:/Codex/2026-06-06/mamba-ccf-c-1-high-resolution/outputs/cranial_bcsp_geov1_20261024/real_data_qc_report_zh_v1.md)
