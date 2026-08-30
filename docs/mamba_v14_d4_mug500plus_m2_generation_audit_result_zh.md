# Mamba v1.4 D4 MUG500+ M2 生成完整性审计结果

> 本文档冻结 D4 M2 派生数据的独立完整性审计结论。该审计只验证数据生成、来源绑定、几何约束和文件完整性，不训练模型、不选择候选，也不访问任何保护数据。

## 审计对象

- 来源数据：冻结的 MUG500+ D4 source100 数据锁。
- 派生数据：`MUG500plusD4M2_v1`。
- 来源颅骨：100 个。
- 每个来源的缺损族：`ellipsoid_small`、`ellipsoid_medium`、`ellipsoid_large`、`irregular_medium`。
- 派生病例：400 个。
- 来源级四折：A、B、C、D，每折 25 个 dev 来源、100 个 dev 病例。

## 冻结身份

| 项目 | SHA256 |
|---|---|
| Audit protocol | `428313d35df014dab835bd474ef92cddc2d95fd988a9762e5eb3d26619117901` |
| Audit implementation | `e50aac810a210c7c1788366103c37764e9f059a640c21e5cd72dbd96b71460d7` |
| Audit tests | `33f49d4253e8a8b58a7b59d03bc5e3f14ecc125ce84f7ba0e19676ddeede3bf6` |
| D4 generator bundle | `4ac9b1cb29f46e79e5dde1adfd8abf868e8a440dd366e25237bafcc5369c7e93` |
| Source manifest | `04255c0598f56243b1a1aba8ea9c01192507f8d79e8a8cda6fbbd5f6bba2e2d1` |
| Portable manifest | `709759f5a32fe8862668b5a457f9f7be60489fcabb63fa83093fd6627278e781` |

## 完整性结果

独立审计逐例读取并验证了全部 400 个 NPZ。审计确认：

- 100 个来源 STL 均重新计算哈希并与冻结 source100 数据锁一致；
- 400 个派生文件的 SHA256 均与生成清单一致，且派生哈希两两唯一；
- manifest 与病例目录严格双射，不存在缺失病例或额外 NPZ；
- 每个来源恰好生成四种预注册缺损族，四个病例始终属于同一来源折；
- A、B、C、D 四折各包含 100 个病例，来源级互斥关系成立；
- `partial`、`implant`、`gt`、`centroid`、`scale` 和 `reference_rim_mask` 的 shape、dtype、有限性及归一化契约全部通过；
- 所有路径均已转换为可解析相对路径，便于服务器与本地恢复；
- 所有预注册几何硬门控均通过。

## 几何统计

| 指标 | 最小值 | 均值 | 最大值 |
|---|---:|---:|---:|
| Reference rim 点数 | 8 | 24.5425 | 73 |
| 移除表面积比例 | 0.00912486 | 0.03766822 | 0.20116118 |

Reference rim 的最小值恰好为协议下限 8 点。这不构成数据审计失败，但说明后续训练与评价必须预注册稀疏 rim 分层统计，避免总体均值掩盖极低支持病例。该观察不得用于回改当前数据生成规则。

## 恢复验证

服务器审计完成后，凭据归档被下载到本地并进行独立恢复验证：

- 归档字节数：381940；
- 归档 SHA256：`3959902e288ef4639e7f11709eea8286db1a9036517473f4cd29f8a7d6970fc0`；
- 归档目录清单差异：0；
- 内部 `files.sha256` 清单：3 个；
- 通过内部哈希复核的冻结文件：34 个；
- 恢复后的 100/400 规模、四折计数、几何统计和安全锁均与服务器结果一致。

## 冻结结论

审计状态为 `generation_integrity_passed_training_and_selection_still_locked`。D4 M2 数据生成完整性正式通过，但本结果不构成训练或候选选择授权：

- `D4_training_authorized = false`；
- `D4_candidate_selection_authorized = false`；
- `protected_data_used = false`。

下一步只能单独冻结 D4 候选定义、训练预算、来源级四折执行、评价指标、安全门控及选择规则。该新协议完成并通过零步 preflight 之前，不得启动训练，也不得访问 holdout、confirmation20 或 official test。
