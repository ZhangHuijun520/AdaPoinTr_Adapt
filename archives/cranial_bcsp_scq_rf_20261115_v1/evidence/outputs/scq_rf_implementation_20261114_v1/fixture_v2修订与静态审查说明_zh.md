# RF人工CPU测试fixture v2修订说明

2026-11-14。本轮仅修订测试并静态审查，不导入候选模块、不执行测试、不连接服务器或使用CUDA。新版状态为`AWAITING_EXPLICIT_USER_AUTHORIZATION`，P3尚未通过。

## 已完成的限定修订

- 新增`test_scq_rf_cpu_v2.py`，保留旧v1源码、失败产物和P3未通过记录。
- 在完整人工模型诊断副本内，将原SCQ第一头的W2.weight设置为固定sin序列乘0.002；两臂使用完全相同的值，保留原诊断bias。生产模块、冻结初始化及零初态等价检查均不变。
- 在第二头零输出初态、第二头非零诊断态、完整8192点原损失反传后三个位置，先落盘逐参数梯度，再执行断言。完整损失的Q2与两个头八个参数分别判断，避免组合断言掩盖失败位置。
- 梯度证据包含是否存在、是否有限、非零元素数、L1、L2和最大绝对值；非有限时不把NaN写入JSON数值。记录存入新输出目录的`gradient_evidence_v2.jsonl`。
- no-decay回归只提取并调用精确继承runtime中的`optimizer_groups`函数，不导入或启动训练runtime。人工fixture检查显式`_no_weight_decay`矩阵、普通矩阵、向量、实际以`.bias`结尾的二维参数及冻结参数，再验证RF分组保留共有矩阵的显式豁免。
- 使用全新`cpu_batch_v2`目录，当前尚未创建；旧失败批次不复用。失败即停，不自动修复重跑。

## 静态检查结论

UTF-8源码语法与AST检查通过；RF两份实现、初始化二进制／清单及旧失败证据哈希保持不变。静态检查只证明修订已落盘且接口可以解析，不证明新断言会通过，也不改变旧P3未通过状态。

待授权范围见[CPU_validation_scope_v2.json](CPU_validation_scope_v2.json)，绑定最终测试与静态审查SHA256。执行应使用已明确的本机PyTorch CPU环境，唯一一次人工批次，不读取真实点集或checkpoint、不执行optimizer step。完成后才依据保存结果做新P3复核。

## 本轮文件

- [新版测试](test_scq_rf_cpu_v2.py)
- [静态核对与不可变材料清单](static_review_v2.json)
- [待单独授权的CPU验证范围](CPU_validation_scope_v2.json)

没有创建CUDA执行请求、训练请求或服务器部署包。
