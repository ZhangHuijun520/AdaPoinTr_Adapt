# Mamba v1.2 D2.2 局部 rim 实现补充协议 v1

> 状态：在任何 D2.2 候选训练前预注册。本补充只消除实现歧义，不改变候选、数据、权重、容差、硬门槛、排序字段或停止规则。

## 适用协议

- 主协议：`mamba-v12-d22-local-rim-trust-v1`
- 主协议 Git tag：`mamba-v12-d22-preregistered-protocol-v1`
- 保护集：`confirmation20`、旧 monitor、official test，仍全部禁止访问

## 冻结澄清

### Radius epsilon

Trust region 中的 `epsilon` 固定为 `1e-6 mm`。在归一化半径公式中逐 case 使用：

```text
epsilon_normalized = 1e-6 / normalization.scale
```

### Final 非劣效 margin

排序第 8 项固定为以下三个归一化门槛占用量的最大值，越小越优：

```text
max(
  delta_final_cd_l1_mm / 0.10,
  delta_final_hd95_mm / 0.50,
  -delta_final_nsd_at_1mm / 0.01
)
```

其中 delta 始终为 `candidate - same-fold/same-seed R0` 的 420-case 聚合均值差。该排序项只在全部硬门槛已通过的候选之间使用。

### GT-rim cache

- validity preflight 使用 evaluator 同一 world-mm 定义生成全 8192 点布尔 mask
- 缓存只避免重复计算，不改变 point set、阈值或 reduction
- 每个 mask 使用确定性 `.npy` 编码并记录 SHA256
- manifest 记录 `case_id`、`normalization_scale`、point count 和 mask SHA256
- 训练读取时逐文件校验 SHA256、shape、dtype 和 point count

### R0 teacher cache

- `cache_sha256` 固定定义为按 `case_id` 排序后的 canonical JSON `entries` 字典 SHA256
- cache JSON 文件另有独立的完整文件 SHA256 sidecar
- canonical JSON 使用 `sort_keys=True`、禁止 NaN、UTF-8 和末尾单个换行
- checkpoint/config 分别记录路径与 SHA256
- cache 必须覆盖且仅覆盖当前 fold-train case set

## 不变项

- R0/R1/R2 定义不变
- `rim_band=2 mm`、`dead-zone=5 mm` 不变
- `lambda_rim=lambda_trust=0.01` 不变
- SmoothL1 `beta=0.1` 不变
- centroid/radius trust 容差不变
- 4-fold、seed 顺序、硬门槛和 one-shot 规则不变
- 不允许任何扫描、D2.2b 或 protected-split 反馈
