# F0 正式只读 post-CUDA freeze audit v2

日期：2026-11-10。**结论：POST_CUDA_FREEZE_AUDIT_PASS。** 仅在已冻结人工输入、native后端、调用范围及资源合同内获得零更新准入；不是颅骨补全效果、3900步训练稳定性或临床可靠性结论。

## 审计对象与范围

Request SHA256：`a9fbc819da73415008ac5643f5b6cea9ab1b3818029129e6f93e2e67bcc23efc`。当前容器shu-common-25721452-notebook-n8xph5-0，UID1000。退出码0，tmux及worker进程均已结束。只读核对输出目录与安装目录，共23个普通文件、511457 bytes；五个输出辅助目录为空，安装目录除八个冻结文件外仅有六个控制文件。

采集前后逐文件SHA256、bytes、inode、mode、mtime/ctime一致，排除读取导致的atime变化，不修改服务器属性。23文件已下载到本审计目录downloaded子目录并逐个核对哈希。原运行payload_manifest的五文件哈希完整匹配；launch.log、worker.pid、exit_code.txt及manifest本身由本次独立清单补齐。再次读取51条冻结复用/安装记录，约711MB哈希覆盖全部匹配，无目录扩扫。

授权回执完整绑定原request；runtime仅单向绑定授权回执SHA；launcher与冻结entry的render_launcher逐字节重新渲染一致；唯一claim绑定相同回执/runtime/launcher。八个安装文件与原运输映射逐字节一致，不覆盖、不换模型或守卫。

## 计数、loss与梯度

71项核验全部通过。26条事件中有19条调用前claim，独立累计结果：完整forward4、完整原始loss4、完整backward4；decoder forward6、局部backward1；optimizer step0。22个native SSM模块的逐模块调用计数准确，合计288。两次eval为batch1，两次train为batch8；真实Mamba-1（mamba_ssm包2.3.1）、native PointNet2与既有torch.cdist Chamfer由原始冻结入口实际运行，非CPU surrogate。

四次完整backward的全部现存参数梯度norm有限；独立重算六个encoder SSM、十六个decoder SSM、共享PE、coarse头及reduce_map共25个模块的norm汇总均为正，与记录一致。411个参数分组无重复，22组A_log及22组D均保留no-decay；没有构造optimizer。有限梯度非确定性的既有披露保留，不新增逐参数梯度位级一致性门槛。

四次loss记录：eval约0.44712266，train约0.37792659；它们仅是人工输入准入值，不是开发集成绩。重复forward/loss符合冻结容差。

## 条件支路及状态

首层conditional SSM后缀、局部graph/merge之前的maxabs响应：feature-null=0.0933622196，full-prefix-null=0.094828397，仅早段64个Memory token扰动=1.85295939e-05。这些是内部特征量，不是mm。重复噪声0，冻结响应阈值1e-7；三种响应均超过阈值。

早段扰动严格保留最后3个Memory输入token和所有Query输入token，结合绑定入口/模型源码，可以在这一人工单层支路测试内排除“仅由边界处causal Conv1d产生响应”的解释。不能据此认为学到了正确的颅骨空间对应。第二病例改变时第一病例输出maxabs差0，未见本次范围内跨病例状态污染；Memory梯度norm约5.9997e-6，条件支路和PE梯度有限且非零。

四次执行的Python/NumPy/CPU/CUDA RNG原始记录前后一致、起始记录一致。eval完整state指纹一致；train只改变increase_dim.1的running_mean、running_var和num_batches_tracked，属于预期BN行为。最终state/RNG/模式恢复断言成功，参数在每次完整调用后均保持原指纹。此处核验日志中的完整序列化状态/哈希及绑定断言源码，没有重新执行张量计算或从checkpoint恢复重算。

## 资源及attention范围

51条资源记录独立重算全部通过：采样RSS最高约1.650GiB，SMI最高14632MiB，Torch allocated峰值约12.613GiB、reserved约13.812GiB。资源记录计时约66.99s，未超过1800s外层预算。RSS/SMI仍是采样监测，不能认证瞬时峰值或专属cgroup硬隔离；预留阈值未放宽。

登记的禁止attention模块为空；冻结dispatch守卫覆盖本次4完整F/B和6局部F/1B，未记录softmax/einsum及已知attention dispatch。原通用库存字段dynamic_kernel_audit_pending=true保持原样；它不能被改写成“全部opaque扩展内部已审计”。本次结论仅覆盖固定源码和已知dispatch守卫，不宣称任意第三方二进制的逐算子语义认证。

## 审计辅助修订与权限边界

保留audit_failure_v1.json：首次本机核验误把Python/NumPy序列化RNG状态也要求为64位SHA，导致辅助检查失败。原始前后状态实际相等。v2仅改为匹配绑定工具真实格式的严格类型/结构核验，同时保留前后全字符串相等、CPU/CUDA哈希及全部原判据；没有修改生产代码、运行结果、容差或资源阈值，也没有重跑GPU。

本次服务器写入0、CUDA调用0、真实数据/checkpoint读取0、测试重跑0、训练启动0。机器证据：post_CUDA_freeze_audit_result_v2.json。后续训练必须绑定native_admission_receipt_v2.json的完整SHA及对应模型实现，不能只相信调用者传入的PASS字符串。

## 下一步

按正式计划准备F0-P-v2_C与F0-P-v2_D，seed0，先C后D，各3900更新；无需重新训练既有T0/M0，也不恢复与本轮scratch训练无关的历史权重。专用训练入口尚缺；原P1入口仅接受T0/M0合同，现有F0 runtime bridge没有CLI和完整授权入口。因此下一步最小implementation-only为F0训练短入口、针对性CPU授权/分派验证及P3；通过后才能创建首个Fold C待授权训练request。当前未创建训练request或执行控制文件。
