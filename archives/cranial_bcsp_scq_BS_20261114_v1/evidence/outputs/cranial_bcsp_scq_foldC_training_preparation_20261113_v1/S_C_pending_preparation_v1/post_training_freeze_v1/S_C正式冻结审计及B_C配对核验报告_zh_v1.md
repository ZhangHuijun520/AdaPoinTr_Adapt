# S_C正式训练后冻结审计与B_C配对核验

日期：2026-11-13。结论：**FORMAL_SCQ_POST_TRAINING_FREEZE_AUDIT_PASS**，30组审计检查全部通过。

本轮只读服务器产物并开展本机日志核验；没有加载模型/权重、运行forward/backward、使用GPU或修改服务器，没有新建后续执行request。

## 1. 训练完成与checkpoint实测

| 项目 | 结果 |
|---|---|
| S_C执行request SHA256 | `1aed46b99b11f83b6707b1a3fe81b7e90a971ec7419019327d3c224b2d2adc86` |
| 退出/进程 | exit0，固定tmux结束，原worker未存活 |
| 完整计数 | 3900 forward、backward、clip、optimizer step；100次LR/BN schedule |
| 遍历/曝光/drop | 100 / 31200 / 300，均从原始批次与日志重新计算 |
| S checkpoint大小 | **487,148,386 bytes** |
| checkpoint核验 | 服务器原始字节两次流式SHA256一致，匹配completion及payload manifest |
| BNCal/evaluation/resume | 均false |

S_C checkpoint SHA256：

`00f1ce94d219a42294c6c5a7874710edbd58431deac44c9522a9ab4f120d2f0b`

服务器路径：

`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_S_foldC_seed0_train_20261113_v1/ckpt-last.pth`

checkpoint只按字节哈希，未下载或反序列化；本次不验证权重内部可恢复性，不为此新增forward。

## 2. 文件与授权链

当前安装根44文件、本次输出16文件，共**60文件**，两次内容清单完全稳定。4个子目录符合预期，无额外文件或符号链接。32份安装payload全部匹配映射，当前三个控制文件匹配本机原字节，授权回执→request、runtime→授权回执的单向绑定及单次claim精确一致。

本机下载19份非checkpoint证据，全部匹配新鲜服务器大小及哈希；12成员payload manifest与当前结果一致。旧B失败、B完成及S控制文件均保留，没有覆盖或清理。

## 3. 完整顺序、曝光和SCQ日志

对3900条metrics及3900条SCQ_geometry逐条检查step/epoch/batch、case/source顺序，全部匹配冻结plan。原315病例、63训练来源与21开发来源边界正确，100次遍历每次39个batch加3个drop完整覆盖315病例。

从实际metrics重新累加case/source曝光、从plan重新计算drop，匹配exposure.json；每病例曝光数加drop数均为100。不能因此声称每个病例实际曝光次数完全相同。

逐步重算LR、BN momentum并核验clip10、有限loss及更新提交标记。原coarse CD/dense CD记录有限，二者之和与原重建loss在FP32舍入容差内相符；没有为审计重新计算模型loss。

SCQ几何摘要的coarse/dense质心、半径与bbox有限且形状正确；Q0及Delta各8个样本摘要完整，所有步骤满足：

- Qused质心−Q0质心与Delta质心相符。
- Delta均值范数不超过最大范数，Delta质心范数不超过均值范数（保留浮点容差）。
- Q0半径、Delta范数均为非负有限值。

这验证日志内部一致性，不等于从完整逐点Q0/Qused/Delta重新计算；训练中本就只保存轻量摘要。残差幅度统计保存在`freeze_verification_v1.json`的`delta_summary`，仅作描述，不据其改阈值或判断解剖精度。

## 4. 与已冻结B_C的配对核验

| 配对项目 | 核验结果 |
|---|---|
| B正式审计/构造证据 | 内容哈希匹配S request绑定 |
| 设备与软件 | 相同容器`t6ibfm-0`、GPU UUID、driver及冻结软件合同 |
| 真实输入合同 | QC、来源、315训练清单、数据根、8k/8k、静态配置均一致 |
| 初始化 | 两臂factory的原LQI parent证据一致，共有初始状态摘要一致 |
| 批次 | 3900个实际case/source批次全部相同，不仅最终order摘要相同 |
| 数值schedule | 每步LR、BN momentum、clip及提交标记相同 |
| 曝光与defaults | order_plan、exposure、optimizer_actual_defaults文件逐字节一致 |
| 原参数组 | S移除新增4参数后的411个共有参数记录与B完全一致 |
| 唯一新增参数 | SCQ的W1/W2权重decay5e−4、bias0；实测新增693507，总40596676 |
| warmstart | S为scratch构造，未加载B checkpoint |

两臂共有初始状态指纹：

`7d1c472d456217e362807b92b54e8f5da4451763472733683f287ede5e91d75b`

S的整体参数/持久状态初始SHA与B不同是新增头/buffer造成的正常现象。配对检查核对的是共有状态、完整parent构造证据和相同初始化规则，不错误要求两个不同结构的完整state字节相同。本次没有重构模型独立重算该共有指纹。

B_C最终checkpoint（此前已冻结）：

`9c4352355d001404e6e43a461244b6a2134884974cf8fba616ec0065c1001418`

## 5. 资源与局限

3902条resource记录阶段/step正确，记录值按原阈值重算全部通过。S_C峰值torch allocated约12.97GiB、reserved约13.79GiB，SMI最高14612MiB，RSS约1.55GiB，均在原预算内。原监测窗口约1530.34秒，训练循环耗时约25.4分钟。

RSS/SMI为采样值，torch为已记录生命周期峰值，不是专属cgroup硬隔离；磁盘最低余量由原guard执行，没有每步disk telemetry；PID命名空间差异只记诊断，不当作失败或设备所有权证明。

本次完成技术冻结和配对可信度核验，**未评价补全精度**。两臂最终训练loss或Delta变大/变小不能证明完整骨片覆盖、接口吻合或严重风险改善。有限梯度非位级确定性披露不变。

## 6. 下一步边界

Fold C首对B/S现已完成并正式冻结。按已锁定的C/D计划，可下一步准备Fold D的B_D待授权request，继而按阶段完成S_D；不根据C训练loss调D，不追加参数搜索、训练次数、BNCal或重复GPU准入。只有相应配对Native预测和冻结评分后才能判断效果；本轮未授权或执行这些工作。

完整机器可读结论：`freeze_verification_v1.json`。服务器两次清单：`remote_inventory_before_v2.json`、`remote_inventory_after_v2.json`。下载证据位于`output/`及`control_S_C_v1/`。审计来源：`local_tools/audit_scq_S_C_training_pair_v1.py`。

所有本机材料保存在项目输出目录；本轮没有推送GitHub、转存长期checkpoint备份或删除服务器文件。
