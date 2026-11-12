# F0：30次 decoder-only 条件诊断

当前状态：本机实施、人工 CPU 合同验证及 P3 完成；服务器只读就绪核对通过。**GPU 诊断尚未执行，尚无条件响应结果，不能据此决定结构修改。**

## 科研问题与冻结范围

复用正式计划第9.2节、既有 Native 缓存和逐层 trace，判断固定 recipient 的 coarse/query 条件下，decoder 对 prefix 条件记忆与局部跨图条件分别是否敏感，以及响应如何沿层级和查询序列传播。保持原模型、权重、采样、点数和数值设置，不追加训练或调参。

沿用10组既定配对：C 折 recipient 来源001／donor003，D 折 recipient004／donor005；每折依次为 bilateral、frontoorbital、parietotemporal、random_1、random_2。具体编号表在 Native 之前枚举，不能声称已经证明在训练前冻结。本轮不根据评价结果更换病例。

| 干预 | Prefix 分支 | Local cross-graph 分支 | 固定项 |
|---|---|---|---|
| prefix_feature_null | 原始 F 在 norm_v 之前置零；保留 learned LayerNorm beta、recipient S 的 PE 和排序 | recipient F/S | recipient z/Q/X、权重 |
| prefix_donor | 成对替换 donor F/S，经 recipient 模型对应层 norm_v、坐标 PE、donor S 排序 | recipient F/S | 同上 |
| local_graph_donor | recipient F/S | donor F/S；重新计算 KNN(8, S_donor, Q_recipient) | 同上 |

decoder 的原接口共用 F/S，直接替换其 memory 参数会混合两种干预。因此新增专用、可移除的精确前置钩子，分离两路；不修改已冻结科研模型源码。

10组×3条件＝30次 decoder 调用、30次原重建头调用；每次16个 self-SSM＋8个 conditional-SSM，合计720次原生 SSM 调用。新增 whole-model、encoder、coarse、query 初始化、Native 重放、loss、backward、optimizer step、BNCal 均为0。模型可以构建并严格加载完整最终权重，但不执行其整体 forward。

## 读出与解释

重建头完整沿用母版：干预后的 decoder 特征经 increase_dim 和全局 max、reduce_map、原 SimpleRebuildFC（含其自身 max pooling），最后加上固定 Q。缓存 z 属于 query 之前的 backbone global feature，不能代替重建头重新池化出的特征。

每条件保存 dense/coarse 与40份逐层数组。共30份预测 NPZ、30份 trace NPZ；每条件输出8层×（5个全体阶段＋prefix_suffix 的 early/middle/late 三组）＝64行响应，共1920行。query 按 recipient Q 的固定字典序分组，区间为[0,86)、[86,171)、[171,256)。

比较 max absolute、mean absolute、RMSE、relative L2 和 allclose；固定 atol=1e-6、rtol=1e-5，relative L2 分母下限1e-12。不把其他模型／设备测得的零噪声宣称为本次实测噪声底，不因响应为零而判运行失败。

第一层 after_self 应与保存的 Native 一致；local-only 干预的第一层 prefix_suffix 也应一致。隔离检查失败即停止。后续层的 prefix 输出可能因为前层局部干预传播而改变，不能要求所有层均不变。

全部结果为离线 OOD 条件敏感性诊断，**不是正式 Native 性能**。dense 同槽位位移不是 Chamfer、覆盖率或临床接口误差。仅关联既有冻结 Native 指标作背景，不读取 GT payload、不重新评分。无响应不证明条件无用，有响应也不证明条件利用正确。由于本轮固定 z/Q/X，不能单独证明训练中 coarse 偏移的因果来源。

正式运行结束后先完成独立只读冻结审计，再讨论最小结构假设；不自动实施结构修改或追加训练。

## 已完成验证

- 人工张量合同34项通过：真实冻结 F0 decoder 和母版 FC 头，使用人工因果 mixer／人工上下文；覆盖三路隔离、donor KNN、固定上下文、原头重算、状态／CPU RNG、异常钩子清理、完整 authorize 路径与拒绝合同。
- 入口集成7项通过：轻量人工 suffix 替身，验证实际入口的30次循环、60份 NPZ、1920行响应结构、两模型状态／RNG记录、首错停止及第五个精确源码的实际加载策略。
- 上述 CPU 验证不构成实际 Mamba／CUDA 条件响应已通过，也不构成科研效果证明；不重复既有 GPU preflight。
- 两次有界服务器只读调用通过：hostname `shu-common-25721452-notebook-zv9bqd-0`、UID1000；RTX4090D UUID `GPU-41b45aa3-f5e3-e609-53cb-9c48bc7716ed`，当时显存占用0 MiB、磁盘可用12,396,265,472 bytes。40份缓存、两份权重及复用相关文件共54个身份核对通过，哈希读取1,119,921,260 bytes；没有解码数组、加载权重、导入 ML、写服务器文件或启动 CUDA。
- 本机 P3 已汇总最终源码哈希、两批 CPU 证据和就绪证据。服务器新安装根与输出根核对为不存在；执行前仍须重验。

## 待授权执行与运输

最终 request SHA256：

`a21965cdefdf4a7903b5cb52b235dc5e30f0cd9d25a25915734967ee6ff7eda2`

request 状态保持 `AWAITING_EXPLICIT_USER_AUTHORIZATION`。

本机运输目录：`frozen_pending_transport_v1`，上传以下四文件至 `/home/jovyan/`：

1. `bcsp_f0_CD_condition_diagnostic_pending_20261111_v1.tar.gz`
2. `bcsp_f0_CD_condition_diagnostic_pending_20261111_v1.tar.gz.sha256`
3. `bcsp_f0_CD_condition_diagnostic_pending_20261111_v1.tar.gz.bytes`
4. `bcsp_f0_CD_condition_diagnostic_pending_20261111_v1.tar.gz.contents.sha256`

压缩包20,841 bytes，SHA256 `dd6f12dd86911e9e4aeb69589e31e01fac15d40bb9bc3413290ee84043575769`。共8成员：7个拟安装文件＋不覆盖安装映射。

单独明确授权上述 request 完整哈希后，才可核验上传及当前资源、不覆盖安装7文件，并按授权回执→回执哈希→runtime→launcher→单次 claim→唯一 tmux 尝试的顺序执行。当前未材料化任何已授权回执、runtime、launcher 或 claim。

沿用7200秒、RSS8GiB、Torch显存20GiB、SMI22528MiB、输出1GiB、磁盘余量4GiB上限。PID查询只作诊断，不恢复已放弃的宿主机 PID 归属硬断言。首个异常、隔离失败或资源越界即停，不自动重试或 resume。
