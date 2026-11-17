# SPCG六模型预测入口实施与首批CPU验证状态

2026-11-17。已新增隔离预测入口，复用既有Native630尝试／资源／状态与RNG／归档函数，接入G0、G1、G2构建与coarse/dense-only输出，绑定六组冻结权重及210份唯一输入元数据。未部署服务器或运行真实预测。

唯一一批24项人工CPU验证在第8项实际G1 factory构建期间停止，前7项通过：六份冻结证据、630索引与来源分折、manifest／坐标绑定、异常索引拒绝、授权链和身份／预算拒绝。G0人工模型构造、人工checkpoint严格加载和一次人工forward已执行；未完成三臂构建检查，未进入630次人工循环。

限定原因：factory.replace_forward直接按source参数打开源码；测试传入的q仍含服务器mother_source.path，而其他exact读取已由本机别名映射。于是factory试图在Windows打开/home/jovyan/.../models/AdaPoinTr.py，产生FileNotFoundError。这是人工fixture路径适配遗漏，没有证据支持科研模型或CUDA失败。

最小后续范围：仅在人工build fixture的q副本中将mother_source替换为同哈希本机record，再做静态复核和一次新的版本化CPU批次。生产入口、factory、模型及冻结服务器路径保持不变。先获得该限定修订及新版CPU批次授权，不能复用失败批次。

失败产物和哈希保存在CPU_batch_v1及CPU_failure_freeze_v1.json。本次未自动修改或重跑；CPU验证未通过，未汇总通过P3，未生成最终execution request、运输包或执行内容。
