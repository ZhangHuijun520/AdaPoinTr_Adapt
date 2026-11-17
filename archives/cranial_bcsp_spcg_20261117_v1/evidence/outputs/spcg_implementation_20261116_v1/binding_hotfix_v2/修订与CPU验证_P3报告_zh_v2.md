# SPCG GPU绑定与启动诊断v2

2026-11-16。限定implementation-only完成，唯一一批12项人工CPU回归通过，新P3通过；原32项模型合同测试未重跑。

新增隔离入口bcsp_spcg_cuda_entry_v2.py。相对原入口只修改authorize、render_launcher和main，并新增validate_request_gpu和startup_query：

- 最终request明确同步environment.CUDA_VISIBLE_DEVICES与identity.gpu_uuid；authorize、launcher和首次查询前均检查一致，实际进程环境也须匹配。
- 首次SMI前独占写入worker.pid及startup_query_attempt.json。异常时将原exception.details（真实command、returncode、stdout/stderr、超时与阶段）写入startup_failure.json后重新抛出，不重试。
- 使用全新v2安装、control、tmux和输出路径；旧request维持已消耗状态，不复用。

模型、head/factory/runtime源文件、U/H初始化字节、五个病例、provider、loss、资源阈值与11forward/3loss/3backward/0step均保持不变。回归用人工SMI替身验证拒绝路径、PID顺序、非零／超时详情、一次调用、成功输出和单向授权；没有调用SMI、模型、服务器或GPU。

最终序列化request在P3绑定完成后，再次完成纯静态跨字段检查、授权/runtime内存渲染和launcher渲染。未生成真实授权回执、runtime或launcher。

request完整SHA256：

`a2b1961158b58199e212130654ddd274ce617c90e24448f22ba70a0062c2343e`

状态AWAITING_EXPLICIT_USER_AUTHORIZATION。运输目录pending_transport_v2，共7个新文件；既有科学实现和初始化复用，不重新上传大资产或重装环境。

上传bcsp_spcg_binding_hotfix_pending_20261116_v2.tar.gz及其.sha256、.bytes、.contents.sha256。归档18,201bytes。上传后需只读核验及单独完整哈希执行授权；当前容器和设备仍以最近证据为依据，执行前必须重新核验，不将本轮本机修订视为服务器已就绪。

CPU通过不代表实际SMI、Mamba、完整CUDA loss／梯度或显存通过。成功执行后仍需正式post-CUDA冻结审计，再准备训练request。
