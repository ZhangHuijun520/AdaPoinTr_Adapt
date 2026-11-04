# Fold C Morton 8k 候选臂：授权执行与启动记录

本次执行依据用户“已上传，单独授权上述哈希”，唯一指向候选 execution request SHA256 `d4a44a990c0b3f0b91522c6f9803074a34e6c3803c243bf08e8a46ace42eeae3`。内层不可变训练 request SHA256 为 `b4d5c09a270972327e4f8ded21a8697d10d8c724c2c0faa9e2b5a3b384aa2859`。

## 核验与修改范围

当前容器 `shu-common-25721452-notebook-v2iwsa-0`、uid 1000、固定 GPU UUID、Python 身份、GPU 空闲与磁盘预算检查通过。上传的五个运输文件、三成员归档、复用代码与证据、315 个候选 NPZ 字节哈希均通过。V1 的 completion、initialization 与最终 checkpoint 重新核对字节哈希；checkpoint 未反序列化或用于初始化。

仅在 `third_party/bcsp_sampling_ab_foldc_seed0_v1/control_Morton_v1` 新增三个冻结控制元数据文件，采用独占、不覆盖写入并核对哈希。复用代码、数据和旧 V1 结果保持不变。

随后单向生成 authorization → authorization SHA256 → runtime → launcher，在创建日志目录之后才重定向，并在唯一一次 tmux 启动前独占创建尝试标记。训练入口保持原有守卫，进入更新前强制比较 scratch 初始化参数和持久状态指纹。

| 产物 | SHA256 |
|---|---|
| authorization_v1.json | 31591f9c39965fd6b21ed92b2c6259b052127e3a8d71fca5913de84eef98093d |
| runtime_v1.json | 90719dedad456654494cea7ec73b850d2ff8d98f3afb0b959980d9c80dbd288e |
| launch_once_v1.sh | b30943c851680056fb3451d16d30b824fb3bf1dbe04096d2c14216e6e524b4d2 |

## 实际运行确认

2026-11-03 11:31:57（服务器日志同口径）只读观察为 `TRAINING_RUNNING`：tmux 存在，worker PID `17570` 存活，已提交第 **12/3900** 步，尚无退出码、失败或 completion 文件。初始化文件已写入；训练入口的初始化配对守卫已通过，否则不能进入当前更新路径。

- 会话：`bcsp_sampling_ab_foldc_morton_seed0_train_v1`
- 输出：`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_sampling_ab_v1/bcsp_sampling_ab_foldC_Morton_in8192_out8192_seed0_train_v1`
- 当前显存：SMI 14074 MiB；torch peak allocated 13206299648 bytes、reserved 14248050688 bytes；RSS 1261326336 bytes。该次记录的资源守卫通过。
- SMI PID 与容器 PID 不同，按既定合同仅作诊断记录，不作所有权保证。

科学合同仍为 Fold C、seed 0、AdaPoinTr B0、8192 输入／8192 目标、315 训练病例、100 traversals、3900 updates、31200 exposures、300 dropped exposures；与 V1 共用配置及实际批次顺序。候选只改变输入采样臂。

## 证据与权限边界

同目录 `precheck_execute_once_observation.json`、`install_execute_once_observation.json`、`materialize_execute_once_observation.json` 与 `startup_observation_04_result.json` 分别保存实际回执。静态短入口检查采用既有字节驱动，最大传输行 1068 bytes；没有修改服务器客户端或生产源码。

本报告证明已实际开始训练，不证明训练完成、模型精度提升或最终冻结审计通过。本次未重训 V1、未 resume／自动重试，未执行评价、BNCal、Fold D 或额外 seed。尝试已消耗；失败应停止，不能再次启动同一 request。训练结束后的正式冻结审计和后续两臂配对评价仍需各自授权。
