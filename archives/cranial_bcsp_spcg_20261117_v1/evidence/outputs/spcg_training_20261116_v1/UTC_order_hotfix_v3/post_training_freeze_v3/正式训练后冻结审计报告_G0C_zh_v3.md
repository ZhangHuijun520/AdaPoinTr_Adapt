# SPCG G0_C正式只读训练后冻结审计

2026-11-16。状态：FORMAL_SPCG_G0_C_POST_TRAINING_FREEZE_PASS。

授权request SHA256：`871c5216815d5e479446108da979e8c77ce6ea5aec2578ac0573652e51a75d63`。

## 结果与checkpoint

退出码0，worker和固定tmux已结束。精确完成3900forward／3900backward／3900clip／3900optimizer step，LR与BN各100次调度；100遍、31200次曝光、300次drop。BNCal、development evaluation、resume均未执行。本轮没有启动任何后续实验。

最终权重：

`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SPCG_G0_foldC_seed0_train_20261116_v3/ckpt-last.pth`

大小478,810,419bytes；本轮流式实测SHA256：

`baffbe5e5b0aa19274c49b9dfa4182d8053813d527c4c2f55c34b395ee00ef69`

与completion及payload_manifest一致。仅读取文件字节，未反序列化checkpoint或加载模型。

## 初态、批次与曝光

构造日志与CUDA准入G0原factory完整证据一致，绑定初始原始张量指纹：`366e5a6c752270708d30a2459933812d92accb8bb24f84adb29a2c6a15053f46`。此算法不同于helper包含shape/dtype的state指纹，未混用比较。

training initialization记录parameter SHA为`2c7d4e3094a98834ed7e2627c610b8015d183146e10270db1a2dccc56c751d8e`，persistent state SHA为`beabbeb8c06c387d6ac54c3ec1825fbe7cd6bd529428c4f79299a5525cef301b`，seed0。本审计通过冻结源码的原始张量指纹断言及factory证据校核，不重新生成模型。

输出order_plan原字节与冻结Fold C order一致，文件SHA为`6ab424177d5227bd34585a710eedca578acdd2eeb226bec10cdfc86ee89cec9d`。规范化order哈希与initialization、completion和exposure一致。

逐条核对全部3900批次的step／epoch／batch／case_ids／source_ids，每批8例；重算病例和来源曝光计数及drop Counter，与exposure.json逐项一致，315病例、63来源、31200曝光、300drop均通过。

## 数值、SPCG日志与资源

3900条metrics和3900条SPCG_geometry完整匹配同一批次。LR严格对应1e-4×max(0.9^(epoch/21),0.02)，BN对应max(0.9×0.5^(epoch/21),0.01)。所有已记录loss与梯度范数有限，clip10，原去噪项为0，原coarse／dense两项之和对应总重建loss。

第一次辅助审计将两个FP32分量转为Python双精度后直接相加，与FP32总loss用1e-9比较而触发断言；保留该记录。最终按真实训练浮点语义将分量之和舍入回FP32，3900步均精确匹配。不改变loss、指标、训练阈值或结果，也未重跑训练。

固定1／39／390／1950／3900五步的Q多样性及总loss梯度日志齐全；Q梯度为有限非零，明确不是coarse独立梯度。G0不存在SPCG head，本日志用于后续同协议配对，不能从训练loss判断G1/G2收益。

3902条资源记录全部通过。Torch peak allocated13,886,325,248bytes、reserved14,772,338,688bytes；最大RSS1,684,918,272bytes、SMI14576MiB，已记录输出最大493,138,820bytes；约1498.38秒。均未超过冻结预算。输出最大来自资源采样，不替代全部文件清单总量，但本轮完整产物清单及哈希也已通过。

## 清单与边界

8个已安装文件的集合、大小和SHA及全部request implementation复用源码哈希一致；授权回执、runtime单向绑定、单次claim通过。输出精确15文件和空tmp目录，manifest无重复、范围及成员SHA一致，无失败或额外checkpoint。

审计剩余日志载荷最初超过本机2048bytes限制，未发至服务器；缩短后继续。已完成checkpoint和初态回读复用，不重复训练。所有辅助失败与回读证据保留。

本轮服务器写入0、模型调用0、checkpoint加载0、SMI查询0。机器结果formal_freeze_result_v3.json及分阶段stdout／stderr保留。

## 下一步

可以按冻结顺序准备G1_C，保持同设备、共同母版、同Fold C order与3900步，不依据本次loss调参。当前训练入口显式限制G0_C；后续需限定适配G1 factory／head字节与日志、针对性CPU验证和P3，通过后创建待授权request，不直接训练或重复GPU准入。
