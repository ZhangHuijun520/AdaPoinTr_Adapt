# P1 Fold D 专用训练入口：实施、CPU回归、P3与T0待授权request

日期：2026-11-06。结论：限定实现与62项人工CPU回归通过，本机P3通过，首个T0_D execution request已冻结为待授权。未部署或启动训练。

## 1. 限定实施

仅新增两个隔离代码文件：bcsp_p1_foldD_training_entry_v1.py及test_p1_foldD_training_entry_v1.py。原Fold C入口、model factory、Mamba encoder、训练runtime、metadata辅助、provider、数据和数值合同保持原字节。AST核验：原有函数/类中只有authorize变更，另增加validate_T0_D_pairing；main、dispatch、TrainingBudget、P1Budget、payload路径与文件守卫均与成功C入口相同。

D入口显式绑定D的QC、315例来源清单、data_root和固定顺序；不再要求D数据/顺序与历史C量化诊断相同。历史C诊断/梯度量化文件本身不改动，依旧绑定同一架构、环境、provider、static配置和原生初始化来源，不能称其为D的新GPU测试。

T0_D要求t0_pairing为null，从scratch开始。后续M0_D要求真实T0_D正式冻结审计及8项精确配对记录：audit、request、construction、initialization、order、completion、run_identity、exposure。核验D/T0身份、共享初始状态、完整实际batch顺序、逐病例/逐来源曝光、丢弃计数及最终3900步完成记录；不能用C证据替代，也不加载T0训练后的checkpoint初始化M0。

## 2. 原训练合同不变

V1采样、共同GT8192、输入/输出8192、coarse256、seed0、batch8、100 traversals、每轮39 batch、3900 updates、31200 exposures、300 drops保持不变。AdamW、LR/BN调度、SSM no-weight-decay标记、FP32、deterministic/TF32false和有限M0梯度非确定性披露全部继承。BNCal/evaluation/resume均false。没有根据Fold C结果改参数、重分折、加权或筛病例。

资源仍为86400秒、RSS8GiB、torch allocated/reserved各20GiB、设备显存22528MiB、输出2GiB、磁盘至少4GiB。PID日志只作诊断；训练资源类、失败先落盘再断言和3902条计数上限均未改动。

## 3. 62项人工CPU回归

完整T0_D与M0_D authorize路径通过，使用真实metadata验证器读取人工420行元数据及D315例allowlist。验证C-only schema/错误fold、历史C数据/顺序、16k、授权回执与runtime反向绑定/漂移、依赖环境漂移、缺失配对、C审计混入D、真实batch顺序/曝光/初始化变化、resume完成标记等均被拒绝。

完整冻结训练runtime在Tiny CPU张量上运行精确3900步，验证forward/backward/clip/optimizer均3900、LR与BN scheduler均100、曝光31200/drop300、实际batch顺序及调度数值、3902资源回调与最终checkpoint哈希。所有数据均人工fixture，未调用真实AdaPoinTr/Mamba、未读真实点集payload、无GPU或服务器调用。测试中的人工请求/回执不是生产执行授权。

资源类另以人工遥测验证内存阈值、失败样本先持久化、PID数值不一致仅记录以及3902上限；无额外GPU preflight。原始结果和fixture保存在CPU_contracts_v1，执行前后源代码/测试哈希保持一致。

## 4. 本机P3

P3核验62项结果、源码与测试哈希、继承类/函数AST及6个原实现哈希。对实际D QC/两份manifest/fold/顺序元数据，用冻结SHA256匹配的本机副本运行原metadata函数，确认D315例/63来源/100轮/3900步。没有把服务器Linux路径猜测转换成Windows路径，也没有解码真实点数组。

沿用前一准备阶段的服务器只读快照：315个D训练文件、29项复用绑定与当前v2iwsa-0 GPU身份已核验；本轮未重新连接服务器。安装/执行前仍须重验当前身份、资源、上传文件及新目标不存在。详见implementation_P3_v1.json。

## 5. 首个T0_D待授权request

文件：transport_payload/T0_foldD_seed0_training_execution_request_v1.json

完整SHA256：`6a9e9bcdbfa60a6a9bc6b80c6d2d1374796aa02c919766c2fb70b3a0aa764f82`

schema：bcsp-p1-foldD-training-request-v1；状态：AWAITING_EXPLICIT_USER_AUTHORIZATION。仅T0_D，不授权M0_D、BNCal、development evaluation或自动重试。首运行ID为bcsp_p1_T0_foldD_seed0_train_20261106_v1；使用全新D安装、control、tmux与结果路径。旧C request不复用。

授权回执、runtime、实际launcher、claim均尚未创建。运输包内仅有带占位哈希的launcher模板，已检查使用Linux POSIX路径，先创建日志目录再重定向，PowerShell须显式exit LASTEXITCODE。实际调用继续使用原文件字节Base64，不经文本解码重编码。

## 6. 运输与下一步

运输包：bcsp_p1_T0_foldD_seed0_training_20261106_v1.tar.gz，17698 bytes，SHA256 `32d4cba38aec92075eaaab4e4f068fbbb9caeb18160f69ec39730bd1a1f818e3`。共6个新目标：专用入口、D配对合同、P3、CPU结果、launcher模板、T0_D request；所有成员已逐一重算哈希。另有.sha256、.bytes、.contents.sha256三个校验文件，映射见transport_manifest_v1.json。

不含权重或点集，复用服务器既有315份D训练数据与既定依赖。下一步将这四个运输文件上传至/home/jovyan；随后单独明确授权本request完整SHA256，才可重验、独占不覆盖安装、按授权→回执哈希→runtime→单次launcher顺序材料化并启动唯一一次T0_D训练。异常即停，不自动修复重跑。

T0_D完成后另做正式只读训练冻结审计，再将实际D证据绑定到M0_D新request；本轮未创建生产M0_D request、未训练或评价，不重复GPU preflight。
