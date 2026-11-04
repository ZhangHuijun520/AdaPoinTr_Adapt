# 固定8k采样对照：首个fresh V1执行记录 v1

当前状态：唯一一次V1训练已进入实际更新循环；尚未结束。观察时间（Asia/Shanghai）：2026-11-03T16:28:01+08:00。

用户原始授权文字保存在explicit_user_grant_v1.json。其“当前v2”引用解析到完整SHA256：`4a889afad90b1a8a52fcb75691c71990d03af8b7d120a96608ac4b9b85cb7a62`；不是旧v1，也不是候选臂授权。

## 本轮执行

- 上传五文件的大小/SHA256、身份/空闲GPU、磁盘及三个新根目录缺省检查通过。
- 安装前再验全部目标不存在；以exclusive create不覆盖安装647文件，全部回读哈希通过。未覆盖既有模型、provider、环境或历史结果。
- 按请求→真实授权回执→授权SHA256→runtime→单次launcher顺序材料化。授权、runtime和launcher的实际哈希与本机预先渲染值一致。
- 复用既有短行WebShell驱动，最大传输行1068字节；客户端源码哈希匹配。原文件字节经Base64承载，没有多层文本转义或服务器临时helper文件。
- 启动脚本先创建日志目录再重定向，记录真实退出码。按冻结入口的明确要求将TMPDIR补全为本次输出/tmp；请求列出的环境字段、科学参数及代码哈希未改变。
- 独占写入CLAIMED_BEFORE_TMUX后只调用一次tmux启动；没有重试。

## 实际启动证据

Run ID：`bcsp_sampling_ab_foldC_V1_in8192_out8192_seed0_train_v1`。

tmux：`bcsp_sampling_ab_foldc_v1_seed0_train_v1`；容器PID：1516。tmux和容器PID均存活。最近观测到step 494/3900，epoch标签12，optimizer_step_committed=true，loss=0.20657748。

资源记录：RSS 1.174 GiB，torch峰值allocated 12.299 GiB，reserved 13.270 GiB，SMI使用14074 MiB。各内存条件均通过。SMI PID与容器PID不同仍仅记诊断警告，不声称已建立可信PID映射或严格独占。

尚无退出码，无failure/startup_failure记录。不是仅凭tmux返回0宣称训练启动。日志中的timm导入FutureWarning不代表本次训练失败。

## 产物与边界

服务器日志：`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_sampling_ab_v1/bcsp_sampling_ab_foldC_V1_in8192_out8192_seed0_train_v1/launch.log`。

退出码：`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_sampling_ab_v1/bcsp_sampling_ab_foldC_V1_in8192_out8192_seed0_train_v1/exit_code.txt`。

预期final checkpoint：`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_sampling_ab_v1/bcsp_sampling_ab_foldC_V1_in8192_out8192_seed0_train_v1/ckpt-last.pth`，本轮没有读取或哈希checkpoint。

授权回执SHA256：`1ea3c04bff3f008124bc72f9e824e93ed4f4f91fa83392a8d3d4c31cce6dc954`。

runtime SHA256：`690242387a7b93bff6e914ff73655b64b47faca2fce0baa0a6fb9ca230c7c398`。

launcher SHA256：`fc1830955a67d1cc66087525ed2a4975eed7e8a220b63f8b7ed0b80b1bef853a`。

本次只允许该V1训练完成至3900更新。没有启动候选臂、Fold D、其他seed、BNCal、development evaluation或模型重试。独立训练后冻结审计和配对初始化证据应按后续明确范围进行，本次启动观察不能替代它们。
