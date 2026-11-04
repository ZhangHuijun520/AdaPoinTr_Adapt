# 欧氏／图距离两臂：开发预测执行记录

2026-11-04。状态：**210预测已完成，正式冻结审计待单独授权。**

本次授权scope SHA256 `4fd0d2736e58530326c37d77fdbd5e76242339c36ea0a7905290a58d0b31ab43`。执行前核验当前hostname／GPU／Python、两个已冻结checkpoint、固定复用资产、5个上传文件和全部213目标／新目录不存在性；随后按冻结映射不覆盖安装，单向材料化授权、runtime、launcher及claim，仅启动一次固定tmux。

只读完成观察显示：欧氏105例＋图距离105例，共210条预测记录；退出码0，tmux与worker退出，无failure。两模型各自参数／BN状态、CPU／CUDA RNG与Python／NumPy RNG前后保持一致。training_updates、BNCal、loss和backward均为0。未进行本机评分、统计比较或额外训练。

完成记录报告归档：`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_blue_noise_ab_v1/bcsp_blue_pair_foldC_seed0_dev_v1/development_predictions_v1.tar.gz`，18,915,240 bytes，SHA256 `135102bb6af6d18e45735ed63041c9fecb471a3a75556d7d2b9ea07d5a2ea2a6`。这些是当前完成记录与状态观察，尚未独立重算归档哈希、逐预测核验或完整冻结；不能替代正式审计，也不据此判断采样胜负。

下一步应单独授权正式只读预测后冻结审计，核验210份预测、归档／内容清单、状态／RNG、调用计数及资源证据；通过后再手动下载并核验，随后单独授权统一CPU评分。当前没有下载、评分或正式gate。
