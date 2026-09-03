# Mamba v1.6 D6 development400 生成与来源四折协议冻结结果

> 本结果冻结生成计划和来源级四折边界。协议锁已完成两次字节级一致复现，但 400 个派生病例尚未生成。

## 生成合同

- development source skull：100。
- 每来源缺损族：4。
- 计划病例：400。
- 缺损族：`ellipsoid_large`、`ellipsoid_medium`、`ellipsoid_small`、`irregular_medium`。
- M2 几何、采样、归一化和硬门控：逐节继承冻结的 M2 v1 协议。
- M2 engine SHA256：`88a839afffadaa4d0eaf3fa7293e2cef0fdb2cccb7beb2af5062a91fc0f3adf7`。
- base protocol SHA256：`1da529947cdce9972a2ce7881c05df891191d54026a96ed229c872cdd7e18768`。

## 来源级四折

- folds：A/B/C/D。
- 每折 dev：25 个来源、100 个病例。
- 每折 train：75 个来源、300 个病例。
- 每个来源的 4 个病例必须同折。
- source-fold leakage：0。
- 分折只依赖冻结 salt 与 source ID，不使用模型或几何指标，不允许人工重分配。

## 协议凭据

- protocol ID：`mamba-v16-d6-mug500plus-development-generation-fourfold-v1`。
- protocol SHA256：`dba67b91bf36bd509af50aa18cb15ff31b15c5552951bc96499951ffad93457c`。
- protocol lock：`mug500plus_d6_development_generation_fourfold_protocol_lock_v1`。
- D6-A slot32 zero-step parent report SHA256：`7f093b50e660e4828bec85b5c0f75ce2f6dc487198c648516b933969ff267b85`。
- development100 final-lock manifest SHA256：`ba62bbe839e044d98a1f73be2fa2d0f2973ca771ab9e0911548dd77e81376ed2`。
- development100 final-lock receipt SHA256：`97e26338d4d4bff743a20e0a830ca6e34f1c64f8dfd0de5115d91f22aec93cef`。

## 结论与下一步

协议锁已通过单元测试、拒绝路径测试、真实数据渲染、二次幂等复现和 `files.sha256` 验证。当前唯一获准的后续动作是使用该锁生成冻结的 D6 development400 数据，并在生成后执行独立 generation audit。

当前状态保持：`generation_started=false`、`gradient_calibration=false`、`training=false`、`seed1=false`、`D6B=false`、`candidate_selection=false`、`proposal_confirmation_accessed=false`。
