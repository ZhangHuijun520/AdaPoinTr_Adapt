# F0 Fold D最小入口、CPU验证与待授权训练request v1

交付收尾日期：2026-11-11。入口、CPU验证、P3及冻结request在2026-11-10生成；本次只补说明与最终只读哈希核验，不更改已冻结文件或其日期/run ID，不连接服务器、不重复测试或GPU preflight。

## 完成结果

新增隔离生产入口bcsp_f0_foldD_training_entry_v1.py和针对性测试文件。29项CPU契约检查全部通过，本机P3完成；原Fold C入口、模型、F0 factory/decoder、原始完整CD loss及3900步生命周期保持不变。测试使用真实冻结元数据/准入锚点核验授权合同，张量输入、前端、loss、SSM及bridge/runtime为明确人工fixture，0 optimizer step；不是实际D折训练。

新入口仅接受F0-P-v2、Fold D、seed0、8192输入/8192输出。保持batch8、100 traversals、3900 updates、31200 exposures、300 drop，以及既有初始化、LR/BN时序与资源阈值。绑定正式native CUDA准入，无需重新preflight。

## C/D配对证明

硬绑定Fold C正式冻结审计SHA256 `d2e98602b245596268eb288ee5adcfb85d4f95975e7463a3e7c280563299c958`，并核查其3900步完成、初始state、实际factory、完整order与checkpoint哈希凭据。这里不加载或复制C折权重；D折仍从scratch构造同一初始化。

同时硬绑定历史M0 Fold D request SHA256 `55793bca2fa9472d45b3cca0b9598154cdb12a84a3eb89633daa52b85a039d5f`，冻结同折QC、315例/63来源、数据根及批次顺序。Fold C顺序不能替代D折顺序，不依据C折训练loss调参或筛病例。历史request仅作数据/协议依据，旧容器身份不用于D折执行。

CPU检查覆盖完整authorize()、无授权/循环绑定/错误哈希/错误折与点数拒绝、C折证据与D折顺序核对、F0工厂分派、8k batch8人工forward/backward、几何日志、参数量与3900条日志终止守卫，以及POSIX启动渲染。

## 就绪范围和局限

2026-11-10只读快照核对了n8xph5-0、固定GPU UUID及9个元数据/复用工具文件哈希，并stat了315个D折训练文件；没有读取NPZ数组或checkpoint。查询时GPU占用1MiB、磁盘约12.35GiB，新安装根/输出/会话不存在。这是历史就绪快照，实际执行前必须重验当前身份、资源、全部目标与315训练文件SHA；不视为设备预留。

## 冻结交付

待授权request：F0_FoldD_training_execution_request_v1.json。

完整SHA256：

`ea45165142676c16b0c18e5616494ee78e1231970590ce4b314bf4c479bcd8b0`

状态：AWAITING_EXPLICIT_USER_AUTHORIZATION。

运输包：bcsp_f0_FoldD_training_pending_20261110_v1.tar.gz，142281 bytes。

运输包SHA256：`fd5801178d821594ce212dcaa39a5b9d5bfd079d5ca5838b10a5e9e638a62440`。

18个普通文件包含专用入口、未改bridge、native准入证明、C折冻结证明、历史M0 D reference、就绪回执、两折合同、P3及待授权request；不含权重或真实点集。原已安装模型/runtime及QC/order按精确绑定复用，不覆盖已有文件。映射见frozen_transport_installation_mapping_v1.json。

本次最终核对了18个tar成员及映射、四个上传文件、入口/测试/P3源哈希，均匹配。请手动上传tar.gz及同名.sha256、.bytes、.contents.sha256到/home/jovyan。上传本身不授权执行；仍需对上述完整request SHA明确授权，才可核验、不覆盖安装并启动唯一一次D折训练。失败即停，不自动重试/resume，不运行BNCal或development evaluation。

本轮没有部署、材料化真实授权回执/runtime/launcher/claim或启动训练。CPU fixtures内的人工授权文件不适用于此真实request。后续执行必须记录实际启动时间，不改写本次冻结标识。
