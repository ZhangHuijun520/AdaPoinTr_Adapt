# H2 Fold D 配对训练准备

2026-11-07。科学合同与必要服务器只读就绪核对完成，实施待单独授权；未部署或启动训练。

## 事前固定范围

按AUX→COUPLE顺序，每臂315个训练病例/63来源、8192输入/8192输出、batch8、3900步、100遍历、31200曝光、300丢弃。各自对应D折21个开发来源，训练/开发来源无重叠。科学设置沿用Fold C，只有预注册D分区和D完整顺序不同；不使用C折loss或开发成绩调参、换病例。

原Fold D M0 request及正式冻结审计哈希已核对；D原始顺序文件SHA256为4f68edd55912be0dccfb3d2a1cc72e499d3d499a36aa5f3788550145b3095720，canonical SHA256为2c9f3e9afb2cfe9ae46c0566bdbced465c64acc2a564654914d2163d74e5e838。两臂均从原M0 seed0初始化加零范围头开始，不从任何最终checkpoint resume。

## 本次只读服务器证据

当前hostname/GPU/UID与已冻结身份一致，GPU占用1 MiB，磁盘空闲10459545600字节。4个D相关元数据文件大小/哈希一致；D目录精确315个正规点集文件全部字节哈希一致，未解码NPZ或加载checkpoint。拟定的新安装根与两运行目录不存在。这是时点就绪核对，不代表独占资源预留；执行前仍需复核。

## 唯一剩余接入缺口

当前H2短入口硬编码Fold C及其M0基线/AUX配对证据，不能直接承载D。建议一次限定implementation-only：新增一个D专用两模式短入口及一个人工CPU测试文件，复用三个已冻结H2模块、原runtime及provider。实际文件策略回归应包含此前遗漏的AUX初始化JSON读取场景，精确到文件、只读、保留大小/哈希检查，不放行整个结果目录。

完成CPU验证和本机P3后，先只创建AUX_D待授权request。AUX_D训练并正式冻结后，再绑定其真实初始化及审计创建COUPLE_D待授权request。不重复GPU preflight、不扩展库存/传输框架；不自动训练或评价。

配套文件：FoldD_H2_paired_training_contract_v1.json、server_readiness_receipt_v1.json、minimal_FoldD_entry_implementation_scope_v1.json。静态AUX/COUPLE配置候选已保存，没有材料化授权回执、runtime或launcher。
