# B_C正式训练冻结审计与S_C准备结论

日期：2026-11-13。状态：**FORMAL_SCQ_POST_TRAINING_FREEZE_AUDIT_PASS**。本轮只读审计，不导入模型、不反序列化checkpoint、不运行GPU或训练；通过后仅创建S_C待授权材料。

## 1. 核心结果

| 项目 | 重新核验结果 |
|---|---|
| 执行request | `95d6dfdb07a0e64a8f80646c65f84da38ff7297344e74541000fe1dbcc899b84` |
| 退出/存活 | exit0，固定tmux结束，原worker未存活 |
| 模型/数据 | B_C原LQI，8k→8k，原63训练来源/315病例；21开发来源分离 |
| 更新/遍历/曝光 | **3900 / 100 / 31200**；300次drop事件；forward/backward/clip/step均3900 |
| 顺序 | 3900条metric与geometry逐条匹配冻结epoch/batch/case/source；原始order文件哈希与canonical绑定一致 |
| 曝光重算 | 从实际metric重新累加case/source，drop从原plan重算，均匹配exposure.json；每病例曝光+drop=100 |
| checkpoint | **478,810,419 bytes**，原始字节在服务器流式哈希两次一致，匹配completion及payload manifest |
| BNCal/evaluation/resume | 均false |

最终checkpoint实测SHA256：

`9c4352355d001404e6e43a461244b6a2134884974cf8fba616ec0065c1001418`

服务器位置：

`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_B_foldC_seed0_train_20261113_v2/ckpt-last.pth`

训练循环记录耗时约1524.32秒（25.4分钟），原监测窗口约1534.72秒。不将耗时作为正式速度基准。

## 2. 证据完整性

安装根37文件（旧24、新5及两次控制共8）与本次输出16文件，共**53文件**，两次完整内容哈希清单一致，3个目录符合预期，无额外文件/链接。安装payload和当前控制文件匹配本机冻结字节，原失败控制/证据继续保留。

下载19份非checkpoint文件到本机并逐份核验哈希。checkpoint未下载或反序列化，仅服务器流式读原始字节两次。payload_manifest精确12成员与当前输出匹配；原单向授权runtime、单次claim及实际执行request身份核验通过。

24组机器可读审计断言全部通过，完整证据见`freeze_verification_v2.json`及两份`remote_inventory_*_v2.json`。

## 3. 初始化和优化器

B模型为真实native构造，39903169参数、411个唯一训练参数记录，无SCQ新增头参数。共有初始状态摘要与正式CUDA准入记录一致：

`7d1c472d456217e362807b92b54e8f5da4451763472733683f287ede5e91d75b`

initialization.json的seed0、参数/持久状态SHA格式及order绑定有效。共有初始状态匹配来自已绑定factory构造时的记录，本次不重新实例化模型逐tensor再算，不将此说成独立恢复forward测试。

按每个参数名/shape重新核验实际weight decay：矩阵5e−4，bias/1D及22组A_log、22组D为0；AdamW实际defaults、betas/eps及foreach/fused合同一致。默认decay字段不被误读为各参数组实际decay。

## 4. 完整日志与资源

3900条metric全部finite；LR、BN momentum按原epoch公式逐条核对，clip10及已提交更新标志完整。3900条SCQ_geometry的batch/case对齐、coarse/dense质心/半径/bbox形状与有限性正确。

作为B臂，所有Q0摘要等于coarse摘要，所有Delta均为0；原coarse/dense CD日志有限，二者之和与原reconstruction loss在FP32舍入容差内一致。日志钩子没有新增forward或loss调用。

3902条resource记录（3900次after_step及before/after_final）阶段/step顺序正确，全部SMI/torch阈值由实际值重新计算通过。最大RSS约1.55GiB，torch peak allocated约12.93GiB、reserved约13.76GiB，SMI最高14576MiB；未触发原RSS8GiB、torch20GiB或SMI22528MiB阈值。

资源为采样/记录峰值，不是专属硬隔离。原runtime在本地guard执行磁盘检查，没有逐行磁盘剩余值；PID只作诊断，不以host/container编号相同作所有权保证。

## 5. 科研结论边界及下一步

本次证明B_C按既定预算完成，并具备可配对的初始化/顺序/最终权重证据；**尚未评价Native补全精度**，不从最终训练loss判断SCQ有效或无效。

S_C材料已在`S_C_pending_preparation_v1/`准备，绑定本次正式B冻结审计与model_construction，复用同设备、同初始化规则、原315训练病例、同order、loss/optimizer/资源及3900步。S从scratch构造，不加载B checkpoint，不根据B训练loss调参；没有部署或启动。

S_C request完整SHA256：

`1aed46b99b11f83b6707b1a3fe81b7e90a971ec7419019327d3c224b2d2adc86`

下一步上传S_C小包及三个校验文件后，需单独授权该完整哈希。S_C运行前仍须新鲜核验同设备/资产/资源；本次冻结审计不自动构成S_C执行授权。
