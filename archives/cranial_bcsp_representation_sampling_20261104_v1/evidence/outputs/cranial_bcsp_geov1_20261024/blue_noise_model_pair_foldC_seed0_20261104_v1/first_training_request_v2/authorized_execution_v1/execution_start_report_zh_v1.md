# 欧氏／表面图采样对照：欧氏臂授权执行启动记录

2026-11-04，状态：训练运行中。用户原文“已上传，按既定边界单独授权上述完整哈希。”解析为scope SHA256 `40a45089ed847261d9477993118b406048dadd09d15e492a402b455bddfdad74`。

5个上传文件核验通过，650目标在写入前全部不存在；不覆盖安装完成并逐文件核验哈希。随后按授权→runtime→launcher单向顺序材料化，创建单次claim后仅调用一次tmux。固定会话：`bcsp_blue_noise_foldc_euclidean_seed0_train_v1`，worker PID `35698`。

启动后只读观察显示已提交112/3900次更新，tmux和worker存活，未见退出码、completion或失败文件。显存SMI 14074MiB，Torch峰值allocated 12.30GiB，RSS 1.18GiB，记录的资源断言通过。SMI/容器PID不同仍按既定diagnostic-only合同记录，不新增PID所有权阻断。

仍为FoldC、seed0、8k→8k、63来源315病例、100遍历、3900更新、31200曝光和300丢弃；本轮未启动图距离臂、开发评价、BNCal或其他实验。后续按独立只读训练后审计核验最终计数、初始化、批次与checkpoint SHA256；本记录不代替该审计。

调用过程的本机静态换行检查先误写9行而实际为8行，修正断言后完成静态检查；该阶段未连接服务器或消耗训练attempt。真正的三个服务器执行阶段均仅执行一次且返回通过。

服务器输出：`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_blue_noise_ab_v1/bcsp_blue_noise_foldC_Euclidean_elimination_in8192_out8192_seed0_train_v1`。
