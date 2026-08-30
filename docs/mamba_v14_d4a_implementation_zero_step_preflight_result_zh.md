# Mamba v1.4 D4-A implementation 与 zero-step preflight 冻结结果

## 1. 结论

D4-A proposal 路径的实现与 zero-step CUDA preflight 已通过。该阶段只验证冻结的 13D 几何描述符、proposal head、case-balanced BCE、反向传播和 top8 + conditioned FPS24 selector，不构成训练、开发集评估或候选选择。

本结果授权的下一步仅为：单独生成并冻结 D4-A head-only training execution authorization。它本身不授权也不启动训练。

## 2. 冻结实现

- candidate：冻结原始顺序中的全部 8192 个 normalized partial points。
- descriptor：13D，包括 normalized xyz、到 16-NN centroid 的 offset、16-NN 距离 mean/population-std/max、covariance eigenvalues/trace（升序）和 radial norm。
- proposal head：`13 -> 128 -> 64 -> 1`，两层 GELU，无 dropout。
- loss：每病例正负类别等权的 binary cross entropy。
- selector：score top8 强制保留，在 score-ranked top256 pool 中以 top8 为条件执行 deterministic Euclidean FPS，再选择 24 个点，共 32 个。
- tie break：score 相同时按 candidate index；FPS 距离相同时按 score rank，再按 candidate index。

## 3. Zero-step 执行

- device：NVIDIA GeForce RTX 4090 D，CUDA。
- folds：A/B/C/D，共 4 折。
- probe：每折恰好 1 个 training case，共 4 个互异病例。
- backward passes：4。
- optimizer constructed：false。
- optimizer steps：0。
- model updates：0。
- checkpoint loaded/written：false / false。
- dev cases accessed：0。
- holdout/protected data accessed：false / false。
- candidate selection started：false。

四个 probe case 为：

- fold A：`mug500plus__A0001__ellipsoid_large`
- fold B：`mug500plus__A0001__ellipsoid_medium`
- fold C：`mug500plus__A0001__ellipsoid_small`
- fold D：`mug500plus__A0002__ellipsoid_large`

这些病例均从相应 fold 的 training case ID 集合中按冻结规则确定。随机初始化下的 selected-hit 只作为路径观测，不作为 gate，也不参与任何选择。

## 4. 通过的实现检查

- chunked 13D descriptor 与 full-cdist reference 一致。
- proposal head 输出与 case-balanced BCE backward 有限。
- 所有可训练参数均得到有限且非零的梯度总范数。
- selector 返回 32 个互异、位于 top256 pool 内的索引，并强制保留 top8。
- backward 前后参数哈希完全相同。
- 未构造 optimizer，未执行 optimizer step。
- 未加载或写入 checkpoint。
- 未读取 dev、holdout 或其他保护数据。

## 5. 冻结凭据

服务器输出目录：

`logs/mamba_v14_d4_contact_support/d4a_zero_step_preflight_v1`

冻结文件 SHA256：

- `zero_step_preflight_receipt.json`：`20b728a1760d906bf89076c5991730275557065c98762c2e6d2ac0d673b91dfc`
- `fold_probe_metrics.csv`：`b3fff3299b8e3f4354a09f9aa552e88386ca57f3ebef8163a42d357e5916cde2`
- `zero_step_preflight_report_zh.md`：`68d177bbf52c98b7a6b06a478786790b5150916e5a94d93aa0dba18fee623dfc`
- `files.sha256`：`85c9f8a322b975a8a79b31ed2ef9f1b3421c635bdf2de75bc335153df7d16a74`

实现 SHA256：

- preflight protocol：`73ecfc9e13bf9284d1b1bcaf0b8357a3235402684348e4a6e3cd9f0f5553eade`
- proposal module：`954adaddc8e73ac614cc0309c4516a75e39d93de344221d61052b799d1f41f9a`
- preflight runner：`13efabd723adad6ae804ff190a2dfabd4e5ee34cddf4d35a136405aaab520397`
- deterministic tests：`c3a5c8cefdae6835f087972ba70be47ed2ea107547931372cc20b18a8809d3db`
- launcher：`62b6d293577a2b437fbad90b5d004e44450f2076d136f231889044f2e3151069`

## 6. 边界与下一步

本阶段没有评价 D4-A 的学习能力，也没有证明 selected-32 对全部 400 个 out-of-fold case 都包含 positive candidate。因此当前仍有：

- `D4A_training_authorized=false`
- `D4_training_authorized=false`
- `D4_candidate_selection_authorized=false`
- `protected_data_accessed=false`

下一步必须使用单独的、receipt-bound 的 D4-A training authorization，固定四折、seed 0、50 epochs、final-epoch-only head、每折一次 one-shot dev evaluation 及 all-case hard gate。在该授权冻结前不得启动训练。
