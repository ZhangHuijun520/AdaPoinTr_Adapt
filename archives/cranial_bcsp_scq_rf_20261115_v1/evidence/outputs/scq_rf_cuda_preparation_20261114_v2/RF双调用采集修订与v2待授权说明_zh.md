# SCQ-RF双调用采集修订与v2待授权说明

2026-11-14。本轮为限定本机implementation-only；没有服务器操作、部署、CUDA、真实点集／checkpoint读取或训练。

## 1. 完成情况

已修正CUDA短入口的位置编码双调用采集：同一`coordinate_pe`先接收query、再接收Memory，两次输入按顺序分别追加保存，不再共用一个可覆盖的快照。decoder的query和Memory输入也分别保存，作为相应角色的比较依据。

在所有坐标合同断言之前，持久化`COORDINATE_CONSUMERS_BEFORE_ASSERTIONS`记录，逐项包含角色、调用次数、shape、dtype、device、有限性、精确相等及最大绝对差。检查query-MLP、decoder query、第一次query位置编码、第二次Memory位置编码、FC重建条件及dense中心。仍使用精确相等，不放宽容差；缺失、多余或角色错误同样拒绝。

原短入口除`phase_checks`内的观察／断言及返回诊断字段外，其余已有顶层函数AST保持相同；仅新增一个坐标合同检查函数。RF模型、factory、冻结初始化、provider及原损失没有修改。

## 2. CPU回归与P3

一次新版人工CPU入口检查**52项全部通过**，新P3通过；此前RF隔离实现59项CPU证据保持有效。新增回归涵盖：

- 真实角色模式：同一位置编码模块先query、再Memory，shape相同、数值不同；五个阶段均记录两次调用。
- 拒绝旧版覆盖记录、缺失第二次调用、多出第三次调用、两角色颠倒、query值错误及Memory值错误六类案例。
- 六类失败均在断言前留下逐消费者诊断；保留成功与异常下的状态／RNG／模式／BN恢复检查。
- 原授权合同、计数上限、资源和POSIX launcher合同保持不变。

CPU入口使用便宜的人工模型、loss与CPU CUDA门面，未调用原生Mamba／PointNet2 CUDA。它只补齐本次观察合同及接口覆盖，不能证明CUDA或科研效果通过。

证据：[静态差量审查](static_review_v2.json)、[52项CPU结果](cpu_entry_batch_v2/result_v1.json)、[新P3](entry_P3_v2.json)。

## 3. 新request与旧尝试边界

新request状态为`AWAITING_EXPLICIT_USER_AUTHORIZATION`：

[SCQ_RF_artificial_cuda_execution_request_v2.json](pending_transport_v2/payload/SCQ_RF_artificial_cuda_execution_request_v2.json)

完整SHA256：

```text
09de6045f2ecc760558039c2c25724e94eae078b52f744aef6e25574575e1bcf
```

旧request `85854f243d29000cc7a0ee87b03f4ce23974fc92d94d6fd479fd695e68c7ab32`标记为已尝试、失败、已消耗、不得复用；其文件和失败证据不修改。新request使用全新安装根、run ID、tmux、控制及输出路径。

新安装根：`/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v2`。

新输出：`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_artificial_cuda_20261114_v2`。

新tmux：`bcsp_scq_rf_cuda_20261114_v2`。

仅7个新文件采用不覆盖安装。RF两份模型源码、RF初始化和实现P3直接复用v1已安装文件，列入精确只读复用哈希；不重新安装模型或wheel。身份仍绑定最近审计的`zbpgzu-0`与原GPU，执行前必须重新核验，漂移停止。

## 4. CUDA合同保持不变

| 阶段 | batch | forward | full loss | backward | step |
|---|---:|---:|---:|---:|---:|
| S-ref eval参考 | 1 | 1 | 0 | 0 | 0 |
| RF-Static eval | 1 | 1 | 1 | 1 | 0 |
| RF-Requery eval | 1 | 1 | 1 | 1 | 0 |
| RF-Static train模式 | 8 | 1 | 1 | 1 | 0 |
| RF-Requery train模式 | 8 | 1 | 1 | 1 | 0 |
| 合计 | — | **5** | **4** | **4** | **0** |

原人工输入／目标seed、8192点、FP32／TF32关闭、初态比较容差、原生调用次数180及状态恢复合同均不变。train模式不是正式训练；不创建optimizer、不更新权重、不读取真实数据或checkpoint。外部超时1800秒，RSS8GiB、torch峰值20GiB、SMI22,528MiB、输出1GiB、空闲磁盘4GiB等阈值不变。失败立即停止，不自动修复重跑。

## 5. 上传与后续授权

本机目录：`E:\Codex\2026-06-06\mamba-ccf-c-1-high-resolution\outputs\scq_rf_cuda_preparation_20261114_v2\pending_transport_v2`。

上传以下四个文件到`/home/jovyan/`：

1. `bcsp_scq_rf_artificial_cuda_pending_20261114_v2.tar.gz`
2. `bcsp_scq_rf_artificial_cuda_pending_20261114_v2.tar.gz.sha256`
3. `bcsp_scq_rf_artificial_cuda_pending_20261114_v2.tar.gz.bytes`
4. `bcsp_scq_rf_artificial_cuda_pending_20261114_v2.tar.gz.contents.sha256`

压缩包44,555字节，SHA256为`e9247e6f213cb1060bf7dc5ce093b371cda6128419e005d201356753527c53f7`；8个归档成员包含7个payload文件和1个安装映射。

上传后需对新request完整哈希单独授权，才能重新核验、不覆盖安装、材料化授权回执／单向runtime／launcher并提交唯一一次新尝试。本轮未创建这些执行控制文件，未执行GPU，也不自动进入训练。
