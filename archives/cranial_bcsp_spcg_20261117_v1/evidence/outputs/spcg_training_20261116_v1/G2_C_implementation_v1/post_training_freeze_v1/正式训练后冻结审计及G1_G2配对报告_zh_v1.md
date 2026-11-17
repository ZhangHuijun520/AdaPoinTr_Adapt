# SPCG G2_C 正式训练后冻结审计及 G1_C／G2_C 配对核验

2026-11-16。结论：`FORMAL_SPCG_G2_C_POST_TRAINING_FREEZE_PASS`，机器可读审计结果中的全部检查通过。

## 审计边界

当前容器为 `shu-common-25721452-notebook-lwwgl9-0`，uid 1000。绑定request完整SHA256：

`f55806333bf52eef358aa718a77b3e7bbc58f2dd59e5de341d56f8ab9df73322`

本轮仅通过WebShell读取精确绑定的产物、配置和日志，在本机保存证据。checkpoint仅流式读取字节计算哈希，未反序列化；服务器写入、模型调用、CUDA执行均为零。未重试训练、运行BNCal、开发集评价或创建后续request。

## 完成状态与checkpoint

| 项目 | 核验结果 |
| --- | --- |
| 退出码 | 0；worker及固定tmux会话已退出 |
| forward／backward／clip／optimizer step | 各3900次 |
| 完整遍历／病例曝光／drop | 100／31200／300 |
| metrics／SPCG geometry／resources记录 | 3900／3900／3902 |
| 总耗时 | 1536.839秒，约25分37秒 |
| 最终checkpoint大小 | 478923818 bytes |
| BNCal／evaluation／resume | 均为false |

最终checkpoint服务器路径：

`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SPCG_G2_foldC_seed0_train_20261116_v1/ckpt-last.pth`

本次重新实测SHA256：

`7b0ee55071b8a4d3d916e9324fd306c5edcdea4079f3c30851591f99651376d8`

与completion及payload manifest一致。产物文件集合、manifest唯一性、各文件大小与哈希、空tmp目录均符合合同。10个安装文件及复用implementation源码哈希符合冻结映射。授权回执、runtime单向绑定和唯一启动claim通过核验。

## G1_C／G2_C配对

两组完整初始化记录相同，包括参数指纹、persistent-state指纹、seed和order指纹。与CUDA准入一致的raw-state初态指纹为：

`3cfdbac9149b99e24ea6641fb9e00cf975754ad21c7a88fc6d34e17e01724ab9`

两组共享同一未训练LQI母版与H初始化字节。G2按冻结factory安装局部k=8聚合head，删除原coarse head，只替换首次coarse生成的一个表达式；head为1845763参数，替换净增8963。相同state字节不意味着聚合公式相同或训练后权重相同。

初始化身份依据冻结源码、运行时构建断言和准入证据；本次未重新构建模型。raw-state与helper参数／persistent-state指纹是不同算法，分别按对应口径比较。

逐条比较全部3900条metrics：step、epoch、batch、case_ids、source_ids、LR、BN momentum和clip阈值一致。order_plan原始字节完全相同，完整exposure字典相同。训练实际病例及曝光可由固定315病例、63来源和100轮计划重建，300次drop与计划一致。

两组优化器默认值和逐参数分组完全一致；数据根、静态配置、资源阈值、设备身份、环境、U/H、母版源码、scratch母版指纹及science合同一致。G1正式冻结凭据有效，其初始化、metrics、顺序、曝光、构建和优化器证据重新核验哈希未改变。G0/G1冻结凭据、U、H和母版源码当前哈希均与request一致。

## SPCG与资源日志

3900条SPCG日志与metrics及order按step、epoch、batch、病例逐条对应；坐标口径为D-only normalized。记录coarse/dense中心与半径、coarse_CD/dense_CD，无非有限数值。loss加和采用与训练实际一致的FP32舍入核验，没有修改loss定义。

指定step 1、39、390、1950、3900均有总loss Q梯度记录，L2有限且大于零。该记录属于总loss，不能单独归因为coarse loss。日志核验不等于证明局部Memory被有效利用或几何精度改善。

3902条资源记录的守卫均通过。峰值RSS为1666289664 bytes；Torch allocated为13930625536 bytes、reserved为14810087424 bytes；SMI显存14612 MiB。继续披露容器PID与SMI PID口径差异，未把诊断性PID记录表述为GPU进程所有权认证。

## 本机证据与下一步

同目录保存 `formal_freeze_result_v1.json`、五阶段远端只读脚本、原始stdout/stderr、各阶段结构化结果及本机SHA256清单，覆盖产物、绑定与初始化、全日志、G1/G2配对、U/H与父凭据。

至此Fold C的G0/G1/G2三组训练均已有正式冻结证据。按原矩阵，下一步应准备 **G0_D专用入口兼容性核对及待授权request**；若需入口适配，先完成限定implementation-only、CPU验证及P3。不得依据本折训练loss调参、选择病例或宣称G2补全效果改善；正式效果仍需完成预定矩阵与统一Native评价。
