# F0 人工 GPU 零更新准入执行观察 v1

日期：2026-11-10。**唯一一次运行已结束，观察到退出码0；正式只读post-CUDA冻结审计尚未进行。**

## 授权及实施

Request SHA256：`a9fbc819da73415008ac5643f5b6cea9ab1b3818029129e6f93e2e67bcc23efc`。

用户在完整哈希确认问题后明确回复“明确授权该完整哈希对应的安装与单次GPU准入”。服务器核验四个上传文件和当前n8xph5-0身份/GPU、直接相关源码/provider/native依赖、精确UTC目标、新安装根/输出及tmux不存在后，不覆盖安装八文件并逐文件核对哈希。生产源码、模型、冻结request、loss和资源阈值均未修改。

在安装根control目录依次生成授权回执、其哈希、单向绑定runtime和launcher；唯一launch claim在tmux调用前独占创建。另有一个本次执行专用的std库控制脚本暂存于项目third_party/f0_cuda_authorized_once_20261110_v1.py，仅负责本次部署和启动，不是模型实现或新增科研工具链；其原始字节及SHA记录在startup_observation_v1.json。

## 运行观察

- 容器：shu-common-25721452-notebook-n8xph5-0；GPU：GPU-aa9e6ffb-fdbb-1836-1c32-7244231d3714，RTX4090D。
- 会话：bcsp_f0_cuda_20261110_v1。最后观察时会话已退出，exit_code.txt为0。
- 完成记录：完整forward4、完整loss4、完整backward4；decoder-only forward6、局部backward1；optimizer step0。native SSM调用计数合计288。
- 入口完成了真实native Mamba、原始完整loss、batch1/batch8及前缀分支功能检查后写入completion。这里只转述完成记录，尚未独立逐项重新核验。
- 最后一条资源记录的Torch累计峰值：allocated约12.61GiB，reserved约13.81GiB；该条SMI读数14632MiB，RSS约1.65GiB，所有记录内子条件为true。当前仅有有界末段快照，不将该SMI/RSS读数冒充全程最高值。
- 真实数据读取0、checkpoint加载0、optimizer未构造，BNCal=false。模型train模式调用仅用于无更新准入；无正式训练、评价或自动重试。

原始捕获保存在observation_v3_stdout.bin；解析后的执行观察为execution_observation_v1.json。动态attention覆盖范围与opaque扩展局限沿用冻结request，本次观察不扩张其证明能力。

## 下一步

单独进行正式只读post-CUDA freeze audit：核验完整产物清单与SHA、退出码、计数/288次native SSM调用、完整梯度、前缀响应及短卷积边界控制、状态/RNG恢复、原始资源全记录及attention证据。通过后才能进入首对训练准备。不得仅依据本观察直接创建或启动训练。
