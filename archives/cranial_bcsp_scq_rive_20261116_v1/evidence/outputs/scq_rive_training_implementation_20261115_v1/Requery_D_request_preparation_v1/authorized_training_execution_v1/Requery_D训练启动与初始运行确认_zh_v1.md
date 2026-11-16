# Requery_D训练启动与初始运行确认 v1

已按单独授权提交唯一一次训练，并确认实际运行。当前qx2k0r-0及冻结GPU身份一致；启动前磁盘可用7514095616字节、SMI显存使用1MiB。74个绑定文件与315份D折训练输入哈希通过，无开发payload读取。实际入口authorize通过，Static_D正式配对证据、共同初始化、D折顺序和3900-step合同未变。

已按单向顺序不覆盖创建授权回执、runtime和单次launcher；随后创建唯一claim并提交一次固定tmux训练。

会话：`SCQ_RIVE_Requery_foldD_seed0_train_20261115_v1`。

PID76045。最新初始观察step51/3900，optimizer_step_committed=true，worker与tmux存活，未出现失败或退出记录。

结果目录：`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RIVE_Requery_foldD_seed0_train_20261115_v1`。

未运行评价或BNCal，未自动重试/resume。当前尚未训练完成，完成后需独立正式只读训练后冻结审计及Static_D/Requery_D配对核验。启动成功不代表科研性能改善。
