# F0／T0／M0 CPU评分授权执行与启动观察

日期：2026-11-11。状态：唯一一次真实本机CPU评分已启动，尚未结束。

用户单独授权的完整request SHA256：

    eaa35866db0c8dc231ee0b6f2cfd8a0d72436d088d5066bbf694acc7313ec175

启动前已重新核验评分入口、指标、P3及全部绑定证据、三个预测归档及校验文件、固定CPU Python、210份参考及210份point文件。CPU包版本与冻结环境一致，实际授权／输出目录在创建前不存在。未覆盖或修改预测归档与原指标。

独占创建本机授权回执和单次attempt记录后启动一个worker。supervisor PID16472，评分worker PID24764。CPU环境禁用CUDA可见设备，OMP／MKL／OpenBLAS均2线程；主合同18000秒、RSS8 GiB、输出2 GiB，外部supervisor超时18030秒。失败保留部分结果，停止且不自动重试或resume。

最近观察时间2026-11-11T04:45:49.737953+00:00，即北京时间12:45:49。观察到40／1050行，8／210个完整病例；最后病例train__003__parietotemporal，最后arm为GT_8192。worker与supervisor进程均存在，无failure.json、无完成标志，stderr为0字节。此数字是当时状态，不能当作最终计数。

固定输出目录：

    E:\Codex\2026-06-06\mamba-ccf-c-1-high-resolution\outputs\cranial_bcsp_fullmamba_20261110\Native_scoring_implementation_v1\unified_scores_v1

固定主日志：

    E:\Codex\2026-06-06\mamba-ccf-c-1-high-resolution\outputs\cranial_bcsp_fullmamba_20261110\Native_scoring_implementation_v1\authorized_execution_v1\stdout_v1.txt

错误日志为同目录stderr_v1.txt；worker_started_v1.json与attempt_started_v1.json记录PID、时间和单次边界。supervisor完成后写execution_result_v1.json，评分器正常完成后写unified_scores_v1/completion.json。

范围仍为T0／M0／F0各210预测、Nop_D／GT_8192共享控制共420行，总1050病例行、210source行。当前未运行服务器操作、GPU、模型forward、训练、BNCal、bootstrap或正式gate。没有解读实际评分数值。

结束后需另行正式只读评分后冻结审计，核验计数、产物哈希和汇总一致性，通过后才解读科研效果。
