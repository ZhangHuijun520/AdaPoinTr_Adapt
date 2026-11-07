# H2 Fold D 专用入口与首个 AUX_D 待授权request

2026-11-07。实施、33项人工CPU检查和本机P3全部完成。未连接服务器、部署、训练或重复GPU preflight。

## 实现与验证

新增一个Fold D专用两模式短入口及一个针对性CPU测试文件；AUX模式不读取前一AUX初始化，COUPLE模式要求正式冻结的AUX_D request、审计和初始指纹。两模式都锁定原M0 D基线、D训练来源与完整顺序，拒绝C折及不匹配模式。未来COUPLE实际分派还核对全量初始参数及持久state指纹与AUX_D一致。

实际文件策略使用pair_read_roots：AUX返回空列表；COUPLE先校验初始化JSON大小/哈希，再只将该精确文件加入只读根。回归在子进程内启用实际audit hook，覆盖原缺失根拒绝、精确读取成功、相邻文件及写入拒绝、秘密/payload拒绝和哈希检查。CPU33项一次通过，包括两模式完整authorize路径、实际五坐标消费者、loss及D数据顺序分派。人工模型facade不代表实际Mamba/CUDA训练验证。

母版模型、factory/encoder、三个H2模块和训练runtime未修改。原payload/file policy、资源监测及计数守卫AST保持不变。新入口只完成fold与mode的必要分派及对应证据/配置验证；不扩展通用框架。

## 固定科研合同

AUX_D仍为63来源/315训练病例，8192输入/8192目标，batch8，100遍历，3900更新，31200曝光，300丢弃。原M0 seed0 scratch初始化之后新增1025参数全零范围头，不加载任何最终checkpoint。辅助项weight0.1、SmoothL1 beta0.1、H1关闭；AUX没有坐标耦合。原优化器、BN/LR、数值设置和全部资源上限不变。不依据Fold C训练loss或成绩调参、筛病例。

已有COUPLE人工CUDA证据复用，不重复。有限Mamba梯度非确定性及采样式资源监测、PID仅诊断口径限制继续披露。原Fold D只读就绪证据已绑定为历史快照；部署执行前必须重验身份、GPU、空间、全部新目标、复用资产及315个点集哈希。本轮没有新的服务器核对。

## 最终待授权request

完整SHA256：

```text
efba40fdc78db788798ba326d9a393c5e0cac48189bb507a8ec4e9fe1d5f2db9
```

状态：AWAITING_EXPLICIT_USER_AUTHORIZATION。仅AUX_D；COUPLE_D尚未创建，须待AUX_D完成并正式冻结后再绑定。

运输包：bcsp_p2_H2_AUX_foldD_pending_20261107_v1.tar.gz，60068字节；SHA256：`53faa00c363145cc16413af174d861bdf32659ed77eb176c3ee531c83bcb9bc3`。包含11个不覆盖安装目标，不重复运输数据、权重、provider或三个H2模块。

请将AUX_D_pending_request_v1目录中的tar.gz、.sha256、.bytes、.contents.sha256四文件上传到/home/jovyan，然后针对上述完整request SHA256单独授权不覆盖安装与唯一一次训练。上传不代表执行授权。

本轮未材料化正式授权回执、runtime、已授权launcher、single-attempt claim或训练输出目录。包内为无授权值的launcher模板。失败即停，不自动重试、resume、评价或BNCal。
