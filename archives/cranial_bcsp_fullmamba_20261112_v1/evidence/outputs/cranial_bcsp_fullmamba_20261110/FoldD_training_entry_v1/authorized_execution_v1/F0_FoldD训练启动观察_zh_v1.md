# F0 Fold D唯一训练启动观察 v1

记录日期：2026-11-11（Asia/Shanghai）。冻结run ID与目录中的20261110保留原标识，服务器日志时间按原样保存。

已按用户对完整request SHA256 ea45165142676c16b0c18e5616494ee78e1231970590ce4b314bf4c479bcd8b0 的明确授权，核验四个上传文件、当前n8xph5-0身份/同一GPU、固定元数据/模型依赖、C折审计/配对证明及315个D折训练文件SHA256。18文件不覆盖安装并逐个回读哈希后，按回执→SHA→单向runtime→launcher顺序材料化，唯一claim在tmux调用前独占创建。

最近一次只读检查已提交81/3900步，epoch=2、batch=2（均0起始）。固定会话bcsp_f0_foldD_train_20261110_v1仍在，无失败/完成/退出码文件；最新资源守卫通过。初始化、实际参数组、完整order和F0_geometry日志已出现，确认真正进入optimizer更新。

输出：/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/F0_foldD_seed0_train_20261110_v1。

模型、loss、runtime及3900合同未改；D折从scratch开始，没有加载C折checkpoint，没有重复GPU preflight、BNCal或评价，也不自动重试/resume。启动观察不代替训练后的正式冻结及C/D配对审计，批次loss不作为开发准确性结论。

本次执行专用std库控制脚本暂存于项目third_party/f0_FoldD_training_authorized_once_20261111_v1.py，仅作冻结范围的核验/部署/启动；原始字节指纹随本机调用claim保存。冻结request、运输包和生产源码保持原字节。
