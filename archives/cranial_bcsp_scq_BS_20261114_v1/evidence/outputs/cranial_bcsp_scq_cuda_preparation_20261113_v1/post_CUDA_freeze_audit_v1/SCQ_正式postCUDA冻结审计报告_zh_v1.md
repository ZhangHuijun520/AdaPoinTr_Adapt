# SCQ-v2 正式 post-CUDA 冻结审计报告

日期：2026-11-13。结论：**FORMAL_SCQ_POST_CUDA_FREEZE_AUDIT_PASS**。

本轮只读重新核验服务器安装/控制/输出文件，下载证据至本机并复核清单、哈希、计数、梯度、状态/RNG恢复记录及显存判据。没有新增forward、loss、backward、GPU操作、真实数据/checkpoint读取或训练。

## 1. 冻结身份与完整性

request SHA256：

`0f5aec8c30d0044547cd8806c5663aeb4f0f9643e254a65ce562f5d45641521b`

审计核验当前hostname为`shu-common-25721452-notebook-t6ibfm-0`、UID1000。运行绑定的设备为RTX4090D、GPU UUID `GPU-aa9e6ffb-fdbb-1836-1c32-7244231d3714`、driver570.190；本次未再次查询或使用CUDA设备。

只读范围限定为原SCQ安装根与原单次输出目录。全部**21个文件、6个子目录**的集合符合预期，没有额外文件或符号链接；累计内容读取未超既定审计上限。9个安装payload匹配原映射，授权回执/runtime/launcher匹配本机原字节；当前服务器输出哈希与**12份本机回读**一致。

| 项目 | 结果 |
|---|---|
| 进程/退出状态 | exit code=0；固定tmux不存在，原worker未存活 |
| 授权与尝试 | 回执绑定request；runtime单向绑定回执SHA256；单次claim内容精确一致 |
| 输出集合 | completion、construction、events、resources、payload_manifest、launch.log、worker.pid、exit_code共8文件 |
| 内部清单 | payload_manifest的4个结果成员名称、大小、SHA256与当前服务器逐项一致 |
| 事件清单 | 恰好20事件；每阶段依次为forward/loss/backward执行前claim、阶段结果、恢复事件 |
| 真实数据/权重 | 运行记录为0次真实数据读取、0次checkpoint加载；审计未重新加载模型 |

审计以内容及稳定的size/mtime/ctime检查，未用读取引起的atime变化判定篡改。

## 2. 工作量与实际native路径

| 阶段 | 模型/batch/模式 | forward | 原loss | backward | optimizer step |
|---|---|---:|---:|---:|---:|
| B_eval1 | 原LQI / 1 / eval | 1 | 1 | 1 | 0 |
| F_eval1 | SCQ-F / 1 / eval | 1 | 1 | 1 | 0 |
| S_eval1 | SCQ-S / 1 / eval | 1 | 1 | 1 | 0 |
| S_train8 | SCQ-S / 8 / train | 1 | 1 | 1 | 0 |
| 合计 | 固定原顺序 | **4** | **4** | **4** | **0** |

无额外decoder-only、warmup或比较forward，未实例化optimizer。22个真实Mamba模块的forward hook计数精确匹配：6个encoder与8个self模块各8次，8个conditional模块各4次，总计**144次模块调用**，不将该数目称为CUDA kernel数量。

construction中7个native模块/扩展来源均属于冻结依赖清单。原LQI参数量实测39,903,169；SCQ-F/S实测40,596,676，新增693,507，与CPU核对一致。

## 3. 初始等价性与梯度

四次native构造的共有初始状态指纹相同：

`7d1c472d456217e362807b92b54e8f5da4451763472733683f287ede5e91d75b`

复用B_eval1输出比较F_eval1/S_eval1，coarse与dense的max-abs差异均为**0**；未放宽容差或追加forward。SCQ初始Delta为0，Qused等于Q0，符合零输出层设计。

每阶段35个冻结共有模块组的梯度范数总和均为正；审计从逐参数范数重新汇总并核对记录，所有已记录梯度范数有限。该结论不等于每一个模型参数都必须有非零梯度，未使用分支也不被误算为活跃。

| SCQ阶段 | W1 weight/bias梯度范数 | W2 weight梯度范数 | W2 bias梯度范数 |
|---|---:|---:|---:|
| F_eval1 | 0 / 0 | 0.3055753 | 0.0656330 |
| S_eval1 | 0 / 0 | 0.3049128 | 0.0656330 |
| S_train8 | 0 / 0 | 0.3471812 | 0.0814380 |

W2初始化为0时，第一层梯度为0是链式法则结果，不是路径失联。已知非零W2下的上游可导性由此前人工CPU证据覆盖；本次没有临时修改W2追加CUDA测试。

人工loss：三个batch1均为0.44809443，S_train8为0.39313275；仅作为人工输入下原完整loss有限、可反传的证据，**不是病例精度，也不说明S优于B/F**。

## 4. 状态、BN及RNG恢复证据

四阶段的参数不变断言和恢复事件均通过。三个eval阶段持久BN状态无变化，记录的Python/NumPy/CPU/CUDA RNG前后指纹一致。S_train8有3个BN buffer临时变化，全部属于running_mean/running_var/num_batches_tracked；恢复事件记录state_dict、RNG、train/eval模式、BN momentum已恢复且梯度清空。

审计重新校验了上述事件与completion阶段记录的一致性，以及执行这些比较/断言的安装源码哈希。**这属于已绑定运行时证据的冻结复核，不是在进程退出后独立重算模型内存状态。** 本次没有为此新增模型加载或forward；没有把有限梯度非确定性的既有披露改成位级重复backward保证。

## 5. 显存和资源

共**21条资源记录**。审计用每条实际值与request阈值重新计算全部判据，均通过，失败子条件均为空。

| 阶段 | PyTorch peak allocated GiB | peak reserved GiB | 阶段恢复时SMI MiB |
|---|---:|---:|---:|
| B_eval1 | 1.74 | 1.86 | 2,390 |
| F_eval1 | 1.77 | 1.91 | 2,442 |
| S_eval1 | 1.77 | 1.91 | 2,442 |
| S_train8 | **12.64** | **13.80** | **14,624** |

全程记录的最大RSS约**1.77 GiB**；最小剩余磁盘约10.28 GiB。预算监测窗口约15.79秒，包含四次串行构造/检查的一部分准备过程；不是训练吞吐或正式性能基准。

原阈值保持：PyTorch allocated/reserved各20GiB、物理SMI22,528MiB、RSS8GiB、磁盘剩余至少4GiB、外部timeout1800秒。上述统计是**SMI/RSS采样与PyTorch记录峰值**，不是专属cgroup硬隔离，也不证明采样间隔中的全部系统状态。SMI物理口径不与torch logical capacity强求字节相等。

## 6. 科研与后续边界

本次完成固定版本、设备和人工输入下的native CUDA技术准入：实际Mamba/PointNet2、完整loss/backward、初始等价性及batch8资源检查通过正式冻结。

尚未证明3900步训练稳定、optimizer状态分配后的显存、真实数据补全收益或SCQ纠错能力。原问题“错位Q0选取的局部Memory能否改善空间配置”仍需既定匹配对照训练及Native开发评价回答。

建议下一步准备**同设备B/S的Fold C首对训练**，复用既有训练逻辑完成必要入口绑定，先生成B_C待授权request。保持两折配置事前固定、同初始化/批次顺序和3900步；不能拿旧异设备LQI成绩直接充当本次匹配B，不根据人工loss调参，不重复本次GPU准入。当前没有训练授权或训练request。

## 7. 本机交付

本目录`post_CUDA_freeze_audit_v1/`包含：

- `freeze_verification_v1.json`：正式机器可读审计结论、逐阶段梯度/恢复摘要及资源。
- `remote_inventory_v1.json`：当前服务器21文件的大小/SHA256与目录清单。
- `output/`：8份完整运行产物。
- `control/`：4份原控制文件，按原字节保存。
- `local_evidence_manifest_v1.json`：下载及审计证据的内容清单。

只读审计来源：`local_tools/freeze_scq_cuda_readonly_v1.py`。材料现存本机项目目录；本轮未推送GitHub、迁入长期备份或清理服务器。
