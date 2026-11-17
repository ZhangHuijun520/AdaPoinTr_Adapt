# SPCG正式post-CUDA冻结审计

2026-11-16。状态：FORMAL_POST_CUDA_FREEZE_PASS。

request SHA256：`93ee5eb84f4e2b3b0de81e0f5b70c899c0cf2b2661f2946ffdead936c07568f6`。

本轮重新读取并核验服务器完整输出、授权链及绑定源码，共哈希10,609,260bytes；未运行模型、SMI、训练或解码真实NPZ数组，服务器无写入。

## 完整性与计数

10个新安装文件集合、大小和SHA匹配；request、授权单向runtime、单次claim一致；worker和tmux均已结束，退出码0。输出文件及五个空cache/tmp目录集合精确一致，payload_manifest无重复、成员范围及内容SHA均通过，五份real_D_00至04.npz均重新哈希匹配。

六个人工forward和五个指定训练D-only forward成功记录完整；三次loss、三次backward，零optimizer step。实际396次原生Mamba forward hook调用：G0/G1各72，G2为252。没有将CUDA执行成功解释为科学效果改善。

## 梯度与恢复

三臂训练阶段所有已记录梯度范数有限，coarse/SPCG头、encoder、decoder和FC头均有非零梯度；Q总loss梯度L2分别约0.111915、0.194068、0.161512。该梯度包含总loss，不是coarse分支独立梯度。

六阶段均记录参数未更新，eval无BN变化、train仅BN buffer变化。三臂最终恢复事件均声明state/RNG/modes为true；绑定入口在发出事件前检查state指纹、CPU/CUDA/Python/NumPy RNG与保存初态一致。

限制：运行结果保存各臂初始state指纹，但未持久化各臂完整的最终state/RNG前后指纹对。本审计基于固定源码的运行时断言和恢复事件核验，没有重新加载模型或独立重算最终RNG指纹。因此不能声称已获得独立、完整可再计算的前后RNG指纹证据；无需为此自动重跑GPU或扩展工具链。

## 资源

24条资源记录全部守卫条件通过，包括complete阶段forward=11。

| 指标 | 本次记录最大值 |
|---|---:|
| Torch peak allocated | 13,749,449,216bytes，约12.81GiB |
| Torch peak reserved | 15,007,219,712bytes，约13.98GiB |
| RSS | 2,100,903,936bytes，约1.96GiB |
| SMI显存 | 14800MiB |
| 最后资源记录墙钟 | 约25.55秒 |

未超20GiB Torch、22528MiB SMI、8GiB RSS及1800秒准入阈值。以上是零更新准入证据，不能证明3900-step训练长期资源或补全精度通过。没有升级依赖处理日志中的非阻断warning。

## 下一阶段

可以进入首折训练入口与合同准备，保持G0_C→G1_C→G2_C顺序、8k→8k、3900更新、共享母版／G1G2 head字节与同折完整批次顺序，不根据scratch输出调参。

现有SPCG runtime仅提供观测与计数辅助，并非已验证的3900-step训练短入口。后续需限定接入原训练生命周期、固定日志步数与1GiB输出预算、人工CPU验证及P3，通过后创建首个G0_C待授权request。复用本次CUDA准入，不重复preflight；训练须单独授权。

本轮未创建训练request或启动任何后续实验。机器证据见formal_audit_result_v3.json，原始回读见server_evidence.json及stdout.bin/stderr.bin。
