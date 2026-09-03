# Mamba v1.6 D6 development100 合成生成与来源级四折预注册

> 本阶段只冻结生成与四折规则，不生成病例、不校准、不训练，也不访问 proposal-confirmation25。

## 生成规则

- 来源固定为 D6 final QC lock 中的 100 个 development 来源。
- 每来源生成四种冻结缺损：`ellipsoid_small`、`ellipsoid_medium`、`ellipsoid_large`、`irregular_medium`。
- 总计 `100 × 4 = 400` 个 deterministic NPZ 病例。
- 完整继承 M2 v1 的 surface sampling、location、defect families、geometry hard gates 和 normalization，禁止在 D6 中修改。
- 输出不可覆盖；生成后必须运行独立 generation audit，审计通过前禁止 calibration 和 training。

## 来源级四折

- 以 source skull 为分组单位，固定 salt 为 `mamba-v16-d6-development100-source-fourfold-v1-20260903`。
- 按 `SHA256(salt|fold|source_id)` 排序后 A/B/C/D round-robin 分配。
- 每折固定 25 个 dev 来源、75 个 train 来源，即 100 个 dev 病例和 300 个 train 病例。
- 同一来源的四个病例必须同折，每个来源恰好一次作为 dev，source leakage 必须为 0。
- 折分配不得使用几何难度、生成结果或模型指标，不允许人工重分配。

## 权限边界

- proposal-confirmation25 仅绑定冻结 ID 哈希，geometry、extraction、derived generation 和模型访问均为 false。
- 协议锁通过后只授权 development400 冻结生成，不自动开始生成。
- D6-A R0/R1 implementation 已冻结；gradient calibration、seed-0 training、seed-1、D6-B、candidate selection 和 official test 继续禁止。
