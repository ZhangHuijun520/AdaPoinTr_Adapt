# SCQ-RF人工CUDA短入口与待授权request

2026-11-14。当前状态：`AWAITING_EXPLICIT_USER_AUTHORIZATION`。本轮仅完成本机准备、一次人工CPU入口合同验证、P3和运输包冻结；未连接服务器、部署、运行CUDA或训练。

## 1. 固定执行范围

| 顺序 | 模型与模式 | batch | forward | 原完整loss | backward | optimizer step |
|---|---|---:|---:|---:|---:|---:|
| 1 | S-ref eval参考 | 1 | 1 | 0 | 0 | 0 |
| 2 | RF-Static eval | 1 | 1 | 1 | 1 | 0 |
| 3 | RF-Requery eval | 1 | 1 | 1 | 1 | 0 |
| 4 | RF-Static train模式 | 8 | 1 | 1 | 1 | 0 |
| 5 | RF-Requery train模式 | 8 | 1 | 1 | 1 | 0 |
| 合计 | 五个阶段 | — | **5** | **4** | **4** | **0** |

train模式仅用于人工张量的零更新loss／backward及BN恢复检查，不是训练实验。输入与目标都是固定seed生成的8192点人工张量；不读取真实点集、GT文件、checkpoint或历史权重。采用实际原生Mamba、PointNet2及原PyTorch `cdist` loss，不安装、编译、升级或下载依赖。

RF两头零初始化时，Qraw=Q1=Q2。参考forward只执行一次；两臂eval与同进程S-ref比较，沿用atol=1e-6／rtol=1e-5。两臂train模式不另做参考forward。没有warmup、decoder-only调用或额外干预。

## 2. 关键检查

- 全部模型共有参数包含原SCQ，五次构造中逐tensor哈希相同；仅新增RF头从共有比较中排除。Static／Requery新增头使用相同冻结字节，seed与初始化不变。
- 原生S-ref预计40,596,676参数，RF两臂预计40,827,847参数；执行时测量并严格核对，CPU人工模型参数量不能替代。
- 每个完整forward记录实际query-MLP、decoder q_pos、坐标编码、FC条件及dense中心，验证最终coarse／Q2真实进入完整路径。
- 四次backward记录Q2及两头逐参数梯度，先落盘后断言；零输出层下W1／V1梯度为零、W2／V2有效是正确预期。原有35个共有模块梯度分组保留。固定非零诊断头的上游可导性已由CPU验证，不追加GPU调用。
- 记录原生SSM optimizer分组与no-decay标记，调用精确继承的分组函数，不构造optimizer。
- 预期22个原生Mamba模块、总计180次原生模块forward hook调用，对应5次完整模型forward。不能把模块调用数写成180次模型预测。
- 每阶段成功或失败均恢复模型state／BN buffer、Python／NumPy／CPU／CUDA RNG、train/eval模式及BN动量，清理梯度和诊断引用。失败即停，不自动重试或resume。

## 3. 本机验证与证据限度

RF隔离实现人工CPU **59项通过**；本次短入口人工CPU **37项通过**，入口P3通过。入口检查使用小型CPU模型、替代loss与CPU CUDA门面，验证真实phase engine、计数、授权合同、恢复及精确读取包装器；没有运行原生Mamba或GPU。

入口CPU的两个人工共有梯度组不代表原生35组已经通过；完整8192点原loss和完整替代计算图的证据来自此前RF实现59项检查。**CPU通过不代表CUDA、显存或科研效果通过。**

- [入口CPU结果](cpu_entry_batch_v1/result_v1.json)
- [入口P3](entry_P3_v1.json)
- [交付清单](pending_delivery_v1.json)

## 4. 资源、身份与执行边界

固定外部超时1800秒，TERM后10秒KILL；RSS上限8GiB，torch allocated／reserved峰值各20GiB，SMI显存上限22,528MiB，输出上限1GiB，磁盘空闲至少4GiB；初始SMI显存占用≤256MiB。沿用资源监测与超限停止，不声称独占cgroup硬隔离或基于SMI PID确定归属。

绑定最近正式审计身份`shu-common-25721452-notebook-zbpgzu-0`及GPU `GPU-dabcc897-ac69-efac-4438-a6186dea9aaa`。该绑定是历史证据，**不是本轮已确认在线**。安装前必须重验当前身份、上传包、所有复用源码／provider／配置／依赖哈希、目标不存在及父路径链接状态；启动前再次重验资源、已安装文件与固定tmux不存在。漂移立即停止，不自动重绑定。

新安装根为`/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v1`，输出为`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_artificial_cuda_20261114_v1`。12个安装文件全部不覆盖写入。任何服务器任务不使用Windows路径执行。

获得单独完整哈希执行授权后，才能按授权回执→回执SHA256→单向runtime→launcher→独占claim→tmux的顺序材料化。当前没有这些执行控制文件。日志父目录先于重定向创建；调用保留原文件字节、原始输出字节和退出码。

## 5. 待授权request

[SCQ_RF_artificial_cuda_execution_request_v1.json](pending_transport_v1/payload/SCQ_RF_artificial_cuda_execution_request_v1.json)

完整SHA256：

```text
85854f243d29000cc7a0ee87b03f4ce23974fc92d94d6fd479fd695e68c7ab32
```

本request只覆盖限定不覆盖安装和唯一一次上述人工CUDA准入，不授权训练、BNCal、真实开发集预测或自动追加调用。完成后仍需正式只读post-CUDA冻结审计，再讨论训练准备。

## 6. 上传四个文件

本机目录：`E:\Codex\2026-06-06\mamba-ccf-c-1-high-resolution\outputs\scq_rf_cuda_preparation_20261114_v1\pending_transport_v1`。

将以下四个文件上传至服务器`/home/jovyan/`，不需要单独上传payload目录：

1. `bcsp_scq_rf_artificial_cuda_pending_20261114_v1.tar.gz`
2. `bcsp_scq_rf_artificial_cuda_pending_20261114_v1.tar.gz.sha256`
3. `bcsp_scq_rf_artificial_cuda_pending_20261114_v1.tar.gz.bytes`
4. `bcsp_scq_rf_artificial_cuda_pending_20261114_v1.tar.gz.contents.sha256`

压缩包895,438字节，SHA256为`1193e0fde217ffd4059c17272d194b022964e390f56c4d8d0b7ba53936edf7ce`，共13个成员：12个payload文件和1个安装映射。安装映射与request相互可核对，但授权回执和runtime不存在反向哈希循环。
