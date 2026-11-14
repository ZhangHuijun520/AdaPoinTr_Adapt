# B_D正式只读训练后冻结审计

日期：2026-11-13。状态：**FORMAL_SCQ_POST_TRAINING_FREEZE_AUDIT_PASS**，27组检查通过。

本轮只读回查服务器文件并在本机审计日志；未导入模型、加载/下载权重、运行CUDA或修改服务器。审计通过后仅准备S_D待授权request。

## 1. 完成与权重身份

| 核验项 | 结果 |
|---|---|
| 执行request SHA256 | `4f1db753d12693eb909d5d795997b542ca7a2082b73b6737521a1154f1777ed4` |
| 退出状态 | exit0、固定tmux结束、原worker未存活 |
| 完整更新 | forward/backward/clip/step各3900，LR/BN scheduler各100 |
| 遍历/曝光/drop | 100 / 31200 / 300，逐条原始记录重算一致 |
| 权重大小 | **478810419 bytes** |
| 权重核验 | 服务器原始字节两次流式SHA256一致，匹配completion和manifest |
| 后续执行 | BNCal/evaluation/resume全部false |

实测checkpoint SHA256：

`f4bdd386c78eb3ebd7e764e9166761d18c3381acf0b0dc2ac91472533f5faf82`

服务器路径：

`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_B_foldD_seed0_train_20261113_v1/ckpt-last.pth`

只对checkpoint原始字节进行核验，未反序列化内部tensor/optimizer；不将本次审计称为模型恢复forward验证。

## 2. 清单与只读证据

安装52文件及输出16文件，共**68文件**，两次内容清单完全一致。5个目录符合预期，无额外/链接成员。原32安装payload、新4文件和当前3控制文件匹配冻结本机字节，原控制/历史失败凭据均保留。

19份非checkpoint回读全部匹配当前服务器大小及SHA256；12成员payload manifest完整。授权单向绑定、原request与唯一claim正确，不依据atime变化推断内容变化。

## 3. 初始化、批次和曝光

原B_D模型实际39903169参数、411个唯一参数组记录，无SCQ新增参数。构造记录与B_C原LQI构造相同，包含共有初始状态指纹：

`7d1c472d456217e362807b92b54e8f5da4451763472733683f287ede5e91d75b`

B_C/B_D完整初始参数及持久状态SHA记录一致，optimizer实际defaults及参数分组文件逐字节一致。共享初始化匹配由绑定factory记录及初始化回执核验，本次未重建模型独立重算完整tensor。

使用首个C训练前已冻结的FoldD数据合同：63训练来源315病例，21开发来源分离。3900条metric与SCQ_geometry的step/epoch/batch/case/source逐条匹配原D plan；不是错误沿用C plan。

D order canonical SHA256：

`2c9f3e9afb2cfe9ae46c0566bdbced465c64acc2a564654914d2163d74e5e838`

从metrics累加病例/来源曝光、从plan累加drop，均匹配exposure；每病例曝光+drop为100，但不把实际曝光次数说成每例完全相同。315训练payload的执行前哈希通过回执已绑定，无dev payload准入。

## 4. loss、几何与资源

3900步原LR/BN公式、clip10、loss有限及已提交更新标志全部核验。原coarse/dense loss钩子日志逐步相加与重建loss在FP32容差内一致。

几何日志形状/有限性、case对齐和bbox一致性通过；B_D的Q0摘要与coarse相同、Delta摘要全0。无额外监督、forward或loss调用。

3902条资源记录阶段/step正确、原阈值重新计算全部通过：torch peak allocated约12.93GiB、reserved约13.76GiB，SMI最高14576MiB，RSS约1.55GiB，监测窗口约1530.55秒；训练循环耗时约25.4分钟。

资源记录是采样/峰值证据，不是独占硬隔离；原磁盘guard未逐步保存磁盘剩余量，PID只作诊断，不声称host/container编号一致。

## 5. 结论与后续

B_D按既定训练预算完成，冻结证据完整，可作为同折S_D的配对基线。尚未取得Native开发评价，不能由训练loss判断补全质量。

S_D待授权request已绑定本次audit/construction，保持同设备、相同scratch共有初始化、同FoldD数据/顺序及3900步，不加载B权重、不据C/D loss调参。没有安装或启动S_D，也未运行BNCal/evaluation。

本目录`freeze_verification_v1.json`为完整机器可读结论，`remote_inventory_before_v2.json`及`remote_inventory_after_v2.json`为两次服务器清单，`output/`和`control_B_D_v1/`保存回读证据。审计来源：`local_tools/audit_scq_B_D_training_v1.py`。
