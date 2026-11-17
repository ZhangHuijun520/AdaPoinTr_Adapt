# SPCG G0_D 正式只读训练后冻结审计

日期：2026-11-17。状态：`FORMAL_SPCG_G0_D_POST_TRAINING_FREEZE_PASS`，41项检查全部通过。

## 范围

当前容器 `shu-common-25721452-notebook-lwwgl9-0`，uid 1000。精确绑定request SHA256：

`a877093becfd3e9763da36565c9401275e2f5ddd4f6d4f223fb4964ddf1d7fea`

本次仅只读核验服务器冻结产物、配置和日志，将原始回传与结论写入本机。未在服务器写入，未反序列化checkpoint、构建模型、调用forward、运行CUDA、重训或进入评价。

## 产物与计数

| 项目 | 核验结果 |
| --- | --- |
| 退出码／进程 | 0；worker和固定tmux均已退出 |
| forward／backward／clip／optimizer step | 各3900 |
| 完整遍历／曝光／drop | 100／31200／300 |
| metrics／几何日志／资源记录 | 3900／3900／3902 |
| 耗时 | 1538.191秒，约25分38秒 |
| 最终checkpoint大小 | 478810419 bytes |
| BNCal／evaluation／resume | 均为false |

checkpoint：

`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SPCG_G0_foldD_seed0_train_20261116_v1/ckpt-last.pth`

重新流式读取计算SHA256：

`3c6f9b213440f5af10777e98c309842f55f96ab46dbbbccf2647748ecae5f5cc`

与completion及payload manifest一致。全部产物文件集合、manifest唯一性、各文件大小与哈希、空tmp目录均符合合同；11个安装文件及复用implementation源码哈希一致。授权回执、runtime单向绑定和单次启动claim通过。

## 初始化与D折顺序

G0 raw-state初态指纹：`366e5a6c752270708d30a2459933812d92accb8bb24f84adb29a2c6a15053f46`，与request、CUDA准入及G0_C冻结依据一致。helper参数指纹和persistent-state指纹分别与G0_C一致，seed均为0。初始化身份依赖冻结源码、运行时断言和准入记录，本次未重新生成模型或读取checkpoint张量。

D折order文件原始SHA256为 `4f68edd55912be0dccfb3d2a1cc72e499d3d499a36aa5f3788550145b3095720`，训练输出副本与其字节完全一致。canonical order指纹为 `2c9f3e9afb2cfe9ae46c0566bdbced465c64acc2a564654914d2163d74e5e838`，在初始化、completion和exposure中一致；两种哈希使用不同算法，不交叉比较。

全3900步的step、epoch、batch、病例ID及来源均与100轮冻结计划一致，曝光及drop映射可完整重建。实际病例仅来自D折315训练病例、63训练来源，与21开发来源不交叉。QC、两档manifest和fold binding元数据当前哈希均符合request；本轮没有重新读取真实NPZ数据payload。

C折G0/G1/G2三份正式冻结凭据重新校验通过。本次不要求C/D批次顺序或最终权重相同：不同折使用各自预定病例及order。

## 几何、数值与资源日志

全部几何日志按step、epoch、batch及case_ids与训练记录对应，使用 `D_only_normalized` 坐标口径，记录coarse/dense中心、半径及coarse_CD/dense_CD，无非有限数值。loss分量和按实际FP32舍入口径核验，LR、BN momentum和clip参数逐步符合冻结设置。日志中的loss_sparse为0不代表coarse监督缺失。

step 1、39、390、1950、3900的总loss Q梯度记录完整，L2有限且大于0。它仅证明这些观测步骤存在总loss反向路径，不能据此声称coarse定位或接口精度改善。

3902条资源记录守卫均通过。峰值RSS为1678323712 bytes，Torch allocated为13886325248 bytes、reserved为14772338688 bytes，SMI显存14576 MiB。保留此前已披露的容器PID与SMI PID口径差异，不声称已获得GPU进程所有权保证。

## 证据与后续

同目录保存 `formal_freeze_result_v1.json`、四阶段远端只读脚本、原始stdout/stderr、结构化回传及本机哈希清单。审计结论仅确认训练完成和冻结合同成立，不能由训练loss推断补全性能。

按原矩阵，下一步准备 **G1_D** 的最小入口兼容性核对及待授权范围，绑定本次G0_D冻结证据，保持相同D折批次顺序、共同scratch母版和3900步合同，不依据本折loss调参。若需新入口，先完成限定implementation-only、CPU验证及P3。未创建或执行下一次训练request，未进入开发集预测、评分或BNCal。
