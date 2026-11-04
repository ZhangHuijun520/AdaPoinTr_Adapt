# PID 命名空间感知的最小训练守卫修订方案 v1

日期：2026-10-26（Asia/Shanghai）  
状态：`DRAFT_AWAITING_USER_REVIEW`  
本次权限：仅起草方案；未实施、未连接服务器、未执行测试或训练。

## 1. 问题与证据边界

父审计：`continuation_train_v2_request_v1/authorized_execution_v1/failure_freeze_pid_audit_v1/failure_PID_audit_report_v1.json`，相对于本文所在目录；SHA256：

`e1f80558c5dd76e4f4882082487a9809516f3d4a981e1162cc1481836fa93348`

审计状态为 `FORMAL_FAILED_RUN_FREEZE_PASS_PID_NAMESPACE_ATTRIBUTION_INCONCLUSIVE`。本次失败发生在第 1 次已提交 optimizer step 之后：worker 的容器 PID 为 1512，SMI 计算进程列表为 `[2851712]`。唯一失败条件是 `compute_PIDs_owned`。显存三项均通过：allocated 12,897,085,952 bytes、reserved 14,245,953,536 bytes、device 14,072 MiB。不能据此放宽显存阈值。

审计时两个进程均已退出。当前容器 `/proc` 仅显示本层 `NSpid/NStgid`，没有恢复该次宿主机映射的证据。不能宣布 2851712 就是 1512，也不能仅凭数字不等宣布存在真实外来进程；本方案不追认失败运行成功，不解释缺少诊断值的更早运行。

拟替换的逻辑仅为“SMI PID 与 `os.getpid()` 裸整数直接比较”。目标是比较同一口径下的进程身份，继续拒绝真实外来进程，并对无法确定的情况停止。

## 2. 可信映射从哪里获得

### 2.1 唯一拟实现路线：已存在、经平台来源确认的只读 procfs 视图

采用一个**事先明确授权、冻结精确路径及来源**的 procfs 视图，以下用符号 `P` 表示。`P` 不是实际路径，不得猜测 `/host/proc` 等路径或扫描寻找挂载。

准入证据必须先确认：该视图由平台提供，确为同一内核的 procfs；其 PID 命名空间与当前 SMI 所报告 PID 的命名空间一致；路径和挂载身份可验证，实验用户不能把它替换成伪造的普通目录。仅有目录名、`filesystem=proc`、只读标志或一次 PID 数字巧合均不充分。平台来源和 SMI 口径仍是当前未补齐的前提，不能由代码凭空证明。

Linux 的 procfs 可见范围取决于该 procfs 挂载关联的 PID 命名空间；`self` 反映调用者在该视图中的 PID。因此，训练 worker 可以在不枚举其他进程的情况下，直接解析经确认的 `P/self`，取得自身在该视图中的进程号。[Linux PID namespace 文档](https://man7.org/linux/man-pages/man7/pid_namespaces.7.html)

**读取动作必须由实际训练 worker 自身执行**，不能让 `cat`、另一个 Python、launcher、监测子进程或事后审计进程读取 `P/self` 后当成训练 worker。采用进程级 TGID；worker 主线程完成读取，不把 CUDA 辅助线程的 TID 自动加入允许集合。

最小获取步骤：

1. 在任何模型 forward/backward/optimizer step 之前，worker 保存自身 `os.getpid()`、本地 `/proc/self/status` 的 TGID、`/proc/self/stat` 的 starttime、`/proc/self/ns/pid` 的 namespace 身份及同内核 boot ID。确认本地 proc 视图与 worker 自身的 PID 口径一致。
2. worker 自身解析 `P/self` 得到候选 `H`；只访问 `P/H/status`、`P/H/stat`、`P/H/ns/pid`，不遍历 `P`，不读取其他 PID 的 cmdline、environ、fd 或内存。
3. 要求 `P/H/status` 的 Pid/Tgid 及 NSpid/NStgid 与主线程关系一致，外层 TGID 为 H、最内层 TGID 等于本地 worker TGID；目标 namespace 身份与 worker 一致、两侧 starttime 一致、boot ID 一致。嵌套列表仅用于核对，不把列表中的所有整数都作为 GPU 允许 PID。
4. 对关键身份字段做读取前后稳定性核对，冻结本次 worker 的 `(boot ID, PID namespace, local TGID, starttime, SMI-domain TGID H)`；每次资源采样重新核对，防止 PID 复用、路径替换或身份漂移。任何缺失、不可读、冲突或变化均为未知映射并停止。

`NStgid` 的排列与 procfs 所属命名空间有关，不能把容器本地只有一项的列表当成宿主机 PID。starttime 是内核报告的进程启动时刻，以启动后的 clock ticks 表示；它用于身份复核，不单独充当身份凭据。[proc_pid_status](https://man7.org/linux/man-pages/man5/proc_pid_status.5.html)，[proc_pid_stat](https://man7.org/linux/man-pages/man5/proc_pid_stat.5.html)

`P/self` 和 `ns/pid` 是本方案明确允许的内核特殊链接；这不放宽项目数据、授权文件、runtime 文件或一般路径的符号链接守卫。必须限定访问根和用途，拒绝普通链接替换及越界目标；namespace 链接按内核 namespace 对象检查，不按普通文件路径解析。

### 2.2 当前可用性与停止点

目前**未证明当前容器存在满足上述条件的 P**。本轮不探查它，也不新建挂载、使用管理员权限、切换 namespace、改容器权限或部署宿主机代理。

后续只有在本方案获确认、精确路径及其平台来源已明确后，才可单独授权一次有界只读前提核对。如果没有这种现成视图，就以 `BLOCKED_TRUSTED_PID_MAPPING_UNAVAILABLE` 结束这条实现路线，不实施一个必然无法提供证据的训练补丁，不启动训练验证猜测。

若平台只能提供管理侧映射接口，应先取得其精确接口及进程身份语义，另行审核是否能替代 P；本方案不开发该接口、不安装代理、不把普通用户填写的 JSON 或环境变量当成可信映射。不能以“框架支持多种 provider”继续扩展工程准备。

## 3. 所有权判定合同

保留原 SMI 查询来源及查询预算。NVIDIA API 提供 GPU 活动进程的 PID 等信息，但本方案不把一般 API 说明当成当前容器 PID 命名空间口径已确认的证据。[NVIDIA NVML](https://developer.nvidia.com/management-library-nvml)

在可信映射有效时，唯一允许身份是**本次存活训练 worker 的 H**。不允许同容器其他进程、子进程、同 UID 进程或历史 worker。对查询范围内原有的全部 SMI PID 保持检查，不缩小列表或过滤掉“不认识”的项。

| 情况 | 分类与动作 |
|---|---|
| 映射有效，非空 SMI 列表只包含 H，其他原有条件全通过 | `OWNED`，允许该检查点继续 |
| 映射有效，SMI 列表含 H 以外的 PID | `FOREIGN_PRESENT`，记录并停止；不向该 PID 发信号 |
| 映射缺失、来源不可信、身份变化或读取失败 | `UNKNOWN_MAPPING`，记录并停止 |
| SMI 超时、非数字、异常或无法得到可靠列表 | `UNKNOWN_GPU_PROCESS_STATE`，记录并停止 |
| 同步后的训练资源检查点得到空列表 | `UNKNOWN_GPU_PROCESS_STATE`，停止；不以 `all([])` 自动通过 |

启动前原有“GPU 空闲、无计算进程”检查仍独立保留；它允许空列表，但不能证明训练时 worker 的映射。不得为了证明映射新增 CUDA context、额外 forward 或试跑。模型运行后的列表应能观察到自身，否则停止，不自动复查重试。

直接整数相等也不能绕过映射来源确认。进程名相同、只有一个进程、显存数值吻合、出现时刻相近、PID 在容器内不存在、旧日志中出现过该 PID，均不是所有权凭据。`UNKNOWN` 不归类为“已证实外来”，但同样禁止继续。

## 4. 最小实现边界与诊断输出（待后续单独授权）

前提核对通过后，最多新增两个实现／测试文件：一个版本化 entry 候选及一个针对性 CPU 测试文件。映射逻辑留在候选 entry 中，不新增通用 provider、库存或传输框架。现有 entry v3、contract v2、runtime v5、数据、模型、wheel、SMI helper 保持原字节。若现有读取守卫不允许精确 P 路径，必须先报告具体冲突；不在本方案下自动扩大其允许范围。

除 PID 判定和相应诊断字段外，不改资源判断、训练调用顺序或科研计算。继续固定 3900 updates、100 epochs、batch 8、Fold C seed 0、8192→8192、原始顺序、严格确定性/TF32 关闭、既定 PointNet2 和 torch.cdist 后端。显存 20 GiB/20 GiB、device 22528 MiB、RSS 8 GiB、输出 2 GiB、磁盘下限 4 GiB、总时限 86400 秒等全部不变；不改变 BNCal/evaluation 禁止状态。

资源事件继续先落盘、flush/fsync，再执行停止断言。保留 `compute_PIDs`、`own_PID`、三项显存值和四项检查结果，增加：

- `ownership_status`、`mapping_source_id`、来源合同版本／指纹；
- 本次 worker 的 local TGID、SMI-domain TGID、namespace 身份、starttime、boot ID；
- 映射前后稳定性结果、原始 SMI PID、被判定为外来的 PID（仅可信映射有效时）；
- 精确失败阶段、允许范围内的失败路径、异常类别、耗时及首个停止原因。

不记录秘密、cmdline、environ 或外来进程内容。读取失败仍应尽力写入结构化失败事件；日志写入/fsync 本身失败必须停止，不能宣称失败日志保证存在。保持现有资源记录上限 3902，不增设训练记录循环。

每次映射采样限定最多 16 个元数据文件／链接、合计最多 64 KiB；只读自身及由可信 self 得到的 H，不扫描进程目录。映射采集的拟定软件耗时预算为 1 秒，超限停止、不重试；这是读取返回后可检查的预算，不宣称可强制中断所有内核阻塞。既有 SMI 10 秒预算、外层总超时与终止规则保持不变。若现有入口无法落实该合同，应在静态审查报告缺口，而非自动新增看门狗框架。

## 5. 一次限定的人工 CPU 回归范围（本轮不执行）

使用人工元数据和模拟 SMI，不访问真实 procfs、不调用 WSL/SMI、不导入 CUDA、不读真实点集。拟固定以下 12 项，每项可含固定子断言，不随机生成或失败后自动修复重跑：

1. 可信跨 namespace 映射：本地 PID 与 H 不等，列表仅 H，通过。
2. 已确认同口径映射：本地 PID 与 H 相等，通过；缺少来源确认则停止。
3. 合法嵌套 NStgid：只允许 H，不放行中间层 PID。
4. H 与外来 PID 并存，停止并准确记录外来 PID。
5. 仅有外来 PID，停止；即使其进程名／UID 假设相同也不放行。
6. 映射来源缺失、不可信或普通文件伪造，停止。
7. TGID、namespace、starttime、boot ID 任一不一致，停止。
8. 两次读取间身份变化、PID 复用或路径替换，停止。
9. 不可读、文件消失、格式异常、字节／次数／耗时超限，停止并记录精确原因。
10. SMI 空列表、超时或解析失败，未知并停止；启动前空闲判定与训练采样明确分开。
11. 原显存各阈值边界及超限仍有效，映射通过不覆盖显存失败，多个错误完整记录。
12. 诊断事件 flush/fsync 先于断言；写入/fsync 失败停止，记录上限仍有效。

实施验收还需静态差异证明非 PID 计算路径不变、接口绑定明确、人工测试结果正式只读冻结审计及本机 P3。CPU 测试通过只证明人工合同，不证明当前平台提供可信映射，也不证明 CUDA 训练通过。

## 6. 完成标准与后续分阶段边界

本方案的完成标准是：可信来源条件、明确停止点、最小代码范围、12 项人工验证、日志与预算均可审核；**当前产物仅为草案**。

后续顺序建议：

1. 审核本草案；若认可路线，先明确平台提供的精确 P 及来源证据，再单独授权有界只读前提核对。证据不足即停，不以训练试探。
2. 前提通过后，单独授权上述最小 implementation-only 和一次人工 CPU 回归；完成冻结审计与 P3。
3. 另行授权运输／安装及正式安装后审计，随后才可创建绑定最终哈希、全新 run/control/output/tmux 的待授权训练 request。
4. 新 request 须再次单独执行授权；此前所有失败 request/launcher/claim 均已消耗，不复用、不 resume、不覆盖。

本轮未生成 execution request、授权回执、runtime 或 launcher；未修改生产守卫、未准备运输包、未操作服务器，未执行 CPU 测试、forward、训练、BNCal 或 evaluation。
