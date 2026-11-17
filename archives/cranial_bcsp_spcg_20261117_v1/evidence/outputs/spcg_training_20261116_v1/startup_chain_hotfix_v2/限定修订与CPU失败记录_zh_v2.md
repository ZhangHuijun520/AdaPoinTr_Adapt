# G0_C启动链与异常收尾限定修订：当前状态

2026-11-16。本轮不操作服务器、不运行模型或重复GPU准入。

新增隔离training_entry_v2候选，原v1源码与训练bridge保持不变：

- load_training_chain按bridge→head→observe→frozen training runtime显式加载，供后续新request绑定head精确大小／SHA。
- fail_with_traceback在guard仍开启时将原始格式化异常落盘，然后SystemExit(1)；finally再关闭guard与UTC，避免未处理原异常在关闭后触发sys.excepthook读取。

唯一一次新CPU批次失败，已保留CPU_batch_v2/failure.json、child_stdout.bin、child_stderr.bin、fixture和子进程源码，未修复或重跑。

本次子进程实际加载bridge、head、observe和frozen runtime，未再出现bcsp_spcg_head_v1找不到的问题；但在额外人工Q.backward检查中，PyTorch延迟导入torch.nested._internal，读取环境内__pycache__/__init__.cpython-39.pyc，被fixture的空read_roots拒绝。生产入口本来有envroot读取根，故这是测试环境合同未对齐，不足以证明Linux生产路径失败。

父测试完成前两项静态检查，尚未完成原始异常收尾注入和12项结果文件；不要把模块已加载的轨迹当成整批通过。父测试随后的FileNotFoundError是因为子进程没有到达chain_checks.json写出，根因应以child_stderr记录为准。

新P3未完成，新request和运输包未创建。模型、数据、loss、3900步和资源合同均未修改。

建议下一步仅修订人工fixture：与生产同口径增加当前CPU环境只读根，保留邻近项目源码、输入、checkpoint和写权限拒绝；不要逐个放行PyTorch内部文件，也不要改生产守卫。静态核对后另执行一次新版本单批CPU验证，继续覆盖实际加载链及失败退出。无需GPU准入。
