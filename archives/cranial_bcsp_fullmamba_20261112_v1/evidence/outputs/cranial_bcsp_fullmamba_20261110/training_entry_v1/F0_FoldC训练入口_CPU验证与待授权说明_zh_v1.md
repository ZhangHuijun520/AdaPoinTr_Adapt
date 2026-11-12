# F0 Fold C训练短入口、CPU验证与待授权request v1

2026-11-10。**implementation-only收尾完成，新版25项人工CPU验证通过，本机P3完成；首个Fold C request保持AWAITING_EXPLICIT_USER_AUTHORIZATION。没有部署或启动训练，没有重复GPU preflight。**

## 实施内容

唯一新增生产实现为bcsp_f0_training_entry_v1.py。它只接受F0-P-v2、Fold C、seed0、8192输入/8192输出；硬绑定正式native CUDA准入回执SHA ff47195c2456c2746ec9ae58cf266bc004375d5f79d87b8e536fa6ab549cf1c0，以及相应审计/构造/完成证明和已测试的四个模型文件。不会仅凭任意PASS字符串放行。复制到新运输包的runtime bridge保持原字节。

模型、F0 factory/decoder、原P1 factory/encoder、原始完整CD loss及3900步runtime不变；metadata、预算监测和UTC工具按原精确哈希复用。维持严格数值设置/TF32=false，披露既有有限梯度非确定性。资源仍为RSS8GiB、Torch20GiB、SMI22528MiB、每run86400s、输出2GiB、磁盘至少4GiB；PID遥测仅诊断，不要求宿主procfs映射。

入口委托原生命周期：batch8、100 traversals、3900次更新、31200曝光、300 drop，AdamW及LR/BN时序不变。以模型forward hook采集coarse/dense的脱离计算图的质心、半径和范围，每步映射原case顺序；不存整层特征、不引入loss或GT定位信息。记录实际total/encoder/decoder/other参数量及初始化，checkpoint保留原schema/stage作为来源标记，真实F0身份由run_identity和模型构造证明标识。

## 验证与已知限制

静态核对所有原实现哈希不变。第一批人工CPU验证到末项launcher断言时失败：测试fixture仍带本机Windows入口路径，无法满足纯POSIX断言。失败文件保留在artificial_cpu_batch_v1。随后仅新增测试v2，将这一渲染fixture入口显式设为POSIX路径，生产入口字节不变；artificial_cpu_batch_v2的25项全部通过。

验证覆盖完整authorize()真实代码路径（使用实际准入哈希、人工QC/批次元数据及仅测试进程内的路径镜像）、缺授权/循环绑定/错误工厂/折与点数变化拒绝、315精确allowlist与越界拒绝、真实F0工厂的人工因果mixer构造、8k batch8的一次人工loss/backward、bridge/runtime调用签名、脱离图的几何日志与case/step绑定、3900日志终止守卫，以及POSIX/86400s launcher渲染。

CPU验证使用明确人工前端、cheap loss、SSM surrogate及bridge/runtime spies，0 optimizer step；它没有再次运行native Mamba或真实3900步。生产bridge的守卫/接口沿用既有冻结实现，实际native Mamba/PointNet2/cdist准入及正式冻结审计直接继承，不重新执行。不能把本次CPU调用当作真实训练或稳定性结论。

## 有界只读就绪证据

当前n8xph5-0的九个原Fold C元数据/复用工具文件SHA匹配，固定315训练点集只进行了存在性/路径链接/大小stat，没有读取NPZ数组；完整315文件SHA在将来明确授权执行前再次逐一核验。原QC、840点集声明和420病例元数据的几何/语义限制完整保留，未替换为新的解剖准确性认证。

同一RTX4090D UUID保持GPU-aa9e6ffb-fdbb-1836-1c32-7244231d3714；就绪查询时显存占用1MiB、磁盘约12.8GiB，新训练安装根、输出与tmux会话不存在。这是快照，执行前必须重验。未读取开发集或confirmation20的点集payload，未恢复历史checkpoint。

## 待授权执行范围

首个run：F0_foldC_seed0_train_20261110_v1。仅Fold C的唯一一次scratch训练，固定3900步，失败即停，不自动重试/resume，不运行Fold D、BNCal或development evaluation。

Request SHA256：

`afd2750a3738f65d6fcfc308153c4358a4ded5e242a7e74796f9d8dec519d32d`

冻结11文件运输包：`bcsp_f0_FoldC_training_pending_20261110_v1.tar.gz`，38163 bytes，SHA256：`4c0c4e28177b3f0ecb8e00d7c4fca4766ccb6c9051cc642e21e993b5de0d7008`。

包内仅专用入口、未改bridge、五个准入证明文件、就绪回执、C/D科学合同、P3与待授权训练request。没有真实点集或权重，已安装模型/runtime与原QC/顺序按哈希复用。安装映射为frozen_transport_installation_mapping_v1.json，不覆盖已有目标。

请手动上传tar.gz、.sha256、.bytes、.contents.sha256到/home/jovyan。只有之后对上述完整训练request SHA单独明确授权，才可重新核验上传/资源/全体目标和315训练文件SHA、不覆盖安装，并按“回执→SHA→单向runtime→launcher→唯一claim→tmux”执行。

本轮未创建此request对应的真实授权回执、runtime、launcher或训练claim；CPU fixtures内的a*/r*.json仅人工测试输入，不能作为真实执行授权。
