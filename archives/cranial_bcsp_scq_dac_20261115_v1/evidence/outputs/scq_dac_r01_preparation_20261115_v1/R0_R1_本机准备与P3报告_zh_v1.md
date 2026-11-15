# SCQ-DAC R0／R1：20例冻结权重机制诊断本机准备报告

日期：2026-11-15。状态：**本机准备完成；执行请求待单独授权**。

## 📋 1. 本轮实际完成的工作

按已确认的 SCQ-DAC 审阅修订v2，完成两个 Requery 权重字节身份核验、固定20例选择、历史Native预测成员提取核验、专用采集接口、人工CPU合同验证和本机P3。没有连接服务器、部署、加载真实checkpoint、运行真实颅骨forward、计算新几何分数或启动训练。

当前用户确认容器为 `shu-common-25721452-notebook-qx2k0r-0`。GPU UUID、驱动、软件栈、实际依赖和输入路径采用既有冻结期望值，**本次未远程复核**；request要求在任何部署/启动前重新核验，发现变化即停，不能以用户确认hostname代替资源证据。

## 📦 2. R0本机资产核验

| 权重 | bytes | SHA256 |
|---|---:|---|
| Requery_C | 489,927,058 | `4816c8768da60de7c8153fcd0793524b2fb3c1dddba04de9cdf0c6eb13f2602b` |
| Requery_D | 489,927,058 | `068288d4beb237dfe820286e22e122a5f427e4e32846c63087320aabc5b25bba` |

两文件位于 `E:/ResearchBackups/AdaPoinTr/BCSP_FULLMAMBA_SCQ_RF/2026-11-15_key_checkpoints_v1/weights/`。重新读取实际字节计算哈希通过；本轮未使用torch反序列化它们。

历史预测归档SHA256：`e6462382010d3061c4aa32936c052416c9bb1d6fa93233cb4159036bd51e9df0`。只从中提取20个选定Requery Native NPZ成员，逐成员对照内容清单哈希，不解压全归档，不重新评分。

旧服务器checkpoint源文件已被授权清理，因此映射采用全新目录：

`/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_dac_r1_20261115_v1/weights/`

没有复用或回填已删除的旧日志路径。其余四个旧模型不恢复。新代码、清单、预测参照和权重共28个映射文件（含request），目前仅冻结映射，未制作运输压缩包、上传或安装。

## 🔍 3. 已冻结的20例

规则：每折、每类型各2例；先纳入既定七例，再以 `SHA256(SCQ_DAC_R1_v2|fold|source_id|defect_type)` 升序补足。实际source ID使用manifest中的 `train:NNN` 字符串，不使用编号的另一种写法。病例顺序与选取依据已写入JSON。

| Fold | 类型 | 病例1 | 病例2 |
|---|---|---|---|
| C | bilateral | 001 | 081 |
| C | frontoorbital | **053（固定）** | 094 |
| C | parietotemporal | **012（固定）** | **025（固定）** |
| C | random_1 | 012 | 042 |
| C | random_2 | **025（固定）** | 076 |
| D | bilateral | 005 | 037 |
| D | frontoorbital | **008（固定）** | **087（固定）** |
| D | parietotemporal | 004 | 044 |
| D | random_1 | 052 | 079 |
| D | random_2 | 062 | **069（固定）** |

七例是已知压力测试；哈希补充病例也属于已开放开发来源，不将该选择标为独立盲测。未依据新分数筛病例，没有新增来源或访问confirmation20。

## 🧮 4. 入口与调用合同

专用采集模块：`bcsp_scq_dac_r1_core_v1.py`；专用入口：`bcsp_scq_dac_r1_entry_v1.py`。

1. 原Requery模型保持不变，通过临时模块hook捕获同次M/F/z、Q0/Q1、N0/N1和原第二头新邻域proposal。
2. 在同一个Q1、同一个h1上重算旧索引N0的相对几何并得到旧proposal。不会把Q0几何误用作Static上下文。
3. 使用已确认v2的逐范数保护余弦、近零alpha=0.5、alpha-only detach，产生Average/DAC两组Q2。
4. 只重放原 `mlp_query → LQI decoder → 原FC重建头`，不重跑encoder/coarse/SCQ/RF。decoder-only期间用hook阻止误入整模型或上游。
5. 临时hook在成功和失败时均移除；无GT、loss、backward或optimizer。

| 调用 | 精确总数 |
|---|---:|
| 完整Native forward | 20 |
| 额外decoder-only | 40 |
| 实际decoder调用 | 60 |
| 原第一头调用 | 20 |
| 第二头新/旧proposal | 20 / 20 |
| loss / backward / optimizer.step | 0 / 0 / 0 |

每次调用前先持久化claim，不自动重试。每个模型结束核对参数/BN状态及RNG指纹。20份输出保存M/F/z、索引、proposal、alpha/cosine、Q阶段与三份dense。

原Native重放容差：归一化坐标atol=1e−5、rtol=1e−4，保存实际差值；不通过时停止，不用GT配准、调容差或重试。R/A/D在这里均是**固定旧权重下的诊断性反事实**，不是新训练模型的正式性能。

## 🧪 5. 人工CPU验证与P3

唯一一批CPU验证 **36项通过**，内部耗时约3.14秒。环境为本机已存在的 `E:/RelocatedData/zhj/.conda/envs/adapointr/python.exe`，未安装依赖。

覆盖：20例选择稳定性/身份篡改拒绝、解析组合边界、微小同向向量与正比例缩放、近零退化、非有限拒绝、alpha detach、实际RF旧上下文descriptor一致性、原母版顶层forward/FC与suffix中性等价、hook清理、调用上限、只读取NPZ的partial字段、实际入口20例人工循环、状态/RNG、完整authorize()和单向runtime、POSIX启动渲染及2048字节行上限。

CPU使用**实际冻结RF残差、原母版顶层forward和FC类**，但encoder/decoder是明确标记的人工替身；只加载测试生成的人工checkpoint和人工NPZ，未加载真实权重/点集。它不证明实际native Mamba/CUDA等价，也没有生成DAC有效性结论。

测试产物全部留在 `cpu_contract_batch_v1/`，已生成只读内容哈希清单；未删除fixture、未重跑测试。本机P3汇总16项检查通过，明确保留真实CUDA、checkpoint数值恢复和远端就绪缺口。

## 🚦 6. 待授权request

文件：`pending_request_v1/SCQ_DAC_R1_execution_request_v1.json`

完整SHA256：

`129afea067a01802185719480591845e5918d52c4d28b9ec675012b1794e14a8`

状态保持 `AWAITING_EXPLICIT_USER_AUTHORIZATION`、`execution_authorized=false`。

固定资源预算：600秒、allocated/reserved各20 GiB、SMI 22,528 MiB、RSS 8 GiB、输出256 MiB、至少保留4 GiB磁盘空间。沿用SMI PID仅诊断口径，不开发跨命名空间所有权框架。真实启动仍以原生CUDA单设备和冻结provider为准，不接受fallback。

没有材料化真实授权回执、runtime、launcher或attempt claim。只在内存中以占位哈希检查启动脚本渲染，未保存可执行脚本。安装映射中的全部目标必须先确认不存在，父目录无链接，采用不覆盖写入；异常立即停止。

request绑定的运行目录：

`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_DAC_R1_frozen20_20261115_v1`

**本request仅采集R1张量与反事实输出，不访问GT、不执行几何评分、不自动作GO决定。** 完成后先正式只读冻结审计，下载核验，再限定复用原GT/评分器做离线解释；这一步才形成是否值得训练的判断。

## 📋 7. 下一步与限制

下一步可合并一次必要服务器只读就绪核对：当前身份/资源、冻结主体与provider、20个输入、复用Native入口和新安装目标。通过后按已冻结映射准备运输包，不扩大框架。实际上传、安装及唯一一次20+40诊断仍遵守分阶段授权。

若资源或代码身份变化，应报告精确差异并重新绑定版本，不能直接套用旧request。若GPU诊断失败，冻结失败证据后停止；不得自动增加调用、训练或调整公式。即使采集成功，也尚未证明方向一致性能减少几何错误。

本轮没有实施可训练DAC模型、没有重装环境、没有重复GPU preflight或自动进入六run训练。
