# Mamba v1.5 D5 development100 合成生成与来源级四折预注册协议

## 1. 本阶段目的

本阶段只冻结 D5 development100 的合成病例生成规则和来源颅骨级四折。它不生成病例、不实现模型、不训练、不选择候选，也不读取 proposal-confirmation25 或 completion-holdout25 的几何数据。

## 2. 数据边界

- development：绑定已通过最终 QC 的 100 个来源颅骨。
- proposal confirmation：仅绑定冻结的 25 个来源 ID 文件 SHA256 和未访问状态。
- completion holdout：仅绑定冻结的 25 个来源 ID 文件 SHA256 和未访问状态。
- 三个分区必须来源互斥；本阶段禁止解压、检查或派生两个 sealed 分区。

## 3. 合成病例

严格继承 M2 v1 的 surface sampling、缺损位置、四类缺损几何、几何硬门控和归一化规则。每个 development 来源固定生成四个病例：`ellipsoid_small`、`ellipsoid_medium`、`ellipsoid_large`、`irregular_medium`，共 `100 × 4 = 400` 例。

## 4. 来源级四折

使用冻结 salt 对 100 个来源 ID 计算 SHA256 排序键，再按 A/B/C/D 轮转分配。每折恰好 25 个 dev 来源和 75 个 train 来源；同一来源的四个病例必须始终处于同一折。

折分不使用几何难度、模型输出或人工调整。任何 salt、来源成员或病例族变更都需要新协议，而不能覆盖本锁。

## 5. 授权边界

协议锁通过后只授权一次独立的、冻结参数的 development400 合成生成。生成完成后必须进行独立完整性审计。在审计通过前，D5-A/D5-B 实现、训练、候选选择以及两个 sealed 分区访问全部保持锁定。
