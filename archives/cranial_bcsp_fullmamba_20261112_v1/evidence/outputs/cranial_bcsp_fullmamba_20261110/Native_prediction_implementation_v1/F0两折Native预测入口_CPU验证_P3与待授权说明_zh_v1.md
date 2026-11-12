# F0 两折 Native 预测入口、CPU 验证、P3 与待授权说明

日期：2026-11-11。实施范围：一个 F0 专用预测入口、一个人工 CPU 测试文件及限定交付证据。未连接服务器，未部署，未运行真实预测或重复 GPU preflight。

## 📋 结论

S0／S1 静态审查通过；唯一一批人工 CPU 验证42项全部通过；本机 P3 状态为 `LOCAL_F0_NATIVE_PREDICTION_P3_PASS`。已创建最终 execution request，保持 `AWAITING_EXPLICIT_USER_AUTHORIZATION`。没有创建真实授权回执、runtime、已授权 launcher、启动 claim 或 tmux。

最终 request SHA256：

`8c2f849a1e3cb9cfbaac5e501f09647fa0de894491501e0d0bd48e09b9e9ee03`

request 为 `pending_request_v1/transport_payload/F0_CD_native_prediction_execution_request_v1.json`，14625字节。其实际序列化内容已在纯内存人工授权记录下通过 authorize 合同；这不是用户执行授权，也未落盘真实执行控制文件。

## 🔧 实现与保持的合同

生产入口为 `bcsp_f0_twofold_native_predict_v1.py`，31713字节，SHA256 `b1318c0ab8441e56dfd7133c83b2ae07435932359f1843fd7c3616c835e6f72b`。人工测试为 `test_f0_native_prediction_cpu_v1.py`，20101字节，SHA256 `13eedc17238c4470f8e945c1bb15abd7577ad4a56340ddc412b38cab32ee2944`。

| 项目 | 实施结果 |
| --- | --- |
| F0 工厂 | 按实际 `build_model(legacy_builder, seed=0)` 签名加载；精确绑定 encoder、P1 factory、F0 decoder、F0 factory 四文件 |
| 两折调度 | C_F0、D_F0 各105例，原开发顺序与 D-only 坐标不变 |
| 权重 | 严格加载冻结最终 checkpoint；epoch99／3900 updates；state_dict 缺键／多键拒绝 |
| Native 输出 | 210份预测均保存8192点 dense 与256点 coarse；无GT配准、过滤、重采样或TTA |
| 同次调用缓存 | 20例 F／S／z／Q／X，10例8层轨迹；全部从原定210次 forward 采集，不额外推理 |
| z 定义 | 使用 query 前 backbone.global_feature；与 decoder 后 rebuild_global_feature 明确区分 |
| 状态 | 每模型前后参数／BN 和各 RNG 不变；每例清除 instrumentation 开关及缓存 |
| 资源 | 保留7200秒、RSS8 GiB、Torch20 GiB、设备22528 MiB、输出1 GiB、磁盘余量4 GiB合同 |
| 单次执行 | 新目录、独占写入、预先记录 forward claim、错误即停、不继续下一模型、不自动重试或resume |
| 禁止项 | loss、backward、optimizer step、BNCal、warmup 均0；不运行未来30次 decoder-only 干预 |

未修改训练代码、模型公式、采样、provider、wheel、数值阈值或已有实现。读取、数值、资源及归档基础函数复用既有入口，其 AST 一致性已验证。新增的构建／冻结脚本仅用于本机交付，不在服务器执行；运输包内的 launcher 文件是带占位符的 `.txt` 审阅模板，不是已授权执行脚本。

## 🧪 CPU 验证与 P3 证据

本机环境为既有 PyTorch CPU Python。主要证据为 `static_review_v1.json`、`artificial_cpu_batch_v1/result_v1.json`、`implementation_P3_v1.json`、`final_pending_binding_verification_v1.json`。

| 验证 | 结果及实际含义 |
| --- | --- |
| 原数据元数据／训练证据 | 两折105例、原来源隔离、坐标／哈希及两份正式冻结审计均匹配；不读取数组 |
| 授权接口 | 完整 authorize、单向 runtime 绑定；拒绝缺授权、错哈希、额外 forward／warmup |
| 实际加载路径 | 在独立子进程真实 audit hook 下加载四份实际源码；拒绝源码写入及相邻未绑定文件 |
| 实际工厂签名 | 使用真实 F0 factory，人工 causal mixer 替代 native Mamba；验证生产签名可调用 |
| 实际 F0 decoder | 同一输入分别开启／关闭 trace，共2次 CPU decoder 调用；输出逐位相同、状态及CPU RNG不变 |
| 缓存合同 | 检查F／S／z／Q／X及40个逐层张量；拒绝Q漂移、层缺失 |
| checkpoint | 仅人工小权重；真实 strict loader 路径，拒绝计数错、缺键、多键 |
| 210次循环 | 使用轻量人工 outer forward；实际母版缓存控制方法；恰好210份预测、20份context、10份trace，105次／模型 |
| 归档及首错 | 人工产物归档清单／哈希匹配；强制失败场景在首个模型第1次尝试停止 |
| 启动渲染 | PurePosixPath、父目录先创建、固定timeout及逐参数验证；不启动进程 |

上述210次是人工 CPU outer fixture 调用；不等于实际颅骨模型的210次推理。真实母版完整 forward 未在本轮 CPU 执行，实际 CUDA Mamba、CUDA RNG 及显存行为也未由本轮测试证明。正式执行仍须核验当前身份与资产、加载真实权重并运行预测，随后做正式只读冻结审计。

## ⚖️ 科研限制与登记说明

沿用正式计划已写明的代表例／donor规则；精确ID在2026-11-11预测前枚举，未找到训练前冻结精确表的证据，不回填日期。C折代表来源001、donor003；D折代表004、donor005，各覆盖原五类缺损。每折五类来自同一个代表来源，机制诊断不代表五个独立患者。最终 request 显式披露此登记时间偏差。

本次没有评分或性能结论。C／D并非独立随机种子重复，训练 loss 不证明补全改善。后续统一评分应复用冻结T0／M0预测，并分别报告完整骨块、接口及退化风险。未改变有限梯度非确定性的既有披露；此次仅预测，不新增 backward。资源守卫为调用前后监测及外部timeout，不宣称专属硬隔离或通用内核审计完成。

## 📦 上传材料与下一步

运输目录：`pending_request_v1`。仅需手动上传以下四文件至服务器 `/home/jovyan/`：

1. `bcsp_f0_CD_native_prediction_pending_20261111_v1.tar.gz`
2. `bcsp_f0_CD_native_prediction_pending_20261111_v1.tar.gz.sha256`
3. `bcsp_f0_CD_native_prediction_pending_20261111_v1.tar.gz.bytes`
4. `bcsp_f0_CD_native_prediction_pending_20261111_v1.tar.gz.contents.sha256`

压缩包66360字节，SHA256：`c4d115add6cd93207fa1a4bd7d44d395d467e6e395b95372ea6b08890319d1bc`。包内13个精确不覆盖安装目标及映射已逐文件回读校验。

新安装根为 `/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_f0_CD_native_prediction_20261111_v1`；新结果根为 `/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/F0_CD_native_development_20261111_v1`。已知容器身份来自上次正式冻结的 n8xph5-0，不构成本轮实时核验。

上传后仍需用户对上述完整 request SHA256 单独执行授权，才可重新核验当前容器、上传包及全部复用资产，按冻结映射不覆盖安装，材料化回执→SHA256→runtime→SHA256→launcher，独占单次claim并启动唯一tmux。异常即停；不重复GPU preflight。预测完成后另行正式冻结审计、下载本机核验，才准备CPU评分。
