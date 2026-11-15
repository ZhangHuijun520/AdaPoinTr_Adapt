# SCQ-RF v3正式post-CUDA冻结审计报告

2026-11-14。仅开展正式只读审计，未导入torch或模型、未重生成初始化、未运行forward／loss／backward、未修改服务器文件或准备训练。

## 1. 正式结论

**SCQ-RF v3人工CUDA零更新验证正式冻结审计通过，27项检查全部满足。** 本次确认冻结RF-Static／RF-Requery路径在当前原生Mamba、PointNet2及PyTorch cdist后端能够执行规定人工forward／loss／backward，并满足计数、梯度、恢复及资源合同。

这不证明真实颅骨补全精度、接口吻合或可靠性改善，也不自动授权训练。旧v1／v2失败记录保留，v3的成功不改写前两次历史。

授权request完整SHA256：

`8a3d0173fa3cec9e737e384c9af99f37e996c79ef3e60bb5e99b14dc275f2cac`

当前核验容器为`shu-common-25721452-notebook-zbpgzu-0`，GPU为`GPU-dabcc897-ac69-efac-4438-a6186dea9aaa`。退出码0，原worker与固定tmux均已结束。

## 2. 文件、授权及初始化

本次有界只读采集32个文件、唯一内容4,768,750字节，服务器采集在60秒预算内。包含8个输出文件、8个安装payload和4个控制文件、8份相关复用源码／初始化及上传压缩包与3个校验文件。

两次读取的哈希及dev／inode／mode／size／mtime／ctime指纹一致，排除atime干扰。全部回读内容与服务器新鲜哈希一致，安装文件与冻结映射一致；授权回执、单向runtime、launcher和唯一claim与本机材料化字节匹配。

`payload_manifest.json`所列completion、construction、events、resources四成员与新鲜哈希一致；日志、PID、退出码及manifest自身也纳入完整清单。没有失败文件、额外产物或仍在写入的任务。

两种初始化均与request及本机原件匹配，逐参数块SHA256与来源清单一致，解码值有限，输出层为零：

| 初始化 | 字节数 | SHA256 |
|---|---:|---|
| 原SCQ第一头及Pfix | 2,784,780 | `e7858ee3ae4c0bf6d68e447727c36514f5bbab42b95e1935f1686620ec089416` |
| RF第二头 | 924,684 | `a4024fbdb49feb41c609ae1171f04c2cb14ab794fc3663855d81395c6a1ea79e` |

修订后的加载器源码及新P3哈希与实际安装文件相符。原CUDA入口、RF factory、原SCQ、LQI及继承helper也重新读取核验。审计使用标准库解析既有初始化字节，没有调用随机值生成函数。

## 3. 精确执行计数与原生模型

| 阶段 | batch | forward | full loss | backward | step |
|---|---:|---:|---:|---:|---:|
| S-ref eval参考 | 1 | 1 | 0 | 0 | 0 |
| RF-Static eval | 1 | 1 | 1 | 1 | 0 |
| RF-Requery eval | 1 | 1 | 1 | 1 | 0 |
| RF-Static train模式 | 8 | 1 | 1 | 1 | 0 |
| RF-Requery train模式 | 8 | 1 | 1 | 1 | 0 |
| 合计 | — | **5** | **4** | **4** | **0** |

37条事件严格匹配五阶段顺序与13个调用前claim；没有warmup、decoder-only调用、optimizer构造／step、真实点集／checkpoint读取、BNCal或开发集评价。

原生模型实际参数为S-ref **40,596,676**，RF两臂 **40,827,847**，各增加231,171参数。五次构造的共有初始状态哈希相同，包含原SCQ，只排除新增RF头。两臂eval与同会话S-ref初态比较通过。

22个原生Mamba模块的hook计数逐项匹配：6个encoder及8个decoder self模块各10次、8个conditional模块各5次，合计180次。这对应5次完整模型forward，不是180次病例预测。7个原生依赖导入来源均在冻结清单内。

原生optimizer分类记录也匹配参数总量，显式SSM no-decay例外保留，RF新增weight／bias分类正确；没有创建optimizer。

## 4. 坐标、梯度与恢复证据

五个阶段中，query-MLP、decoder query、第一次query位置编码、第二次Memory位置编码、FC重建条件和dense中心共六类比较全部精确相等，最大绝对差均为0。位置编码共享模块严格调用两次，query与Memory角色分别记录，没有覆盖快照。

四次反传的35组共有模块梯度范数由逐参数记录独立重算，全部有限且有效。Q2梯度有效；原SCQ的W2和新增RF的V2 weight／bias梯度有效，W1／V1梯度为零，符合两头输出层零初始化预期。逐头记录与完整梯度清单一致，没有将初始隐藏层零梯度误判为失败。

各阶段记录的参数未变，eval RNG前后指纹相同；train模式仅BN统计发生预期临时变化。所有阶段的状态、Python／NumPy／CPU／CUDA RNG、模块模式及BN动量恢复和梯度清理记录均为true，事件与completion逐条一致。

审计验证的是已绑定执行代码、事件、指纹及断言的一致性；进程退出后未重新加载模型，不能声称独立恢复了运行时内存来复演这些检查。初始两臂输出／人工loss相同也不说明重查询有效或无效，因两头均为零输出初态。

## 5. 资源复核

28条资源记录的阈值全部重新计算通过，五个阶段均有恢复后样本，监测日志从before_construction至complete完整结束。

| 项目 | 已记录最大值或最小余量 | 冻结阈值 |
|---|---:|---:|
| RSS | 1,906,741,248字节，约1.78GiB | ≤8GiB |
| torch peak allocated | 13,601,458,176字节，约12.67GiB | ≤20GiB |
| torch peak reserved | 14,852,030,464字节，约13.83GiB | ≤20GiB |
| SMI显存占用 | 14,651MiB | ≤22,528MiB |
| 最小空闲磁盘 | 8,862,564,352字节 | ≥4GiB |
| 监测区间 | 约26.34秒 | ≤1800秒 |

监测区间不含整个本机运输和准备过程，也不是benchmark。torch为阶段内记录峰值，SMI／RSS为采样值；这些证据不是独占硬隔离或连续物理峰值保证。

## 6. 后续边界

可以回到正式计划的训练准备，不必重复本次GPU准入。建议下一步仅核对同设备首个**S-ref Fold C**训练入口与3900-step合同，再准备待授权request；RF-Static／Requery的首对或三臂训练仍应按既定顺序和独立授权执行。

本轮没有创建训练request、材料化训练配置／launcher或启动训练，不因CUDA通过自动进入真实数据实验。

机器可读结果及完整证据清单：[freeze_verification_v3.json](freeze_verification_v3.json)。
