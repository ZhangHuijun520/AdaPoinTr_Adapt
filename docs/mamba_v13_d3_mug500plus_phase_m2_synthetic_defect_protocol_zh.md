# MUG500+ Phase M2 合成缺损生成与数据边界预注册协议

## 1. 阶段定位

本阶段是 D3 `Contact-Support Structuralization` 的数据构造阶段，不是模型训练阶段。其唯一目标是在已经冻结的 `mug500plus-m1-healthy125-v1` 上，建立一套可复现、可审计、与 D2/D2.2 失败病例隔离的合成缺损生成规则。

M2 完成前，S0/S1/S2 训练保持锁定。M2 完成后仍需通过独立 manifest 审计、受保护数据指纹重叠审计以及 100/25 skull-level 划分锁定，才允许进入 D3 训练。

## 2. 已冻结的数据边界

- 来源仅限 MUG500+ v20 的 125 个健康 A-series `clear STL`；
- 125 个 STL 必须全部来自 `mug500plus-m1-healthy125-v1` 数据锁；
- 每个文件的字节数、SHA256 和三角形数必须与数据锁逐项一致；
- 125 个颅骨必须全部通过既有几何 QC，规范化表面重复组必须为 0；
- B-series、craniotomy skulls、真实 implant、SkullBreak confirmation20、旧 monitor、official test 均不得访问；
- D2/D2.1/D2.2 的失败病例不得参与缺损位置、尺寸、权重或规则设计。

## 3. 科学问题与可证伪性

M2 不声称生成具有临床解剖标签的缺损。它只构造几何方向族，用于后续回答两个预注册问题：

1. 与 2 mm evaluator 对齐的 dense contact-existence/tail objective 是否足以消除 dense zero-contact；
2. 仅依赖 defective partial 的 rim-aware query allocation 是否能从 coarse 阶段避免 contact-support omission。

若新数据上的预注册门控失败，则冻结为负结果，不根据 development 指标回改生成器或候选规则。

## 4. 合成缺损规则

### 4.1 每颅骨四个固定族

| 缺损族 | 切向半径 U | 切向半径 V | 法向半径 | 说明 |
|---|---:|---:|---:|---|
| `ellipsoid_small` | 0.10 | 0.12 | 0.16 | 小型椭球几何缺损 |
| `ellipsoid_medium` | 0.13 | 0.16 | 0.20 | 中型椭球几何缺损 |
| `ellipsoid_large` | 0.17 | 0.20 | 0.24 | 大型椭球几何缺损 |
| `irregular_medium` | 0.14 | 0.17 | 0.20 | 主椭球并集两个固定偏移子叶 |

表中比例均相对于原始 STL 轴对齐包围盒的最大边长。每个健康颅骨必须生成四种缺损，因此预期总量固定为 `125 x 4 = 500` 个病例。

### 4.2 位置和旋转

- 使用 32 个 Fibonacci sphere 确定性候选方向；
- 位置基准由原始完整颅骨三角面中心在候选方向上的最大投影确定；
- 四个缺损族使用固定 family stride，几何失败重试使用固定 retry stride；
- 局部切平面旋转由 SHA256 派生的 PCG64 随机种子确定；
- 所有位置与旋转只依赖完整健康颅骨几何和预注册种子，不使用模型结果或受保护数据。

### 4.3 几何硬门控

- 移除表面积比例必须位于 `[0.003, 0.25]`；
- 移除三角形数至少 256；
- 剩余三角形数至少 4096；
- 最多尝试 16 个确定性位置；
- 四个缺损族必须全部成功，否则该颅骨和整次生成失败；
- 禁止静默跳过、替换病例或临时调整尺度。

## 5. 点云与归一化契约

- `partial`：从缺损后剩余表面按三角形面积加权采样 8192 点；
- `implant`：从被移除表面按三角形面积加权采样 8192 点；
- `gt`：从完整表面独立采样 8192 点；
- 参考 rim 定义为 `partial` 中到 `implant` 最近距离不超过 2 mm 的点；
- 每例至少包含 8 个参考 rim 点，最多确定性重采样 32 次；
- 归一化中心为采样后的 defective partial 均值；
- 归一化尺度为 defective partial 相对该中心的最大半径；
- 同一中心与尺度同时用于 `partial`、`implant` 和 `gt`；
- 推理端不得使用 `implant`、`gt` 或 reference rim。

输出采用固定成员顺序和固定 ZIP 时间戳的 deterministic NPZ，防止同一输入在重复生成时产生不同文件哈希。

## 6. 随机性冻结

- master seed：`20260823`；
- RNG：NumPy PCG64；
- 子种子：`SHA256(protocol_id|master_seed|skull_id|defect_type|role|attempt)`；
- 不允许覆盖已经存在的 derived case；
- 生成开始后不得修改协议 JSON 或生成器代码；
- 生成器代码哈希和协议哈希共同形成 `generator_bundle_sha256`。

## 7. 后续划分规则

生成和 manifest 审计完成后，按 source skull 而不是 derived case 划分：

- development：100 个 source skull，共 400 个病例；
- locked holdout：25 个 source skull，共 100 个病例；
- development 内四折，每折恰好 25 个 source skull；
- 同一 source skull 的四个缺损病例必须进入同一分区和同一折；
- locked holdout 在方法、候选和选择规则冻结前不可查看指标。

## 8. M2 执行顺序

1. 运行单元测试，验证几何方向、缺损门控、点采样、归一化和 deterministic NPZ；
2. 逐文件审计 healthy125 的字节数、SHA256 和三角形数；
3. 写入不可变 M2 protocol receipt；
4. 执行 `--preflight_only`，确认不会写出 derived case；
5. 归档 protocol receipt 后，另开 tmux 任务正式生成 500 个病例并显示 tqdm；
6. 对 manifest、500 个 NPZ、来源指纹和 protected fingerprints 做完整审计；
7. 锁定精确 100/25 skull-level protocol；
8. 只有第 7 步通过后才允许实现或训练 S0/S1/S2。

## 9. 当前允许与禁止

当前允许：协议检查、单元测试、healthy125 preflight、生成器哈希冻结。

当前禁止：正式生成、查看 holdout 指标、启动 D3 训练、访问 MUG500+ B-series/craniotomy 数据、根据 D2/D2.2 失败病例修改生成规则。
