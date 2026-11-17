# SPCG G1_C 正式训练后冻结审计及 G0_C／G1_C 配对核验

日期：2026-11-16。结论：`FORMAL_SPCG_G1_C_POST_TRAINING_FREEZE_PASS`，37项检查全部通过。

## 范围与依据

本次仅通过 WebShell 只读核验当前 `lwwgl9-0` 容器内的冻结 request、安装文件、控制链及训练产物，并在本机保存原始回传和审计结论。服务器写入、模型调用、checkpoint 反序列化均为零。未训练、未重试、未运行 BNCal 或开发集评价。

绑定的 G1_C request SHA256：

`2d8ef3fff5db90653d0408ac6db72911e2c84b75aa61c9f03c8033aaf56ac0e4`

## 完成状态与实测产物

| 项目 | 审计结果 |
| --- | --- |
| 退出码 | 0；worker 和固定 tmux 均已退出 |
| optimizer updates | 3900 |
| forward／backward／clip／step | 各3900次 |
| 完整遍历 | 100 |
| 病例曝光／drop | 31,200／300 |
| metrics／SPCG geometry／resource 记录 | 3900／3900／3902 |
| 耗时 | 1510.813秒，约25分11秒 |
| 最终 checkpoint 大小 | 478,923,818 bytes |
| BNCal／evaluation／resume | 均为 false |

checkpoint 路径：

`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SPCG_G1_foldC_seed0_train_20261116_v1/ckpt-last.pth`

重新流式读取字节后得到 SHA256：

`dd5ad567eadc66ef1b47d708128f48aa2221ee1df6bbd954b830cc59a11835ce`

该哈希与 completion 及 payload manifest 一致。产物文件集合、空 tmp 目录、清单唯一性、清单大小及各文件哈希均通过。9个安装文件与冻结映射一致，复用 implementation 文件哈希一致；授权回执、runtime 单向绑定及单次启动 claim 一致。

## G0_C／G1_C 配对

逐条核对两组全部3900条 metrics：step、epoch、batch、case_ids、source_ids、LR、BN momentum 和 clip 阈值全部一致。order_plan 原始字节相同，exposure 完整映射相同；315个训练病例的实际曝光及每轮丢弃记录均可由冻结计划重建。

两组数据根、静态配置、设备身份、环境和顺序文件绑定一致。G0 既有正式冻结凭据全部通过，所引用的 G0 初始化、metrics、顺序及曝光文件重新计算哈希后未改变。

初始化核验区分两个层次：

- **共同母版**：G1 构建过程先核验同一个未训练 G0/LQI 母版 raw-state 指纹，未加载 G0 已训练权重。
- **完整 G1 初态**：替换 head 后，raw-state 指纹为 `3cfdbac9149b99e24ea6641fb9e00cf975754ad21c7a88fc6d34e17e01724ab9`，与冻结 request 和 CUDA 准入 G1 记录一致。完整 G1 与 G0 的指纹不同是结构改变的预期结果。

本次初始化结论依据冻结源码、运行时构建断言及准入证据，不在审计中重新生成模型或逐张量读取 checkpoint。raw-state 指纹与训练 helper 的参数／persistent-state 指纹算法不同，不交叉比较。

## SPCG 与资源日志

全部3900条几何日志与训练 step、批次病例一一对应，坐标口径为 `D_only_normalized`，记录 coarse／dense 中心、半径和 coarse_CD／dense_CD。日志未出现非有限值。loss 求和按实际 FP32 加法舍入口径核验，通过；不将指标日志中的命名字段误当作独立 loss 组成。

step 1、39、390、1950、3900 的 Q 梯度记录均存在，L2 有限且大于零，来源标记为总 loss，不能据此宣称独立 coarse loss 的贡献已量化。

所有3902条资源记录均报告守卫通过。峰值 RSS 为1,666,269,184 bytes，Torch allocated 为13,929,265,664 bytes，reserved 为14,805,893,120 bytes，SMI 显存为14,608 MiB。PID 口径差异按已接受的诊断性合同保留，不把它表述为已获得 GPU 进程所有权保证。

## 证据文件与后续边界

同目录保存 `formal_freeze_result_v1.json`、四阶段远端只读脚本、原始 stdout／stderr 和各阶段结构化结果。它们分别覆盖 checkpoint／清单、授权与初始化、全量日志、G0/G1 配对。

本次通过仅确认训练完成和对照合同成立，尚不能证明补全精度或接口吻合改善。下一步按冻结矩阵准备 **G2_C 待授权训练 request**，保持原始协议，不根据 G1 训练 loss 调参；本次未创建该 request，也未授权下一次训练。
