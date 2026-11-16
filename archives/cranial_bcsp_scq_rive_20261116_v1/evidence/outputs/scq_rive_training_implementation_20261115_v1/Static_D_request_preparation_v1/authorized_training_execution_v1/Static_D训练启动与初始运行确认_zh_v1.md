# Static_D 训练启动与初始运行确认

已按单独授权完成一次训练启动，当前观察为运行中，尚未完成。

当前容器 qx2k0r-0，GPU UUID 与冻结值一致；启动前显存使用 1 MiB，可用磁盘 8045723648 字节。72 个绑定资产、D 折 315 个训练输入（63 来源）哈希核验通过，未读取开发 payload。实际 authorize 路径通过，3900 更新合同及有效 3600 秒预算未变。

按授权回执→runtime→单次 launcher 顺序不覆盖材料化，随后创建唯一 claim，提交固定 tmux 会话。无自动重试。

会话：`SCQ_RIVE_Static_foldD_seed0_train_20261115_v1`。

PID：59827。初始观察已完成 step 3，optimizer_step_committed=true，worker 和会话均存活，尚无退出码或失败文件。这仅证明启动成功，不表示训练完成或科研效果改善。

结果目录：`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RIVE_Static_foldD_seed0_train_20261115_v1`。

未运行 BNCal 或评价。后续完成需核验退出码及计数，并单独执行正式只读训练后冻结审计。
