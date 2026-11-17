# SPCG G0_C启动链v2：新P3与待授权请求

2026-11-16。新P3已完成，依据最终v2入口与12项真实加载链／失败收尾CPU检查，继承未改bridge的16项人工生命周期验证及正式CUDA冻结证据。此前失败批次保留，不重跑GPU准入。

核心变化仅为显式bridge→head→observe→training runtime加载、将head精确绑定纳入request／只读守卫，以及守卫仍活跃时保存完整异常后SystemExit(1)，finally再关闭guard／UTC。Windows二进制适配和环境只读根调整仅限人工测试进程。

模型、head字节、初始化、loss、数据、Fold C完整批次order、3900步及资源阈值均未改动。首run仍G0_C，8k→8k，3900更新、100遍、31200曝光、300drop。1GiB输出、3600秒、8GiB RSS、20GiB Torch、22528MiB SMI保持原合同，启动前按折块重验至少8.5GiB可用。

新request：pending_transport_v2/payload/SPCG_G0_C_training_execution_request_v2.json。

完整SHA256：`6a1ff266ff9eae8db51b5809b7db3aa87b72900625d267a4ee3b0a5a9a489f42`。

状态AWAITING_EXPLICIT_USER_AUTHORIZATION；新安装根、control、run和tmux为v2。旧v1 request已消耗不得复用；旧安装不覆盖。新request复用原bridge、观察runtime、精确head、provider、数据及CUDA冻结凭据，最小包只新增入口与审阅证据。

运输目录pending_transport_v2。上传bcsp_spcg_G0_C_startup_hotfix_pending_20261116_v2.tar.gz及其.sha256、.bytes、.contents.sha256四文件。归档16,448bytes，10个拟安装文件＋映射。

本轮仅本机冻结，未连接服务器、重新测试或运行GPU；没有材料化真实授权回执、runtime、launcher或claim。最终序列化request的授权／runtime／启动器合同仅在内存静态检查。

上传后需单独完整SHA执行授权，重新核对当前身份、GPU、复用资产、315训练输入及新目标后才可不覆盖安装、单次启动。CPU通过不代表生产训练已通过；无需重复GPU准入，也不从一次启动成功推导后续训练授权。
