# F0 Fold C唯一一次训练启动记录 v1

日期：2026-11-10。用户已明确授权完整request SHA256 afd2750a3738f65d6fcfc308153c4358a4ded5e242a7e74796f9d8dec519d32d 对应的不覆盖安装和单次训练。

四上传文件、当前n8xph5-0/UID1000/同一GPU、直接相关依赖及315个训练文件SHA256均匹配；原63来源/315例QC和100遍完整批次计划保持。11文件不覆盖安装后逐个哈希核验，随后按单向绑定材料化授权回执、runtime、launcher，并在唯一tmux调用前独占创建claim。模型/loss/runtime/资源阈值未修改，无新的GPU preflight。

会话：bcsp_f0_foldC_train_20261110_v1。
输出：/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/F0_foldC_seed0_train_20261110_v1。

最近一次只读观察已提交103/3900步，epoch=2（0起始），batch=24。tmux仍在，无失败/退出码/完成文件，最新资源守卫记录通过。已出现初始化、实际optimizer参数组、order_plan、模型构造及F0_geometry日志，证明确已进入训练，不仅是tmux创建成功。

一次批次loss仅作进程健康信息，不据此解读开发精度。此观察不代替训练后正式冻结审计。没有启动Fold D、BNCal或development evaluation，不会自动重试/resume。

原始启动与状态回传、控制脚本字节哈希以及当前机器可读观察保存在本目录。训练执行辅助控制脚本暂存于项目third_party/f0_FoldC_training_authorized_once_20261110_v1.py，不属于模型修改；固定11文件与训练request保持原字节。
