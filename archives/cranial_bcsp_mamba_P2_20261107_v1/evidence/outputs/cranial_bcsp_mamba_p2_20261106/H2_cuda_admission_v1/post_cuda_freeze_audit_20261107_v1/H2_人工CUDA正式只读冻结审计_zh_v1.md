# H2人工CUDA检查：正式只读冻结审计 v1

日期：2026-11-07。**结论：FORMAL_POST_H2_CUDA_FREEZE_AUDIT_PASS；只支持本次人工eval／autograd路径通过，不自动授权训练。**

## 1. 审计范围与结果

16组检查全部通过。当前容器、12个输出文件的精确集合／大小／SHA256与前后内容属性一致；atime不参与稳定性指纹。58项精确冻结资产（包括源码、provider／扩展、人工输入、P3、request及授权控制文件）重新哈希一致，读取约711MB，不扫描额外目录或真实数据。

8项payload_manifest成员逐一核验，其他文件为manifest本身、worker PID、退出码和日志；当前tmux和worker均不在，退出码0、无failure。新下载的12文件全部与服务器SHA256一致，原启动回读材料保留。

## 2. 精确执行合同

AUX和COUPLE各一次forward、一次loss、一次backward，共2／2／0，四条操作前claim顺序一致，无重复调用、warmup、optimizer构造或step。真实数据读取、checkpoint加载、训练及BNCal均为0。

实际采用M0原factory／六个native Mamba模块、冻结PointNet2 provider和torch.cdist原重建loss。七个native SSM导入路径与精确依赖一致，Mamba版本2.3.1。两臂共同初始化记录／mixer指纹一致，新增头1025参数及原SSM no-decay分组均符合合同。

## 3. 梯度与状态／RNG

| 项目 | AUX | COUPLE |
|---|---:|---:|
| 保存的梯度范数条数 | 356 | 356 |
| 非零梯度范数条数 | 356 | 356 |
| head W梯度范数 | 0.176744897 | 0.176744897 |
| head bias梯度范数 | 0.100000001 | 0.100000001 |
| 人工delta | 0.100037999 | 0.100037999 |
| 实际尺度s | 1 | 1.0983777 |

保存的每条梯度范数均有限且非负，head、原coarse头与encoder均有非零梯度；参数名称与分组对应。另独立核对head bias范数符合仅辅助项的SL1导数幅度，未强求两臂或重复运行的梯度逐位相同。有限Mamba backward非确定性的既有披露不变。

两臂各自的完整参数／persistent buffer哈希在F/B前后相同；CPU／CUDA RNG字节哈希和Python／NumPy RNG序列化记录前后完全一致，未恢复RNG来掩盖变化。Python／NumPy长记录另转换为紧凑SHA256用于报告，不执行或采样其状态。

模型始终eval；BN／dropout未切换train，故此检查不覆盖训练模式BN行为。人工头先核对正式训练零初始化，再在快照前统一配置固定非零参数；不加载或修改真实训练权重。

## 4. 软耦合及loss记录的一致性

从保存的delta、半径、经验中心独立核对：动态目标来自原Q；SL1 beta0.1和0.1权重；总loss只加一次辅助项；AUX实际s=1；COUPLE非中性有界软尺度；coarse质心与半径缩放关系成立。使用明确的FP32记录算术核对容差，不改变任何科学评分阈值或执行数值合同。

本机仅用stdlib解码冻结人工NPZ的两个FP32数组，核验数组哈希并重算人工GT经验中心／半径以对照日志；没有读取真实点集、checkpoint、运行模型、CUDA或backward。原CD数值及完整骨块表面误差未重新计算。

## 5. 资源记录

7条资源记录的阶段／forward计数顺序正确，所有阈值独立核对通过。采样最大RSS 1.529 GiB；torch allocated峰值 1.691 GiB、reserved峰值 1.820 GiB；物理设备使用最大 2352 MiB。

torch逻辑分配与SMI物理设备用量按各自口径记录，不要求两者相等；PID按既有合同只作诊断。该资源证据仅来自人工batch1，不能据此保证batch8训练或3900步稳定。采样间隙不构成硬隔离／连续资源上界证明。

## 6. 证据限度和后续边界

- 完整模型状态哈希已保存并比较，但人工模型张量／权重未持久化，不能从权重独立重算这些哈希。
- 未保存完整梯度张量。本次独立核验范数有限性、参数对应和辅助bias导数；每元素有限性仍依赖已绑定执行代码的检查，不能在不重跑的情况下重新求梯度。
- 本次没有新增forward／backward、优化器、状态恢复、服务器写入或真实数据读取。
- 结论是H2新路径在该设备的人工eval／autograd检查完整通过；不是训练模式BN、batch8资源准入、3900-step完整性、模型收益或临床准确性证明。
- 后续可以准备首个H2训练的精确入口／合同与待授权范围，但必须独立授权，不因本审计通过自动启动四次训练、BNCal、评价或修改参数。

## 7. 可追溯标识

request SHA256：`6e20c58d6ceee32b2f77858b9bb394535d39d999630302e0a115299e66de6e7a`。
正式机器可读报告：`formal_audit_report_v1.json`，含两臂梯度摘要、状态／RNG紧凑指纹、资源最大值及12文件完整哈希。
远端只读文件证据：`remote_file_audit_v1.json`。
全量下载：`downloads/`；所有审计调用原始stdout／stderr留在同目录。
