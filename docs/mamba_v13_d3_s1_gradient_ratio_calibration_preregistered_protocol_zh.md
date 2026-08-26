# Mamba v1.3 D3 S1 training-only 梯度比校准预注册修订协议

> 状态：在任何 S1 校准测量之前冻结。本阶段只测量每折唯一的 S1 辅助损失权重，不运行 S1 训练、不评价 development、不访问 locked holdout，也不启动模型选择。

## 1. 目的与独立性

S2 head-only feasibility 已以 `392/400` 命中冻结为未通过硬门控的负结果。该结果只锁死 S2 calibration 与完整 S2 训练，不改变此前独立预注册的 S1 科学问题：与评估器 2 mm 定义一致的 dense contact-existence 和 GT-rim worst-10% tail objective，能否消除 dense zero-contact。

实现哈希优先使用最初 Round-A 父锁；若父锁中的 model/contact 实现与当前源码不同，只允许由更晚的、且已被 S2 负结果回执引用的 feasibility base lock 接管。当前源码必须逐字节匹配该更晚冻结哈希，其他文件漂移仍然硬失败。这是冻结链延续，不是跳过源码校验。

S1 权重不能人工指定，也不能依据 development 指标调整。本修订协议只授权一次 training-only 梯度范数校准，校准本身不构成候选选择。

## 2. 数据与执行边界

- 仅使用冻结 `100/25` source-skull 数据锁中的 development training fold。
- 四折 `A-D` 分别有 300 个训练病例；每折只消费 seed-0 train loader 的前 8 个完整 batch。
- batch size 固定为 8，`drop_last=true`，每折恰好记录 64 个 batch slots。
- 禁止构建或遍历 dev loader；禁止访问 locked holdout、旧 monitor、confirmation20 或 official test。
- 每折只允许生成一次不可覆盖的校准目录。已有完整回执时只校验并退出；存在残缺目录时硬失败。

## 3. 模型状态

- 从冻结 S1 fold template 按 seed 0 初始化，不加载任何 checkpoint。
- S1 与 S0 参数结构相同；校准时仅暂时关闭 auxiliary weight，以获得纯 reconstruction gradient。
- Mamba adapter alpha scale 固定为 `0.0`，对应 epoch 0 第一次 optimizer step 之前的状态。
- 不构造 optimizer，不调用 `backward()` 或 `optimizer.step()`，不保存 checkpoint。
- 测量前快照模型 state 与 Python/NumPy/PyTorch CPU/CUDA RNG；测量后恢复并验证。BN running statistics 和任何参数变化都不得持久化。

## 4. 梯度比与唯一权重

每个 batch 使用同一次 forward graph 分别计算：

1. reconstruction loss 对全部可训练参数的 global L2 gradient norm；
2. unit-weight S1 auxiliary loss 对同一参数集合的 global L2 gradient norm；
3. 缺失梯度按 0 处理；
4. raw ratio 为 `aux_norm / max(reconstruction_norm, 1e-12)`；
5. fold raw ratio 为恰好 8 个 batch ratio 的中位数；
6. calibrated weight 唯一固定为 `0.075 / fold_raw_ratio`。

任何梯度范数、ratio 或最终 weight 非有限、为 0 或为负，均使该折校准硬失败。禁止 clip、round、人工修正或重跑。

## 5. 冻结凭据

每折回执必须冻结：模板与授权哈希、8 个 batch 的 case ID、case-list SHA256、两类 gradient L2、raw ratio、fold median、最终 weight、模型状态恢复和 RNG 恢复结果。四折完成凭据只有在 A-D 全部通过且 hash 链完整时生成。

四折完成后只允许下一步单独物化 receipt-bound S1 runtime configs。校准凭据本身不授权 S1 训练，不授权 S2，不授权 holdout，也不启动 selection。

## 6. 明确禁止

- 根据 development、亚组或失败病例调整权重；
- 重跑已冻结 fold 或挑选更好的一次；
- 加载 S0/S2 checkpoint 进行 S1 校准；
- 在本阶段组合 S1 与 S2；
- 自动启动 S1 training、BNCal、development evaluation 或 Round-A selection；
- 以 S2 负结果为理由修改 S1 loss、阈值、tail fraction 或门控。
