# H2 人工 CUDA 短入口：协议、CPU验证与待授权说明 v1

日期：2026-11-07。状态：**AWAITING_EXPLICIT_USER_AUTHORIZATION**。本轮仅本机准备；未连接服务器、部署、使用GPU、加载真实权重或训练。

## 1. 唯一执行范围

两个由原M0 factory从零构建的人工模型：H2-AUX与H2-COUPLE，各一次forward、一次loss、一次backward，合计 **2 forward／2 backward／0 optimizer step**。不构造optimizer，不warmup，不额外复跑，不读取真实点集或checkpoint。

每次batch1，输入8192、GT8192、coarse256、dense8192。使用既有真实PointNet2 provider、Mamba与原torch.cdist重建loss后端，不能换后端绕过失败。原先接受并披露的有限Mamba梯度非确定性继续保留：本次要求有限、非零的关键梯度，不要求AUX／COUPLE梯度逐位相等。

## 2. 模式与状态语义

采用 **eval＋enable_grad**，而非inference_mode，也非训练模式。BN／dropout维持eval；调用原始eval forward得到(coarse,dense)，在无去噪合同下组合成原loss所需的四元组：`(coarse, coarse[:,:0], dense[:,:0], dense)`。不新增forward，不切换BN模式。

先确认新头按正式训练合同为全零，再给这两个**人工模型**统一设置 `weight=1e-3/1024`、`bias=0.1`，以覆盖非零软耦合及辅助梯度路径。该设置发生在状态／RNG快照之前；不代表正式训练初值，也不涉及已训练权重。

随后保存每臂的完整参数／persistent buffer指纹以及Python、NumPy、CPU、CUDA RNG指纹；F/B后原样核对，**不通过恢复状态或RNG掩盖变化**。梯度可产生，但权重／BN不得更新；关键head、coarse头、encoder梯度需有限且非零。所有已有梯度均检查有限。

这是H2新增路径的准入，不验证训练模式BN、batch8资源、3900步稳定性、跨seed可靠性或科研收益。即使通过，也不自动获得四次训练授权。

## 3. 人工输入与数据边界

固定文件：`artificial_h2_input_v1.npz`。仅含 `partial`／`target` 两个8192×3 FP32数组，由解析椭球螺旋与解析曲线生成；不是颅骨病例，也不是对真实数据作脱敏变换。

SHA256：`48d63827a1724e8b3f758af8463bae54840df102a0c39e11e6158e0227c1a566`，152,710 bytes。服务器只加载这份冻结字节，不重新计算三角函数生成输入，避免跨版本输入差异。公式和数组哈希见 `artificial_fixture_definition_v1.json`。

读取策略只允许该精确人工NPZ；真实NPZ、NRRD、STL、checkpoint等payload不在allowlist。既有模型／provider源码只按原精确绑定使用，不扩大通用库存或真实数据权限。

## 4. CPU验证与P3

新增8项人工CPU入口检查全部通过：固定人工文件校验；完整2F／2B／0路径；BN／完整状态／RNG指纹不变；非零COUPLE而AUX不耦合；无optimizer；builder和loss失败计数／停止；授权／runtime单向绑定；原优化器分组与输出不覆盖。

CPU调用冻结父模型实际forward／get_loss函数体，但局部算子、encoder、decoder和loss使用人工组件，**不等于真实Mamba、PointNet2、Chamfer或CUDA通过**。原H2实现的33项检查及三个最终模块哈希同时绑定，未修改其源码。

入口P3状态：`LOCAL_H2_CUDA_ENTRY_CPU_P3_PASS`。生产bootstrap、精确provider／源码策略及资源监测复用既有P1路径，未在本轮对服务器执行。两个failure-injection属于人工CPU验证，不是GPU执行尝试或科研重试。

## 5. 设备与资源预算

request绑定此前核验并完成冻结特征任务的 `shu-common-25721452-notebook-1lvq9b-0`，GPU UUID为`GPU-4009474d-3c21-c7a6-b03d-7b46cebafa52`、4090 D／driver570.190。**这些是冻结期望，不是本轮新观测**；未来部署／启动前必须重新匹配，不得在容器更换后直接执行。

wall上限900秒，为两次native构建／F/B留保守预算，不是运行时保证。RSS8GiB、torch峰值20GiB、设备使用22528MiB、输出1GiB、空闲磁盘至少4GiB；初始设备使用不超过256MiB。PID只作诊断，不重新引入平台无法证明的跨namespace所有权合同。

失败即停，不自动修复、重试、resume、追加forward/backward或更换输入。唯一tmux、launch claim、输出和控制文件路径均已冻结；安装只能不覆盖写入。

## 6. 授权与运输

待授权request：`H2_artificial_cuda_execution_request_v1.json`。

完整SHA256：

```text
6e20c58d6ceee32b2f77858b9bb394535d39d999630302e0a115299e66de6e7a
```

运输包：`bcsp_p2_H2_artificial_cuda_pending_20261107_v1.tar.gz`，173,395 bytes。

SHA256：`0b9a746712e100dffc22dce2706df4db3e62260d7bdc0dbfe4b3be3cdcb5b61d`。

包内10文件：CUDA入口、三个H2模块、人工NPZ及定义、两份P3、request、单次launcher模板。无真实数据／checkpoint，无已授权回执、runtime或已材料化launcher。

请上传压缩包及同名 `.sha256`、`.bytes`、`.contents.sha256` 至 `/home/jovyan/`。上传不是执行授权。单独明确授权完整request哈希后，才可做必要核验、不覆盖安装、按“授权回执→哈希→runtime→launcher”材料化并唯一启动；本轮均未执行。

完成后必须正式只读冻结审计，再决定是否满足H2训练准备的数值／路径条件。CPU或CUDA准入都不能证明完整骨块或接口改善。
