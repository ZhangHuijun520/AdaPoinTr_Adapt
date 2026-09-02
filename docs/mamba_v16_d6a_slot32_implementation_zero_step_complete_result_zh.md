# Mamba v1.6 D6-A slot32 implementation 与 artificial zero-step 完整结果

> 本阶段只实现和验证 D6-A R0/R1 机制。所有输入均为无 D6 身份的人工张量；未下载、提取或读取 D6 geometry，未生成 D6 病例，未构造 optimizer，未训练，未访问 confirmation 或其他 sealed 数据。

## 1. 冻结科学问题

D5 V1 在 400 个 development case 上由 V0 的 `322/400` 提升到 `368/400`，但 scalar top-32 仍有 32 个 rank-tail miss。D6-A 只允许检验一个结构变化：在保持 8192 candidates、32 proposal、D5 V1 27D descriptor 与 shared point representation 不变的条件下，以 32 个 slot 的联合全局唯一 assignment 替代单一 scalar top-32。

R0 是精确 D5 V1 reference，不具备推进资格。R1 是唯一实验候选。

## 2. R1 实现

R1 包含：

- `27-64-64` shared point encoder；
- mean/max 128D global context；
- `219-128-64-1` shared point calibration branch；
- 32 个 64D learnable slots；
- 一层单头 slot-to-point cross attention；
- `64-128-64` FFN；
- `32 x 8192` slot-conditioned pointer logits；
- shared point calibration logits 作为 pointer bias；
- deterministic maximum-weight rectangular linear assignment。

R1 trainable parameters=`94,529`，通过预注册的 `<=100,000` 参数门控。R0 trainable parameters=`42,433`。

Final inference 对 32 个 slot 运行全局 assignment，必须输出 32 个不同 candidate indices。训练 hard-forward 使用完全相同的 assignment；soft-backward 使用固定温度 `1.0` 的 row-softmax straight-through estimator。因此 loss forward selected set 与 inference selected set 一致。

GT `reference_rim_mask` 只允许进入独立 loss/scoring API。`infer_indices(descriptors)` 的签名不接收 GT，人工测试已验证不存在 GT inference leakage。

## 3. 实现测试

全部测试通过：

- R1 参数数不超过 100,000；
- 相同输入重复运行得到相同 assignment；
- 每例恰好 32 个 unique indices；
- global assignment score 不低于被禁止的 slot-order greedy；
- 全相等 tie case 固定返回 candidate indices `0..31`；
- STE forward 与 hard inference assignment 完全一致；
- 提高 positive logit 会降低 `L_support`；
- collapsed slots 产生正的 collision penalty；
- separated sharp slots 降低 `L_shape`；
- empty positive mask、NaN/Inf、短输入和错误 candidate count 均 hard fail；
- tiny artificial optimization 可学习到包含 positive 的 assignment；
- inference API 不含 GT 参数。

## 4. SciPy compatibility amendment

原机制协议将 SciPy 精确钉死为 `1.11.x`。服务器实际环境为 `1.15.3`，正式 forward 尚未开始且 D6 access=`0`。因此在执行前签发只覆盖依赖版本约束的 amendment：

- 原值：SciPy `1.11.x`；
- 修订值：SciPy `>=1.11,<2.0`；
- required API：`scipy.optimize.linear_sum_assignment(..., maximize=True)`；
- 每次正式执行前必须重跑 determinism、tie、uniqueness、global-optimum 与 hard-forward/inference-equivalence tests。

该 amendment 未改变 architecture、assignment、tie rule、slot/proposal budget、loss、parameter gate、数据权限或未来门控。

Amendment SHA256：`5c5cd38d7dd2386c9886a007f4318be5328bac014c50f94b31dd713bb9890914`。

## 5. 正式 artificial CUDA zero-step

服务器环境：

- Python：`/opt/conda/envs/adapointr-mamba/bin/python`；
- PyTorch：`2.4.1+cu118`；
- SciPy：`1.15.3`；
- GPU：NVIDIA GeForce RTX 4090 D。

执行结果：

- artificial cases：4；
- R0/R1 forward passes：8；
- R0/R1 backward passes：8；
- selected indices：每例 `32/32` unique；
- losses 与 gradients：全部 finite；
- optimizer constructed：`False`；
- optimizer steps：`0`；
- model updates：`0`；
- checkpoint loaded/written：`False/False`；
- parameter state hash before/after：完全一致；
- D6 cases accessed：`0`；
- D6 geometry accessed：`False`；
- protected/sealed accessed：`False`。

随机初始化下的 selected-hit 仅验证路径，不构成效果 gate，也不用于模型选择。

## 6. 正式哈希链

### Mechanism lock

- mechanism protocol：`2fff4782d429a3ea70607560bee9f464fb7b4eb7cea261376a91eb648a72f284`
- mechanism receipt：`acd62da63f0788ed2cbca2d48a49114c4cf8cd89b49a878d7fcba94e7ecd2a89`
- mechanism `files.sha256`：`4cbad1016851057152ad536bb69462df9a2c0b3d2440780336e3f24ac69d1a12`

### Implementation

- `utils/mamba_d6a_slot_allocator.py`：`2e71ff22800a8215001de6fb8963c3016b5056763b0e905a8149180578a75d43`
- implementation tests：`94e8933fd45b80864e62f009afdf3043d35529f7f62f7a5f6c0870f5b1c86a00`
- zero-step protocol：`cc2796f679c989bb3c345cb7a3fd628e7aa81d642c204bba31e1b8cb8f7a2895`
- zero-step runner：`be0982332db9ef9c7cbac85ed7827a2b1fb320c42d6e4c6a494a7fd0a460f12c`
- Linux execution script：`b794447b88c6a2b38a1fb5c596e4f0172bfdfa094fe3e430fda48b87f450d7ea`

### Server zero-step result

- result `files.sha256`：`8d8495a30421f143aef4f660169a0777cffcecc5e11a53f396ee1de6fccfbbf9`
- receipt：`63271b3567d3ad06994e63b67eac0d7f2f006055a5b93bb2ea1e1fe23efa8c7a`
- artificial metrics：`e2368eeee94152233e57b05f1d40ceb2ac87d58e23d4e3ebff49160297307709`
- result report：`cb581d6fb06b0e8bb213d854c92135eb3323859b46fe400b48221fcde77301b1`

## 7. 结论与权限

D6-A mechanism implementation 和 artificial CUDA zero-step 通过。该结果只证明代码路径、梯度、assignment、唯一性、确定性和权限边界正确，不证明 R1 在 D6 上有效。

下一步只允许下载并校验冻结的 D6 development100 ZIP，随后通过单独协议进行 model-independent extraction/QC。当前仍禁止：

- D6 derived generation；
- gradient-ratio calibration；
- R0/R1 seed-0 training；
- seed-1；
- proposal confirmation25 extraction/access；
- D6-B；
- candidate selection；
- protected 或 official-test access。
