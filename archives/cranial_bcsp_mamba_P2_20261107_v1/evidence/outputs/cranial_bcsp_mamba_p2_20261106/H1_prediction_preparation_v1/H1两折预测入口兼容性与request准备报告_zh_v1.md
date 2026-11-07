# H1两折预测：入口兼容性核对与request准备

状态：**输入与科研范围已冻结；现有入口不直接兼容；最终execution request尚未创建。**

本轮仅本机只读检查现有入口和冻结证据，并保存候选输入索引、协议与准备草案。没有修改预测入口或模型源码，没有运行测试、连接服务器、加载权重或执行预测。

## 1. 已冻结的范围

| 模型 | 开发病例 | checkpoint SHA256 |
|---|---:|---|
| Fold C M-H1 seed0 | 105 | `6839d694cdd8068085dceea1426aa9d55e71faeaff39a9032bf21af6b1e8b5b4` |
| Fold D M-H1 seed0 | 105 | `6a76aa7dc156c0e2eeef29d4e03b253f624373ced8a48abebe1af4c99d7e789d` |

两个checkpoint均407224375 bytes；来源于正式训练后冻结审计。每折21开发来源×5缺损，train63/dev21隔离，C/D开发来源不重叠。每折固定105例的顺序、输入路径/bytes/hash、D-only归一化和target指纹均从P1已审计M0输入索引逐字段继承；210个病例唯一。

特别注意：C开发输入实际存于`bcsp_geov1_foldd_8192_seed0_v1/points`，D开发输入实际存于`bcsp_geov1_foldc_8192_seed0_v1/points`。这是已有分折训练数据交叉存放的精确路径，不是本轮猜测、搬移或数据泄漏。来源隔离按case/source allowlist及冻结hash判断，不能根据目录名字改路径。

输出预算严格为**两个H1模型，共210次forward**。不重新预测T0或M0基线；后续与已冻结M0预测进行离线配对。既有基线预测正式审计状态已核对，本轮未重新打开其大归档；统一评分前仍需核验本机归档内容和病例/输入/目标/坐标配对。

## 2. 兼容与不兼容之处

### 可复用的部分

- 相同模型/factory/encoder，不改变state_dict的参数名称或形状；H1是训练loss配置，不新增参数。源码支持相同strict checkpoint load，但本次未实际加载验证。
- 现有`load_checkpoint()`允许epoch99/update3900、旧stage `BCSP_INPUT_DENSITY_V1`，与H1训练保存格式一致；旧stage只作来源标记，不能单凭它识别H1，必须绑定P2冻结审计及checkpoint哈希。
- `load_partial()`只取partial数组；eval/inference_mode、checkpoint严格加载、256coarse与8192dense输出检查、文件允许清单、factory/encoder精确source读取可保持。
- 参数/BN状态及Python、NumPy、CPU/CUDA RNG在每105例前后保持；数值/TF32/provider守卫、资源采样和失败即停可沿用。
- 既有geometry_summary利用同次输出记录coarse/dense矩与相对位移，不需额外forward。

### 必须适配的五处

| 原入口约束 | H1两折的实际需求 |
|---|---|
| `validate_index()`硬编码同折T0/M0两臂，105+105 | 改为C_M_H1与D_M_H1各105，分别绑定对应fold的dev/train与来源 |
| `helper.validate_model()`拒绝`coarse_geometry_guard_enabled` | 精确允许唯一centroid_radius/.1/.1/1e-6，其他可选目标仍关闭 |
| `main()`要求静态model与基线YAML完全相等 | 只允许额外唯一H1配置，不能放宽为任意差量 |
| `validate_evidence()`期待P1 T0/M0配对receipt | 对应P2 C/D正式冻结审计、H1 request与checkpoint hash，检查M0配对有效性 |
| fold、input root、output root和代表病例为单折常量 | 精确两折分派，新版本输出/控制路径；代表病例按fold取，预算合计210 |

现有`execute_pair()`虽然恰好也是总210次，但不能因此直接使用：模型与病例配对含义不同。预测manifest必须写实际fold，不能沿用硬编码C；source provenance也不能仅校验C的前105行。

## 3. 不变的科研与执行合同

- 8k输入/8k输出；batch1；warmup0、TTA0、loss0、backward0、optimizer0、BNCal0。
- 顺序C后D，每个模型105例。任何失败停止，不自动继续下一模型、不retry/resume。
- 不依据训练loss筛病例、调参或选择checkpoint；只用两折冻结的最终权重。
- Native归一化输出；毫米评分后续用既有D-only frame；无GT对齐/ICP。
- 每个模型在eval/inference_mode运行；比较前后参数/BN和各RNG。Mamba初始化消耗的随机数不等于推理期间可以消耗RNG，snapshot应放在加载/构建完成后。
- 继承既有固定代表病例保存coarse数组：C7例、D5例；全量记录同次forward的几何摘要。不是新增instrumentation或代表病例扫描。
- 资源沿用预测合同：wall7200s、RSS8GiB、torch峰值20GiB、SMI22528MiB、产物1GiB、空闲磁盘4GiB；当前设备/资产未在本轮远端复核。
- 不在GPU预测任务中计算评分、bootstrap或正式gate，不重复GPU preflight。

H1仅用于训练loss，在eval中不调用loss。保留H1真实配置是为了准确复现模型身份，不能把配置关闭来迎合旧验证器，也不能放宽其他目标。

## 4. 本轮交付与剩余步骤

同目录已保存：

1. `H1_C_D_input_index_candidate_v1.json`：210个固定输入及两权重精确绑定。
2. `H1_C_D_prediction_protocol_candidate_v1.json`：预测次数、state/RNG、资源和禁止项。
3. `prediction_request_preparation_draft_v1.json`：非执行草案，`is_execution_request=false`，明确缺少最终入口哈希。
4. `compatibility_anchors_C_v1.json`、`compatibility_anchors_D_v1.json`：原代码函数行号/来源哈希。

不能生成可供执行授权的最终request，是因为原入口确定不兼容，新的入口尚未实施和验证。将不存在或未经验证的入口哈希写入“待授权request”会让授权对象不完整，容易再次发生启动校验失败。

建议下一步单独限定**implementation-only**：新增一个P2 H1两折预测入口＋针对性人工CPU测试，复用现有安全读取与checkpoint/推理函数；覆盖完整authorize/index/evidence分派、两折105计数、fold正确写入、H1唯一配置、状态/RNG及失败停止。通过P3后，再创建绑定最终入口哈希的待授权execution request。旧P1入口保持不变；不新增通用框架、不部署、不运行GPU。

这项适配是预测任务的必要小差量，不涉及新科研模块、训练或新的GPU准入循环。
