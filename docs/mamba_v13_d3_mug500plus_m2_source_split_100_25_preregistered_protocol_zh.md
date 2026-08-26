# MUG500+ M2 `100/25` source-skull 数据锁预注册协议

## 1. 协议目的

本协议只负责在 MUG500+ M2 的 125 个健康来源颅骨之间生成独立、确定且不可覆盖的 `100 development / 25 locked holdout` 划分。它建立在 protected-overlap audit v2.1 已通过的前提上，不重新解释 v1/v2 结果，也不启动 D3 训练。

## 2. 冻结输入

- M1 healthy125 数据锁；
- M2 generation audit v1 的 portable manifest、summary 和哈希清单；
- v2.1 adjudication receipt 与哈希清单。

所有输入均按预注册 SHA256 校验。划分过程不读取模型预测、模型指标、缺损难度统计或 protected dataset 数组。

预生成校验曾发现 `m2_generation_audit.files_manifest_sha256` 在人工抄录时遗漏 1 个字符。该错误在任何输出目录或 split assignment 产生前被硬门控拦截；协议已按冻结文件复算值透明修正，并新增所有谱系 SHA256 必须为 64 位的检查。

## 3. 划分单位与规模

- 唯一划分单位：`source_skull`；
- 总计：125 个来源颅骨、500 个派生病例；
- development：100 个来源颅骨、400 个病例；
- locked holdout：25 个来源颅骨、100 个病例；
- development 内 A/B/C/D 四折，每折 25 个来源颅骨、100 个病例；
- 同一来源颅骨的四种缺损必须处于同一 partition 和同一 fold。

## 4. 确定性算法

沿用 D3 初始协议在数据划分生成前已经固定的 salt：

```text
mamba-v13-d3-independent-data-v1-20260811
```

1. 为每个 `skull_id` 计算 `SHA256(salt|holdout|skull_id)`；
2. 按十六进制哈希升序取前 25 个作为 locked holdout；
3. 对剩余 100 个计算 `SHA256(salt|fold|skull_id)`；
4. 按哈希升序后依次轮转分配至 A、B、C、D；
5. 不允许人工交换病例或根据任何结果重新选择 salt。

## 5. Holdout 使用边界

数据锁可以记录 holdout 的 skull/case ID，但方法冻结前禁止：

- 对 holdout 运行模型推理；
- 计算或查看 holdout 指标；
- 对 holdout 进行结果可视化或人工比较；
- 根据 holdout 修改模型、loss、query、门控或选择规则。

后续 one-shot holdout 使用必须由单独的 method-freeze receipt 授权。

## 6. 数据锁效果

数据锁成功后只允许进入 D3 candidate protocol、配置和执行凭据的冻结步骤。`training_unlocked` 仍为 `false`，本工具不会启动训练、评估或推理。

当前状态：`preregistered_not_generated`。
