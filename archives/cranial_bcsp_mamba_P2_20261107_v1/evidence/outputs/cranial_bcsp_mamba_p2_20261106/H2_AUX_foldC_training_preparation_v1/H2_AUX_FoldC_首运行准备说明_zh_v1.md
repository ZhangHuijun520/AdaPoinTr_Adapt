# H2-AUX Fold C 首运行：准备完成，等待单独执行授权

日期：2026-11-07。

## 科研目的与边界

本运行检验：在原有 M0 编码特征上添加一个预测骨块尺度残差的辅助头，是否能改善后续补全。它是 H2 的 AUX 对照臂，生成路径不使用尺度变换；不得将辅助尺度预测改善直接解释为骨块形状或接口改善。后续需要按既定两折协议与 COUPLE 臂及冻结 M0 比较。本 request 只包含 AUX Fold C，不授权其他运行或评价。

唯一科学增量是 1024→1、共1025个参数的范围头，以及固定0.1权重的 SmoothL1 辅助项（beta=0.1）。正式训练权重和偏置全部为0；不消耗额外初始化随机数。人工 CUDA 验证中的非零头部干预仅为测试 fixture，禁止用于本训练初始化。H1 与其他可选监督保持关闭。

## 原合同保持不变

- SkullBreak 原 Fold C 训练来源63个、315病例；不访问开发集、确认集。
- 输入8192点，目标8192点；不更改缺损构造、表面采样、归一化或目标表示。
- 原 M0 从头初始化，不载入任何最终 checkpoint；精确绑定原初始化记录。
- 原完整批次顺序：batch8，100次遍历，每次39步；3900次更新、31200次曝光、300次丢弃。
- 原 AdamW、学习率、BN 日程、FP32及数值设置保持不变。
- BNCal、评价、resume及自动重试均不允许。

## 本次已完成的证据

1. 新增隔离的 H2-AUX Fold C 训练入口，复用已通过人工 CUDA 的三个 H2 实现文件；没有修改母版模型、原 factory、encoder 或原 P1 runtime。
2. S0/S1 静态检查通过。唯一一批24项人工 CPU 合同检查全部通过，包括完整 authorize()、实际 AUX adapter 分派、零初始化、H1拒绝、原数据/顺序传递及错误授权拒绝。
3. 人工 CPU fixture 明确模拟 native factory 边界；仅在测试进程内临时替换 fixture 证据标志/审计哈希，随后恢复并检查生产常量。生产入口没有人工放行开关。没有运行真实训练或真实数据 forward。
4. 本机 P3 完成。资源监测、payload路径和文件访问策略与父入口 AST 相同；三个 H2 实现哈希与既有 CUDA 准入版本一致。
5. 有界服务器只读就绪核对通过：当前 hostname/UID/GPU 身份、必要资产大小和 SHA256、原初始化元数据、315个训练点集的文件名/类型与字节哈希均一致；没有解码 NPZ 数组或加载 checkpoint。
6. 新安装目录和运行目录均不存在。核对时 GPU 显存占用1 MiB，磁盘空闲11,316,232,192字节。该快照不代表资源预留；执行前必须复核。

## 资源预算与披露

沿用原上限：墙钟86400秒，进程RSS 8 GiB，物理设备显存22528 MiB，Torch峰值20 GiB，输出2 GiB，空闲磁盘最低4 GiB。使用原每步监测和超限停止机制，不声明具备 cgroup 硬隔离或连续监测保证。PID信息仅作诊断，不跨命名空间推定进程所有权；启动仍要求固定 GPU 身份及显存占用≤256 MiB。

原生 Mamba 有限梯度非确定性按已确认政策保留并披露。既有人工 CUDA 仅验证 eval/autograd、小批人工输入；不证明 batch8训练模式BN、3900步稳定性或科研收益。此次不重复 GPU preflight。

## 待授权材料

request：`first_FoldC_request_v1/transport_payload/H2_AUX_foldC_seed0_training_execution_request_v1.json`

完整 SHA256：

```text
0ca0aeea9f918d037e5cff0e1f0e9af95ed3b17b9979ff63c6789a3672991517
```

状态：`AWAITING_EXPLICIT_USER_AUTHORIZATION`。

运输包包含13个不覆盖安装文件。原315个点集、provider、依赖和原初始化记录直接复用，不运输、不安装依赖。上传以下同目录四文件到 `/home/jovyan`：

```text
bcsp_p2_H2_AUX_foldC_pending_20261107_v1.tar.gz
bcsp_p2_H2_AUX_foldC_pending_20261107_v1.tar.gz.sha256
bcsp_p2_H2_AUX_foldC_pending_20261107_v1.tar.gz.bytes
bcsp_p2_H2_AUX_foldC_pending_20261107_v1.tar.gz.contents.sha256
```

压缩包 SHA256：`8f76cdaacd06fba2353624885fe7ea24d4b16afb949f1ee781fe33e78d279324`；大小65611字节。

本次只冻结安装映射与无授权值的 launcher 模板；未创建正式授权回执、runtime config、已授权 launcher、attempt claim或训练输出目录。上传不等于执行授权。后续需针对上述 request 完整哈希单独授权限定不覆盖安装及唯一一次训练；失败即停，不自动重试或 resume。
