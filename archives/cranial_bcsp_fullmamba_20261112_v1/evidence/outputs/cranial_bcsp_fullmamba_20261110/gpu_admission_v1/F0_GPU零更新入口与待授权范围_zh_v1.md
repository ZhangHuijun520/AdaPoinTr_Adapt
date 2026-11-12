# F0 人工 GPU 零更新准入准备记录 v1

日期：2026-11-10。当前状态：**AWAITING_EXPLICIT_USER_AUTHORIZATION**。本轮完成入口、27项人工CPU合同验证、本机P3、设备与直接相关资产只读核对及八文件运输包；未部署或运行CUDA。

## 科研验证范围

- 真实F0/native Mamba-1，锁定既有2.3.1实现、PointNet2编译provider和PyTorch cdist Chamfer；不编译、下载、升级或切换loss。
- 完整模型：batch1 eval两次、batch8 train两次，共4次完整forward、4次原始完整loss/backward；8192输入、8192输出。eval输出转换为原始无denoise loss四元组，保持原始coarse+fine损失，不使用CPU fixture损失。
- 局部decoder：2病例、六次forward，顺序为原条件两次、feature-null、完整prefix-token-null、早段64个prefix token扰动、只改变第二病例。另一次原条件首层conditional后缀标量backward。
- 六次均运行完整八层decoder；响应单独取首层conditional SSM后缀、局部graph/merge之前。早段扰动保持末3个Memory token与全部Query token不变，用于排除单纯边界短卷积解释，不宣称证明解剖对应。
- 共0次optimizer step，不创建optimizer，不读取真实数据或checkpoint，不进行BNCal、development evaluation或训练。预期native SSM调用288次：完整4×36＋局部6×24；模型forward与SSM算子调用分别计数。

## 状态、数值与判据

完整检查从同一初始化、RNG及BN状态分别开始；eval状态不变，train的BN更新需记录。每次检查后恢复初始权重、BN、模式、momentum和RNG。记录全部现存梯度有限性，检查22个SSM模块、共享PE、coarse及reduce_map的非零模块梯度，不要求所有参数逐项非零或梯度位级相同。

FP32、TF32=false、严格deterministic设置；有限native Mamba梯度非确定性沿用既有披露。输出/loss重复容差atol=1e-6、rtol=1e-5。前缀响应需超过max(1e-7,10×原条件重复maxabs噪声)，执行后不调整阈值。模块库存和实际dispatch拒绝已知SDPA/flash/efficient/multihead attention；记录softmax/einsum供归属核对，不能把任何einsum自动当作attention。opaque扩展内部不声称得到逐算子语义认证。

## 当前设备与预算

已核对hostname `shu-common-25721452-notebook-n8xph5-0`、UID1000、GPU `GPU-aa9e6ffb-fdbb-1836-1c32-7244231d3714`、RTX4090D、driver570.190及Python3.10.20。身份查询时SMI占用1MiB，磁盘约12.8GiB可用。旧身份不继承；实际执行前须重新检查设备空闲、依赖哈希及安装目标。

沿用RSS8GiB、Torch allocated/reserved峰值20GiB、SMI22528MiB、输出1GiB、磁盘至少4GiB。短准入外层timeout1800s、TERM后10s强制终止；2s采样、单次SMI查询10s且不重试。1800s为限定四次全loss F/B及六次局部调用的保守预算，不是性能承诺。RSS/GPU为采样监测，不能保证瞬时峰值或专属cgroup隔离。PID仅诊断，不再引入宿主procfs映射框架。

## 本机验证与边界

唯一一批27项人工CPU验证通过：执行真正的入口authorize/计数/full_checks/decoder_checks逻辑；使用便宜loss和明确的因果surrogate。真实母版八层decoder类由冻结源码AST加载。CPU通过不证明native Mamba、完整Chamfer、CUDA梯度或显存通过。原四文件实现和原P1/P2源码再次核对未变。

本机初次沙箱WSL调用返回E_ACCESSDENIED，未到服务器；经工具批准的非管理员沙箱外只读调用成功。保留原始stdout/stderr字节，不将该启动权限问题认定为科研失败。后续只读核对仅覆盖直接绑定资产，没有通用库存扫描；无服务器写入。

## 运输与授权

运输包：`bcsp_f0_artificial_cuda_pending_20261110_v1.tar.gz`，23707 bytes。

运输包SHA256：`d7aaac39bd37533753ba8dcd6de526ac5bc9532d2150c60cc5c9aeaf86d55c24`。

Request：`F0_artificial_cuda_execution_request_v1.json`，SHA256：

`a9fbc819da73415008ac5643f5b6cea9ab1b3818029129e6f93e2e67bcc23efc`

包内八个普通文件：专用入口、F0 decoder/factory、原P1 encoder/factory/runtime副本、本机entry P3和request。安装映射位于`frozen_transport_installation_mapping_v1.json`；新目录不覆盖安装，复用既有helper/scope/provider，不重装依赖。四个上传文件为tar.gz、.sha256、.bytes、.contents.sha256，建议手动上传到/home/jovyan。

本轮未创建授权回执、runtime config、实际launcher、launch claim或tmux。完整SHA单独授权后，才可核验上传和当前就绪、不覆盖安装，按“回执→哈希→单向绑定runtime→launcher”材料化并执行唯一一次准入；失败即停，不自动重试。

成功也先做正式只读post-CUDA freeze audit，再进入首对训练准备；不自动启动训练。证据见entry_P3_v1.json、final_contract_review_v1.json、artificial_cpu_entry_batch_v1/result.json与delivery_receipt_v1.json。
